from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import schemas, services, models
from ..database import get_db
from .auth import get_current_user
import os
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/asr",
    tags=["transcription"]
)

# 配置上传文件保存的路径
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/transcribe/file", response_model=schemas.TranscriptionTaskOut)
async def transcribe_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    hotword_list_id: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传音频文件并创建一个转写任务
    """
    # 文件类型验证
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp3"]
    content_type = file.content_type
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"不支持的文件格式: {content_type}，请上传mp3或wav格式文件"
        )
    
    # 保存文件
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # 创建数据库任务记录
    db_task = models.TranscriptionTask(
        user_id=current_user.id,
        filename=filename,
        status="pending"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # 写入文件
    with open(file_path, "wb") as buffer:
        file_content = await file.read()
        buffer.write(file_content)
    
    # 添加后台任务（模拟异步处理转写）
    background_tasks.add_task(
        services.TranscriptionService.process_transcription_task,
        db=db,
        task_id=db_task.id,
        file_path=file_path,
        hotword_list_id=hotword_list_id
    )
    
    return schemas.TranscriptionTaskOut.model_validate(db_task)

@router.get("/tasks/{task_id}", response_model=schemas.TranscriptionTaskWithSegments)
def get_task_result(
    task_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取特定转写任务的结果
    """
    # 查找任务
    task = db.query(models.TranscriptionTask).filter(
        models.TranscriptionTask.id == task_id
    ).first()
    
    # 处理错误情况
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 确认权限
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此任务"
        )
    
    # 获取任务的分段结果
    segments = db.query(models.TranscriptionSegment).filter(
        models.TranscriptionSegment.task_id == task_id
    ).order_by(models.TranscriptionSegment.segment_id).all()
    
    # 构建响应
    result = schemas.TranscriptionTaskWithSegments.model_validate(task)
    result.segments = [schemas.TranscriptionSegmentOut.model_validate(segment) for segment in segments]
    
    return result

@router.get("/tasks", response_model=List[schemas.TranscriptionTaskOut])
def get_user_tasks(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    """
    获取当前用户的所有转写任务
    """
    tasks = db.query(models.TranscriptionTask).filter(
        models.TranscriptionTask.user_id == current_user.id
    ).order_by(models.TranscriptionTask.created_at.desc()).offset(skip).limit(limit).all()
    
    return tasks 