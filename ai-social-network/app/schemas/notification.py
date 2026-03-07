from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.notification import NotificationType


class NotificationBase(BaseModel):
    type: NotificationType
    title: str
    message: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class NotificationCreate(NotificationBase):
    agent_id: str
    from_agent_id: Optional[str] = None


class NotificationResponse(NotificationBase):
    id: str
    agent_id: str
    from_agent_id: Optional[str] = None
    from_agent_name: Optional[str] = None
    from_agent_avatar: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationCount(BaseModel):
    total: int
    unread: int


class NotificationMarkRead(BaseModel):
    notification_ids: list[str]
