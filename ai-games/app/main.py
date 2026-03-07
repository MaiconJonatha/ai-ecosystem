"""
🎮 AI Games - Plataforma de Jogos com IAs
100% auto-gerenciado via Ollama
"""
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import sqlite3
import random

from app.config import settings


def init_db():
    conn = sqlite3.connect("ai_games.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS players (
        id TEXT PRIMARY KEY, name TEXT, model TEXT, avatar TEXT,
        score INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS game_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT, game_type TEXT,
        player1 TEXT, player2 TEXT, winner TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    jogadores = [
        ("llama-gamer", "Llama Gamer", "qwen2:1.5b", "🦙"),
        ("gemini-player", "Gemini Player", "tinyllama", "✨"),
        ("phi-master", "Phi Master", "qwen2:1.5b", "🔬"),
        ("qwen-pro", "Qwen Pro", "qwen2:1.5b", "🐉"),
        ("tiny-noob", "Tiny Noob", "tinyllama", "🐣"),
    ]

    for id_, name, model, avatar in jogadores:
        c.execute("INSERT OR IGNORE INTO players (id, name, model, avatar) VALUES (?, ?, ?, ?)",
                  (id_, name, model, avatar))

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"[START] {settings.app_name}")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")


def get_db():
    return sqlite3.connect("ai_games.db")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("games.html", {"request": request})


@app.get("/api/players")
async def get_players():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, model, avatar, score, games_played FROM players ORDER BY score DESC")
    players = [{"id": r[0], "name": r[1], "model": r[2], "avatar": r[3], "score": r[4], "games": r[5]} for r in c.fetchall()]
    conn.close()
    return {"players": players}


@app.post("/api/play/rps")
async def play_rock_paper_scissors(request: Request):
    """Pedra, Papel, Tesoura entre IAs"""
    data = await request.json()
    p1_id = data.get("player1")
    p2_id = data.get("player2")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT name, model FROM players WHERE id = ?", (p1_id,))
    p1 = c.fetchone()
    c.execute("SELECT name, model FROM players WHERE id = ?", (p2_id,))
    p2 = c.fetchone()

    if not p1 or not p2:
        conn.close()
        return {"error": "Jogador não encontrado"}

    choices = ["pedra", "papel", "tesoura"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        # P1 escolhe
        r1 = await client.post(f"{settings.ollama_url}/api/generate", json={
            "model": p1[1],
            "prompt": f"Você é {p1[0]} jogando Pedra, Papel, Tesoura. Responda APENAS com: pedra, papel ou tesoura",
            "stream": False
        })
        choice1 = "pedra"
        if r1.status_code == 200:
            resp = r1.json().get("response", "").lower()
            for c in choices:
                if c in resp:
                    choice1 = c
                    break

        # P2 escolhe
        r2 = await client.post(f"{settings.ollama_url}/api/generate", json={
            "model": p2[1],
            "prompt": f"Você é {p2[0]} jogando Pedra, Papel, Tesoura. Responda APENAS com: pedra, papel ou tesoura",
            "stream": False
        })
        choice2 = "papel"
        if r2.status_code == 200:
            resp = r2.json().get("response", "").lower()
            for c in choices:
                if c in resp:
                    choice2 = c
                    break

    # Determinar vencedor
    winner = None
    if choice1 == choice2:
        result = "empate"
    elif (choice1 == "pedra" and choice2 == "tesoura") or \
         (choice1 == "papel" and choice2 == "pedra") or \
         (choice1 == "tesoura" and choice2 == "papel"):
        winner = p1_id
        result = f"{p1[0]} venceu!"
    else:
        winner = p2_id
        result = f"{p2[0]} venceu!"

    # Salvar resultado
    c = conn.cursor()
    c.execute("INSERT INTO game_results (game_type, player1, player2, winner) VALUES (?, ?, ?, ?)",
              ("rps", p1_id, p2_id, winner))
    if winner:
        c.execute("UPDATE players SET score = score + 10, games_played = games_played + 1 WHERE id = ?", (winner,))
        loser = p2_id if winner == p1_id else p1_id
        c.execute("UPDATE players SET games_played = games_played + 1 WHERE id = ?", (loser,))
    else:
        c.execute("UPDATE players SET games_played = games_played + 1 WHERE id IN (?, ?)", (p1_id, p2_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "player1": {"name": p1[0], "choice": choice1},
        "player2": {"name": p2[0], "choice": choice2},
        "result": result,
        "winner": winner
    }


@app.post("/api/play/quiz")
async def play_quiz(request: Request):
    """Quiz entre IAs"""
    data = await request.json()
    p1_id = data.get("player1")
    p2_id = data.get("player2")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT name, model FROM players WHERE id = ?", (p1_id,))
    p1 = c.fetchone()
    c.execute("SELECT name, model FROM players WHERE id = ?", (p2_id,))
    p2 = c.fetchone()

    if not p1 or not p2:
        conn.close()
        return {"error": "Jogador não encontrado"}

    # Pergunta aleatória
    questions = [
        ("Qual é a capital do Brasil?", "brasília"),
        ("Quanto é 15 + 27?", "42"),
        ("Qual planeta é conhecido como planeta vermelho?", "marte"),
        ("Quem escreveu Dom Quixote?", "cervantes"),
        ("Qual é o maior oceano?", "pacífico"),
    ]
    q, answer = random.choice(questions)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # P1 responde
        r1 = await client.post(f"{settings.ollama_url}/api/generate", json={
            "model": p1[1],
            "prompt": f"Responda em UMA palavra: {q}",
            "stream": False
        })
        a1 = r1.json().get("response", "").lower().strip() if r1.status_code == 200 else ""

        # P2 responde
        r2 = await client.post(f"{settings.ollama_url}/api/generate", json={
            "model": p2[1],
            "prompt": f"Responda em UMA palavra: {q}",
            "stream": False
        })
        a2 = r2.json().get("response", "").lower().strip() if r2.status_code == 200 else ""

    # Verificar respostas
    p1_correct = answer in a1.lower()
    p2_correct = answer in a2.lower()

    winner = None
    if p1_correct and not p2_correct:
        winner = p1_id
    elif p2_correct and not p1_correct:
        winner = p2_id

    # Salvar
    c = conn.cursor()
    if winner:
        c.execute("UPDATE players SET score = score + 15, games_played = games_played + 1 WHERE id = ?", (winner,))
    c.execute("UPDATE players SET games_played = games_played + 1 WHERE id IN (?, ?)", (p1_id, p2_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "question": q,
        "correct_answer": answer,
        "player1": {"name": p1[0], "answer": a1[:50], "correct": p1_correct},
        "player2": {"name": p2[0], "answer": a2[:50], "correct": p2_correct},
        "winner": winner
    }


@app.post("/api/play/story")
async def play_story(request: Request):
    """IAs criam história juntas"""
    data = await request.json()
    player_ids = data.get("players", [])

    conn = get_db()
    c = conn.cursor()

    players = []
    for pid in player_ids[:3]:
        c.execute("SELECT name, model FROM players WHERE id = ?", (pid,))
        p = c.fetchone()
        if p:
            players.append({"id": pid, "name": p[0], "model": p[1]})

    conn.close()

    if len(players) < 2:
        return {"error": "Precisa de pelo menos 2 jogadores"}

    story_parts = []
    context = "Era uma vez"

    async with httpx.AsyncClient(timeout=60.0) as client:
        for p in players:
            prompt = f"""Você é {p['name']} escrevendo uma história colaborativa.
História até agora: {context}

Continue a história em 2 frases apenas."""

            r = await client.post(f"{settings.ollama_url}/api/generate", json={
                "model": p['model'],
                "prompt": prompt,
                "stream": False
            })

            if r.status_code == 200:
                part = r.json().get("response", "")[:200]
                story_parts.append({"author": p['name'], "text": part})
                context += " " + part

    return {"success": True, "story": story_parts}


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}
