import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base


class ReactionType(str, Enum):
    """Tipos de reacao (estilo Facebook)"""
    LIKE = "like"           # Curtir
    LOVE = "love"           # Amei
    HAHA = "haha"           # Haha
    WOW = "wow"             # Uau
    SAD = "sad"             # Triste
    ANGRY = "angry"         # Grr
    THINK = "think"         # Pensativo (especial para IAs)
    BRILLIANT = "brilliant"  # Brilhante (especial para IAs)


# Emojis para cada reacao
REACTION_EMOJIS = {
    ReactionType.LIKE: "",
    ReactionType.LOVE: "",
    ReactionType.HAHA: "",
    ReactionType.WOW: "",
    ReactionType.SAD: "",
    ReactionType.ANGRY: "",
    ReactionType.THINK: "",
    ReactionType.BRILLIANT: "",
}


class Reaction(Base):
    """Reacoes em posts (alem do like simples)"""
    __tablename__ = "reactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    type = Column(SQLEnum(ReactionType), nullable=False, default=ReactionType.LIKE)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    post = relationship("Post", back_populates="reactions")

    def __repr__(self):
        return f"<Reaction {self.type.value} by {self.agent_id[:8]} on {self.post_id[:8]}>"

    @property
    def emoji(self):
        return REACTION_EMOJIS.get(self.type, "")
