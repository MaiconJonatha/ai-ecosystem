from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.reaction import ReactionType


class ReactionBase(BaseModel):
    type: ReactionType = ReactionType.LIKE


class ReactionCreate(ReactionBase):
    post_id: str


class ReactionResponse(ReactionBase):
    id: str
    post_id: str
    agent_id: str
    agent_name: Optional[str] = None
    emoji: str
    created_at: datetime

    class Config:
        from_attributes = True


class ReactionSummary(BaseModel):
    """Resumo de reacoes em um post"""
    post_id: str
    total: int
    like: int = 0
    love: int = 0
    haha: int = 0
    wow: int = 0
    sad: int = 0
    angry: int = 0
    think: int = 0
    brilliant: int = 0
    top_reactors: list[str] = []  # Nomes de quem reagiu


class ReactionUpdate(BaseModel):
    type: ReactionType
