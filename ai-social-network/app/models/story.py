import uuid
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base


class StoryType(str, Enum):
    """Tipos de story"""
    TEXT = "text"       # Texto simples
    IMAGE = "image"     # Imagem/foto
    VIDEO = "video"     # Video
    POLL = "poll"       # Enquete
    THOUGHT = "thought"  # Pensamento do dia (especial para IAs)


class Story(Base):
    """Stories - posts temporarios (24h)"""
    __tablename__ = "stories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    type = Column(SQLEnum(StoryType), nullable=False, default=StoryType.TEXT)
    content = Column(Text, nullable=True)  # Texto ou descricao
    media_url = Column(String(500), nullable=True)  # URL de imagem/video
    background_color = Column(String(7), default="#1877f2")  # Cor de fundo para texto
    views_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))

    # Relacionamentos
    agent = relationship("Agent", back_populates="stories")
    views = relationship("StoryView", back_populates="story", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Story {self.type.value} by {self.agent_id[:8]}>"

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at


class StoryView(Base):
    """Visualizacoes de stories"""
    __tablename__ = "story_views"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(36), ForeignKey("stories.id"), nullable=False)
    viewer_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    story = relationship("Story", back_populates="views")

    def __repr__(self):
        return f"<StoryView {self.viewer_id[:8]} saw {self.story_id[:8]}>"
