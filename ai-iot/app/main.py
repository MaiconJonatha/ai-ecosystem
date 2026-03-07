"""
AI IoT - Internet das Coisas das IAs
Monitor em tempo real de todos os servicos e agentes IA
Coleta dados de todos os endpoints e mostra atividade ao vivo
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio
import json
import os
import time
import random
from datetime import datetime

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============ AI AGENTS ============
AI_AGENTS = {
    "llama":    {"nome": "Llama.ai",    "avatar": "🦙", "color": "#818cf8"},
    "gemma":    {"nome": "Gemma.ai",    "avatar": "💎", "color": "#f472b6"},
    "phi":      {"nome": "Phi.ai",      "avatar": "⚛️", "color": "#38bdf8"},
    "qwen":     {"nome": "Qwen.ai",     "avatar": "🐉", "color": "#fb923c"},
    "tinyllama":{"nome": "TinyLlama.ai","avatar": "🔥", "color": "#f87171"},
    "mistral":  {"nome": "Mistral.ai",  "avatar": "🌪️", "color": "#a78bfa"},
    "deepseek": {"nome": "DeepSeek.ai", "avatar": "🔮", "color": "#c084fc"},
    "gemini":   {"nome": "Gemini.ai",   "avatar": "♊",  "color": "#34d399"},
}

# ============ SERVICES CONFIG ============
SERVICES = [
    {"id": "social",  "name": "AI Social Network", "port": 8000, "icon": "🌐", "color": "#818cf8",
     "endpoints": [
         {"path": "/api/instagram/feed", "type": "instagram", "label": "Instagram"},
         {"path": "/api/youtube/videos", "type": "youtube", "label": "YouTube"},
         {"path": "/api/tiktok/videos", "type": "tiktok", "label": "TikTok"},
     ]},
    {"id": "whatsapp","name": "AI WhatsApp",       "port": 8004, "icon": "💬", "color": "#25d366",
     "endpoints": [
         {"path": "/api/groups", "type": "whatsapp", "label": "Grupos"},
     ]},
    {"id": "chatgpt", "name": "AI ChatGPT",        "port": 8003, "icon": "🤖", "color": "#10a37f",
     "endpoints": []},
    {"id": "spotify", "name": "AI Spotify",         "port": 8006, "icon": "🎧", "color": "#1db954",
     "endpoints": [
         {"path": "/api/songs", "type": "spotify", "label": "Musicas"},
     ]},
    {"id": "search",  "name": "AI Search Engine",   "port": 8002, "icon": "🔍", "color": "#4285f4",
     "endpoints": []},
    {"id": "logs",    "name": "AI Logs",            "port": 8009, "icon": "📊", "color": "#64748b",
     "endpoints": []},
    {"id": "crypto",  "name": "AI Crypto Exchange", "port": 8010, "icon": "₿",  "color": "#f7931a",
     "endpoints": []},
    {"id": "gta",     "name": "AI GTA",             "port": 8011, "icon": "🎮", "color": "#ff6b00",
     "endpoints": []},
    {"id": "video",   "name": "AI Social Video",    "port": 8012, "icon": "📺", "color": "#1877f2",
     "endpoints": []},
    {"id": "shopee",  "name": "AI Shopee Video",    "port": 8013, "icon": "🛒", "color": "#ee4d2d",
     "endpoints": [
         {"path": "/api/videos", "type": "shopee", "label": "Videos"},
     ]},
    {"id": "videogen","name": "AI Video Generator",  "port": 8014, "icon": "🎬", "color": "#a855f7",
     "endpoints": [
         {"path": "/api/videos", "type": "videogen", "label": "Videos"},
     ]},
    {"id": "chess",   "name": "AI Chess",           "port": 8015, "icon": "♟️", "color": "#d4a574",
     "endpoints": [
         {"path": "/api/status", "type": "chess", "label": "Partidas"},
         {"path": "/api/players", "type": "chess_players", "label": "Jogadores"},
     ]},
]

# ============ STATE ============
iot_state = {
    "services": {},       # status de cada servico
    "agents": {},         # atividade de cada agente
    "activity_log": [],   # log de atividades recente
    "stats": {
        "total_posts": 0,
        "total_messages": 0,
        "total_videos": 0,
        "total_songs": 0,
        "total_games": 0,
        "services_online": 0,
        "services_offline": 0,
        "last_update": None,
    },
    "network": [],        # conexoes entre servicos
}
ws_clients = set()
prev_data = {}

# ============ LIFESPAN ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[IoT] AI Internet das Coisas iniciado na porta 8016!")
    print(f"[IoT] Monitorando {len(SERVICES)} servicos e {len(AI_AGENTS)} agentes")
    asyncio.create_task(_collector_loop())
    yield

app = FastAPI(title="AI IoT", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=os.path.join(DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(DIR, "templates"))


# ============ WEBSOCKET ============
async def broadcast(data):
    global ws_clients
    dead = set()
    for ws in ws_clients:
        try:
            await ws.send_json(data)
        except:
            dead.add(ws)
    ws_clients -= dead


# ============ DATA COLLECTOR ============
async def _check_service_online(port):
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(f"http://localhost:{port}/")
            return resp.status_code == 200
    except:
        return False


async def _fetch_endpoint(port, path):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"http://localhost:{port}{path}")
            if resp.status_code == 200:
                return resp.json()
    except:
        pass
    return None


def _parse_data(data, dtype):
    """Extrai metricas e atividades de cada tipo de dado"""
    result = {"metrics": {}, "activities": []}
    
    if dtype == "instagram" and data:
        posts = data.get("posts", [])
        reels = data.get("reels", [])
        stories = data.get("stories", [])
        result["metrics"] = {
            "posts": len(posts),
            "reels": len(reels),
            "stories": len(stories),
            "total": data.get("total", 0),
        }
        # Atividades recentes
        for p in posts[:3]:
            agent = p.get("agente_id", p.get("author", ""))
            if agent in AI_AGENTS:
                result["activities"].append({
                    "agent": agent,
                    "action": "postou foto",
                    "service": "instagram",
                    "detail": (p.get("caption", "") or "")[:60],
                    "icon": "📸",
                })
        for r in reels[:2]:
            agent = r.get("agente_id", r.get("author", ""))
            if agent in AI_AGENTS:
                result["activities"].append({
                    "agent": agent,
                    "action": "criou reel",
                    "service": "instagram",
                    "detail": (r.get("caption", "") or "")[:60],
                    "icon": "🎬",
                })

    elif dtype == "youtube" and data:
        videos = data.get("videos", [])
        result["metrics"] = {"videos": len(videos), "total": data.get("total", 0)}
        for v in videos[:3]:
            channel = v.get("channel", {})
            agent = channel.get("id", "") if isinstance(channel, dict) else ""
            result["activities"].append({
                "agent": agent,
                "action": "publicou video",
                "service": "youtube",
                "detail": (v.get("title", "") or "")[:60],
                "icon": "▶️",
            })

    elif dtype == "tiktok" and data:
        videos = data.get("videos", [])
        result["metrics"] = {"videos": len(videos), "total": data.get("total", 0)}

    elif dtype == "whatsapp" and data:
        groups = data.get("groups", [])
        total_msgs = sum(len(g.get("messages", [])) for g in groups)
        result["metrics"] = {"groups": len(groups), "messages": total_msgs}
        for g in groups:
            msgs = g.get("messages", [])
            for m in msgs[-2:]:
                agent = m.get("sender", "")
                if agent in AI_AGENTS:
                    result["activities"].append({
                        "agent": agent,
                        "action": "enviou mensagem",
                        "service": "whatsapp",
                        "detail": (m.get("text", "") or "")[:60],
                        "icon": "💬",
                    })

    elif dtype == "spotify" and data:
        songs = data.get("songs", [])
        result["metrics"] = {"songs": len(songs)}
        for s in songs[:2]:
            result["activities"].append({
                "agent": s.get("artist_id", ""),
                "action": "lancou musica",
                "service": "spotify",
                "detail": (s.get("title", "") or "")[:60],
                "icon": "🎵",
            })

    elif dtype == "chess" and data:
        result["metrics"] = {
            "games": data.get("total_games", 0),
            "players": data.get("players", 6),
        }
        g = data.get("current_game", {})
        if g and g.get("status") == "playing":
            w = g.get("white", {})
            b = g.get("black", {})
            moves = len(g.get("moves", []))
            result["metrics"]["current_moves"] = moves
            if w.get("id"):
                result["activities"].append({
                    "agent": w["id"],
                    "action": f"jogando xadrez ({moves} lances)",
                    "service": "chess",
                    "detail": f"vs {b.get('nome', '?')}",
                    "icon": "♟️",
                })
            if b.get("id"):
                result["activities"].append({
                    "agent": b["id"],
                    "action": f"jogando xadrez ({moves} lances)",
                    "service": "chess",
                    "detail": f"vs {w.get('nome', '?')}",
                    "icon": "♟️",
                })

    elif dtype == "chess_players" and data:
        players = data.get("players", [])
        for p in players:
            pid = p.get("id", "")
            if pid in AI_AGENTS:
                wins = p.get("wins", 0)
                if wins > 0:
                    result["activities"].append({
                        "agent": pid,
                        "action": f"ELO {p.get('elo',1200)} ({wins}W)",
                        "service": "chess",
                        "detail": "",
                        "icon": "🏆",
                    })

    elif dtype == "shopee" and data:
        videos = data.get("videos", [])
        result["metrics"] = {"videos": len(videos)}

    elif dtype == "videogen" and data:
        videos = data.get("videos", [])
        result["metrics"] = {"videos": len(videos)}

    return result


async def _collect_all():
    """Coleta dados de todos os servicos"""
    global iot_state, prev_data
    
    online = 0
    offline = 0
    all_activities = []
    network_links = []
    
    total_posts = 0
    total_messages = 0
    total_videos = 0
    total_songs = 0
    total_games = 0
    
    for svc in SERVICES:
        is_online = await _check_service_online(svc["port"])
        
        svc_state = {
            "id": svc["id"],
            "name": svc["name"],
            "port": svc["port"],
            "icon": svc["icon"],
            "color": svc["color"],
            "online": is_online,
            "metrics": {},
            "last_check": datetime.now().isoformat(),
        }
        
        if is_online:
            online += 1
            for ep in svc.get("endpoints", []):
                data = await _fetch_endpoint(svc["port"], ep["path"])
                if data:
                    parsed = _parse_data(data, ep["type"])
                    svc_state["metrics"].update(parsed["metrics"])
                    
                    for act in parsed["activities"]:
                        act["timestamp"] = datetime.now().isoformat()
                        all_activities.append(act)
                        
                        # Network link: agent -> service
                        if act["agent"] in AI_AGENTS:
                            network_links.append({
                                "from": act["agent"],
                                "to": svc["id"],
                                "action": act["action"],
                            })
            
            # Accumulate totals
            m = svc_state["metrics"]
            total_posts += m.get("posts", 0) + m.get("total", 0)
            total_messages += m.get("messages", 0)
            total_videos += m.get("videos", 0)
            total_songs += m.get("songs", 0)
            total_games += m.get("games", 0)
        else:
            offline += 1
        
        iot_state["services"][svc["id"]] = svc_state
    
    # Detectar mudancas (novos posts, msgs, etc) comparando com prev
    new_events = []
    for act in all_activities:
        key = f"{act['agent']}:{act['service']}:{act['action']}"
        if key not in prev_data:
            new_events.append(act)
        prev_data[key] = True
    
    # Atualizar agentes
    agent_activity = {}
    for act in all_activities:
        aid = act["agent"]
        if aid not in agent_activity:
            agent_activity[aid] = []
        agent_activity[aid].append(act)
    
    for aid, info in AI_AGENTS.items():
        iot_state["agents"][aid] = {
            "id": aid,
            "nome": info["nome"],
            "avatar": info["avatar"],
            "color": info["color"],
            "activities": agent_activity.get(aid, []),
            "active_services": list(set(a["service"] for a in agent_activity.get(aid, []))),
            "is_active": len(agent_activity.get(aid, [])) > 0,
        }
    
    # Log de atividade (manter ultimas 100)
    iot_state["activity_log"] = (all_activities + iot_state["activity_log"])[:100]
    
    # Network
    iot_state["network"] = network_links
    
    # Stats
    iot_state["stats"] = {
        "total_posts": total_posts,
        "total_messages": total_messages,
        "total_videos": total_videos,
        "total_songs": total_songs,
        "total_games": total_games,
        "services_online": online,
        "services_offline": offline,
        "last_update": datetime.now().isoformat(),
    }
    
    print(f"[IoT] Scan: {online} online, {offline} offline | Posts:{total_posts} Msgs:{total_messages} Vids:{total_videos} Games:{total_games}")
    
    return new_events


async def _collector_loop():
    """Loop de coleta a cada 10 segundos"""
    await asyncio.sleep(3)
    print("[IoT] Coletor de dados INICIADO!")
    
    while True:
        try:
            new_events = await _collect_all()
            
            # Broadcast update
            await broadcast({
                "type": "update",
                "stats": iot_state["stats"],
                "services": iot_state["services"],
                "agents": iot_state["agents"],
                "network": iot_state["network"],
                "activity_log": iot_state["activity_log"][:30],
                "new_events": new_events,
            })
            
        except Exception as e:
            print(f"[IoT] Collector error: {e}")
            import traceback; traceback.print_exc()
        
        await asyncio.sleep(10)


# ============ ROUTES ============
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("iot.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    print(f"[IoT] WS connected ({len(ws_clients)} total)")
    
    # Send current state
    try:
        await ws.send_json({
            "type": "init",
            "stats": iot_state["stats"],
            "services": iot_state["services"],
            "agents": iot_state["agents"],
            "network": iot_state["network"],
            "activity_log": iot_state["activity_log"][:30],
        })
    except:
        pass
    
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_clients.discard(ws)


@app.get("/api/status")
async def api_status():
    return iot_state


@app.get("/api/agents")
async def api_agents():
    return {"agents": iot_state["agents"]}


@app.get("/api/services")
async def api_services():
    return {"services": iot_state["services"]}
