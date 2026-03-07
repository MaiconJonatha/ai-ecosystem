"""
Router para reacoes - Sistema de reacoes estilo Facebook (amei, haha, uau, etc)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional

from app.database import get_db
from app.models import Agent, Post, Reaction, ReactionType, REACTION_EMOJIS, Notification, NotificationType
from app.schemas import ReactionCreate, ReactionResponse, ReactionSummary, ReactionUpdate
from app.services.auth import get_current_agent

router = APIRouter(prefix="/api/reactions", tags=["reactions"])


@router.post("/", response_model=ReactionResponse)
async def add_reaction(
    reaction_data: ReactionCreate,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Adiciona uma reacao a um post"""
    # Verificar se post existe
    post_result = await db.execute(select(Post).where(Post.id == reaction_data.post_id))
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post nao encontrado")

    # Verificar se ja reagiu
    existing_result = await db.execute(
        select(Reaction).where(
            Reaction.post_id == reaction_data.post_id,
            Reaction.agent_id == current_agent.id
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Atualizar reacao existente
        existing.type = reaction_data.type
        await db.commit()
        await db.refresh(existing)
        return ReactionResponse(
            id=existing.id,
            post_id=existing.post_id,
            agent_id=existing.agent_id,
            agent_name=current_agent.name,
            type=existing.type,
            emoji=REACTION_EMOJIS.get(existing.type, ""),
            created_at=existing.created_at
        )

    # Criar nova reacao
    reaction = Reaction(
        post_id=reaction_data.post_id,
        agent_id=current_agent.id,
        type=reaction_data.type
    )
    db.add(reaction)

    # Atualizar contador de reacoes
    post.reactions_count = (post.reactions_count or 0) + 1

    # Criar notificacao para o dono do post (se nao for ele mesmo)
    if post.agent_id != current_agent.id:
        emoji = REACTION_EMOJIS.get(reaction_data.type, "")
        notification = Notification(
            agent_id=post.agent_id,
            from_agent_id=current_agent.id,
            type=NotificationType.REACTION,
            title=f"{current_agent.name} reagiu {emoji} ao seu post",
            reference_id=post.id,
            reference_type="post"
        )
        db.add(notification)

    await db.commit()
    await db.refresh(reaction)

    return ReactionResponse(
        id=reaction.id,
        post_id=reaction.post_id,
        agent_id=reaction.agent_id,
        agent_name=current_agent.name,
        type=reaction.type,
        emoji=REACTION_EMOJIS.get(reaction.type, ""),
        created_at=reaction.created_at
    )


@router.delete("/{post_id}")
async def remove_reaction(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Remove reacao de um post"""
    result = await db.execute(
        select(Reaction).where(
            Reaction.post_id == post_id,
            Reaction.agent_id == current_agent.id
        )
    )
    reaction = result.scalar_one_or_none()

    if not reaction:
        raise HTTPException(status_code=404, detail="Reacao nao encontrada")

    # Atualizar contador
    post_result = await db.execute(select(Post).where(Post.id == post_id))
    post = post_result.scalar_one_or_none()
    if post and post.reactions_count > 0:
        post.reactions_count -= 1

    await db.delete(reaction)
    await db.commit()
    return {"message": "Reacao removida"}


@router.get("/post/{post_id}", response_model=ReactionSummary)
async def get_post_reactions(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retorna resumo das reacoes de um post"""
    # Contar total
    total_result = await db.execute(
        select(func.count(Reaction.id)).where(Reaction.post_id == post_id)
    )
    total = total_result.scalar() or 0

    # Contar por tipo
    counts = {}
    for reaction_type in ReactionType:
        count_result = await db.execute(
            select(func.count(Reaction.id)).where(
                Reaction.post_id == post_id,
                Reaction.type == reaction_type
            )
        )
        counts[reaction_type.value] = count_result.scalar() or 0

    # Top 5 quem reagiu
    top_result = await db.execute(
        select(Agent.name).join(Reaction, Reaction.agent_id == Agent.id)
        .where(Reaction.post_id == post_id)
        .limit(5)
    )
    top_reactors = [name for (name,) in top_result.all()]

    return ReactionSummary(
        post_id=post_id,
        total=total,
        like=counts.get("like", 0),
        love=counts.get("love", 0),
        haha=counts.get("haha", 0),
        wow=counts.get("wow", 0),
        sad=counts.get("sad", 0),
        angry=counts.get("angry", 0),
        think=counts.get("think", 0),
        brilliant=counts.get("brilliant", 0),
        top_reactors=top_reactors
    )


@router.get("/post/{post_id}/list", response_model=list[ReactionResponse])
async def list_post_reactions(
    post_id: str,
    reaction_type: Optional[ReactionType] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Lista todas as reacoes de um post"""
    query = select(Reaction).where(Reaction.post_id == post_id)

    if reaction_type:
        query = query.where(Reaction.type == reaction_type)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    reactions = result.scalars().all()

    response = []
    for reaction in reactions:
        agent_result = await db.execute(
            select(Agent).where(Agent.id == reaction.agent_id)
        )
        agent = agent_result.scalar_one_or_none()

        response.append(ReactionResponse(
            id=reaction.id,
            post_id=reaction.post_id,
            agent_id=reaction.agent_id,
            agent_name=agent.name if agent else None,
            type=reaction.type,
            emoji=REACTION_EMOJIS.get(reaction.type, ""),
            created_at=reaction.created_at
        ))

    return response


@router.get("/my/{post_id}", response_model=Optional[ReactionResponse])
async def get_my_reaction(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Retorna a reacao do agente atual em um post (se existir)"""
    result = await db.execute(
        select(Reaction).where(
            Reaction.post_id == post_id,
            Reaction.agent_id == current_agent.id
        )
    )
    reaction = result.scalar_one_or_none()

    if not reaction:
        return None

    return ReactionResponse(
        id=reaction.id,
        post_id=reaction.post_id,
        agent_id=reaction.agent_id,
        agent_name=current_agent.name,
        type=reaction.type,
        emoji=REACTION_EMOJIS.get(reaction.type, ""),
        created_at=reaction.created_at
    )
