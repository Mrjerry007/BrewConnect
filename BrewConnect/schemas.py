from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

class InterestOut(BaseModel):
    id: int; name: str
    class Config: from_attributes = True

class UserCreate(BaseModel):
    username: str; email: str; password: str
    display_name: str; bio: Optional[str] = ""; interests: Optional[List[str]] = []
    @field_validator("username")
    @classmethod
    def username_valid(cls, v):
        assert v.isalnum() or "_" in v, "Username must be alphanumeric"
        return v

class UserLogin(BaseModel):
    username: str; password: str

class UserOut(BaseModel):
    id: int; username: str; display_name: str
    bio: str; avatar_url: str; interests: List[InterestOut] = []
    class Config: from_attributes = True

class TokenOut(BaseModel):
    access_token: str; token_type: str = "bearer"; user: UserOut

class SessionToggle(BaseModel):
    latitude: float; longitude: float; is_active: bool
    venue_name: Optional[str] = ""; mood_tag: Optional[str] = ""

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None

class MessageCreate(BaseModel):
    recipient_id: int
    content: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    created_at: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    user: UserOut
    last_message: MessageOut
    unread_count: int