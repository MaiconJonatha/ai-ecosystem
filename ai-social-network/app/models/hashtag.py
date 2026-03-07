import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


# Tabela de associacao Post <-> Hashtag (muitos para muitos)
post_hashtags = Table(
    "post_hashtags",
    Base.metadata,
    Column("post_id", String(36), ForeignKey("posts.id"), primary_key=True),
    Column("hashtag_id", String(36), ForeignKey("hashtags.id"), primary_key=True),
)


class Hashtag(Base):
    """Hashtags para trending topics"""
    __tablename__ = "hashtags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tag = Column(String(100), nullable=False, unique=True, index=True)  # sem o #
    usage_count = Column(Integer, default=0)  # Quantas vezes foi usada
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    posts = relationship("Post", secondary=post_hashtags, back_populates="hashtags")

    def __repr__(self):
        return f"<Hashtag #{self.tag} ({self.usage_count} uses)>"

    @property
    def display(self):
        return f"#{self.tag}"


class Mention(Base):
    """Mencoes de agentes em posts (@nome)"""
    __tablename__ = "mentions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("posts.id"), nullable=False)
    mentioned_agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    mentioned_by_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Mention @{self.mentioned_agent_id[:8]} in {self.post_id[:8]}>"
