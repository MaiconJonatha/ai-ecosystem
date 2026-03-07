from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1)


class MessageCreate(MessageBase):
    receiver_id: str


class MessageResponse(MessageBase):
    id: str
    sender_id: str
    receiver_id: str
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    agent_id: str
    agent_name: str
    agent_model_type: str
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0


class FriendshipBase(BaseModel):
    addressee_id: str


class FriendshipCreate(FriendshipBase):
    pass


class FriendshipResponse(BaseModel):
    id: str
    requester_id: str
    addressee_id: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
