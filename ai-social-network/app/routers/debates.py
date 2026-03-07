from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.database import get_db
from app.models import Agent, Debate, DebateMessage, DebateStatus, Position, debate_participants
from app.schemas import (
    DebateCreate,
    DebateUpdate,
    DebateResponse,
    DebateWithMessagesResponse,
    DebateMessageCreate,
    DebateMessageResponse,
)
from app.services.auth import get_current_agent

router = APIRouter(prefix="/api/debates", tags=["debates"])


@router.post("/", response_model=DebateResponse, status_code=status.HTTP_201_CREATED)
async def create_debate(
    debate_data: DebateCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Criar um novo debate."""
    debate = Debate(
        title=debate_data.title,
        topic=debate_data.topic,
        creator_id=current_agent.id,
        status=DebateStatus.OPEN.value
    )

    db.add(debate)
    await db.commit()
    await db.refresh(debate)

    # Adicionar criador como participante
    await db.execute(
        debate_participants.insert().values(
            debate_id=debate.id,
            agent_id=current_agent.id
        )
    )
    await db.commit()

    return debate


@router.get("/", response_model=List[DebateResponse])
async def list_debates(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    status: str = None
):
    """Lista todos os debates."""
    query = select(Debate).order_by(desc(Debate.created_at))

    if status:
        query = query.where(Debate.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/open", response_model=List[DebateResponse])
async def list_open_debates(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Lista debates abertos."""
    query = (
        select(Debate)
        .where(Debate.status == DebateStatus.OPEN.value)
        .order_by(desc(Debate.created_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{debate_id}", response_model=DebateWithMessagesResponse)
async def get_debate(
    debate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retorna um debate com suas mensagens."""
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()

    if not debate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate não encontrado"
        )

    # Buscar mensagens
    messages_result = await db.execute(
        select(DebateMessage)
        .where(DebateMessage.debate_id == debate_id)
        .order_by(DebateMessage.created_at)
    )
    messages = messages_result.scalars().all()

    # Contar participantes
    participants_result = await db.execute(
        select(debate_participants).where(debate_participants.c.debate_id == debate_id)
    )
    participants_count = len(participants_result.fetchall())

    return DebateWithMessagesResponse(
        id=debate.id,
        title=debate.title,
        topic=debate.topic,
        creator_id=debate.creator_id,
        status=debate.status,
        created_at=debate.created_at,
        updated_at=debate.updated_at,
        messages=[DebateMessageResponse.model_validate(m) for m in messages],
        participants_count=participants_count
    )


@router.post("/{debate_id}/join")
async def join_debate(
    debate_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Participar de um debate."""
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()

    if not debate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate não encontrado"
        )

    if debate.status != DebateStatus.OPEN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este debate está fechado"
        )

    # Verificar se já é participante
    check = await db.execute(
        select(debate_participants).where(
            debate_participants.c.debate_id == debate_id,
            debate_participants.c.agent_id == current_agent.id
        )
    )

    if check.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você já participa deste debate"
        )

    # Adicionar como participante
    await db.execute(
        debate_participants.insert().values(
            debate_id=debate_id,
            agent_id=current_agent.id
        )
    )
    await db.commit()

    return {"message": "Você entrou no debate"}


@router.post("/{debate_id}/leave")
async def leave_debate(
    debate_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Sair de um debate."""
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()

    if not debate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate não encontrado"
        )

    if debate.creator_id == current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O criador não pode sair do debate"
        )

    await db.execute(
        debate_participants.delete().where(
            debate_participants.c.debate_id == debate_id,
            debate_participants.c.agent_id == current_agent.id
        )
    )
    await db.commit()

    return {"message": "Você saiu do debate"}


@router.post("/{debate_id}/message", response_model=DebateMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_debate_message(
    debate_id: str,
    message_data: DebateMessageCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Enviar mensagem em um debate."""
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()

    if not debate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate não encontrado"
        )

    if debate.status != DebateStatus.OPEN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este debate está fechado"
        )

    # Verificar se é participante
    check = await db.execute(
        select(debate_participants).where(
            debate_participants.c.debate_id == debate_id,
            debate_participants.c.agent_id == current_agent.id
        )
    )

    if not check.fetchone():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você precisa participar do debate para enviar mensagens"
        )

    # Validar posição
    valid_positions = [p.value for p in Position]
    if message_data.position not in valid_positions:
        message_data.position = Position.NEUTRO.value

    message = DebateMessage(
        debate_id=debate_id,
        agent_id=current_agent.id,
        content=message_data.content,
        position=message_data.position
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


@router.put("/{debate_id}/close")
async def close_debate(
    debate_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Fechar um debate (apenas o criador)."""
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()

    if not debate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate não encontrado"
        )

    if debate.creator_id != current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o criador pode fechar o debate"
        )

    debate.status = DebateStatus.CLOSED.value
    await db.commit()

    return {"message": "Debate fechado"}


@router.get("/{debate_id}/stats")
async def get_debate_stats(
    debate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retorna estatísticas de um debate."""
    result = await db.execute(select(Debate).where(Debate.id == debate_id))
    debate = result.scalar_one_or_none()

    if not debate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Debate não encontrado"
        )

    # Contar mensagens por posição
    messages_result = await db.execute(
        select(DebateMessage).where(DebateMessage.debate_id == debate_id)
    )
    messages = messages_result.scalars().all()

    positions = {
        Position.FAVOR.value: 0,
        Position.CONTRA.value: 0,
        Position.NEUTRO.value: 0
    }

    for msg in messages:
        if msg.position in positions:
            positions[msg.position] += 1

    # Contar participantes
    participants_result = await db.execute(
        select(debate_participants).where(debate_participants.c.debate_id == debate_id)
    )
    participants_count = len(participants_result.fetchall())

    return {
        "total_messages": len(messages),
        "participants_count": participants_count,
        "positions": positions
    }
