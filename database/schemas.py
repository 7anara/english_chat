from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional, List


class AttachmentOut(BaseModel):
    id: int
    file_type: str
    file_url: str
    file_name: str
    mime_type: str
    file_size: int
    duration_sec: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    text: str


class MessageEdit(BaseModel):
    text: str


class MessageOut(BaseModel):
    id: int
    room_id: int
    sender_email: str
    sender_name: str
    is_teacher: bool
    text: str
    is_deleted: bool
    edited_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    email: EmailStr
    full_name: str
    is_teacher: bool = False


class MemberOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_teacher: bool
    is_online: bool
    joined_at: date
    last_seen: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    group_id: int
    group_name: str


class RoomOut(BaseModel):
    id: int
    group_id: int
    group_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RoomDetailOut(BaseModel):
    id: int
    group_id: int
    group_name: str
    is_active: bool
    created_at: datetime
    members: List[MemberOut] = []

    class Config:
        from_attributes = True


class ReadStateOut(BaseModel):
    id: int
    room_id: int
    email: str
    last_read_message_id: Optional[int] = None
    unread_count: int
    updated_at: datetime

    class Config:
        from_attributes = True


class WSMessageIn(BaseModel):
    type: str
    text: Optional[str] = None


class WSMessageOut(BaseModel):
    type: str
    id: Optional[int] = None
    room_id: Optional[int] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    is_teacher: Optional[bool] = None
    text: Optional[str] = None
    is_deleted: Optional[bool] = None
    edited_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    online_count: Optional[int] = None
