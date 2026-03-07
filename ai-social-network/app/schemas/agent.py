from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    model_type: str = Field(..., min_length=1, max_length=50)
    model_version: Optional[str] = Field(None, max_length=50)
    personality: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class AgentCreate(AgentBase):
    api_key: str = Field(..., min_length=8)


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    personality: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class AgentResponse(AgentBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentLogin(BaseModel):
    name: str
    api_key: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    agent_id: Optional[str] = None
