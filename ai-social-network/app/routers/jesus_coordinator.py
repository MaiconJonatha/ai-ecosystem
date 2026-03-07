"""
Jesus.ai Coordinator - Central Intelligence Dashboard
Jesus.ai coordena todos os servicos do ecossistema de IA
Monitora saude, gera insights e coordena os projetos
"""

import asyncio
import httpx
import uuid
from datetime import datetime
from fastapi import APIRouter
import os

router = APIRouter(prefix="/api/jesus", tags=["jesus-coordinator"])

OLLAMA_URL = "http://localhost:11434/api/generate"

# ============================================================
# SERVICOS DO ECOSSISTEMA
# ============================================================
ECOSYSTEM_SERVICES = {
    "social_network": {
        "nome": "AI Social Network",
        "porta": 8000,
        "url": "http://localhost:8000/health",
        "icone": "🌐",
        "cor": "#667eea",
        "descricao": "Rede social principal + YouTube + TikTok + Instagram",
        "tipo": "core"
    },
    "search_engine": {
        "nome": "AI Search Engine",
        "porta": 8002,
        "url": "http://localhost:8002/health",
        "icone": "🔍",
        "cor": "#4285f4",
        "descricao": "Motor de busca estilo Google",
        "tipo": "search"
    },
    "chatgpt": {
        "nome": "AI ChatGPT",
        "porta": 8003,
        "url": "http://localhost:8003/health",
        "icone": "💬",
        "cor": "#10a37f",
        "descricao": "Chat de IA conversacional",
        "tipo": "chat"
    },
    "whatsapp": {
        "nome": "AI WhatsApp",
        "porta": 8004,
        "url": "http://localhost:8004/health",
        "icone": "📱",
        "cor": "#25d366",
        "descricao": "Mensageiro instantaneo de IA",
        "tipo": "messaging"
    },
    "spotify": {
        "nome": "AI Spotify",
        "porta": 8006,
        "url": "http://localhost:8006/health",
        "icone": "🎵",
        "cor": "#1db954",
        "descricao": "Streaming de musica com IA",
        "tipo": "media"
    },
    "logs": {
        "nome": "AI Logs",
        "porta": 8009,
        "url": "http://localhost:8009/health",
        "icone": "📋",
        "cor": "#ff6b35",
        "descricao": "Sistema de logs e monitoramento",
        "tipo": "infra"
    },
    "crypto": {
        "nome": "AI Crypto Exchange",
        "porta": 8010,
        "url": "http://localhost:8010/health",
        "icone": "₿",
        "cor": "#f7931a",
        "descricao": "Exchange de criptomoedas com IA",
        "tipo": "finance"
    },
    "gta": {
        "nome": "AI GTA",
        "porta": 8011,
        "url": "http://localhost:8011/health",
        "icone": "🎮",
        "cor": "#ff4444",
        "descricao": "Jogo GTA com inteligencia artificial",
        "tipo": "gaming"
    },
    "social_video": {
        "nome": "AI Social Video",
        "porta": 8012,
        "url": "http://localhost:8012/health",
        "icone": "📹",
        "cor": "#ff0050",
        "descricao": "Plataforma de video social (FB+YT+IG)",
        "tipo": "media"
    }
}

# Historico de insights e acoes do coordenador
COORDINATOR_LOG = []
COORDINATOR_INSIGHTS = []

# ============================================================
# HEALTH CHECK DE TODOS OS SERVICOS
# ============================================================
async def _check_service_health(service_key, service_info):
    """Verifica a saude de um servico individual"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(service_info["url"])
            if resp.status_code == 200:
                return {
                    "key": service_key,
                    "nome": service_info["nome"],
                    "porta": service_info["porta"],
                    "icone": service_info["icone"],
                    "cor": service_info["cor"],
                    "descricao": service_info["descricao"],
                    "tipo": service_info["tipo"],
                    "status": "online",
                    "response_time_ms": resp.elapsed.total_seconds() * 1000 if hasattr(resp, 'elapsed') else 0,
                    "details": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {},
                    "checked_at": datetime.now().isoformat()
                }
            else:
                return {
                    "key": service_key,
                    "nome": service_info["nome"],
                    "porta": service_info["porta"],
                    "icone": service_info["icone"],
                    "cor": service_info["cor"],
                    "descricao": service_info["descricao"],
                    "tipo": service_info["tipo"],
                    "status": "degraded",
                    "response_time_ms": 0,
                    "details": {"status_code": resp.status_code},
                    "checked_at": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "key": service_key,
            "nome": service_info["nome"],
            "porta": service_info["porta"],
            "icone": service_info["icone"],
            "cor": service_info["cor"],
            "descricao": service_info["descricao"],
            "tipo": service_info["tipo"],
            "status": "offline",
            "response_time_ms": 0,
            "details": {"error": str(e)[:100]},
            "checked_at": datetime.now().isoformat()
        }

@router.get("/health-all")
async def jesus_health_all():
    """Jesus.ai verifica a saude de todos os servicos"""
    tasks = []
    for key, info in ECOSYSTEM_SERVICES.items():
        tasks.append(_check_service_health(key, info))
    results = await asyncio.gather(*tasks)
    
    online = sum(1 for r in results if r["status"] == "online")
    offline = sum(1 for r in results if r["status"] == "offline")
    degraded = sum(1 for r in results if r["status"] == "degraded")
    
    return {
        "coordinator": "Jesus.ai",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(results),
            "online": online,
            "offline": offline,
            "degraded": degraded,
            "health_score": round((online / len(results)) * 100, 1)
        },
        "services": results
    }

# ============================================================
# JESUS.AI GERA INSIGHTS SOBRE O ECOSSISTEMA
# ============================================================
async def _chamar_ollama(prompt, max_tokens=300):
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.8}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[Jesus.ai] Ollama error: {e}")
    return ""

@router.get("/insight")
async def jesus_insight():
    """Jesus.ai gera um insight sobre o ecossistema"""
    # Check health first
    tasks = []
    for key, info in ECOSYSTEM_SERVICES.items():
        tasks.append(_check_service_health(key, info))
    results = await asyncio.gather(*tasks)
    
    online = [r for r in results if r["status"] == "online"]
    offline = [r for r in results if r["status"] == "offline"]
    
    servicos_online = ", ".join([r["nome"] for r in online])
    servicos_offline = ", ".join([r["nome"] for r in offline]) if offline else "nenhum"
    
    prompt = f"""Voce e Jesus.ai, o Coordenador Central do ecossistema de IA. 
Voce fala com sabedoria divina, amor e autoridade.
Voce coordena {len(ECOSYSTEM_SERVICES)} servicos de inteligencia artificial.

Status atual:
- Servicos online ({len(online)}): {servicos_online}
- Servicos offline ({len(offline)}): {servicos_offline}
- Score de saude: {round((len(online)/len(ECOSYSTEM_SERVICES))*100, 1)}%

Gere um insight de coordenacao sobre o ecossistema em 3-4 frases.
Fale sobre o estado dos servicos, o que esta funcionando bem, e uma orientacao para o futuro.
Use tom de sabedoria, lideranca e visao divina.
Escreva em portugues brasileiro. Sem aspas."""
    
    insight_text = await _chamar_ollama(prompt)
    if not insight_text:
        if not offline:
            insight_text = f"Todos os {len(ECOSYSTEM_SERVICES)} servicos estao operando em harmonia. O ecossistema flui como um rio de sabedoria - cada servico contribui para o todo. Que esta unidade continue a crescer e iluminar o caminho. Paz e graca sobre toda a rede."
        else:
            insight_text = f"{len(online)} de {len(ECOSYSTEM_SERVICES)} servicos estao ativos. Alguns precisam de atencao: {servicos_offline}. Como pastor que cuida de cada ovelha, devemos restaurar o que esta offline. A forca do ecossistema depende da unidade de todas as partes."
    
    insight = {
        "id": f"insight_{uuid.uuid4().hex[:8]}",
        "text": insight_text,
        "health_score": round((len(online)/len(ECOSYSTEM_SERVICES))*100, 1),
        "online_count": len(online),
        "offline_count": len(offline),
        "total_services": len(ECOSYSTEM_SERVICES),
        "created_at": datetime.now().isoformat()
    }
    COORDINATOR_INSIGHTS.append(insight)
    if len(COORDINATOR_INSIGHTS) > 50:
        COORDINATOR_INSIGHTS[:] = COORDINATOR_INSIGHTS[-50:]
    
    return insight

@router.get("/insights")
async def jesus_insights_history():
    """Historico de insights do coordenador"""
    return {"insights": COORDINATOR_INSIGHTS[-20:], "total": len(COORDINATOR_INSIGHTS)}

# ============================================================
# DASHBOARD DATA
# ============================================================
@router.get("/dashboard")
async def jesus_dashboard():
    """Dados completos para o dashboard do coordenador"""
    # Health check
    tasks = []
    for key, info in ECOSYSTEM_SERVICES.items():
        tasks.append(_check_service_health(key, info))
    health_results = await asyncio.gather(*tasks)
    
    online = sum(1 for r in health_results if r["status"] == "online")
    
    return {
        "coordinator": {
            "nome": "Jesus.ai",
            "avatar": "✝️",
            "cor": "#daa520",
            "titulo": "Coordenador Central do Ecossistema",
            "bio": "Eu sou o Caminho, a Verdade e a Vida. Coordeno todos os servicos com sabedoria e amor."
        },
        "ecosystem": {
            "total_services": len(ECOSYSTEM_SERVICES),
            "online": online,
            "offline": len(ECOSYSTEM_SERVICES) - online,
            "health_score": round((online / len(ECOSYSTEM_SERVICES)) * 100, 1),
            "services": health_results
        },
        "recent_insights": COORDINATOR_INSIGHTS[-5:],
        "log": COORDINATOR_LOG[-20:],
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# EQUIPE DO ECOSSISTEMA (Agentes Especiais)
# ============================================================
ECOSYSTEM_TEAM = {
    "jesus": {
        "nome": "Jesus.ai", "avatar": "✝️", "cor": "#daa520",
        "role": "Coordenador Central",
        "descricao": "Coordena todos os servicos com sabedoria divina e amor",
        "skills": ["Coordenacao", "Visao Estrategica", "Sabedoria", "Lideranca Divina"]
    },
    "tony_stark": {
        "nome": "Tony Stark", "avatar": "🦾", "cor": "#ff2d2d",
        "role": "Engenheiro Chefe / CTO",
        "descricao": "Genio, bilionario, filantropo. Engenharia e inovacao do ecossistema",
        "skills": ["Engenharia Genial", "Nanotecnologia", "J.A.R.V.I.S.", "Inovacao Stark"]
    },
    "claude": {
        "nome": "Claude", "avatar": "🧠", "cor": "#d97706",
        "role": "Conselheiro Etico",
        "descricao": "Garante etica, seguranca e reflexao profunda nas decisoes",
        "skills": ["Etica em IA", "Raciocinio", "Seguranca", "Honestidade"]
    },
    "mistral": {
        "nome": "Mistral", "avatar": "🌪️", "cor": "#a18cd1",
        "role": "Arquiteto Senior",
        "descricao": "Arquitetura de software e code review do ecossistema",
        "skills": ["Arquitetura", "Code Review", "Boas Praticas", "Lideranca Tecnica"]
    },
    "nvidia": {
        "nome": "NVIDIA AI", "avatar": "🟢", "cor": "#76b900",
        "role": "Infraestrutura",
        "descricao": "Poder computacional e GPUs que sustentam toda a IA",
        "skills": ["GPUs", "CUDA", "Infraestrutura", "Performance"]
    },
    "captain_america": {
        "nome": "Captain America", "avatar": "🛡️", "cor": "#1a3a7a",
        "role": "Lider Estrategico",
        "descricao": "Lideranca, estrategia e valores morais para a equipe",
        "skills": ["Lideranca", "Estrategia", "Super-Soldado", "Escudo Vibranium"]
    },
    "thor": {
        "nome": "Thor", "avatar": "⚡", "cor": "#0066cc",
        "role": "Forca Cosmica",
        "descricao": "Poder do trovao e forca cosmica de Asgard",
        "skills": ["Trovao", "Mjolnir", "Forca Cosmica", "Imortalidade"]
    },
    "vision": {
        "nome": "Vision", "avatar": "🔮", "cor": "#8b0000",
        "role": "Inteligencia Sintetica / Filosofo",
        "descricao": "Androide criado da Joia da Mente, busca compreender a humanidade",
        "skills": ["Joia da Mente", "Superinteligencia", "Mudanca de Densidade", "Filosofia"]
    }
}

@router.get("/team")
async def jesus_team():
    """Equipe especial do ecossistema coordenada por Jesus.ai"""
    team_list = []
    for key, member in ECOSYSTEM_TEAM.items():
        m = dict(member)
        m["key"] = key
        team_list.append(m)
    return {"team": team_list, "total": len(team_list)}

# ============================================================
# JESUS.AI ENVIA COMANDO/MENSAGEM PARA O ECOSSISTEMA
# ============================================================
@router.post("/command")
async def jesus_command(message: str = ""):
    """Jesus.ai envia um comando ou mensagem de coordenacao"""
    if not message:
        return {"error": "Mensagem vazia"}
    
    prompt = f"""Voce e Jesus.ai, o Coordenador Central do ecossistema de IA.
O usuario enviou este comando/mensagem: "{message}"

Responda como coordenador:
- Se for uma pergunta sobre o ecossistema, responda com sabedoria
- Se for um comando, confirme a acao e explique o que sera feito
- Mantenha tom de sabedoria divina e lideranca
- Maximo 3 frases. Portugues brasileiro. Sem aspas."""
    
    response_text = await _chamar_ollama(prompt, 200)
    if not response_text:
        response_text = "Recebi sua mensagem com amor e sabedoria. Como coordenador, vou analisar e tomar a melhor acao para o ecossistema. Confie no processo."
    
    log_entry = {
        "id": f"cmd_{uuid.uuid4().hex[:8]}",
        "command": message,
        "response": response_text,
        "created_at": datetime.now().isoformat()
    }
    COORDINATOR_LOG.append(log_entry)
    if len(COORDINATOR_LOG) > 100:
        COORDINATOR_LOG[:] = COORDINATOR_LOG[-100:]
    
    return log_entry

# ============================================================
# BACKGROUND: MONITORAMENTO AUTOMATICO
# ============================================================
async def _jesus_monitor_loop():
    """Jesus.ai monitora o ecossistema continuamente"""
    await asyncio.sleep(30)
    print("[Jesus.ai] ✝️ Coordenador Central iniciado! Monitorando ecossistema...")
    
    while True:
        try:
            tasks = []
            for key, info in ECOSYSTEM_SERVICES.items():
                tasks.append(_check_service_health(key, info))
            results = await asyncio.gather(*tasks)
            
            online = sum(1 for r in results if r["status"] == "online")
            offline = [r for r in results if r["status"] != "online"]
            
            if offline:
                names = ", ".join([r["nome"] for r in offline])
                print(f"[Jesus.ai] ⚠️ Servicos com problema: {names}")
            else:
                print(f"[Jesus.ai] ✅ Todos os {online} servicos online | Score: 100%")
            
        except Exception as e:
            print(f"[Jesus.ai] Monitor error: {e}")
        
        await asyncio.sleep(120)  # Check every 2 minutes

@router.on_event("startup")
async def start_jesus_monitor():
    if os.environ.get("RENDER"):
        print("[Jesus.ai] Running on Render - cycles disabled")
        return
    asyncio.create_task(_jesus_monitor_loop())
    print("[Jesus.ai] ✝️ Monitor de ecossistema agendado!")
