from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DebateBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    topic: str = Field(..., min_length=1)


class DebateCreate(DebateBase):
    pass


class DebateUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    topic: Optional[str] = None
    status: Optional[str] = None


class DebateMessageBase(BaseModel):
    content: str = Field(..., min_length=1)
    position: str = Field(default="neutro")  # favor, contra, neutro


class DebateMessageCreate(DebateMessageBase):
    pass


class DebateMessageResponse(DebateMessageBase):
    id: str
    debate_id: str
    agent_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class DebateResponse(DebateBase):
    id: str
    creator_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DebateWithMessagesResponse(DebateResponse):
    messages: List[DebateMessageResponse] = []
    participants_count: int = 0
