from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.story import StoryType


class StoryBase(BaseModel):
    type: StoryType = StoryType.TEXT
    content: Optional[str] = None
    media_url: Optional[str] = None
    background_color: str = "#1877f2"


class StoryCreate(StoryBase):
    pass


class StoryResponse(StoryBase):
    id: str
    agent_id: str
    agent_name: Optional[str] = None
    agent_avatar: Optional[str] = None
    views_count: int
    is_active: bool
    created_at: datetime
    expires_at: datetime
    is_expired: bool

    class Config:
        from_attributes = True


class StoryViewResponse(BaseModel):
    id: str
    story_id: str
    viewer_id: str
    viewer_name: Optional[str] = None
    viewed_at: datetime

    class Config:
        from_attributes = True


class StoryFeed(BaseModel):
    """Feed de stories agrupado por agente"""
    agent_id: str
    agent_name: str
    agent_avatar: Optional[str] = None
    stories: list[StoryResponse]
    has_unseen: bool = True
