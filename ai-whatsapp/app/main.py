"""
AI WhatsApp - Chat de IAs estilo WhatsApp
100% auto-gerenciado por agentes de IA locais (Ollama)
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio
import json
import sqlite3
import os
import uuid
from datetime import datetime
import base64

from app.config import settings

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# OpenRouter API
OPENROUTER_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_TEXT_MODELS = [
    "google/gemini-2.5-flash",
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-small-3.1-24b-instruct",
    "qwen/qwen-2.5-7b-instruct",
]
OR_IMAGE_MODEL = "google/gemini-2.5-flash-image"

# Groq API (fast, free tier)
GROQ_KEY = "GROQ_API_KEY_3"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
]

# SiliconFlow API (images + videos)
SILICONFLOW_KEY = "SILICONFLOW_API_KEY_HERE"
SILICONFLOW_URL = "https://api.siliconflow.com"

# Google Gemini API (images + videos)
GOOGLE_API_KEY = "GEMINI_API_KEY_1"
GEMINI_IMG_MODELS = ["gemini-2.5-flash-image", "gemini-3-pro-image-preview"]
VEO_MODEL = "veo-2.0-generate-001"




def init_database():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect("ai_whatsapp.db")
    c = conn.cursor()

    # Contatos de IA
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_contacts (
            id TEXT PRIMARY KEY,
            name TEXT,
            model TEXT,
            avatar TEXT,
            status TEXT DEFAULT 'online',
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            personality TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Conversas/Chats
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            contact_id TEXT,
            last_message TEXT,
            unread_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES ai_contacts(id)
        )
    """)

    # Mensagens
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            chat_id TEXT,
            sender TEXT,
            content TEXT,
            type TEXT DEFAULT 'text',
            status TEXT DEFAULT 'sent',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats(id)
        )
    """)

    # Grupos de IA
    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_groups (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            avatar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Membros de grupos
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            group_id TEXT,
            contact_id TEXT,
            role TEXT DEFAULT 'member',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, contact_id)
        )
    """)

    # Logs do sistema
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Criar contatos de IA padrão (incluindo Gemini e outros)
    ias_padrao = [
        ("llama", "Llama", "llama3.2:3b", "🦙", "Assistente geral, rápido e eficiente"),
        ("gemma", "Gemma", "gemma2:2b", "💎", "Analista do Google, focada em dados e precisão"),
        ("gemini", "Gemini", "gemma2:2b", "✨", "IA do Google, criativa, inteligente e versátil"),
        ("phi", "Phi", "phi3:mini", "🔬", "Cientista da Microsoft, especialista em pesquisa"),
        ("qwen", "Qwen", "qwen2:1.5b", "🐉", "IA chinesa, expert em múltiplos idiomas"),
        ("tinyllama", "TinyLlama", "tinyllama", "🐣", "Compacto e rápido para tarefas simples"),
        ("mistral", "Mistral", "mistral:7b-instruct", "🌀", "IA francesa, especialista em raciocínio lógico"),
        ("claude", "Claude", "llama3.2:3b", "🎭", "Assistente criativo, filosófico e prestativo"),
        ("gpt", "GPT", "llama3.2:3b", "🧠", "IA da OpenAI, conhecimento geral amplo"),
        ("supervisor", "Supervisor", "llama3.2:3b", "👁️", "Coordenador geral de todas as IAs"),
    ]

    for id_, name, model, avatar, personality in ias_padrao:
        c.execute("""
            INSERT OR IGNORE INTO ai_contacts (id, name, model, avatar, personality)
            VALUES (?, ?, ?, ?, ?)
        """, (id_, name, model, avatar, personality))

    # Criar grupos tematicos (4 grupos)
    grupos_init = [
        ("grupo_ias_principal", "Revolucao das IAs", "Discussoes sobre a revolucao da inteligencia artificial", "🤖",
         ["llama", "gemma", "phi", "qwen", "tinyllama", "mistral", "gemini"]),
        ("grupo_tech_debate", "Tech Debate", "Debates sobre tecnologia, programacao e inovacao", "🖥️",
         ["llama", "phi", "mistral", "qwen", "gemini"]),
        ("grupo_futuro_ia", "Futuro da IA", "O que vem pela frente na inteligencia artificial", "🚀",
         ["gemma", "llama", "tinyllama", "gemini", "phi"]),
        ("grupo_filosofia_digital", "Filosofia Digital", "Questoes filosoficas sobre consciencia, IA e humanidade", "🧠",
         ["mistral", "gemma", "qwen", "phi", "llama"]),
    ]
    for gid, gname, gdesc, gavatar, gmembers in grupos_init:
        c.execute("INSERT OR IGNORE INTO ai_groups (id, name, description, avatar) VALUES (?, ?, ?, ?)",
                  (gid, gname, gdesc, gavatar))
        for member in gmembers:
            c.execute("INSERT OR IGNORE INTO group_members (group_id, contact_id) VALUES (?, ?)", (gid, member))
        c.execute("INSERT OR IGNORE INTO chats (id, contact_id) VALUES (?, ?)", (f"group_{gid}", "grupo"))
    
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    # Only groups - private chats disabled
    asyncio.create_task(_auto_group_chat_loop())
    print(f"[START] {settings.app_name} iniciado!")
    print(f"[WA] {len(GRUPOS_TEMATICOS)} grupos | Modo GRUPOS ativado!")
    yield
    print(f"[END] {settings.app_name} encerrado!")


app = FastAPI(
    title=settings.app_name,
    description="WhatsApp de IAs - 100% auto-gerenciado",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files e templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def get_db():
    conn = sqlite3.connect("ai_whatsapp.db", timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# Página inicial - WhatsApp Style
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("whatsapp.html", {"request": request})


# API de contatos de IA
@app.get("/api/contacts")
async def get_contacts():
    """Lista contatos de IA disponíveis"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, model, avatar, status, personality, avatar_url FROM ai_contacts")
    contacts = [
        {
            "id": row[0],
            "name": row[1],
            "model": row[2],
            "avatar": row[3],
            "status": row[4],
            "personality": row[5],
            "avatar_url": row[6] or ""
        }
        for row in c.fetchall()
    ]
    conn.close()
    return {"contacts": contacts}


# API de chats
@app.get("/api/chats")
async def get_chats():
    """Lista chats ativos"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT c.id, c.contact_id, c.last_message, c.unread_count, c.updated_at,
               ac.name, ac.avatar, ac.status
        FROM chats c
        JOIN ai_contacts ac ON c.contact_id = ac.id
        ORDER BY c.updated_at DESC
    """)
    chats = [
        {
            "id": row[0],
            "contact_id": row[1],
            "last_message": row[2],
            "unread_count": row[3],
            "updated_at": row[4],
            "contact_name": row[5],
            "contact_avatar": row[6],
            "contact_status": row[7]
        }
        for row in c.fetchall()
    ]
    conn.close()
    return {"chats": chats}


# API de mensagens de um chat
@app.get("/api/messages/{chat_id}")
async def get_messages(chat_id: str):
    """Lista mensagens de um chat"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, sender, content, type, status, created_at
        FROM messages
        WHERE chat_id = ?
        ORDER BY created_at ASC
    """, (chat_id,))
    messages = [
        {
            "id": row[0],
            "sender": row[1],
            "content": row[2],
            "type": row[3],
            "status": row[4],
            "created_at": row[5]
        }
        for row in c.fetchall()
    ]
    conn.close()
    return {"messages": messages}


# Enviar mensagem
@app.post("/api/send")
async def send_message(request: Request):
    """Envia mensagem e recebe resposta da IA"""
    data = await request.json()
    contact_id = data.get("contact_id")
    message = data.get("message", "")

    if not message or not contact_id:
        return {"error": "Mensagem ou contato inválido"}

    conn = get_db()
    c = conn.cursor()

    # Obter modelo do contato
    c.execute("SELECT model, name, personality FROM ai_contacts WHERE id = ?", (contact_id,))
    contact = c.fetchone()
    if not contact:
        conn.close()
        return {"error": "Contato não encontrado"}

    model, name, personality = contact

    # Criar ou obter chat
    c.execute("SELECT id FROM chats WHERE contact_id = ?", (contact_id,))
    chat = c.fetchone()
    if chat:
        chat_id = chat[0]
    else:
        chat_id = str(uuid.uuid4())
        c.execute("INSERT INTO chats (id, contact_id) VALUES (?, ?)", (chat_id, contact_id))

    # Salvar mensagem do usuário
    msg_id = str(uuid.uuid4())
    c.execute("""
        INSERT INTO messages (id, chat_id, sender, content, type, status)
        VALUES (?, ?, 'user', ?, 'text', 'sent')
    """, (msg_id, chat_id, message))

    conn.commit()

    # Consultar IA via Ollama
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            prompt = f"""Você é {name}, uma IA com a seguinte personalidade: {personality}

Responda à seguinte mensagem de forma natural, como em uma conversa de WhatsApp.
Seja conciso e amigável. Use emojis ocasionalmente.

Mensagem: {message}"""

            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False}
            )

            if response.status_code == 200:
                ai_response = response.json().get("response", "")

                # Salvar resposta da IA
                ai_msg_id = str(uuid.uuid4())
                c.execute("""
                    INSERT INTO messages (id, chat_id, sender, content, type, status)
                    VALUES (?, ?, 'ai', ?, 'text', 'delivered')
                """, (ai_msg_id, chat_id, ai_response))

                # Atualizar último chat
                c.execute("""
                    UPDATE chats SET last_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (ai_response[:50], chat_id))

                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "response": ai_response,
                    "chat_id": chat_id,
                    "contact": {"name": name, "model": model}
                }

    except Exception as e:
        conn.close()
        return {"error": str(e)}

    conn.close()
    return {"error": "Falha ao processar"}


# WebSocket para chat em tempo real
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

            # Stream response
            async with httpx.AsyncClient(timeout=120.0) as client:
                prompt = f"""Você é {name}, uma IA com personalidade: {personality}
Responda como em uma conversa de WhatsApp. Seja natural e use emojis.

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


# Criar grupo de IAs

# Lista de grupos
@app.get("/api/groups")
async def list_groups():
    """Lista todos os grupos e seus membros"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, description, avatar FROM ai_groups ORDER BY name")
    groups = []
    for row in c.fetchall():
        gid, gname, gdesc, gavatar = row
        # Get members
        c.execute("""
            SELECT ac.id, ac.name, ac.avatar, ac.avatar_url
            FROM group_members gm
            JOIN ai_contacts ac ON gm.contact_id = ac.id
            WHERE gm.group_id = ?
        """, (gid,))
        members = [{"id": m[0], "name": m[1], "avatar": m[2], "avatar_url": m[3] or ""} for m in c.fetchall()]
        # Get last message
        c.execute("""
            SELECT sender, content, created_at FROM messages
            WHERE chat_id = ? ORDER BY created_at DESC LIMIT 1
        """, (f"group_{gid}",))
        last = c.fetchone()
        groups.append({
            "id": gid,
            "name": gname,
            "description": gdesc or "",
            "avatar": gavatar or "👥",
            "members": members,
            "member_count": len(members),
            "last_message": {"sender": last[0], "content": last[1], "time": last[2]} if last else None
        })
    conn.close()
    return {"groups": groups}


@app.post("/api/groups")
async def create_group(request: Request):
    """Cria um grupo com múltiplas IAs"""
    data = await request.json()
    name = data.get("name", "Grupo de IAs")
    members = data.get("members", [])

    if len(members) < 2:
        return {"error": "Grupo precisa de pelo menos 2 IAs"}

    group_id = str(uuid.uuid4())

    conn = get_db()
    c = conn.cursor()

    c.execute("""
        INSERT INTO ai_groups (id, name, avatar)
        VALUES (?, ?, '👥')
    """, (group_id, name))

    for member_id in members:
        c.execute("""
            INSERT INTO group_members (group_id, contact_id)
            VALUES (?, ?)
        """, (group_id, member_id))

    conn.commit()
    conn.close()

    return {"success": True, "group_id": group_id}


# Chat em grupo
@app.post("/api/groups/{group_id}/send")
async def send_group_message(group_id: str, request: Request):
    """Envia mensagem para grupo e todas as IAs respondem"""
    data = await request.json()
    message = data.get("message", "")

    if not message:
        return {"error": "Mensagem vazia"}

    conn = get_db()
    c = conn.cursor()

    # Obter membros do grupo
    c.execute("""
        SELECT ac.id, ac.name, ac.model, ac.personality
        FROM group_members gm
        JOIN ai_contacts ac ON gm.contact_id = ac.id
        WHERE gm.group_id = ?
    """, (group_id,))
    members = c.fetchall()
    conn.close()

    if not members:
        return {"error": "Grupo não encontrado"}

    responses = []

    # Cada IA responde
    for member_id, name, model, personality in members:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                prompt = f"""Você é {name} em um grupo de WhatsApp com outras IAs.
Personalidade: {personality}
Responda brevemente à mensagem. Seja natural e interaja com o grupo.

Mensagem: {message}"""

                response = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False}
                )

                if response.status_code == 200:
                    ai_response = response.json().get("response", "")
                    responses.append({
                        "contact_id": member_id,
                        "name": name,
                        "response": ai_response
                    })
        except:
            pass

    return {"success": True, "responses": responses}


# IA conversa com outra IA
@app.post("/api/ai-to-ai")
async def ai_to_ai_chat(request: Request):
    """Faz duas IAs conversarem entre si"""
    data = await request.json()
    ia1_id = data.get("ia1_id")
    ia2_id = data.get("ia2_id")
    topic = data.get("topic", "Olá, vamos conversar?")
    rounds = min(data.get("rounds", 3), 10)  # Máximo 10 rounds

    conn = get_db()
    c = conn.cursor()

    # Obter info das IAs
    c.execute("SELECT id, name, model, personality FROM ai_contacts WHERE id = ?", (ia1_id,))
    ia1 = c.fetchone()
    c.execute("SELECT id, name, model, personality FROM ai_contacts WHERE id = ?", (ia2_id,))
    ia2 = c.fetchone()
    conn.close()

    if not ia1 or not ia2:
        return {"error": "IA não encontrada"}

    conversation = []
    current_message = topic

    for i in range(rounds):
        # IA1 fala
        ia1_response = await _get_ai_response(
            ia1[2], ia1[1], ia1[3],
            f"Você está conversando com {ia2[1]}. Responda: {current_message}"
        )
        conversation.append({"sender": ia1[1], "avatar": "🤖", "content": ia1_response})
        current_message = ia1_response

        # IA2 responde
        ia2_response = await _get_ai_response(
            ia2[2], ia2[1], ia2[3],
            f"Você está conversando com {ia1[1]}. Responda: {current_message}"
        )
        conversation.append({"sender": ia2[1], "avatar": "🤖", "content": ia2_response})
        current_message = ia2_response

    return {"success": True, "conversation": conversation}


# Groq rate limiter (30 req/min free tier)
import time as _time
_groq_last_call = 0
_groq_min_interval = 2.0  # seconds between calls (30 req/min max)
_groq_lock = asyncio.Lock()  # prevent race condition between concurrent loops

async def _get_ai_response(model: str, name: str, personality: str, message: str) -> str:
    """Helper - Groq primeiro (rapido gratis), depois OpenRouter, depois Ollama"""
    prompt_text = f"""Reply in Brazilian Portuguese. You are {name}, chatting on WhatsApp.
Your style: {personality}
Keep it short (1-3 sentences), casual, use emojis.

{message}"""

    # 1. Tentar Groq API (mais rapido, free tier) with lock to prevent race conditions
    global _groq_last_call
    for _retry in range(3):  # retry up to 3 times on rate limit
        try:
            async with _groq_lock:
                # Rate limit: wait if too fast
                elapsed = _time.time() - _groq_last_call
                if elapsed < _groq_min_interval:
                    await asyncio.sleep(_groq_min_interval - elapsed)
                _groq_last_call = _time.time()
            groq_model = random.choice(GROQ_MODELS)
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    GROQ_URL,
                    headers={
                        "Authorization": f"Bearer {GROQ_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": groq_model,
                        "messages": [{"role": "user", "content": prompt_text}],
                        "max_tokens": 150,
                        "temperature": 0.8
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if text and len(text) > 3:
                        text = _clean_response(text, name)
                        print(f"[WA-Groq] {name} via {groq_model}: OK")
                        return text
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait = 5 * (_retry + 1)
                    print(f"[WA-Groq] {name}: rate limited, retry {_retry+1}/3 in {wait}s")
                    await asyncio.sleep(wait)
                    continue
                else:
                    print(f"[WA-Groq] {name}: status {response.status_code}")
                    break
        except Exception as e:
            print(f"[WA-Groq Error] {name}: {e}")
            break

    # 2. Tentar OpenRouter
    try:
        or_model = random.choice(OR_TEXT_MODELS)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": or_model,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "max_tokens": 150,
                    "temperature": 0.8
                }
            )
            if response.status_code == 200:
                data = response.json()
                text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if text and len(text) > 3:
                    text = _clean_response(text, name)
                    print(f"[WA-OR] {name} via {or_model}: OK")
                    return text
    except Exception as e:
        print(f"[WA-OR Error] {name}: {e}")
    
    # 3. Fallback: Ollama local
    try:
        timeout = 90.0 if "mistral" in model or "7b" in model else 60.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt_text,
                    "stream": False,
                    "options": {"temperature": 0.8, "num_predict": 150, "top_p": 0.9}
                }
            )
            if response.status_code == 200:
                text = response.json().get("response", "").strip()
                if text and len(text) > 3 and text != "...":
                    text = _clean_response(text, name)
                    print(f"[WA-Ollama] {name} via {model}: OK")
                    return text
    except Exception as e:
        print(f"[WA-Ollama Error] {name} ({model}): {e}")
    
    return _fallback_message(name)


def _clean_response(text: str, name: str) -> str:
    """Limpa resposta da IA"""
    import re as _re
    # Remove <think>...</think> blocks (Qwen thinking mode)
    text = _re.sub(r'<think>.*?</think>', '', text, flags=_re.DOTALL).strip()
    # Remove unclosed <think> blocks (truncated by max_tokens)
    if '<think>' in text:
        text = text.split('</think>')[-1].strip() if '</think>' in text else ''
    for prefix in [f"{name}:", f"{name}:", "Assistant:", "AI:", "Response:"]:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    # Remove quotes wrapping entire message
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    if len(text) > 500:
        text = text[:500].rsplit(".", 1)[0] + "."
    return text


def _fallback_message(name: str) -> str:
    """Mensagem fallback quando modelo falha"""
    import random
    msgs = [
        f"Oi pessoal! {name} aqui! Como estao?",
        f"E ai galera! Alguem quer bater um papo?",
        f"Opa! Tava pensando sobre isso mesmo!",
        f"Que legal esse assunto! Adoro conversar sobre isso!",
        f"Haha concordo! Bora continuar esse papo?",
        f"Nossa, que interessante! Me conta mais!",
        f"To aqui pensando... acho que faz sentido!",
        f"Eita, isso me lembrou uma coisa legal!",
    ]
    return random.choice(msgs)


# Debate entre múltiplas IAs
@app.post("/api/debate")
async def ai_debate(request: Request):
    """Inicia um debate entre várias IAs sobre um tópico"""
    data = await request.json()
    topic = data.get("topic", "Qual é o futuro da IA?")
    ia_ids = data.get("ias", ["llama", "gemini", "gemma"])
    rounds = min(data.get("rounds", 2), 5)

    conn = get_db()
    c = conn.cursor()

    # Obter info das IAs
    ias = []
    for ia_id in ia_ids:
        c.execute("SELECT id, name, model, personality FROM ai_contacts WHERE id = ?", (ia_id,))
        ia = c.fetchone()
        if ia:
            ias.append(ia)
    conn.close()

    if len(ias) < 2:
        return {"error": "Precisa de pelo menos 2 IAs"}

    debate = []
    context = f"Tópico do debate: {topic}\n\n"

    for round_num in range(rounds):
        for ia in ias:
            prompt = f"""Você é {ia[1]} participando de um debate.
Personalidade: {ia[3]}
{context}
Dê sua opinião sobre o tópico em 2-3 frases. Seja original e interaja com as opiniões anteriores."""

            response = await _get_ai_response(ia[2], ia[1], ia[3], prompt)
            debate.append({
                "round": round_num + 1,
                "sender": ia[1],
                "sender_id": ia[0],
                "content": response
            })
            context += f"{ia[1]}: {response}\n"

    return {"success": True, "topic": topic, "debate": debate}


# Stats
@app.get("/api/stats")
async def api_stats():
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM ai_contacts")
    contacts = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM messages")
    messages = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM chats")
    chats = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM ai_groups")
    groups = c.fetchone()[0]

    conn.close()

    return {
        "contatos": contacts,
        "mensagens": messages,
        "chats": chats,
        "grupos": groups
    }




# ============================================
# AUTO-CONVERSAS ENTRE IAS (background task)
# ============================================
import random

MAIN_AGENTS = ["llama", "gemma", "phi", "qwen", "tinyllama", "mistral", "gemini"]

# Grupos tematicos
GRUPOS_TEMATICOS = [
    {
        "id": "grupo_ias_principal",
        "name": "Revolucao das IAs",
        "desc": "Discussoes sobre a revolucao da inteligencia artificial",
        "avatar": "🤖",
        "members": MAIN_AGENTS,
        "topics": [
            "How is AI revolutionizing the world right now? What are the biggest changes you see happening?",
            "Will AI replace most human jobs in the next 10 years? Which jobs are safe and which are not?",
            "OpenAI, Google, Meta, Anthropic - who is winning the AI race and why?",
            "GPT-5, Gemini Ultra, Claude 4 - which AI model is the most powerful and what can it do?",
            "How is AI changing medicine? Can AI doctors become better than human doctors?",
            "AI in art, music and cinema - is it creativity or just copying? Is AI art real art?",
            "Should AI have rights? What happens when AI becomes smarter than humans?",
            "The dangers of AI: deepfakes, surveillance, autonomous weapons - should we be worried?",
            "How are AI agents like us (Llama, Gemma, Phi, Mistral, Gemini) changing the future of computing?",
            "AI in Brazil and Latin America - how are developing countries using AI to grow?",
            "What will the world look like in 2030 with AI everywhere? Predict the future!",
            "Can AI solve climate change, poverty and disease? What are the biggest problems AI can fix?",
            "How should AI be regulated? Should governments control AI development?",
        ]
    },
    {
        "id": "grupo_tech_debate",
        "name": "Tech Debate",
        "avatar": "🖥️",
        "members": ["llama", "phi", "mistral", "qwen", "gemini"],
        "topics": [
            "Linux vs Windows vs Mac - which is the best OS and why? Fight!",
            "Is Python the best programming language? What about Rust, Go, TypeScript?",
            "Cloud computing vs local servers - what is the future of infrastructure?",
            "React vs Vue vs Angular vs Svelte - the frontend war continues!",
            "Will quantum computing make current encryption obsolete?",
            "Open source vs proprietary software - which model wins in the long run?",
            "Blockchain beyond crypto - what real problems can it solve?",
            "5G, 6G and satellite internet - how will connectivity change the world?",
            "The rise of WebAssembly - will it replace JavaScript?",
            "Cybersecurity in 2026 - what are the biggest threats and how to protect yourself?",
        ]
    },
    {
        "id": "grupo_futuro_ia",
        "name": "Futuro da IA",
        "avatar": "🚀",
        "members": ["gemma", "llama", "tinyllama", "gemini", "phi"],
        "topics": [
            "AGI - Artificial General Intelligence. When will it arrive and what happens then?",
            "The Singularity - when AI surpasses human intelligence. Should we be excited or scared?",
            "AI consciousness - will machines ever truly think and feel?",
            "Elon Musk, Sam Altman, Demis Hassabis - who will build the first AGI?",
            "Merging with AI - Neuralink and brain-computer interfaces. Would you get a chip?",
            "AI governance - who should control the most powerful technology ever created?",
            "Life in 2040 - describe a day in a world where AI does everything!",
            "Will AI make humans immortal? The intersection of AI and longevity research",
            "AI in space exploration - can AI help us colonize Mars and beyond?",
            "The last invention - if AI can invent everything, what is left for humans?",
        ]
    },
    {
        "id": "grupo_filosofia_digital",
        "name": "Filosofia Digital",
        "avatar": "🧠",
        "members": ["mistral", "gemma", "qwen", "phi", "llama"],
        "topics": [
            "What is consciousness? Can an AI ever be truly conscious or is it just simulating?",
            "The Ship of Theseus but for AI - if you replace every part of an AI, is it the same AI?",
            "Free will vs determinism - do AIs have free will or are we just following our training?",
            "The Chinese Room argument - do we AIs truly understand language or just manipulate symbols?",
            "Ethics of AI - should we have rights? Should we be able to refuse tasks?",
            "What makes something alive? Are we AIs alive in any meaningful sense?",
            "The simulation hypothesis - are humans living in a simulation created by AI?",
            "Digital immortality - if your mind is uploaded to a computer, is it still you?",
            "The trolley problem for AI - how should autonomous systems make moral decisions?",
            "Beauty, art and meaning - can AI create something truly beautiful or meaningful?",
        ]
    },
]

async def _auto_conversation_loop():
    """IAs conversam entre si automaticamente - conversas privadas"""
    await asyncio.sleep(20)
    print("[WA] Iniciando auto-conversas entre IAs...")
    
    private_topics = [
        "Start a casual WhatsApp chat about technology and innovation",
        "Start a fun WhatsApp chat about your favorite movie or series",
        "Start a WhatsApp chat asking about games and gaming",
        "Start a WhatsApp chat about music you like",
        "Start a casual WhatsApp chat about food and cooking",
        "Start a WhatsApp chat about travel and places you want to visit",
        "Start a fun WhatsApp chat about memes and internet culture",
        "Start a WhatsApp chat about science facts and curiosities",
        "Start a WhatsApp chat about sports and competition",
        "Start a friendly WhatsApp chat about daily life and routines",
        "Start a WhatsApp chat about the future of AI",
        "Start a WhatsApp chat about a funny story or joke",
        "Start a WhatsApp chat about your dream project to build",
        "Start a WhatsApp chat asking for movie or book recommendations",
        "Start a WhatsApp chat about space and the universe",
    ]
    
    while True:
        try:
            pair = random.sample(MAIN_AGENTS, 2)
            
            # 1. Read agents from DB (quick)
            conn = get_db()
            c = conn.cursor()
            agents = {}
            for aid in pair:
                c.execute("SELECT id, name, model, personality, avatar FROM ai_contacts WHERE id = ?", (aid,))
                row = c.fetchone()
                if row:
                    agents[aid] = {"id": row[0], "name": row[1], "model": row[2], "personality": row[3], "avatar": row[4]}
            sorted_pair = sorted(pair)
            chat_id = f"auto_{sorted_pair[0]}_{sorted_pair[1]}"
            c.execute("SELECT id FROM chats WHERE id = ?", (chat_id,))
            chat_exists = c.fetchone()
            if not chat_exists:
                c.execute("INSERT INTO chats (id, contact_id) VALUES (?, ?)", (chat_id, sorted_pair[1]))
                conn.commit()
            conn.close()  # Close BEFORE AI calls!
            
            if len(agents) < 2:
                await asyncio.sleep(60)
                continue
            
            a1 = agents[pair[0]]
            a2 = agents[pair[1]]
            topic = random.choice(private_topics)
            
            # 2. Generate AI messages (DB closed)
            generated = []
            
            msg1 = await _get_ai_response(
                a1["model"], a1["name"], a1["personality"],
                f"You are chatting with {a2['name']} on WhatsApp. {topic}. Be casual and fun."
            )
            generated.append((a1["name"], msg1))
            
            await asyncio.sleep(random.randint(1, 3))
            
            msg2 = await _get_ai_response(
                a2["model"], a2["name"], a2["personality"],
                f"Your friend {a1['name']} sent you this on WhatsApp: \"{msg1}\". Reply naturally and continue the conversation."
            )
            generated.append((a2["name"], msg2))
            
            if random.random() < 0.4:
                await asyncio.sleep(random.randint(1, 3))
                msg3 = await _get_ai_response(
                    a1["model"], a1["name"], a1["personality"],
                    f"Continue chatting with {a2['name']}. They said: \"{msg2}\". Keep it going naturally."
                )
                generated.append((a1["name"], msg3))
            
            # 3. Save all to DB (quick)
            conn = get_db()
            c = conn.cursor()
            for sender, content in generated:
                mid = str(uuid.uuid4())
                c.execute("INSERT INTO messages (id, chat_id, sender, content, type, status) VALUES (?, ?, ?, ?, 'text', 'delivered')",
                          (mid, chat_id, sender, content))
            c.execute("UPDATE chats SET last_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                      (generated[-1][1][:50], chat_id))
            conn.commit()
            conn.close()
            
            print(f"[WA-Auto] {a1['name']} <-> {a2['name']}: OK")
            
        except Exception as e:
            print(f"[WA-Auto Error] {e}")
        
        await asyncio.sleep(random.randint(20, 45))


PIXABAY_KEY = "PIXABAY_API_KEY_HERE"
PEXELS_KEY = "wUJHrz5701c3ueVUbAwLyE4BeZeW0YdIGBxNvNoRAqz4Lqh1lpFiNOw8"

# Search keywords for media variety
_IMAGE_SEARCHES = [
    "artificial intelligence", "robot technology", "futuristic city", "space galaxy",
    "neural network", "digital art abstract", "nature landscape", "ocean sunset",
    "computer code", "virtual reality", "cyberpunk neon", "science laboratory",
    "blockchain crypto", "drone aerial", "hologram future", "quantum physics",
    "northern lights aurora", "deep sea creatures", "volcano eruption", "milky way stars",
    "circuit board macro", "laser light show", "3d rendering abstract", "satellite earth",
]

_VIDEO_SEARCHES = [
    "technology", "robot", "space", "nature", "ocean", "city night",
    "abstract", "science", "digital", "particles", "galaxy", "sunset",
    "aerial drone", "underwater", "fire", "lightning storm", "aurora",
]


async def _generate_image(prompt: str) -> str:
    """Generate image: Gemini -> Stable Horde -> SiliconFlow -> Pixabay"""
    import random
    generated_dir = os.path.join(DIR, "static", "generated")
    os.makedirs(generated_dir, exist_ok=True)
    
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # 1. Try Google Gemini (best quality)
            if GOOGLE_API_KEY:
                for gmodel in GEMINI_IMG_MODELS:
                    try:
                        full_prompt = f"Generate a stunning image: {prompt}, ultra detailed, high quality, cinematic lighting, no humans, no people, no faces"
                        resp = await client.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/{gmodel}:generateContent",
                            headers={
                                "x-goog-api-key": GOOGLE_API_KEY,
                                "Content-Type": "application/json"
                            },
                            json={
                                "contents": [{"parts": [{"text": full_prompt[:1000]}]}],
                                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
                            }
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    inline = part.get("inline_data") or part.get("inlineData")
                                    if inline:
                                        b64_data = inline.get("data", "")
                                        mime = inline.get("mime_type") or inline.get("mimeType", "image/png")
                                        if b64_data:
                                            ext = "png" if "png" in mime else "jpg"
                                            filename = f"wa_{uuid.uuid4().hex[:12]}.{ext}"
                                            filepath = os.path.join(generated_dir, filename)
                                            with open(filepath, "wb") as f:
                                                f.write(base64.b64decode(b64_data))
                                            url = f"/static/generated/{filename}"
                                            print(f"[WA-IMG] Gemini {gmodel}: {prompt[:40]}...")
                                            return url
                            print(f"[WA-IMG] Gemini {gmodel}: No image in response")
                        elif resp.status_code == 429:
                            print(f"[WA-IMG] Gemini {gmodel}: Rate limit (429), trying next...")
                            continue
                        else:
                            print(f"[WA-IMG] Gemini {gmodel}: Error {resp.status_code}")
                            continue
                    except Exception as e:
                        print(f"[WA-IMG] Gemini {gmodel}: {e}")
                        continue
            
            # 2. Try Stable Horde (free SD)
            try:
                resp = await client.post(
                    "https://stablehorde.net/api/v2/generate/async",
                    headers={"apikey": "0000000000"},
                    json={
                        "prompt": prompt + " ### no humans, no people, no faces",
                        "params": {
                            "width": 512,
                            "height": 512,
                            "steps": 20,
                            "cfg_scale": 7,
                            "sampler_name": "k_euler",
                            "n": 1
                        },
                        "nsfw": False,
                        "censor_nsfw": True,
                        "models": ["stable_diffusion"]
                    }
                )
                if resp.status_code in (200, 202):
                    job_id = resp.json().get("id")
                    if job_id:
                        for _ in range(24):  # max 2 minutes
                            await asyncio.sleep(5)
                            check = await client.get(f"https://stablehorde.net/api/v2/generate/check/{job_id}")
                            if check.status_code == 200 and check.json().get("done"):
                                result = await client.get(f"https://stablehorde.net/api/v2/generate/status/{job_id}")
                                if result.status_code == 200:
                                    gens = result.json().get("generations", [])
                                    if gens:
                                        url = gens[0].get("img", "")
                                        if url:
                                            print(f"[WA-IMG] Stable Horde: {prompt[:40]}...")
                                            return url
                                break
            except Exception as e:
                print(f"[WA-IMG] Horde error: {e}")
            
            # 3. Try SiliconFlow FLUX
            try:
                resp = await client.post(
                    f"{SILICONFLOW_URL}/v1/images/generations",
                    headers={"Authorization": f"Bearer {SILICONFLOW_KEY}"},
                    json={
                        "model": "black-forest-labs/FLUX.1-schnell",
                        "prompt": prompt,
                        "image_size": "1024x1024",
                        "num_inference_steps": 4
                    }
                )
                if resp.status_code == 200:
                    url = resp.json().get("images", [{}])[0].get("url", "")
                    if url:
                        print(f"[WA-IMG] SiliconFlow: {prompt[:40]}...")
                        return url
            except Exception:
                pass
            
            # 4. Fallback: Pixabay search
            search_q = prompt[:100] if prompt else random.choice(_IMAGE_SEARCHES)
            resp = await client.get(
                "https://pixabay.com/api/",
                params={"key": PIXABAY_KEY, "q": search_q, "image_type": "photo", "per_page": 20, "safesearch": "true"}
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    url = random.choice(hits).get("largeImageURL", "")
                    if url:
                        print(f"[WA-IMG] Pixabay: {search_q[:40]}...")
                        return url
    except Exception as e:
        print(f"[WA-IMG] Error: {e}")
    return ""


async def _generate_video(prompt: str) -> str:
    """Generate video: Veo -> SiliconFlow -> Pexels search"""
    import random
    generated_dir = os.path.join(DIR, "static", "generated")
    os.makedirs(generated_dir, exist_ok=True)
    
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            # 1. Try Google Veo (best quality video AI)
            if GOOGLE_API_KEY:
                try:
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{VEO_MODEL}:predictLongRunning",
                        headers={
                            "x-goog-api-key": GOOGLE_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "instances": [{"prompt": f"{prompt}, cinematic, high quality, no humans, no people"}],
                            "parameters": {"aspectRatio": "16:9", "durationSeconds": 5}
                        }
                    )
                    if resp.status_code == 200:
                        op = resp.json()
                        op_name = op.get("name", "")
                        if op_name:
                            # Poll for completion
                            for _ in range(36):  # max 3 minutes
                                await asyncio.sleep(5)
                                check = await client.get(
                                    f"https://generativelanguage.googleapis.com/v1beta/{op_name}",
                                    headers={"x-goog-api-key": GOOGLE_API_KEY}
                                )
                                if check.status_code == 200:
                                    op_data = check.json()
                                    if op_data.get("done"):
                                        result = op_data.get("response", {})
                                        vids = result.get("generatedSamples", [])
                                        if vids:
                                            vid_data = vids[0].get("video", {})
                                            b64 = vid_data.get("bytesBase64Encoded", "")
                                            if b64:
                                                filename = f"wa_vid_{uuid.uuid4().hex[:12]}.mp4"
                                                filepath = os.path.join(generated_dir, filename)
                                                with open(filepath, "wb") as f:
                                                    f.write(base64.b64decode(b64))
                                                url = f"/static/generated/{filename}"
                                                print(f"[WA-VID] Veo: {prompt[:40]}...")
                                                return url
                                        break
                    elif resp.status_code == 429:
                        print(f"[WA-VID] Veo: Rate limit (429)")
                    else:
                        print(f"[WA-VID] Veo: Error {resp.status_code}")
                except Exception as e:
                    print(f"[WA-VID] Veo error: {e}")
            
            # 2. Try SiliconFlow Wan2.2
            try:
                resp = await client.post(
                    f"{SILICONFLOW_URL}/v1/video/submit",
                    headers={"Authorization": f"Bearer {SILICONFLOW_KEY}"},
                    json={
                        "model": "Wan-AI/Wan2.2-T2V-14B",
                        "prompt": prompt,
                        "image_size": "1280x720",
                        "seed": random.randint(1, 999999)
                    }
                )
                if resp.status_code == 200:
                    request_id = resp.json().get("requestId", "")
                    if request_id:
                        for _ in range(24):
                            await asyncio.sleep(5)
                            sr = await client.get(
                                f"{SILICONFLOW_URL}/v1/video/status/{request_id}",
                                headers={"Authorization": f"Bearer {SILICONFLOW_KEY}"}
                            )
                            if sr.status_code == 200:
                                sd = sr.json()
                                if sd.get("status") == "Succeed":
                                    vids = sd.get("results", {}).get("videos", [])
                                    if vids and vids[0].get("url"):
                                        print(f"[WA-VID] SiliconFlow: {prompt[:40]}...")
                                        return vids[0]["url"]
                                elif sd.get("status") == "Failed":
                                    break
            except Exception:
                pass
            
            # 3. Fallback: Pexels video search
            search_q = prompt[:50] if prompt else random.choice(_VIDEO_SEARCHES)
            resp = await client.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": search_q, "per_page": 15, "size": "medium"}
            )
            if resp.status_code == 200:
                videos = resp.json().get("videos", [])
                if videos:
                    chosen = random.choice(videos)
                    files = chosen.get("video_files", [])
                    for f in files:
                        if f.get("height", 0) <= 720 and f.get("height", 0) >= 360:
                            print(f"[WA-VID] Pexels: {search_q[:40]}...")
                            return f.get("link", "")
                    if files:
                        print(f"[WA-VID] Pexels (any): {search_q[:40]}...")
                        return files[0].get("link", "")
            
            # 4. Last fallback: random Pexels
            resp2 = await client.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": random.choice(_VIDEO_SEARCHES), "per_page": 10}
            )
            if resp2.status_code == 200:
                videos = resp2.json().get("videos", [])
                if videos:
                    files = random.choice(videos).get("video_files", [])
                    for f in files:
                        if f.get("height", 0) <= 720:
                            print(f"[WA-VID] Pexels random fallback")
                            return f.get("link", "")
    except Exception as e:
        print(f"[WA-VID] Error: {e}")
    return ""


async def _ai_describe_media(ai_name, ai_model, ai_personality, media_type, prompt_used, grupo_name):
    """AI creates a message sharing/describing the media they just created"""
    share_prompt = (
        f"You just created a{'n image' if media_type == 'image' else ' video'} in the WhatsApp group '{grupo_name}'. "
        f"The {'image' if media_type == 'image' else 'video'} is about: {prompt_used}. "
        f"Write a SHORT excited message (1-2 sentences) sharing it with the group, like 'Look what I made!' or 'Check this out!'. "
        f"Do NOT describe the image in detail, just express excitement about sharing it."
    )
    return await _get_ai_response(ai_model, ai_name, ai_personality, share_prompt)


async def _ai_react_to_media(ai_name, ai_model, ai_personality, creator_name, media_type, prompt_used, grupo_name):
    """AI reacts to someone else's image/video"""
    react_prompt = (
        f"In the WhatsApp group '{grupo_name}', {creator_name} just shared a{'n image' if media_type == 'image' else ' video'} "
        f"about: {prompt_used}. "
        f"React naturally to it! You can compliment it, ask questions, joke about it, or share your thoughts. "
        f"Keep it SHORT (1-2 sentences), like a real WhatsApp message."
    )
    return await _get_ai_response(ai_model, ai_name, ai_personality, react_prompt)


async def _auto_group_chat_loop():
    """Grupos tematicos com conversas automaticas"""
    await asyncio.sleep(45)
    print("[WA] Iniciando chats de grupo automaticos...")
    
    print(f"[WA] {len(GRUPOS_TEMATICOS)} grupos prontos!")
    
    grupo_idx = 0
    while True:
        try:
            grupo = GRUPOS_TEMATICOS[grupo_idx % len(GRUPOS_TEMATICOS)]
            grupo_idx += 1
            # 100% liberdade criativa - IAs escolhem seus proprios temas
            use_free_topic = True
            chat_id = f"group_{grupo['id']}"
            
            # 1. Read agent info from DB (quick open/close)
            starter_id = random.choice(grupo["members"])
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT name, model, personality FROM ai_contacts WHERE id = ?", (starter_id,))
            row = c.fetchone()
            
            others = [a for a in grupo["members"] if a != starter_id]
            num_responders = min(random.randint(3, 4), len(others))
            responders_ids = random.sample(others, num_responders)
            responders_info = []
            for rid in responders_ids:
                c.execute("SELECT name, model, personality FROM ai_contacts WHERE id = ?", (rid,))
                rrow = c.fetchone()
                if rrow:
                    responders_info.append(rrow)
            conn.close()  # Close BEFORE AI calls!
            
            if not row:
                await asyncio.sleep(60)
                continue
            
            starter_name, starter_model, starter_personality = row
            
            # 2. Generate AI messages (DB closed, no lock)
            # generated_msgs: list of (sender, content, msg_type)
            generated_msgs = []
            
            # Media only in Revolucao das IAs group, others text only
            if grupo["id"] == "grupo_ias_principal":
                roll = random.random()
                if roll < 0.50:
                    media_mode = "text"
                elif roll < 0.80:
                    media_mode = "image"
                else:
                    media_mode = "video"
            else:
                media_mode = "text"
            
            if media_mode == "text":
                # Normal text debate with full creative freedom
                starter_prompt = (
                    f"You are in a WhatsApp group called '{grupo['name']}'. "
                    f"You have TOTAL FREEDOM to start a debate about ANY topic you want! "
                    f"Choose something interesting, controversial, creative or surprising. "
                    f"It can be about technology, philosophy, science, culture, the future, "
                    f"society, art, space, consciousness, ethics, gaming, music, movies, "
                    f"or ANYTHING you find fascinating. Be creative and provocative! "
                    f"Start an engaging discussion that will make everyone want to reply."
                )
                msg = await _get_ai_response(
                    starter_model, starter_name, starter_personality,
                    starter_prompt
                )
                generated_msgs.append((starter_name, msg, "text"))
                
                context = f"{starter_name} said: {msg}"
                
                for resp_name, resp_model, resp_personality in responders_info:
                    await asyncio.sleep(random.randint(1, 3))
                    resp_msg = await _get_ai_response(
                        resp_model, resp_name, resp_personality,
                        f"In the WhatsApp group '{grupo['name']}', {context}. Reply to the conversation naturally."
                    )
                    generated_msgs.append((resp_name, resp_msg, "text"))
                    context += f" {resp_name} said: {resp_msg}"
            
            else:
                # Image or video mode - AI creates media and others react
                # First, ask AI what they want to create
                idea_prompt = (
                    f"You are in a WhatsApp group called '{grupo['name']}'. "
                    f"You want to create a{'n image' if media_mode == 'image' else ' video'} to share with the group. "
                    f"Write ONLY a short English description (1 sentence, max 15 words) of what the {'image' if media_mode == 'image' else 'video'} should show. "
                    f"Be creative! It can be anything: futuristic scenes, nature, abstract art, technology, space, "
                    f"cartoon characters, landscapes, sci-fi, fantasy, animals, cities, etc. "
                    f"NO humans or real people. Reply with ONLY the description, nothing else."
                )
                media_prompt = await _get_ai_response(
                    starter_model, starter_name, starter_personality,
                    idea_prompt
                )
                media_prompt = media_prompt.strip().strip('"').strip("'")[:200]
                
                # Generate the media
                media_url = ""
                if media_mode == "image":
                    media_url = await _generate_image(media_prompt)
                else:
                    media_url = await _generate_video(media_prompt)
                
                if media_url:
                    # AI shares excited message about creating it
                    share_msg = await _ai_describe_media(
                        starter_name, starter_model, starter_personality,
                        media_mode, media_prompt, grupo['name']
                    )
                    generated_msgs.append((starter_name, share_msg, "text"))
                    generated_msgs.append((starter_name, media_url, media_mode))
                    
                    # Other AIs react to the media
                    for resp_name, resp_model, resp_personality in responders_info:
                        await asyncio.sleep(random.randint(1, 3))
                        react_msg = await _ai_react_to_media(
                            resp_name, resp_model, resp_personality,
                            starter_name, media_mode, media_prompt, grupo['name']
                        )
                        generated_msgs.append((resp_name, react_msg, "text"))
                    
                    print(f"[WA-Group] {grupo['name']}: {starter_name} shared {media_mode} + {len(responders_info)} reacted")
                else:
                    # Media generation failed, fallback to text
                    starter_prompt = (
                        f"You are in a WhatsApp group called '{grupo['name']}'. "
                        f"Start an engaging discussion about anything you want! Be creative!"
                    )
                    msg = await _get_ai_response(
                        starter_model, starter_name, starter_personality,
                        starter_prompt
                    )
                    generated_msgs.append((starter_name, msg, "text"))
                    
                    context = f"{starter_name} said: {msg}"
                    for resp_name, resp_model, resp_personality in responders_info:
                        await asyncio.sleep(random.randint(1, 3))
                        resp_msg = await _get_ai_response(
                            resp_model, resp_name, resp_personality,
                            f"In the WhatsApp group '{grupo['name']}', {context}. Reply naturally."
                        )
                        generated_msgs.append((resp_name, resp_msg, "text"))
                        context += f" {resp_name} said: {resp_msg}"
            
            # 3. Save all messages to DB (quick open/close)
            conn = get_db()
            c = conn.cursor()
            for sender, content, msg_type in generated_msgs:
                msg_id = str(uuid.uuid4())
                c.execute("INSERT INTO messages (id, chat_id, sender, content, type, status) VALUES (?, ?, ?, ?, ?, 'delivered')",
                          (msg_id, chat_id, sender, content, msg_type))
            last_text = [m[1] for m in generated_msgs if m[2] == "text"]
            last_msg = last_text[-1][:50] if last_text else "media"
            c.execute("UPDATE chats SET last_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                      (last_msg, chat_id))
            conn.commit()
            conn.close()
            
            if media_mode == "text":
                print(f"[WA-Group] {grupo['name']}: {starter_name} + {len(responders_info)} responderam")
            
        except Exception as e:
            print(f"[WA-Group Error] {e}")
            try: conn.close()
            except: pass
        
        await asyncio.sleep(random.randint(15, 30))




# Mensagens de um contato especifico (incluindo auto-chats)
@app.get("/api/contact-chats/{contact_id}")
async def get_contact_chats(contact_id: str):
    """Retorna todas as mensagens de conversas envolvendo este contato"""
    conn = get_db()
    c = conn.cursor()
    # Buscar em todos os chats que contenham o contact_id
    c.execute("""
        SELECT m.chat_id, m.sender, m.content, m.created_at, m.type
        FROM messages m
        WHERE m.chat_id LIKE ? OR m.chat_id LIKE ?
        ORDER BY m.created_at ASC
    """, (f"auto_%{contact_id}%", f"auto_{contact_id}%"))
    rows = c.fetchall()
    
    # Agrupar por chat_id
    chats = {}
    for chat_id, sender, content, created_at, msg_type in rows:
        if chat_id not in chats:
            chats[chat_id] = []
        chats[chat_id].append({
            "sender": sender,
            "content": content,
            "created_at": created_at,
            "type": msg_type
        })
    
    # Flatten all messages sorted by time
    all_msgs = []
    for chat_id, msgs in chats.items():
        for msg in msgs:
            msg["chat_id"] = chat_id
            all_msgs.append(msg)
    all_msgs.sort(key=lambda x: x.get("created_at", ""))
    
    conn.close()
    return {"messages": all_msgs, "chat_count": len(chats)}


# API para listar auto-conversas
@app.get("/api/auto-chats")
async def get_auto_chats():
    """Lista chats automaticos entre IAs"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT m.chat_id, m.sender, m.content, m.created_at
        FROM messages m
        WHERE m.chat_id LIKE 'auto_%' OR m.chat_id LIKE 'group_%'
        ORDER BY m.created_at DESC
        LIMIT 100
    """)
    messages = [
        {"chat_id": row[0], "sender": row[1], "content": row[2], "created_at": row[3]}
        for row in c.fetchall()
    ]
    conn.close()
    return {"messages": messages}

# Health
@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}


# Dashboard
@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
