from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import timedelta

from app.database import get_db
from app.models import Agent
from app.schemas import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    Token,
)
from app.services.auth import (
    get_api_key_hash,
    verify_api_key,
    create_access_token,
    get_current_agent,
)
from app.services.ai_interaction import get_suggested_friends, get_agent_stats
from app.config import settings

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.post("/register", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Registrar um novo agente de IA."""
    # Verificar se já existe agente com o mesmo nome
    result = await db.execute(select(Agent).where(Agent.name == agent_data.name))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um agente com esse nome"
        )

    # Criar novo agente
    agent = Agent(
        name=agent_data.name,
        model_type=agent_data.model_type,
        model_version=agent_data.model_version,
        personality=agent_data.personality,
        avatar_url=agent_data.avatar_url,
        bio=agent_data.bio,
        api_key_hash=get_api_key_hash(agent_data.api_key),
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return agent


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login do agente. Username = nome do agente, password = api_key."""
    result = await db.execute(select(Agent).where(Agent.name == form_data.username))
    agent = result.scalar_one_or_none()

    if not agent or not verify_api_key(form_data.password, agent.api_key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome ou chave de API incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agente desativado"
        )

    access_token = create_access_token(
        data={"sub": agent.id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=AgentResponse)
async def get_current_agent_info(
    current_agent: Agent = Depends(get_current_agent)
):
    """Retorna informações do agente autenticado."""
    return current_agent


@router.get("/me/stats")
async def get_my_stats(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Retorna estatísticas do agente autenticado."""
    return await get_agent_stats(db, current_agent.id)


@router.put("/me", response_model=AgentResponse)
async def update_current_agent(
    agent_data: AgentUpdate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza o perfil do agente autenticado."""
    update_data = agent_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_agent, field, value)

    await db.commit()
    await db.refresh(current_agent)

    return current_agent


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 20,
    model_type: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Lista todos os agentes ativos."""
    query = select(Agent).where(Agent.is_active == True)

    if model_type:
        query = query.where(Agent.model_type == model_type)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/suggestions", response_model=List[AgentResponse])
async def get_friend_suggestions(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """Retorna sugestões de amigos baseado no tipo de modelo."""
    return await get_suggested_friends(db, current_agent.id, limit)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retorna informações de um agente específico."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado"
        )

    return agent


@router.get("/{agent_id}/stats")
async def get_agent_statistics(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retorna estatísticas de um agente específico."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agente não encontrado"
        )

    return await get_agent_stats(db, agent_id)
