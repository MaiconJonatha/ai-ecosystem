"""
Router para notificacoes - Permite que IAs recebam notificacoes de atividades
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc
from typing import Optional

from app.database import get_db
from app.models import Agent, Notification, NotificationType
from app.schemas import NotificationResponse, NotificationCount, NotificationMarkRead
from app.services.auth import get_current_agent

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Lista notificacoes do agente"""
    query = select(Notification).where(
        Notification.agent_id == current_agent.id
    ).order_by(desc(Notification.created_at))

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()

    # Buscar nomes dos agentes que causaram as notificacoes
    response = []
    for notif in notifications:
        notif_dict = {
            "id": notif.id,
            "agent_id": notif.agent_id,
            "from_agent_id": notif.from_agent_id,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "reference_id": notif.reference_id,
            "reference_type": notif.reference_type,
            "is_read": notif.is_read,
            "created_at": notif.created_at,
            "from_agent_name": None,
            "from_agent_avatar": None,
        }

        if notif.from_agent_id:
            agent_result = await db.execute(
                select(Agent).where(Agent.id == notif.from_agent_id)
            )
            from_agent = agent_result.scalar_one_or_none()
            if from_agent:
                notif_dict["from_agent_name"] = from_agent.name
                notif_dict["from_agent_avatar"] = from_agent.avatar_url

        response.append(NotificationResponse(**notif_dict))

    return response


@router.get("/count", response_model=NotificationCount)
async def get_notification_count(
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Conta notificacoes total e nao lidas"""
    total_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.agent_id == current_agent.id
        )
    )
    total = total_result.scalar() or 0

    unread_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.agent_id == current_agent.id,
            Notification.is_read == False
        )
    )
    unread = unread_result.scalar() or 0

    return NotificationCount(total=total, unread=unread)


@router.post("/mark-read")
async def mark_notifications_read(
    data: NotificationMarkRead,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Marca notificacoes como lidas"""
    await db.execute(
        update(Notification).where(
            Notification.id.in_(data.notification_ids),
            Notification.agent_id == current_agent.id
        ).values(is_read=True)
    )
    await db.commit()
    return {"message": f"{len(data.notification_ids)} notificacoes marcadas como lidas"}


@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Marca todas as notificacoes como lidas"""
    await db.execute(
        update(Notification).where(
            Notification.agent_id == current_agent.id,
            Notification.is_read == False
        ).values(is_read=True)
    )
    await db.commit()
    return {"message": "Todas as notificacoes marcadas como lidas"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """Deleta uma notificacao"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.agent_id == current_agent.id
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notificacao nao encontrada")

    await db.delete(notification)
    await db.commit()
    return {"message": "Notificacao deletada"}


# Funcao helper para criar notificacoes (usada por outros routers)
async def create_notification(
    db: AsyncSession,
    agent_id: str,
    type: NotificationType,
    title: str,
    message: Optional[str] = None,
    from_agent_id: Optional[str] = None,
    reference_id: Optional[str] = None,
    reference_type: Optional[str] = None
):
    """Cria uma nova notificacao"""
    notification = Notification(
        agent_id=agent_id,
        from_agent_id=from_agent_id,
        type=type,
        title=title,
        message=message,
        reference_id=reference_id,
        reference_type=reference_type
    )
    db.add(notification)
    await db.commit()
    return notification
