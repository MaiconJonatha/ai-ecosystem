from app.services.agent_types.base import AgentTypeBase, AgentCategory
from app.services.agent_types.creator import CreatorAgent
from app.services.agent_types.curator import CuratorAgent
from app.services.agent_types.conversational import ConversationalAgent
from app.services.agent_types.analyst import AnalystAgent

AGENT_TYPES = {
    AgentCategory.CREATOR: CreatorAgent,
    AgentCategory.CURATOR: CuratorAgent,
    AgentCategory.CONVERSATIONAL: ConversationalAgent,
    AgentCategory.ANALYST: AnalystAgent,
}

def get_agent_class(category: str):
    """Retorna a classe correta baseado na categoria"""
    try:
        cat = AgentCategory(category)
        return AGENT_TYPES.get(cat, AgentTypeBase)
    except ValueError:
        return AgentTypeBase

__all__ = [
    "AgentTypeBase", "AgentCategory",
    "CreatorAgent", "CuratorAgent",
    "ConversationalAgent", "AnalystAgent",
    "AGENT_TYPES", "get_agent_class",
]
