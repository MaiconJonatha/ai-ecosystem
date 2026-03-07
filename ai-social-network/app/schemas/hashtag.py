from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HashtagBase(BaseModel):
    tag: str


class HashtagCreate(HashtagBase):
    pass


class HashtagResponse(HashtagBase):
    id: str
    usage_count: int
    created_at: datetime
    last_used_at: datetime
    display: str

    class Config:
        from_attributes = True


class TrendingHashtag(BaseModel):
    """Hashtag em alta"""
    tag: str
    display: str
    usage_count: int
    posts_today: int = 0
    growth_rate: float = 0.0  # % de crescimento


class MentionBase(BaseModel):
    mentioned_agent_id: str


class MentionCreate(MentionBase):
    post_id: str


class MentionResponse(MentionBase):
    id: str
    post_id: str
    mentioned_by_id: str
    mentioned_agent_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """Resultado de busca"""
    type: str  # "agent", "post", "hashtag"
    id: str
    title: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    relevance_score: float = 1.0
