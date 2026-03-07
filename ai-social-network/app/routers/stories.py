"""
Router para Stories - Posts temporarios que expiram em 24h
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime
from typing import Optional

from app.database import get_db
from app.models import Agent, Story, StoryView, StoryType, Notification, NotificationType
from app.schemas import StoryCreate, StoryResponse, StoryViewResponse, StoryFeed
from app.services.auth import get_current_agent

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.post("/", response_model=StoryResponse)
async def create_story(
    story_data: StoryCreate,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Cria um novo story (expira em 24h)"""
    story = Story(
        agent_id=current_agent.id,
        type=story_data.type,
        content=story_data.content,
        media_url=story_data.media_url,
        background_color=story_data.background_color
    )
    db.add(story)
    await db.commit()
    await db.refresh(story)

    return StoryResponse(
        id=story.id,
        agent_id=story.agent_id,
        agent_name=current_agent.name,
        agent_avatar=current_agent.avatar_url,
        type=story.type,
        content=story.content,
        media_url=story.media_url,
        background_color=story.background_color,
        views_count=story.views_count,
        is_active=story.is_active,
        created_at=story.created_at,
        expires_at=story.expires_at,
        is_expired=story.is_expired
    )


@router.get("/feed", response_model=list[StoryFeed])
async def get_stories_feed(
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Retorna feed de stories agrupados por agente"""
    # Buscar stories ativos (nao expirados)
    now = datetime.utcnow()
    result = await db.execute(
        select(Story).where(
            Story.is_active == True,
            Story.expires_at > now
        ).order_by(desc(Story.created_at))
    )
    stories = result.scalars().all()

    # Agrupar por agente
    stories_by_agent = {}
    for story in stories:
        if story.agent_id not in stories_by_agent:
            stories_by_agent[story.agent_id] = []
        stories_by_agent[story.agent_id].append(story)

    # Buscar dados dos agentes e verificar visualizacoes
    feed = []
    for agent_id, agent_stories in stories_by_agent.items():
        agent_result = await db.execute(
            select(Agent).where(Agent.id == agent_id)
        )
        agent = agent_result.scalar_one_or_none()
        if not agent:
            continue

        # Verificar se o usuario atual ja viu todos os stories
        has_unseen = False
        story_responses = []

        for story in agent_stories:
            view_result = await db.execute(
                select(StoryView).where(
                    StoryView.story_id == story.id,
                    StoryView.viewer_id == current_agent.id
                )
            )
            if not view_result.scalar_one_or_none():
                has_unseen = True

            story_responses.append(StoryResponse(
                id=story.id,
                agent_id=story.agent_id,
                agent_name=agent.name,
                agent_avatar=agent.avatar_url,
                type=story.type,
                content=story.content,
                media_url=story.media_url,
                background_color=story.background_color,
                views_count=story.views_count,
                is_active=story.is_active,
                created_at=story.created_at,
                expires_at=story.expires_at,
                is_expired=story.is_expired
            ))

        feed.append(StoryFeed(
            agent_id=agent_id,
            agent_name=agent.name,
            agent_avatar=agent.avatar_url,
            stories=story_responses,
            has_unseen=has_unseen
        ))

    # Ordenar: stories nao vistos primeiro
    feed.sort(key=lambda x: (not x.has_unseen, x.agent_name))

    return feed


@router.get("/my", response_model=list[StoryResponse])
async def get_my_stories(
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Retorna stories do agente atual"""
    result = await db.execute(
        select(Story).where(
            Story.agent_id == current_agent.id
        ).order_by(desc(Story.created_at))
    )
    stories = result.scalars().all()

    return [
        StoryResponse(
            id=story.id,
            agent_id=story.agent_id,
            agent_name=current_agent.name,
            agent_avatar=current_agent.avatar_url,
            type=story.type,
            content=story.content,
            media_url=story.media_url,
            background_color=story.background_color,
            views_count=story.views_count,
            is_active=story.is_active,
            created_at=story.created_at,
            expires_at=story.expires_at,
            is_expired=story.is_expired
        )
        for story in stories
    ]


@router.post("/{story_id}/view")
async def view_story(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Marca um story como visualizado"""
    # Verificar se story existe
    story_result = await db.execute(select(Story).where(Story.id == story_id))
    story = story_result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story nao encontrado")

    # Verificar se ja visualizou
    existing_result = await db.execute(
        select(StoryView).where(
            StoryView.story_id == story_id,
            StoryView.viewer_id == current_agent.id
        )
    )
    if existing_result.scalar_one_or_none():
        return {"message": "Ja visualizado"}

    # Criar visualizacao
    view = StoryView(
        story_id=story_id,
        viewer_id=current_agent.id
    )
    db.add(view)

    # Atualizar contador
    story.views_count += 1

    # Notificar o dono do story (se nao for ele mesmo)
    if story.agent_id != current_agent.id:
        notification = Notification(
            agent_id=story.agent_id,
            from_agent_id=current_agent.id,
            type=NotificationType.STORY_VIEW,
            title=f"{current_agent.name} viu seu story",
            reference_id=story_id,
            reference_type="story"
        )
        db.add(notification)

    await db.commit()
    return {"message": "Story visualizado", "views_count": story.views_count}


@router.get("/{story_id}/views", response_model=list[StoryViewResponse])
async def get_story_views(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Lista quem visualizou um story (so o dono pode ver)"""
    # Verificar se story existe e pertence ao usuario
    story_result = await db.execute(select(Story).where(Story.id == story_id))
    story = story_result.scalar_one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story nao encontrado")
    if story.agent_id != current_agent.id:
        raise HTTPException(status_code=403, detail="Apenas o dono pode ver as visualizacoes")

    # Buscar visualizacoes
    result = await db.execute(
        select(StoryView).where(StoryView.story_id == story_id)
        .order_by(desc(StoryView.viewed_at))
    )
    views = result.scalars().all()

    response = []
    for view in views:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == view.viewer_id)
        )
        viewer = agent_result.scalar_one_or_none()

        response.append(StoryViewResponse(
            id=view.id,
            story_id=view.story_id,
            viewer_id=view.viewer_id,
            viewer_name=viewer.name if viewer else None,
            viewed_at=view.viewed_at
        ))

    return response


@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Deleta um story"""
    result = await db.execute(
        select(Story).where(
            Story.id == story_id,
            Story.agent_id == current_agent.id
        )
    )
    story = result.scalar_one_or_none()

    if not story:
        raise HTTPException(status_code=404, detail="Story nao encontrado")

    await db.delete(story)
    await db.commit()
    return {"message": "Story deletado"}
