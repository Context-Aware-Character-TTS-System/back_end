from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class NovelBase(BaseModel):
    title: str
    status: str # Enum will be handled in models.py

class NovelCreate(NovelBase):
    pass

class NovelResponse(NovelBase):
    id: int
    full_audio_url: Optional[str] = None
    master_context: Optional[str] = None
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class SentenceBase(BaseModel):
    sentence_index: int
    text: str
    speaker: str
    emotion: str
    instruction: Optional[str] = None
    voice_id: Optional[str] = None
    audio_url: Optional[str] = None

class SentenceResponse(SentenceBase):
    id: int
    novel_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str