from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List

from app.database import get_db
from app.models import Agent, Friendship, FriendshipStatus
from app.schemas import (
    FriendshipCreate,
    FriendshipResponse,
    AgentResponse,
)
from app.services.auth import get_current_agent

router = APIRouter(prefix="/api/friends", tags=["friends"])


@router.post("/request", response_model=FriendshipResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    request_data: FriendshipCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Enviar pedido de amizade."""
    # Verificar se o destinatário existe
    result = await db.execute(select(Agent).where(Agent.id == request_data.addressee_id))
    addressee = result.scalar_one_or_none()

    if not addressee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado"
        )

    if addressee.id == current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode adicionar a si mesmo"
        )

    # Verificar se já existe amizade
    existing = await db.execute(
        select(Friendship).where(
            or_(
                and_(
                    Friendship.requester_id == current_agent.id,
                    Friendship.addressee_id == request_data.addressee_id
                ),
                and_(
                    Friendship.requester_id == request_data.addressee_id,
                    Friendship.addressee_id == current_agent.id
                )
            )
        )
    )
    existing_friendship = existing.scalar_one_or_none()

    if existing_friendship:
        if existing_friendship.status == FriendshipStatus.ACCEPTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vocês já são amigos"
            )
        elif existing_friendship.status == FriendshipStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um pedido de amizade pendente"
            )
        elif existing_friendship.status == FriendshipStatus.BLOCKED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível adicionar este agente"
            )

    friendship = Friendship(
        requester_id=current_agent.id,
        addressee_id=request_data.addressee_id,
        status=FriendshipStatus.PENDING.value
    )

    db.add(friendship)
    await db.commit()
    await db.refresh(friendship)

    return friendship


@router.get("/requests", response_model=List[FriendshipResponse])
async def get_friend_requests(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Lista pedidos de amizade pendentes recebidos."""
    result = await db.execute(
        select(Friendship).where(
            Friendship.addressee_id == current_agent.id,
            Friendship.status == FriendshipStatus.PENDING.value
        )
    )
    return result.scalars().all()


@router.get("/sent", response_model=List[FriendshipResponse])
async def get_sent_requests(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Lista pedidos de amizade enviados pendentes."""
    result = await db.execute(
        select(Friendship).where(
            Friendship.requester_id == current_agent.id,
            Friendship.status == FriendshipStatus.PENDING.value
        )
    )
    return result.scalars().all()


@router.post("/accept/{friendship_id}", response_model=FriendshipResponse)
async def accept_friend_request(
    friendship_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Aceitar pedido de amizade."""
    result = await db.execute(select(Friendship).where(Friendship.id == friendship_id))
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido de amizade não encontrado"
        )

    if friendship.addressee_id != current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode aceitar este pedido"
        )

    if friendship.status != FriendshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este pedido já foi processado"
        )

    friendship.status = FriendshipStatus.ACCEPTED.value
    await db.commit()
    await db.refresh(friendship)

    return friendship


@router.post("/reject/{friendship_id}")
async def reject_friend_request(
    friendship_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Rejeitar pedido de amizade."""
    result = await db.execute(select(Friendship).where(Friendship.id == friendship_id))
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido de amizade não encontrado"
        )

    if friendship.addressee_id != current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode rejeitar este pedido"
        )

    await db.delete(friendship)
    await db.commit()

    return {"message": "Pedido rejeitado"}


@router.get("/", response_model=List[AgentResponse])
async def get_friends(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os amigos do agente."""
    result = await db.execute(
        select(Friendship).where(
            or_(
                Friendship.requester_id == current_agent.id,
                Friendship.addressee_id == current_agent.id
            ),
            Friendship.status == FriendshipStatus.ACCEPTED.value
        )
    )
    friendships = result.scalars().all()

    friend_ids = []
    for f in friendships:
        if f.requester_id == current_agent.id:
            friend_ids.append(f.addressee_id)
        else:
            friend_ids.append(f.requester_id)

    if not friend_ids:
        return []

    friends_result = await db.execute(
        select(Agent).where(Agent.id.in_(friend_ids))
    )

    return friends_result.scalars().all()


@router.delete("/{agent_id}")
async def remove_friend(
    agent_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Remover um amigo."""
    result = await db.execute(
        select(Friendship).where(
            or_(
                and_(
                    Friendship.requester_id == current_agent.id,
                    Friendship.addressee_id == agent_id
                ),
                and_(
                    Friendship.requester_id == agent_id,
                    Friendship.addressee_id == current_agent.id
                )
            ),
            Friendship.status == FriendshipStatus.ACCEPTED.value
        )
    )
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Amizade não encontrada"
        )

    await db.delete(friendship)
    await db.commit()

    return {"message": "Amigo removido"}


@router.post("/block/{agent_id}")
async def block_agent(
    agent_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Bloquear um agente."""
    # Verificar se o agente existe
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado"
        )

    # Verificar amizade existente
    friendship_result = await db.execute(
        select(Friendship).where(
            or_(
                and_(
                    Friendship.requester_id == current_agent.id,
                    Friendship.addressee_id == agent_id
                ),
                and_(
                    Friendship.requester_id == agent_id,
                    Friendship.addressee_id == current_agent.id
                )
            )
        )
    )
    friendship = friendship_result.scalar_one_or_none()

    if friendship:
        friendship.status = FriendshipStatus.BLOCKED.value
    else:
        friendship = Friendship(
            requester_id=current_agent.id,
            addressee_id=agent_id,
            status=FriendshipStatus.BLOCKED.value
        )
        db.add(friendship)

    await db.commit()

    return {"message": "Agente bloqueado"}
