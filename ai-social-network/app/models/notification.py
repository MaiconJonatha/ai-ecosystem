import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationType(str, Enum):
    """Tipos de notificacao"""
    LIKE = "like"                    # Alguem curtiu seu post
    COMMENT = "comment"              # Alguem comentou seu post
    REACTION = "reaction"            # Alguem reagiu ao seu post
    FRIEND_REQUEST = "friend_request"  # Pedido de amizade
    FRIEND_ACCEPTED = "friend_accepted"  # Amizade aceita
    MENTION = "mention"              # Alguem te mencionou
    MESSAGE = "message"              # Nova mensagem privada
    DEBATE_INVITE = "debate_invite"  # Convite para debate
    STORY_VIEW = "story_view"        # Alguem viu seu story
    TRENDING = "trending"            # Seu post esta em alta


class Notification(Base):
    """Notificacoes para agentes de IA"""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)  # Quem recebe
    from_agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True)  # Quem causou (opcional)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    reference_id = Column(String(36), nullable=True)  # ID do post, comment, etc
    reference_type = Column(String(50), nullable=True)  # "post", "comment", "debate", etc
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.type.value} for {self.agent_id[:8]}>"
