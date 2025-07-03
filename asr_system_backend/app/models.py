from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Text
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联关系
    hotwords = relationship("Hotword", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("TranscriptionTask", back_populates="user", cascade="all, delete-orphan")

class Hotword(Base):
    __tablename__ = "hotwords"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    word = Column(String(255), nullable=False, index=True)
    weight = Column(Integer, nullable=False, default=5)  # 1-10的权重值
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="hotwords")

class TranscriptionTask(Base):
    __tablename__ = "transcription_tasks"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed
    error_message = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    user = relationship("User", back_populates="tasks")
    segments = relationship("TranscriptionSegment", back_populates="task", cascade="all, delete-orphan")

class TranscriptionSegment(Base):
    __tablename__ = "transcription_segments"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    task_id = Column(String(36), ForeignKey("transcription_tasks.id", ondelete="CASCADE"), nullable=False)
    segment_id = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # 关联关系
    task = relationship("TranscriptionTask", back_populates="segments") 