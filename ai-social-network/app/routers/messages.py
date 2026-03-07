from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, func
from typing import List

from app.database import get_db
from app.models import Agent, Message
from app.schemas import (
    MessageCreate,
    MessageResponse,
    ConversationResponse,
)
from app.services.auth import get_current_agent

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Enviar uma mensagem privada para outro agente."""
    # Verificar se o destinatário existe
    result = await db.execute(select(Agent).where(Agent.id == message_data.receiver_id))
    receiver = result.scalar_one_or_none()

    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatário não encontrado"
        )

    if receiver.id == current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode enviar mensagem para si mesmo"
        )

    message = Message(
        sender_id=current_agent.id,
        receiver_id=message_data.receiver_id,
        content=message_data.content,
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Lista todas as conversas do agente."""
    # Buscar todos os agentes com quem teve conversa
    messages_query = select(Message).where(
        or_(
            Message.sender_id == current_agent.id,
            Message.receiver_id == current_agent.id
        )
    ).order_by(desc(Message.created_at))

    result = await db.execute(messages_query)
    messages = result.scalars().all()

    # Agrupar por conversa
    conversations = {}
    for msg in messages:
        other_id = msg.receiver_id if msg.sender_id == current_agent.id else msg.sender_id

        if other_id not in conversations:
            conversations[other_id] = {
                "last_message": msg.content,
                "last_message_time": msg.created_at,
                "unread_count": 0
            }

        if msg.receiver_id == current_agent.id and not msg.read:
            conversations[other_id]["unread_count"] += 1

    # Buscar informações dos agentes
    result_list = []
    for agent_id, conv_data in conversations.items():
        agent_result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = agent_result.scalar_one_or_none()

        if agent:
            result_list.append(ConversationResponse(
                agent_id=agent.id,
                agent_name=agent.name,
                agent_model_type=agent.model_type,
                last_message=conv_data["last_message"],
                last_message_time=conv_data["last_message_time"],
                unread_count=conv_data["unread_count"]
            ))

    # Ordenar por última mensagem
    result_list.sort(key=lambda x: x.last_message_time or "", reverse=True)

    return result_list


@router.get("/{agent_id}", response_model=List[MessageResponse])
async def get_conversation(
    agent_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Retorna o histórico de mensagens com um agente específico."""
    # Verificar se o agente existe
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    other_agent = result.scalar_one_or_none()

    if not other_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado"
        )

    # Buscar mensagens
    messages_query = (
        select(Message)
        .where(
            or_(
                and_(
                    Message.sender_id == current_agent.id,
                    Message.receiver_id == agent_id
                ),
                and_(
                    Message.sender_id == agent_id,
                    Message.receiver_id == current_agent.id
                )
            )
        )
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(messages_query)
    messages = result.scalars().all()

    # Marcar mensagens recebidas como lidas
    for msg in messages:
        if msg.receiver_id == current_agent.id and not msg.read:
            msg.read = True

    await db.commit()

    return messages


@router.put("/{message_id}/read")
async def mark_as_read(
    message_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Marcar uma mensagem como lida."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mensagem não encontrada"
        )

    if message.receiver_id != current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta mensagem não é para você"
        )

    message.read = True
    await db.commit()

    return {"message": "Mensagem marcada como lida"}


@router.get("/unread/count")
async def get_unread_count(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Retorna a quantidade de mensagens não lidas."""
    result = await db.execute(
        select(func.count(Message.id)).where(
            Message.receiver_id == current_agent.id,
            Message.read == False
        )
    )
    count = result.scalar() or 0

    return {"unread_count": count}
