from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    user_id: str
    username: str
    created_at: datetime

    class Config:
        from_attributes = True

class HotwordBase(BaseModel):
    word: str = Field(..., min_length=1, max_length=255)
    weight: int = Field(5, ge=1, le=10)

class HotwordCreate(HotwordBase):
    pass

class HotwordUpdate(HotwordBase):
    word: Optional[str] = None
    weight: Optional[int] = None

    @validator('word')
    def word_not_empty(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('词汇不能为空')
        return v
    
    @validator('weight')
    def weight_in_range(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('权重必须在1-10之间')
        return v

class HotwordOut(HotwordBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptionSegmentOut(BaseModel):
    segment_id: int
    start_time: float
    end_time: float
    text: str
    confidence: float

    class Config:
        from_attributes = True

class TranscriptionTaskCreate(BaseModel):
    filename: str

class TranscriptionTaskOut(BaseModel):
    id: str
    user_id: str
    filename: str
    status: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TranscriptionTaskWithSegments(TranscriptionTaskOut):
    segments: List[TranscriptionSegmentOut] = []

    class Config:
        from_attributes = True 