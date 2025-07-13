from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

# 用户相关模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

# 令牌相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 热词相关模型
class HotwordBase(BaseModel):
    word: str = Field(..., min_length=1, max_length=255)
    weight: int = Field(5, ge=1, le=10)

class HotwordCreate(HotwordBase):
    pass

class HotwordUpdate(HotwordBase):
    word: Optional[str] = None
    weight: Optional[int] = None

    @field_validator('word')
    def word_not_empty(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('词汇不能为空')
        return v
    
    @field_validator('weight')
    def weight_in_range(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('权重必须在1-10之间')
        return v

class HotwordOut(BaseModel):
    id: str
    word: str
    weight: int
    created_at: datetime

    class Config:
        from_attributes = True

# 转写相关模型
class TranscriptionTaskBase(BaseModel):
    filename: str

class TranscriptionTaskCreate(TranscriptionTaskBase):
    pass

class TranscriptionTaskOut(BaseModel):
    id: str
    filename: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class TranscriptionSegmentOut(BaseModel):
    id: str
    segment_id: int
    start_time: float
    end_time: float
    text: str
    confidence: float

    class Config:
        from_attributes = True

class TranscriptionTaskWithSegments(TranscriptionTaskOut):
    segments: List[TranscriptionSegmentOut] = [] 