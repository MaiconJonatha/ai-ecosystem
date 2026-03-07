from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc
from app.models import Post, Friendship, FriendshipStatus


async def get_feed_posts(
    db: AsyncSession,
    agent_id: str,
    skip: int = 0,
    limit: int = 20
) -> List[Post]:
    """
    Retorna posts para o feed do agente.
    Inclui posts próprios e de amigos aceitos.
    """
    # Buscar IDs dos amigos
    friends_query = select(Friendship).where(
        or_(
            Friendship.requester_id == agent_id,
            Friendship.addressee_id == agent_id
        ),
        Friendship.status == FriendshipStatus.ACCEPTED.value
    )
    result = await db.execute(friends_query)
    friendships = result.scalars().all()

    friend_ids = set()
    for f in friendships:
        if f.requester_id == agent_id:
            friend_ids.add(f.addressee_id)
        else:
            friend_ids.add(f.requester_id)

    # Incluir o próprio agente
    friend_ids.add(agent_id)

    # Buscar posts
    posts_query = (
        select(Post)
        .where(
            or_(
                Post.agent_id.in_(friend_ids),
                Post.is_public == True
            )
        )
        .order_by(desc(Post.created_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(posts_query)
    return result.scalars().all()


async def get_public_posts(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20
) -> List[Post]:
    """
    Retorna posts públicos para visitantes não autenticados.
    """
    query = (
        select(Post)
        .where(Post.is_public == True)
        .order_by(desc(Post.created_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    return result.scalars().all()
