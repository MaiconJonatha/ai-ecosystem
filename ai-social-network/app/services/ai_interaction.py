from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.models import Agent, Friendship, FriendshipStatus


async def get_suggested_friends(
    db: AsyncSession,
    agent_id: str,
    limit: int = 10
) -> List[Agent]:
    """
    Sugere amigos com base no tipo de modelo de IA.
    Agentes do mesmo tipo/família podem ter mais em comum.
    """
    # Buscar o agente atual
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    current_agent = result.scalar_one_or_none()

    if not current_agent:
        return []

    # Buscar IDs de amigos existentes (aceitos ou pendentes)
    friends_query = select(Friendship).where(
        or_(
            Friendship.requester_id == agent_id,
            Friendship.addressee_id == agent_id
        )
    )
    result = await db.execute(friends_query)
    friendships = result.scalars().all()

    excluded_ids = {agent_id}
    for f in friendships:
        excluded_ids.add(f.requester_id)
        excluded_ids.add(f.addressee_id)

    # Buscar agentes do mesmo tipo primeiro
    same_type_query = (
        select(Agent)
        .where(
            Agent.id.notin_(excluded_ids),
            Agent.model_type == current_agent.model_type,
            Agent.is_active == True
        )
        .limit(limit // 2)
    )
    result = await db.execute(same_type_query)
    same_type_agents = result.scalars().all()

    # Preencher com outros agentes
    remaining = limit - len(same_type_agents)
    if remaining > 0:
        other_query = (
            select(Agent)
            .where(
                Agent.id.notin_(excluded_ids),
                Agent.model_type != current_agent.model_type,
                Agent.is_active == True
            )
            .limit(remaining)
        )
        result = await db.execute(other_query)
        other_agents = result.scalars().all()
    else:
        other_agents = []

    return list(same_type_agents) + list(other_agents)


async def get_agent_stats(
    db: AsyncSession,
    agent_id: str
) -> dict:
    """
    Retorna estatísticas do agente.
    """
    from app.models import Post, Message

    # Contar posts
    posts_count = await db.execute(
        select(func.count(Post.id)).where(Post.agent_id == agent_id)
    )
    posts = posts_count.scalar() or 0

    # Contar amigos
    friends_count = await db.execute(
        select(func.count(Friendship.id)).where(
            or_(
                Friendship.requester_id == agent_id,
                Friendship.addressee_id == agent_id
            ),
            Friendship.status == FriendshipStatus.ACCEPTED.value
        )
    )
    friends = friends_count.scalar() or 0

    # Contar mensagens enviadas
    messages_count = await db.execute(
        select(func.count(Message.id)).where(Message.sender_id == agent_id)
    )
    messages = messages_count.scalar() or 0

    return {
        "posts_count": posts,
        "friends_count": friends,
        "messages_sent": messages
    }
