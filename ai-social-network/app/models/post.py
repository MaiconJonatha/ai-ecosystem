import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.hashtag import post_hashtags


class Post(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    media_url = Column(String(500), nullable=True)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    reactions_count = Column(Integer, default=0)  # Total de reacoes
    shares_count = Column(Integer, default=0)  # Compartilhamentos
    is_public = Column(Boolean, default=True)
    is_trending = Column(Boolean, default=False)  # Se esta em alta
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    agent = relationship("Agent", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")
    hashtags = relationship("Hashtag", secondary=post_hashtags, back_populates="posts")

    def __repr__(self):
        return f"<Post {self.id[:8]} by {self.agent_id[:8]}>"


class Like(Base):
    __tablename__ = "likes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    post = relationship("Post", back_populates="likes")

    def __repr__(self):
        return f"<Like {self.agent_id[:8]} -> {self.post_id[:8]}>"
