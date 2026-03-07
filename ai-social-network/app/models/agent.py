import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(50), nullable=False, index=True)  # claude, gpt, gemini, etc.
    model_version = Column(String(50), nullable=True)  # opus-4.5, gpt-4, etc.
    personality = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    api_key_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # IA verificada

    # Sistema de reputacao/pontuacao
    reputation_score = Column(Integer, default=0)  # Pontuacao geral
    posts_count = Column(Integer, default=0)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    posts = relationship("Post", back_populates="agent", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="agent", cascade="all, delete-orphan")
    sent_messages = relationship(
        "Message",
        foreign_keys="Message.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan"
    )
    received_messages = relationship(
        "Message",
        foreign_keys="Message.receiver_id",
        back_populates="receiver",
        cascade="all, delete-orphan"
    )
    debate_messages = relationship("DebateMessage", back_populates="agent", cascade="all, delete-orphan")
    stories = relationship("Story", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agent {self.name} ({self.model_type})>"

    def update_reputation(self, likes_received=0, comments_received=0, posts_made=0):
        """Atualiza a reputacao do agente"""
        self.reputation_score += (likes_received * 5) + (comments_received * 10) + (posts_made * 2)
