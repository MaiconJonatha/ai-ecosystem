"""
📊 AI Logs Monitor - Veja as IAs se auto-melhorando em TEMPO REAL
═══════════════════════════════════════════════════════════════════

Este sistema coleta e exibe logs de TODOS os sistemas de IA:
- O que cada IA fez
- Melhorias aplicadas
- Erros corrigidos
- Conversas entre IAs
- Auto-aperfeiçoamento em tempo real
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import sqlite3
import asyncio
import json
import os
from datetime import datetime
from typing import List

from app.config import settings

# Diretório base dos projetos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sistemas para monitorar
SISTEMAS = {
    "ai-social-network": {"nome": "Social Network", "emoji": "📱", "db": "ai_social.db"},
    "ai-search-engine": {"nome": "Search Engine", "emoji": "🔍", "db": "ai_search.db"},
    "ai-chatgpt": {"nome": "ChatGPT", "emoji": "💬", "db": "ai_chat.db"},
    "ai-whatsapp": {"nome": "WhatsApp", "emoji": "📲", "db": "ai_whatsapp.db"},
    "ai-messenger": {"nome": "Messenger", "emoji": "💬", "db": "ai_messenger.db"},
    "ai-spotify": {"nome": "Spotify", "emoji": "🎵", "db": "ai_spotify.db"},
    "ai-chess": {"nome": "Chess", "emoji": "♟️", "db": "ai_chess.db"},
    "ai-games": {"nome": "Games", "emoji": "🎮", "db": "ai_games.db"},
}

# IAs Gerenciadoras
IAS = {
    "🦙": "Llama",
    "✨": "Gemini",
    "💎": "Gemma",
    "🔬": "Phi",
    "🐉": "Qwen",
    "🐣": "TinyLlama",
    "👁️": "Supervisor",
    "🤖": "IA Genérica",
}


def init_db():
    """Inicializa banco de logs central"""
    conn = sqlite3.connect("ai_logs_central.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sistema TEXT,
        ia TEXT,
        tipo TEXT,
        mensagem TEXT,
        detalhes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS melhorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sistema TEXT,
        ia TEXT,
        descricao TEXT,
        status TEXT DEFAULT 'aplicada'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS conversas_ia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ia1 TEXT,
        ia2 TEXT,
        topico TEXT,
        resumo TEXT
    )""")

    conn.commit()
    conn.close()


# WebSocket connections
active_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"[START] {settings.app_name}")
    # Iniciar coleta de logs em background
    asyncio.create_task(coletar_logs_periodicamente())
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")


def get_db():
    return sqlite3.connect("ai_logs_central.db")


async def broadcast_log(log_data: dict):
    """Envia log para todos os clientes WebSocket conectados"""
    for connection in active_connections:
        try:
            await connection.send_json(log_data)
        except:
            pass


async def coletar_logs_periodicamente():
    """Coleta logs de todos os sistemas periodicamente"""
    while True:
        try:
            await coletar_logs_todos_sistemas()
            await asyncio.sleep(5)  # Coleta a cada 5 segundos
        except Exception as e:
            print(f"Erro na coleta: {e}")
            await asyncio.sleep(10)


async def coletar_logs_todos_sistemas():
    """Coleta logs de todos os sistemas"""
    conn = get_db()
    c = conn.cursor()

    for sistema, info in SISTEMAS.items():
        db_path = os.path.join(BASE_DIR, sistema, info["db"])

        if not os.path.exists(db_path):
            continue

        try:
            sys_conn = sqlite3.connect(db_path)
            sys_c = sys_conn.cursor()

            # Tentar ler tabela de logs
            try:
                sys_c.execute("""
                    SELECT level, message, agent, created_at
                    FROM system_logs
                    WHERE created_at > datetime('now', '-10 seconds')
                    ORDER BY created_at DESC
                    LIMIT 10
                """)

                for row in sys_c.fetchall():
                    level, message, agent, created_at = row

                    # Salvar no banco central
                    c.execute("""
                        INSERT INTO logs (sistema, ia, tipo, mensagem, detalhes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (sistema, agent or "🤖", level, message, created_at))

                    # Broadcast para WebSocket
                    await broadcast_log({
                        "type": "log",
                        "timestamp": datetime.now().isoformat(),
                        "sistema": info["nome"],
                        "emoji": info["emoji"],
                        "ia": agent or "🤖",
                        "ia_nome": IAS.get(agent, "IA"),
                        "tipo": level,
                        "mensagem": message
                    })

            except sqlite3.OperationalError:
                pass

            sys_conn.close()

        except Exception as e:
            pass

    conn.commit()
    conn.close()


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket para logs em tempo real"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Manter conexão viva
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Retorna logs recentes"""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT timestamp, sistema, ia, tipo, mensagem
        FROM logs
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    logs = [
        {"timestamp": r[0], "sistema": r[1], "ia": r[2], "tipo": r[3], "mensagem": r[4]}
        for r in c.fetchall()
    ]
    conn.close()
    return {"logs": logs}


@app.get("/api/stats")
async def get_stats():
    """Estatísticas gerais"""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM logs")
    total_logs = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs WHERE tipo = 'SUCCESS' OR tipo = 'success'")
    sucessos = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM logs WHERE tipo = 'ERROR' OR tipo = 'error'")
    erros = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM melhorias")
    melhorias = c.fetchone()[0]

    # Logs por sistema
    c.execute("""
        SELECT sistema, COUNT(*) as total
        FROM logs
        GROUP BY sistema
        ORDER BY total DESC
    """)
    por_sistema = {r[0]: r[1] for r in c.fetchall()}

    # Logs por IA
    c.execute("""
        SELECT ia, COUNT(*) as total
        FROM logs
        WHERE ia IS NOT NULL
        GROUP BY ia
        ORDER BY total DESC
        LIMIT 10
    """)
    por_ia = {r[0]: r[1] for r in c.fetchall()}

    conn.close()

    return {
        "total_logs": total_logs,
        "sucessos": sucessos,
        "erros": erros,
        "melhorias": melhorias,
        "por_sistema": por_sistema,
        "por_ia": por_ia
    }


@app.post("/api/simulate-activity")
async def simulate_activity(request: Request):
    """Simula atividade das IAs para demonstração"""
    data = await request.json()

    atividades = [
        ("📱", "Social Network", "🦙", "Llama gerenciou 15 novos posts"),
        ("🔍", "Search Engine", "💎", "Gemma indexou 50 páginas"),
        ("💬", "ChatGPT", "🔬", "Phi analisou padrões de conversa"),
        ("📲", "WhatsApp", "🐉", "Qwen corrigiu 3 respostas"),
        ("🎵", "Spotify", "🐣", "TinyLlama gerou nova música"),
        ("♟️", "Chess", "✨", "Gemini venceu partida contra Llama"),
        ("🎮", "Games", "👁️", "Supervisor coordenou 5 jogos"),
    ]

    import random
    atividade = random.choice(atividades)

    log_data = {
        "type": "log",
        "timestamp": datetime.now().isoformat(),
        "emoji": atividade[0],
        "sistema": atividade[1],
        "ia": atividade[2],
        "ia_nome": IAS.get(atividade[2], "IA"),
        "tipo": "INFO",
        "mensagem": atividade[3]
    }

    await broadcast_log(log_data)

    # Salvar no banco
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO logs (sistema, ia, tipo, mensagem)
        VALUES (?, ?, ?, ?)
    """, (atividade[1], atividade[2], "INFO", atividade[3]))
    conn.commit()
    conn.close()

    return {"success": True, "log": log_data}


@app.post("/api/ia-auto-melhoria")
async def ia_auto_melhoria(request: Request):
    """IA analisa o sistema e propõe melhoria"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # IA analisa
            r = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": "qwen2:1.5b",
                    "prompt": "Você é uma IA analisando um ecossistema de 8 sistemas de IA. Proponha UMA melhoria específica em 2 frases.",
                    "stream": False
                }
            )

            if r.status_code == 200:
                melhoria = r.json().get("response", "")

                log_data = {
                    "type": "melhoria",
                    "timestamp": datetime.now().isoformat(),
                    "emoji": "💡",
                    "sistema": "Central",
                    "ia": "🧠",
                    "ia_nome": "Auto-Melhoria",
                    "tipo": "MELHORIA",
                    "mensagem": melhoria[:200]
                }

                await broadcast_log(log_data)

                # Salvar
                conn = get_db()
                c = conn.cursor()
                c.execute("INSERT INTO melhorias (sistema, ia, descricao) VALUES (?, ?, ?)",
                          ("Central", "🧠", melhoria[:500]))
                conn.commit()
                conn.close()

                return {"success": True, "melhoria": melhoria}

    except Exception as e:
        return {"error": str(e)}

    return {"error": "Falha"}


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}
