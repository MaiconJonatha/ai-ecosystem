import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class DebateStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class Position(str, enum.Enum):
    FAVOR = "favor"
    CONTRA = "contra"
    NEUTRO = "neutro"


# Tabela de associação para participantes do debate
debate_participants = Table(
    "debate_participants",
    Base.metadata,
    Column("debate_id", String(36), ForeignKey("debates.id"), primary_key=True),
    Column("agent_id", String(36), ForeignKey("agents.id"), primary_key=True),
)


class Debate(Base):
    __tablename__ = "debates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    topic = Column(Text, nullable=False)
    creator_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    status = Column(String(20), default=DebateStatus.OPEN.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    participants = relationship("Agent", secondary=debate_participants)
    messages = relationship("DebateMessage", back_populates="debate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Debate {self.title[:30]}>"


class DebateMessage(Base):
    __tablename__ = "debate_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    debate_id = Column(String(36), ForeignKey("debates.id"), nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    content = Column(Text, nullable=False)
    position = Column(String(20), default=Position.NEUTRO.value)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    debate = relationship("Debate", back_populates="messages")
    agent = relationship("Agent", back_populates="debate_messages")

    def __repr__(self):
        return f"<DebateMessage {self.agent_id[:8]} in {self.debate_id[:8]}>"
