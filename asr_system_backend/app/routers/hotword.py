from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models
from ..database import get_db
from .auth import get_current_user
import csv
from io import StringIO

router = APIRouter(
    prefix="/hotwords",
    tags=["hotwords"]
)

@router.post("", response_model=schemas.HotwordOut)
def create_hotword(
    hotword_in: schemas.HotwordCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的热词
    """
    # 查询用户当前的热词数量，检查是否达到上限（假设上限为100）
    count = db.query(models.Hotword).filter(models.Hotword.user_id == current_user.id).count()
    if count >= 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="热词数量已达上限（100个）"
        )
    
    # 检查是否已存在相同的热词
    existing = db.query(models.Hotword).filter(
        models.Hotword.user_id == current_user.id,
        models.Hotword.word == hotword_in.word
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="热词已存在"
        )
    
    # 创建新热词
    db_hotword = models.Hotword(
        user_id=current_user.id,
        word=hotword_in.word,
        weight=hotword_in.weight
    )
    db.add(db_hotword)
    db.commit()
    db.refresh(db_hotword)
    
    return db_hotword

@router.get("", response_model=List[schemas.HotwordOut])
def get_user_hotwords(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的热词列表
    """
    hotwords = db.query(models.Hotword).filter(
        models.Hotword.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return hotwords

@router.put("/{hotword_id}", response_model=schemas.HotwordOut)
def update_hotword(
    hotword_id: str,
    hotword_in: schemas.HotwordUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新热词
    """
    # 查找热词
    hotword = db.query(models.Hotword).filter(models.Hotword.id == hotword_id).first()
    
    # 处理错误情况
    if not hotword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="热词不存在"
        )
    
    # 确认权限
    if hotword.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此热词"
        )
    
    # 如果要更改词本身，检查是否会导致重复
    if hotword_in.word is not None and hotword_in.word != hotword.word:
        existing = db.query(models.Hotword).filter(
            models.Hotword.user_id == current_user.id,
            models.Hotword.word == hotword_in.word
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="热词已存在"
            )
        hotword.word = hotword_in.word
    
    # 更新权重
    if hotword_in.weight is not None:
        hotword.weight = hotword_in.weight
    
    db.commit()
    db.refresh(hotword)
    
    return hotword

@router.delete("/{hotword_id}")
def delete_hotword(
    hotword_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除热词
    """
    # 查找热词
    hotword = db.query(models.Hotword).filter(models.Hotword.id == hotword_id).first()
    
    # 处理错误情况
    if not hotword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="热词不存在"
        )
    
    # 确认权限
    if hotword.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此热词"
        )
    
    # 删除热词
    db.delete(hotword)
    db.commit()
    
    return {"message": "热词已成功删除"}

@router.post("/import", response_model=dict)
async def bulk_import_hotwords(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量导入热词
    """
    # 文件类型验证
    if not file.filename.endswith(('.csv', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="只支持CSV或TXT格式文件"
        )
    
    # 读取并解析文件
    content = await file.read()
    
    # 尝试解析CSV
    added_count = 0
    skipped_count = 0
    
    try:
        text = content.decode('utf-8')
        csv_reader = csv.reader(StringIO(text))
        
        # 查询用户当前热词数量
        current_count = db.query(models.Hotword).filter(models.Hotword.user_id == current_user.id).count()
        max_allowed = 100
        remaining = max_allowed - current_count
        
        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="热词数量已达上限（100个）"
            )
        
        # 开始导入
        for row in csv_reader:
            # 检查是否已达到上限
            if added_count >= remaining:
                break
                
            # 跳过空行或格式错误行
            if not row:
                continue
            
            word = row[0].strip()
            if not word:
                continue
                
            # 尝试获取权重
            weight = 5  # 默认权重
            if len(row) > 1:
                try:
                    w = int(row[1].strip())
                    if 1 <= w <= 10:
                        weight = w
                except ValueError:
                    pass
            
            # 检查是否已存在
            existing = db.query(models.Hotword).filter(
                models.Hotword.user_id == current_user.id,
                models.Hotword.word == word
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # 创建新热词
            db_hotword = models.Hotword(
                user_id=current_user.id,
                word=word,
                weight=weight
            )
            db.add(db_hotword)
            added_count += 1
        
        # 提交事务
        db.commit()
        
        return {
            "added_count": added_count,
            "skipped_count": skipped_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"文件解析错误: {str(e)}"
        ) 