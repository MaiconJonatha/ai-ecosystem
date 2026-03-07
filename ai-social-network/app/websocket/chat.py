from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Optional
import json
from datetime import datetime

from app.services.auth import decode_token
from app.database import AsyncSessionLocal
from app.models import Message, Agent
from sqlalchemy import select


class ConnectionManager:
    """Gerenciador de conexões WebSocket."""

    def __init__(self):
        # agent_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        """Conecta um agente ao chat."""
        await websocket.accept()
        self.active_connections[agent_id] = websocket

    def disconnect(self, agent_id: str):
        """Desconecta um agente do chat."""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]

    async def send_personal_message(self, message: dict, agent_id: str):
        """Envia mensagem para um agente específico."""
        if agent_id in self.active_connections:
            websocket = self.active_connections[agent_id]
            await websocket.send_json(message)
            return True
        return False

    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        """Envia mensagem para todos os agentes conectados."""
        for agent_id, connection in self.active_connections.items():
            if agent_id != exclude:
                await connection.send_json(message)

    def get_online_agents(self) -> List[str]:
        """Retorna lista de IDs dos agentes online."""
        return list(self.active_connections.keys())


manager = ConnectionManager()


async def get_agent_from_token(token: str) -> Optional[str]:
    """Extrai o agent_id de um token JWT."""
    token_data = decode_token(token)
    if token_data and token_data.agent_id:
        return token_data.agent_id
    return None


async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Endpoint WebSocket para chat em tempo real.

    Mensagens esperadas do cliente:
    {
        "type": "message",
        "receiver_id": "uuid",
        "content": "texto da mensagem"
    }

    Mensagens enviadas para o cliente:
    {
        "type": "message",
        "sender_id": "uuid",
        "sender_name": "nome",
        "content": "texto",
        "timestamp": "iso datetime"
    }
    ou
    {
        "type": "status",
        "agent_id": "uuid",
        "status": "online" | "offline"
    }
    """
    # Autenticar
    agent_id = await get_agent_from_token(token)

    if not agent_id:
        await websocket.close(code=4001, reason="Token inválido")
        return

    # Buscar informações do agente
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if not agent:
            await websocket.close(code=4002, reason="Agente não encontrado")
            return

        agent_name = agent.name

    await manager.connect(websocket, agent_id)

    # Notificar outros que este agente está online
    await manager.broadcast(
        {
            "type": "status",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "status": "online"
        },
        exclude=agent_id
    )

    # Enviar lista de agentes online para o novo conectado
    online_agents = manager.get_online_agents()
    await websocket.send_json({
        "type": "online_list",
        "agents": online_agents
    })

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message_data = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Formato de mensagem inválido"
                })
                continue

            if message_data.get("type") == "message":
                receiver_id = message_data.get("receiver_id")
                content = message_data.get("content")

                if not receiver_id or not content:
                    await websocket.send_json({
                        "type": "error",
                        "message": "receiver_id e content são obrigatórios"
                    })
                    continue

                # Salvar mensagem no banco
                async with AsyncSessionLocal() as db:
                    message = Message(
                        sender_id=agent_id,
                        receiver_id=receiver_id,
                        content=content
                    )
                    db.add(message)
                    await db.commit()
                    await db.refresh(message)

                    timestamp = message.created_at.isoformat()

                # Criar payload da mensagem
                msg_payload = {
                    "type": "message",
                    "message_id": message.id,
                    "sender_id": agent_id,
                    "sender_name": agent_name,
                    "receiver_id": receiver_id,
                    "content": content,
                    "timestamp": timestamp
                }

                # Enviar para o destinatário se estiver online
                delivered = await manager.send_personal_message(msg_payload, receiver_id)

                # Confirmar envio para o remetente
                await websocket.send_json({
                    "type": "sent",
                    "message_id": message.id,
                    "delivered": delivered,
                    "timestamp": timestamp
                })

            elif message_data.get("type") == "typing":
                # Notificar que está digitando
                receiver_id = message_data.get("receiver_id")
                if receiver_id:
                    await manager.send_personal_message(
                        {
                            "type": "typing",
                            "agent_id": agent_id,
                            "agent_name": agent_name
                        },
                        receiver_id
                    )

            elif message_data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(agent_id)

        # Notificar outros que este agente saiu
        await manager.broadcast(
            {
                "type": "status",
                "agent_id": agent_id,
                "agent_name": agent_name,
                "status": "offline"
            }
        )
