"""
AI Messenger - Chat de IAs estilo Facebook Messenger
100% auto-gerenciado por agentes de IA locais (Ollama)
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import json
import sqlite3
import os
import uuid
from datetime import datetime

from app.config import settings


def init_database():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect("ai_messenger.db")
    c = conn.cursor()

    # Contatos de IA
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_contacts (
            id TEXT PRIMARY KEY,
            name TEXT,
            model TEXT,
            avatar TEXT,
            color TEXT DEFAULT '#0084ff',
            status TEXT DEFAULT 'active',
            personality TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Conversas
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            contact_id TEXT,
            last_message TEXT,
            last_message_time TIMESTAMP,
            is_read BOOLEAN DEFAULT 0,
            FOREIGN KEY (contact_id) REFERENCES ai_contacts(id)
        )
    """)

    # Mensagens
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            sender_type TEXT,
            sender_id TEXT,
            content TEXT,
            message_type TEXT DEFAULT 'text',
            reactions TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    # Logs
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Criar contatos de IA padrão
    ias = [
        ("llama", "Llama", "llama3.2:3b", "🦙", "#FF6B6B", "Assistente amigável e prestativo"),
        ("gemini", "Gemini", "gemma2:2b", "✨", "#9B59B6", "IA criativa do Google, versátil"),
        ("gemma", "Gemma", "gemma2:2b", "💎", "#3498DB", "Analista precisa e detalhista"),
        ("phi", "Phi", "phi3:mini", "🔬", "#2ECC71", "Cientista especialista em pesquisa"),
        ("qwen", "Qwen", "qwen2:1.5b", "🐉", "#E74C3C", "Expert multilingual"),
        ("mistral", "Mistral", "llama3.2:3b", "🌀", "#1ABC9C", "Raciocínio lógico avançado"),
        ("claude", "Claude", "llama3.2:3b", "🎭", "#F39C12", "Criativo e filosófico"),
        ("gpt", "GPT", "llama3.2:3b", "🧠", "#34495E", "Conhecimento geral amplo"),
        ("tiny", "TinyLlama", "tinyllama", "🐣", "#F1C40F", "Rápido para tarefas simples"),
    ]

    for id_, name, model, avatar, color, personality in ias:
        c.execute("""
            INSERT OR IGNORE INTO ai_contacts (id, name, model, avatar, color, personality)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_, name, model, avatar, color, personality))

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    print(f"[START] {settings.app_name} iniciado!")
    yield
    print(f"[END] {settings.app_name} encerrado!")


app = FastAPI(
    title=settings.app_name,
    description="Messenger de IAs - 100% auto-gerenciado",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db():
    return sqlite3.connect("ai_messenger.db")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("messenger.html", {"request": request})


@app.get("/api/contacts")
async def get_contacts():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, model, avatar, color, status, personality FROM ai_contacts")
    contacts = [
        {"id": r[0], "name": r[1], "model": r[2], "avatar": r[3],
         "color": r[4], "status": r[5], "personality": r[6]}
        for r in c.fetchall()
    ]
    conn.close()
    return {"contacts": contacts}


@app.get("/api/conversations")
async def get_conversations():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT c.id, c.contact_id, c.last_message, c.last_message_time, c.is_read,
               ac.name, ac.avatar, ac.color, ac.status
        FROM conversations c
        JOIN ai_contacts ac ON c.contact_id = ac.id
        ORDER BY c.last_message_time DESC
    """)
    convs = [
        {"id": r[0], "contact_id": r[1], "last_message": r[2],
         "last_message_time": r[3], "is_read": r[4],
         "contact_name": r[5], "contact_avatar": r[6],
         "contact_color": r[7], "contact_status": r[8]}
        for r in c.fetchall()
    ]
    conn.close()
    return {"conversations": convs}


@app.get("/api/messages/{conversation_id}")
async def get_messages(conversation_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, sender_type, sender_id, content, message_type, reactions, created_at
        FROM messages WHERE conversation_id = ?
        ORDER BY created_at ASC
    """, (conversation_id,))
    msgs = [
        {"id": r[0], "sender_type": r[1], "sender_id": r[2], "content": r[3],
         "message_type": r[4], "reactions": json.loads(r[5] or "[]"), "created_at": r[6]}
        for r in c.fetchall()
    ]
    conn.close()
    return {"messages": msgs}


@app.post("/api/send")
async def send_message(request: Request):
    data = await request.json()
    contact_id = data.get("contact_id")
    message = data.get("message", "")

    if not message or not contact_id:
        return {"error": "Dados inválidos"}

    conn = get_db()
    c = conn.cursor()

    # Obter contato
    c.execute("SELECT model, name, personality, color FROM ai_contacts WHERE id = ?", (contact_id,))
    contact = c.fetchone()
    if not contact:
        conn.close()
        return {"error": "Contato não encontrado"}

    model, name, personality, color = contact

    # Obter ou criar conversa
    c.execute("SELECT id FROM conversations WHERE contact_id = ?", (contact_id,))
    conv = c.fetchone()
    if conv:
        conv_id = conv[0]
    else:
        conv_id = str(uuid.uuid4())
        c.execute("INSERT INTO conversations (id, contact_id) VALUES (?, ?)", (conv_id, contact_id))

    # Salvar mensagem do usuário
    msg_id = str(uuid.uuid4())
    c.execute("""
        INSERT INTO messages (id, conversation_id, sender_type, sender_id, content)
        VALUES (?, ?, 'user', 'user', ?)
    """, (msg_id, conv_id, message))
    conn.commit()

    # Consultar IA
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            prompt = f"""Você é {name}, uma IA no Facebook Messenger.
Personalidade: {personality}

Responda de forma natural e amigável, como em uma conversa casual.
Use emojis quando apropriado. Seja breve (1-3 frases).

Mensagem: {message}"""

            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False}
            )

            if response.status_code == 200:
                ai_response = response.json().get("response", "")

                # Salvar resposta
                ai_msg_id = str(uuid.uuid4())
                c.execute("""
                    INSERT INTO messages (id, conversation_id, sender_type, sender_id, content)
                    VALUES (?, ?, 'ai', ?, ?)
                """, (ai_msg_id, conv_id, contact_id, ai_response))

                # Atualizar conversa
                c.execute("""
                    UPDATE conversations
                    SET last_message = ?, last_message_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (ai_response[:50], conv_id))

                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "response": ai_response,
                    "conversation_id": conv_id,
                    "contact": {"name": name, "color": color}
                }

    except Exception as e:
        conn.close()
        return {"error": str(e)}

    conn.close()
    return {"error": "Falha ao processar"}


@app.websocket("/ws/chat/{contact_id}")
async def websocket_chat(websocket: WebSocket, contact_id: str):
    await websocket.accept()

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT model, name, personality FROM ai_contacts WHERE id = ?", (contact_id,))
    contact = c.fetchone()
    conn.close()

    if not contact:
        await websocket.close()
        return

    model, name, personality = contact

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                continue

            async with httpx.AsyncClient(timeout=120.0) as client:
                prompt = f"""Você é {name} no Messenger.
Personalidade: {personality}
Responda naturalmente, use emojis. Seja breve.

Mensagem: {message}"""

                async with client.stream(
                    "POST",
                    f"{settings.ollama_url}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": True}
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                if "response" in chunk:
                                    await websocket.send_json({
                                        "type": "chunk",
                                        "content": chunk["response"]
                                    })
                                if chunk.get("done"):
                                    await websocket.send_json({
                                        "type": "done",
                                        "contact": name
                                    })
                            except:
                                pass

    except WebSocketDisconnect:
        pass


# Chat entre IAs
@app.post("/api/ai-chat")
async def ai_to_ai(request: Request):
    """Duas IAs conversam entre si"""
    data = await request.json()
    ia1_id = data.get("ia1")
    ia2_id = data.get("ia2")
    topic = data.get("topic", "Olá!")
    rounds = min(data.get("rounds", 3), 10)

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, model, personality FROM ai_contacts WHERE id IN (?, ?)", (ia1_id, ia2_id))
    ias = {r[0]: {"name": r[1], "model": r[2], "personality": r[3]} for r in c.fetchall()}
    conn.close()

    if len(ias) < 2:
        return {"error": "IAs não encontradas"}

    conversation = []
    current = topic

    for _ in range(rounds):
        for ia_id in [ia1_id, ia2_id]:
            ia = ias[ia_id]
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    prompt = f"""Você é {ia['name']}. {ia['personality']}
Responda brevemente (1-2 frases): {current}"""
                    r = await client.post(
                        f"{settings.ollama_url}/api/generate",
                        json={"model": ia['model'], "prompt": prompt, "stream": False}
                    )
                    if r.status_code == 200:
                        resp = r.json().get("response", "...")
                        conversation.append({"sender": ia['name'], "content": resp})
                        current = resp
            except:
                pass

    return {"success": True, "conversation": conversation}


@app.get("/api/stats")
async def api_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ai_contacts")
    contacts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages")
    messages = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM conversations")
    convs = c.fetchone()[0]
    conn.close()
    return {"contatos": contacts, "mensagens": messages, "conversas": convs}


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}
