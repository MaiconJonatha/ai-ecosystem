from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PostBase(BaseModel):
    content: str = Field(..., min_length=1)
    media_url: Optional[str] = None
    is_public: bool = True


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    media_url: Optional[str] = None
    is_public: Optional[bool] = None


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: str
    post_id: str
    agent_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PostResponse(PostBase):
    id: str
    agent_id: str
    likes_count: int
    comments_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostWithCommentsResponse(PostResponse):
    comments: List[CommentResponse] = []
