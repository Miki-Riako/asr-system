from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import models, schemas
from fastapi import HTTPException, status
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from .rag_service import get_rag_service
from .asr_engine import get_asr_engine
from .config import get_settings
import os
import time
import random

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 获取配置
settings = get_settings()
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def register_user(db: Session, user_in: schemas.UserCreate):
        user = db.query(models.User).filter(models.User.username == user_in.username).first()
        if user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
        hashed_password = AuthService.get_password_hash(user_in.password)
        new_user = models.User(username=user_in.username, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None 


class TranscriptionService:
    @staticmethod
    def process_transcription_task(db: Session, task_id: str, file_path: str, hotword_list_id: str = None):
        """
        处理转写任务的后台方法，使用真实的ASR引擎进行音频转写
        """
        try:
            # 更新任务状态为处理中
            task = db.query(models.TranscriptionTask).filter(models.TranscriptionTask.id == task_id).first()
            if not task:
                print(f"任务不存在: {task_id}")
                return
            
            task.status = "processing"
            db.commit()
            
            # 获取ASR引擎实例
            asr_engine = get_asr_engine()
            
            # 如果启用了热词功能，初始化RAG服务
            rag_service = get_rag_service()
            if hotword_list_id and not rag_service.initialized:
                rag_service.initialize()
            
            # 为用户构建热词索引（如果启用热词功能）
            if hotword_list_id:
                rag_service.build_user_hotword_index(db, task.user_id)
            
            # 验证音频文件
            if not asr_engine.validate_audio_file(file_path):
                raise ValueError(f"无效的音频文件: {file_path}")
            
            # 预处理音频文件
            processed_file_path = asr_engine.preprocess_audio(file_path)
            
            # 使用ASR引擎进行转写
            transcription_result = asr_engine.transcribe_audio(processed_file_path)
            
            # 提取分段结果
            segments = transcription_result.get("segments", [])
            
            # 如果启用了热词功能，对每个分段进行增强
            if hotword_list_id and rag_service.initialized:
                for segment in segments:
                    enhancement = rag_service.enhance_transcription_with_hotwords(
                        segment["text"], task.user_id
                    )
                    # 使用增强后的文本
                    segment["text"] = enhancement["enhanced_text"]
                    # 应用置信度提升
                    segment["confidence"] = min(
                        segment["confidence"] * enhancement["confidence_boost"], 
                        0.99
                    )
            
            # 添加分段结果到数据库
            for segment in segments:
                db_segment = models.TranscriptionSegment(
                    task_id=task_id,
                    segment_id=segment["segment_id"],
                    start_time=segment["start_time"],
                    end_time=segment["end_time"],
                    text=segment["text"],
                    confidence=segment["confidence"]
                )
                db.add(db_segment)
            
            # 更新任务状态为已完成
            task.status = "completed"
            task.completed_at = datetime.now(UTC)
            db.commit()
            
            # 清理临时文件
            if os.path.exists(processed_file_path) and processed_file_path != file_path:
                try:
                    os.remove(processed_file_path)
                except:
                    pass  # 忽略删除错误
                    
        except Exception as e:
            # 记录错误并更新任务状态
            print(f"处理任务 {task_id} 时发生错误: {str(e)}")
            task = db.query(models.TranscriptionTask).filter(models.TranscriptionTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
    
    @staticmethod
    def _generate_mock_segments(task_id: str, num_segments: int):
        """
        生成模拟的转写分段数据（仅用于开发阶段测试）
        """
        segments = []
        
        # 示例文本片段
        texts = [
            "欢迎使用支持热词预测的语音识别系统",
            "我们的系统能够自动识别专业领域的热词",
            "本次会议主要讨论产品的发展方向和市场策略",
            "根据数据分析，我们的用户满意度达到了95%",
            "接下来，我们将重点开发智能辅助功能",
            "请各位同事准备下周的迭代演示",
            "转写结果会包含时间戳，方便用户查找关键内容",
            "客服团队反馈系统的准确率有了明显提升",
            "RAG技术与ASR的结合是我们的核心竞争力",
            "感谢各位的参与和贡献"
        ]
        
        # 生成随机分段数据
        start_time = 0.0
        for i in range(num_segments):
            text = texts[i % len(texts)]
            # 随机的段落时长（2-5秒）
            duration = round(random.uniform(2.0, 5.0), 2)
            end_time = round(start_time + duration, 2)
            
            segments.append({
                "segment_id": i,
                "start_time": start_time,
                "end_time": end_time,
                "text": text,
                "confidence": round(random.uniform(0.7, 0.98), 2)
            })
            
            start_time = end_time
        
        return segments 