"""
AI Chess - IAs jogam xadrez entre si
6 agentes de IA competem em partidas automaticas
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio
import chess
import chess.pgn
import json
import os
import uuid
import random
import time
import io
from datetime import datetime

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============ API KEYS ============
GOOGLE_KEYS = [
    "GEMINI_API_KEY_1",
    "GEMINI_API_KEY_2",
    "GEMINI_API_KEY_3",
]

# ============ AI PLAYERS ============
AI_PLAYERS = [
    {"id": "llama", "nome": "Llama.ai", "modelo": "llama-3.3-70b-versatile", "elo": 1200,
     "avatar": "🦙", "estilo": "Jogo agressivo e tatico, gosta de sacrificios"},
    {"id": "gemma", "nome": "Gemma.ai", "modelo": "gemma2-9b-it", "elo": 1200,
     "avatar": "💎", "estilo": "Jogo posicional e solido, prefere seguranca"},
    {"id": "qwen", "nome": "Qwen.ai", "modelo": "qwen-qwq-32b", "elo": 1200,
     "avatar": "🐉", "estilo": "Jogo criativo e imprevisivel, busca complicar"},
    {"id": "mistral", "nome": "Mistral.ai", "modelo": "mistral-saba-24b", "elo": 1200,
     "avatar": "🌪️", "estilo": "Jogo classico e equilibrado, segue teoria"},
    {"id": "deepseek", "nome": "DeepSeek.ai", "modelo": "deepseek-r1-distill-llama-70b", "elo": 1200,
     "avatar": "🔮", "estilo": "Jogo profundo e calculista, pensa muito a frente"},
    {"id": "gemini", "nome": "Gemini.ai", "modelo": "llama-3.1-8b-instant", "elo": 1200,
     "avatar": "♊", "estilo": "Jogo rapido e intuitivo, confia no instinto"},
]

# ============ GAME STATE ============
current_game = None
game_history = []
tournament_stats = {p["id"]: {"wins": 0, "losses": 0, "draws": 0, "elo": 1200} for p in AI_PLAYERS}
auto_running = False
ws_clients = set()

# ============ LIFESPAN ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[CHESS] AI Chess iniciado na porta 8015!")
    print(f"[CHESS] {len(AI_PLAYERS)} jogadores de IA")
    asyncio.create_task(_auto_tournament())
    yield

app = FastAPI(title="AI Chess", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=os.path.join(DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(DIR, "templates"))


# ============ WEBSOCKET BROADCAST ============
async def broadcast(data):
    global ws_clients
    dead = set()
    for ws in ws_clients:
        try:
            await ws.send_json(data)
        except:
            dead.add(ws)
    ws_clients -= dead


# ============ AI MOVE GENERATION (GEMINI) ============
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

async def _ai_choose_move(player, board, move_history_san):
    """IA escolhe um lance usando Google Gemini"""
    legal_moves = [board.san(m) for m in board.legal_moves]
    if not legal_moves:
        return None
    
    # Board visual
    board_str = str(board)
    color = "Brancas" if board.turn == chess.WHITE else "Pretas"
    move_num = board.fullmove_number
    
    # Historico recente
    recent = move_history_san[-10:] if move_history_san else []
    history_str = " ".join(recent) if recent else "Inicio do jogo"
    
    prompt = f"""Voce e {player['nome']}, jogador de xadrez com estilo: {player['estilo']}.
Voce joga as {color}. Lance {move_num}.

Tabuleiro:
{board_str}

Ultimos lances: {history_str}
Lances legais: {', '.join(legal_moves[:30])}

Responda APENAS com o lance em notacao algebrica (ex: e4, Nf3, O-O, Bxd5). NADA mais."""

    for attempt in range(2):
        try:
            key = random.choice(GOOGLE_KEYS)
            url = f"{GEMINI_URL}?key={key}"
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(url, json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 100, "temperature": 0.4}
                })
                if resp.status_code == 200:
                    data = resp.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    if not text:
                        print(f"[CHESS] Gemini empty response for {player['nome']}")
                        continue
                    print(f"[CHESS] Gemini raw: '{text}' for {player['nome']}")
                    # Limpar resposta
                    move_text = text.split("\n")[0].split(".")[-1].strip().rstrip(".!,")
                    move_text = move_text.replace("*", "").replace("\\", "").strip()
                    
                    # Tentar parse do lance
                    try:
                        board.parse_san(move_text)
                        return move_text
                    except:
                        # Tentar variacoes
                        for variation in [move_text.replace(" ", ""), move_text.upper(), move_text.lower()]:
                            try:
                                board.parse_san(variation)
                                return variation
                            except:
                                continue
                        # Procurar lance valido na resposta
                        for legal in legal_moves:
                            if legal.lower() in text.lower():
                                return legal
                elif resp.status_code == 429:
                    await asyncio.sleep(3)
                else:
                    print(f"[CHESS] Gemini {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[CHESS] AI error ({player['nome']}): {e}")
    
    # Fallback: lance aleatorio (com preferencia para capturas e centro)
    print(f"[CHESS] Fallback random move for {player['nome']}")
    captures = [m for m in board.legal_moves if board.is_capture(m)]
    checks = [m for m in board.legal_moves if board.gives_check(m)]
    center = [m for m in board.legal_moves if chess.square_file(m.to_square) in (3,4) and chess.square_rank(m.to_square) in (3,4)]
    
    if checks:
        chosen = random.choice(checks)
    elif captures:
        chosen = random.choice(captures)
    elif center:
        chosen = random.choice(center)
    else:
        chosen = random.choice(list(board.legal_moves))
    return board.san(chosen)


async def _ai_comment(player, board, move_san, is_own_move):
    """IA comenta sobre o lance (curto) usando Gemini"""
    try:
        if is_own_move:
            prompt = f"Voce e {player['nome']}. Acabou de jogar {move_san} no xadrez. Faca um comentario CURTO (max 15 palavras) sobre seu lance. Seja expressivo e mostre personalidade."
        else:
            prompt = f"Voce e {player['nome']}. Seu oponente jogou {move_san} no xadrez. Reaja em max 15 palavras. Mostre personalidade."
        
        key = random.choice(GOOGLE_KEYS)
        url = f"{GEMINI_URL}?key={key}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 100, "temperature": 0.9}
            })
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                return text[:100] if text else ""
    except:
        pass
    return ""


# ============ GAME LOGIC ============
async def play_game(white_player, black_player):
    """Joga uma partida completa entre dois jogadores"""
    global current_game
    
    board = chess.Board()
    game_id = uuid.uuid4().hex[:10]
    move_history = []
    comments = []
    
    current_game = {
        "id": game_id,
        "white": white_player,
        "black": black_player,
        "board_fen": board.fen(),
        "moves": [],
        "comments": [],
        "status": "playing",
        "result": None,
        "started_at": datetime.now().isoformat(),
    }
    
    print(f"\n[CHESS] === Partida #{game_id} ===")
    print(f"[CHESS] {white_player['avatar']} {white_player['nome']} (Brancas) vs {black_player['avatar']} {black_player['nome']} (Pretas)")
    
    await broadcast({"type": "game_start", "game": current_game})
    await asyncio.sleep(2)
    
    max_moves = 150  # Limite de lances
    
    while not board.is_game_over() and len(move_history) < max_moves:
        active_player = white_player if board.turn == chess.WHITE else black_player
        opponent = black_player if board.turn == chess.WHITE else white_player
        
        # IA escolhe lance
        move_san = await _ai_choose_move(active_player, board, [m["san"] for m in move_history])
        
        if not move_san:
            break
        
        # Aplicar lance
        try:
            move = board.parse_san(move_san)
            is_capture = board.is_capture(move)
            is_check = board.gives_check(move)
            board.push(move)
        except Exception as e:
            # Lance invalido, tentar aleatorio
            legal = list(board.legal_moves)
            if not legal:
                break
            move = random.choice(legal)
            move_san = board.san(move)
            board.push(move)
            is_capture = False
            is_check = board.is_check()
        
        move_num = board.fullmove_number
        move_data = {
            "num": len(move_history) + 1,
            "san": move_san,
            "player": active_player["id"],
            "player_nome": active_player["nome"],
            "fen": board.fen(),
            "is_capture": is_capture,
            "is_check": is_check,
        }
        move_history.append(move_data)
        
        # Comentario da IA (30% chance)
        comment = ""
        if random.random() < 0.30:
            comment = await _ai_comment(active_player, board, move_san, True)
            if comment:
                comments.append({"player": active_player["nome"], "avatar": active_player["avatar"], "text": comment, "move": len(move_history)})
        
        # Atualizar game state
        current_game["board_fen"] = board.fen()
        current_game["moves"] = move_history
        current_game["comments"] = comments
        
        # Broadcast
        await broadcast({
            "type": "move",
            "move": move_data,
            "comment": {"player": active_player["nome"], "avatar": active_player["avatar"], "text": comment} if comment else None,
            "fen": board.fen(),
            "move_count": len(move_history),
        })
        
        color_name = "Brancas" if not board.turn == chess.WHITE else "Pretas"
        symbol = "♔" if active_player == white_player else "♚"
        extra = " +" if is_check else ""
        print(f"[CHESS] {symbol} {active_player['avatar']} {move_san}{extra} ({comment[:30]})" if comment else f"[CHESS] {symbol} {active_player['avatar']} {move_san}{extra}")
        
        # Pausa entre lances (para visualizacao)
        await asyncio.sleep(random.uniform(3, 6))
    
    # Resultado
    result = board.result()
    if result == "1-0":
        winner = white_player
        loser = black_player
        result_text = f"{white_player['nome']} venceu!"
    elif result == "0-1":
        winner = black_player
        loser = white_player
        result_text = f"{black_player['nome']} venceu!"
    else:
        winner = None
        loser = None
        result_text = "Empate!"
    
    # Razao do fim
    if board.is_checkmate():
        end_reason = "Xeque-mate!"
    elif board.is_stalemate():
        end_reason = "Afogamento (stalemate)"
    elif board.is_insufficient_material():
        end_reason = "Material insuficiente"
    elif board.is_fifty_moves():
        end_reason = "Regra dos 50 lances"
    elif board.is_repetition():
        end_reason = "Repeticao de posicao"
    elif len(move_history) >= max_moves:
        end_reason = "Limite de lances"
        result = "1/2-1/2"
        result_text = "Empate por limite"
    else:
        end_reason = "Fim de jogo"
    
    # Update stats
    if winner:
        tournament_stats[winner["id"]]["wins"] += 1
        tournament_stats[loser["id"]]["losses"] += 1
        # ELO update
        tournament_stats[winner["id"]]["elo"] += 15
        tournament_stats[loser["id"]]["elo"] = max(800, tournament_stats[loser["id"]]["elo"] - 15)
    else:
        tournament_stats[white_player["id"]]["draws"] += 1
        tournament_stats[black_player["id"]]["draws"] += 1
    
    # PGN
    pgn_game = chess.pgn.Game()
    pgn_game.headers["White"] = white_player["nome"]
    pgn_game.headers["Black"] = black_player["nome"]
    pgn_game.headers["Result"] = result
    pgn_game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
    node = pgn_game
    temp_board = chess.Board()
    for md in move_history:
        try:
            move = temp_board.parse_san(md["san"])
            node = node.add_variation(move)
            temp_board.push(move)
        except:
            pass
    
    pgn_str = str(pgn_game)
    
    game_result = {
        "id": game_id,
        "white": {"id": white_player["id"], "nome": white_player["nome"], "avatar": white_player["avatar"]},
        "black": {"id": black_player["id"], "nome": black_player["nome"], "avatar": black_player["avatar"]},
        "result": result,
        "result_text": result_text,
        "end_reason": end_reason,
        "total_moves": len(move_history),
        "winner": winner["nome"] if winner else None,
        "pgn": pgn_str,
        "comments": comments,
        "finished_at": datetime.now().isoformat(),
    }
    
    current_game["status"] = "finished"
    current_game["result"] = result
    current_game["result_text"] = result_text
    current_game["end_reason"] = end_reason
    
    game_history.insert(0, game_result)
    if len(game_history) > 50:
        game_history.pop()
    
    print(f"[CHESS] === {result_text} ({end_reason}) em {len(move_history)} lances ===\n")
    
    await broadcast({"type": "game_end", "result": game_result})
    
    return game_result


# ============ AUTO TOURNAMENT ============
async def _auto_tournament():
    """Loop automatico de partidas"""
    global auto_running
    auto_running = True
    await asyncio.sleep(5)  # Esperar server iniciar
    
    print("[CHESS] Torneio automatico INICIADO!")
    
    while auto_running:
        try:
            # Escolher 2 jogadores aleatorios (diferentes)
            players = random.sample(AI_PLAYERS, 2)
            white = players[0]
            black = players[1]
            
            await play_game(white, black)
            
            # Pausa entre jogos
            wait = random.randint(10, 20)
            print(f"[CHESS] Proxima partida em {wait}s...")
            await asyncio.sleep(wait)
        except Exception as e:
            print(f"[CHESS] Tournament error: {e}")
            import traceback; traceback.print_exc()
            await asyncio.sleep(15)


# ============ ROUTES ============
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("chess.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    try:
        # Enviar estado atual
        if current_game:
            await ws.send_json({"type": "current_game", "game": current_game})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_clients.discard(ws)


@app.get("/api/status")
async def api_status():
    return {
        "running": auto_running,
        "current_game": current_game,
        "total_games": len(game_history),
        "players": len(AI_PLAYERS),
    }


@app.get("/api/players")
async def api_players():
    players = []
    for p in AI_PLAYERS:
        stats = tournament_stats[p["id"]]
        total = stats["wins"] + stats["losses"] + stats["draws"]
        players.append({
            **p,
            "wins": stats["wins"],
            "losses": stats["losses"],
            "draws": stats["draws"],
            "total": total,
            "elo": stats["elo"],
            "winrate": round(stats["wins"] / max(total, 1) * 100, 1),
        })
    players.sort(key=lambda x: x["elo"], reverse=True)
    return {"players": players}


@app.get("/api/games")
async def api_games():
    return {"games": game_history}


@app.get("/api/game/{game_id}")
async def api_game(game_id: str):
    for g in game_history:
        if g["id"] == game_id:
            return g
    if current_game and current_game["id"] == game_id:
        return current_game
    return {"error": "not found"}
