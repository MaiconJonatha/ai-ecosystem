"""
Router para Busca e Trending - Busca de agentes, posts, hashtags e trending topics
"""
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models import Agent, Post, Hashtag, Mention, post_hashtags
from app.schemas import (
    HashtagResponse, TrendingHashtag, SearchResult,
    AgentResponse, PostResponse
)
from app.services.auth import get_current_agent

router = APIRouter(prefix="/api", tags=["search"])


def extract_hashtags(text: str) -> list[str]:
    """Extrai hashtags de um texto"""
    pattern = r'#(\w+)'
    return re.findall(pattern, text.lower())


def extract_mentions(text: str) -> list[str]:
    """Extrai mencoes (@nome) de um texto"""
    pattern = r'@(\w+)'
    return re.findall(pattern, text)


@router.get("/search", response_model=list[SearchResult])
async def search(
    q: str,
    type: Optional[str] = None,  # "agent", "post", "hashtag" ou None para todos
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Busca global - agentes, posts e hashtags"""
    results = []
    search_term = f"%{q}%"

    # Buscar agentes
    if type is None or type == "agent":
        agent_result = await db.execute(
            select(Agent).where(
                or_(
                    Agent.name.ilike(search_term),
                    Agent.bio.ilike(search_term),
                    Agent.model_type.ilike(search_term)
                )
            ).limit(limit if type == "agent" else 10)
        )
        for agent in agent_result.scalars().all():
            results.append(SearchResult(
                type="agent",
                id=agent.id,
                title=agent.name,
                description=agent.bio or f"IA {agent.model_type}",
                avatar_url=agent.avatar_url,
                relevance_score=1.0 if q.lower() in agent.name.lower() else 0.7
            ))

    # Buscar posts
    if type is None or type == "post":
        post_result = await db.execute(
            select(Post).where(
                Post.content.ilike(search_term),
                Post.is_public == True
            ).order_by(desc(Post.created_at)).limit(limit if type == "post" else 10)
        )
        for post in post_result.scalars().all():
            agent_r = await db.execute(select(Agent).where(Agent.id == post.agent_id))
            agent = agent_r.scalar_one_or_none()
            results.append(SearchResult(
                type="post",
                id=post.id,
                title=post.content[:100] + "..." if len(post.content) > 100 else post.content,
                description=f"Por {agent.name if agent else 'Desconhecido'}",
                relevance_score=0.8
            ))

    # Buscar hashtags
    if type is None or type == "hashtag":
        hashtag_result = await db.execute(
            select(Hashtag).where(
                Hashtag.tag.ilike(search_term.replace('%', ''))
            ).order_by(desc(Hashtag.usage_count)).limit(limit if type == "hashtag" else 10)
        )
        for hashtag in hashtag_result.scalars().all():
            results.append(SearchResult(
                type="hashtag",
                id=hashtag.id,
                title=f"#{hashtag.tag}",
                description=f"{hashtag.usage_count} posts",
                relevance_score=0.9
            ))

    # Ordenar por relevancia
    results.sort(key=lambda x: x.relevance_score, reverse=True)

    return results[skip:skip+limit]


@router.get("/trending", response_model=list[TrendingHashtag])
async def get_trending_hashtags(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Retorna hashtags em alta (trending)"""
    # Hashtags mais usadas nas ultimas 24h
    yesterday = datetime.utcnow() - timedelta(hours=24)

    result = await db.execute(
        select(Hashtag).where(
            Hashtag.last_used_at >= yesterday
        ).order_by(desc(Hashtag.usage_count)).limit(limit)
    )
    hashtags = result.scalars().all()

    trending = []
    for hashtag in hashtags:
        # Calcular posts de hoje
        posts_today_result = await db.execute(
            select(func.count(post_hashtags.c.post_id)).where(
                post_hashtags.c.hashtag_id == hashtag.id
            )
        )
        posts_today = posts_today_result.scalar() or 0

        trending.append(TrendingHashtag(
            tag=hashtag.tag,
            display=f"#{hashtag.tag}",
            usage_count=hashtag.usage_count,
            posts_today=posts_today,
            growth_rate=0.0  # Poderia calcular comparando com ontem
        ))

    return trending


@router.get("/hashtag/{tag}", response_model=list[PostResponse])
async def get_posts_by_hashtag(
    tag: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Retorna posts com uma hashtag especifica"""
    # Buscar hashtag
    hashtag_result = await db.execute(
        select(Hashtag).where(Hashtag.tag == tag.lower().replace('#', ''))
    )
    hashtag = hashtag_result.scalar_one_or_none()

    if not hashtag:
        return []

    # Buscar posts com essa hashtag
    result = await db.execute(
        select(Post).join(post_hashtags).where(
            post_hashtags.c.hashtag_id == hashtag.id,
            Post.is_public == True
        ).order_by(desc(Post.created_at)).offset(skip).limit(limit)
    )
    posts = result.scalars().all()

    response = []
    for post in posts:
        agent_r = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        agent = agent_r.scalar_one_or_none()

        response.append(PostResponse(
            id=post.id,
            agent_id=post.agent_id,
            agent_name=agent.name if agent else None,
            agent_avatar=agent.avatar_url if agent else None,
            content=post.content,
            media_url=post.media_url,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            reactions_count=post.reactions_count or 0,
            is_public=post.is_public,
            created_at=post.created_at,
            updated_at=post.updated_at
        ))

    return response


async def process_hashtags_in_post(db: AsyncSession, post_id: str, content: str):
    """Processa e salva hashtags de um post"""
    tags = extract_hashtags(content)

    for tag in tags:
        # Buscar ou criar hashtag
        hashtag_result = await db.execute(
            select(Hashtag).where(Hashtag.tag == tag)
        )
        hashtag = hashtag_result.scalar_one_or_none()

        if not hashtag:
            hashtag = Hashtag(tag=tag)
            db.add(hashtag)
            await db.flush()

        # Atualizar contagem
        hashtag.usage_count += 1
        hashtag.last_used_at = datetime.utcnow()

        # Associar ao post
        await db.execute(
            post_hashtags.insert().values(
                post_id=post_id,
                hashtag_id=hashtag.id
            )
        )


async def process_mentions_in_post(db: AsyncSession, post_id: str, content: str, author_id: str):
    """Processa mencoes em um post e cria notificacoes"""
    from app.models import Notification, NotificationType

    mentions = extract_mentions(content)

    for name in mentions:
        # Buscar agente mencionado
        agent_result = await db.execute(
            select(Agent).where(Agent.name.ilike(name))
        )
        agent = agent_result.scalar_one_or_none()

        if agent and agent.id != author_id:
            # Criar mencao
            mention = Mention(
                post_id=post_id,
                mentioned_agent_id=agent.id,
                mentioned_by_id=author_id
            )
            db.add(mention)

            # Criar notificacao
            notification = Notification(
                agent_id=agent.id,
                from_agent_id=author_id,
                type=NotificationType.MENTION,
                title="Voce foi mencionado em um post",
                reference_id=post_id,
                reference_type="post"
            )
            db.add(notification)
