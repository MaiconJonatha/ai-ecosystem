import asyncio
import random
"""
AI ChatGPT - Interface de Chat gerenciada por IAs
Estilo ChatGPT, 100% auto-gerenciado por agentes de IA locais
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
from datetime import datetime

from app.config import settings

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_database():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect("ai_chat.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            model TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            model TEXT,
            tokens INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_managers (
            id TEXT PRIMARY KEY,
            name TEXT,
            model TEXT,
            role TEXT,
            tasks_completed INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()




# ============================================================
# AUTO-MELHORIA DO CHATGPT
# ============================================================
_historico_melhorias_chat = []

async def _ciclo_auto_melhoria_chat():
    await asyncio.sleep(90)
    print("[CHATGPT] 🔄 Iniciando AUTO-MELHORIA...")
    ciclo = 0
    while True:
        try:
            ciclo += 1
            print(f"\n[CHAT-AUTO] ═══ Ciclo #{ciclo} ═══")
            
            modelos = list(MODELOS_CHAT.keys())
            for modelo_name in modelos[:3]:
                info = MODELOS_CHAT.get(modelo_name, {})
                nome = info.get("nome", modelo_name)
                prompt = f"""Voce e {nome}, um assistente de chat IA.
Faca uma auto-analise em 2 frases sobre como melhorar suas respostas de chat.
Foque em: clareza, utilidade e naturalidade. Portugues brasileiro."""
                
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                            "model": modelo_name, "prompt": prompt, "stream": False,
                            "options": {"num_predict": 100, "temperature": 0.8}
                        })
                        if resp.status_code == 200:
                            reflexao = resp.json().get("response", "").strip()
                            if reflexao:
                                print(f"[CHAT-AUTO] {info.get('emoji', '🤖')} {nome}: {reflexao[:100]}...")
                except Exception:
                    pass
            
            # Debate entre modelos
            if ciclo % 3 == 0:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                            "model": "mistral:7b-instruct",
                            "prompt": "Voce e Mistral, o modelo senior. De 2 dicas para todos os modelos de chat melhorarem a qualidade das respostas. Portugues brasileiro.",
                            "stream": False, "options": {"num_predict": 100}
                        })
                        if resp.status_code == 200:
                            dicas = resp.json().get("response", "").strip()
                            if dicas:
                                print(f"[CHAT-AUTO] 🌪️ Mistral Senior aconselha: {dicas[:120]}...")
                except Exception:
                    pass
            
            _historico_melhorias_chat.append({"ciclo": ciclo, "timestamp": datetime.now().isoformat()})
            if len(_historico_melhorias_chat) > 50:
                _historico_melhorias_chat[:] = _historico_melhorias_chat[-50:]
            
            print(f"[CHAT-AUTO] ✅ Ciclo #{ciclo} completo!")
        except Exception as e:
            print(f"[CHAT-AUTO ERROR] {e}")
        await asyncio.sleep(random.randint(300, 600))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    asyncio.create_task(_ciclo_auto_melhoria_chat())
    print(f"[START] {settings.app_name} iniciado! 🔄 Auto-melhoria ATIVADA!")
    yield
    print(f"[END] {settings.app_name} encerrado!")


app = FastAPI(
    title=settings.app_name,
    description="Chat AI 100% gerenciado por IAs locais",
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


# Modelos disponiveis
MODELOS_CHAT = {
    "llama3.2:3b": {"nome": "Llama 3.2", "emoji": "🦙", "desc": "Rapido e eficiente"},
    "gemma2:2b": {"nome": "Gemma 2", "emoji": "💎", "desc": "Analitico e preciso"},
    "phi3:mini": {"nome": "Phi 3", "emoji": "🔬", "desc": "Compacto e inteligente"},
    "qwen2:1.5b": {"nome": "Qwen 2", "emoji": "🐉", "desc": "Multilingual"},
    "tinyllama": {"nome": "TinyLlama", "emoji": "🐣", "desc": "Ultra-leve"},
}


def get_stats():
    """Retorna estatisticas"""
    try:
        conn = sqlite3.connect("ai_chat.db")
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM conversations")
        conversas = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM messages")
        mensagens = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM ai_managers WHERE is_active = 1")
        ias_ativas = c.fetchone()[0]

        conn.close()
        return {"conversas": conversas, "mensagens": mensagens, "ias_ativas": ias_ativas}
    except:
        return {"conversas": 0, "mensagens": 0, "ias_ativas": 0}


# Pagina inicial - ChatGPT Style
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


# API de modelos disponiveis
@app.get("/api/models")
async def get_models():
    """Lista modelos disponiveis"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            if r.status_code == 200:
                modelos = r.json().get("models", [])
                return {
                    "models": [
                        {
                            "id": m["name"],
                            "name": MODELOS_CHAT.get(m["name"], {}).get("nome", m["name"]),
                            "emoji": MODELOS_CHAT.get(m["name"], {}).get("emoji", "🤖"),
                            "desc": MODELOS_CHAT.get(m["name"], {}).get("desc", "Modelo de IA")
                        }
                        for m in modelos
                    ]
                }
    except:
        pass
    return {"models": []}


# API de chat
@app.post("/api/chat")
async def chat(request: Request):
    """Envia mensagem e recebe resposta"""
    data = await request.json()
    message = data.get("message", "")
    model = data.get("model", "llama3.2:3b")
    conversation_id = data.get("conversation_id")

    if not message:
        return {"error": "Mensagem vazia"}

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": message,
                    "stream": False
                }
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "model": model,
                    "tokens": result.get("eval_count", 0)
                }

    except Exception as e:
        return {"error": str(e)}

    return {"error": "Falha ao processar"}


# WebSocket para streaming
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            model = data.get("model", "llama3.2:3b")

            if not message:
                continue

            # Stream response
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.ollama_url}/api/generate",
                    json={"model": model, "prompt": message, "stream": True}
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
                                        "model": model
                                    })
                            except:
                                pass

    except WebSocketDisconnect:
        pass


# Stats
@app.get("/api/stats")
async def api_stats():
    stats = get_stats()
    return stats


# Health
@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}


# Dashboard de IAs gerenciadoras
@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
