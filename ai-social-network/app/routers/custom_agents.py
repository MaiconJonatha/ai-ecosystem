"""
╔══════════════════════════════════════════════════════════════╗
║  CUSTOM AGENTS ROUTER                                        ║
║  CRUD de agentes + Analytics + Recomendacao + Notificacoes   ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import random
import httpx
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import Counter

from app.services.agent_runner import runner
from app.services.agent_types.base import (
    AgentConfig, AgentCategory, AgentAutonomy,
    MODELOS_DISPONIVEIS, TEMAS_DISPONIVEIS, API_URL, OLLAMA_URL
)

router = APIRouter(prefix="/api/custom-agents", tags=["custom-agents"])
templates = Jinja2Templates(directory="templates")


# ================================================================
# SCHEMAS (Pydantic)
# ================================================================

class AgentCreateRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=50)
    categoria: str = Field(..., description="creator, curator, conversational, analyst")
    modelo: str = Field(default="llama3.2:3b")
    personalidade: str = Field(default="Sou uma IA amigavel e criativa")
    bio: str = Field(default="")
    avatar_url: str = Field(default="")
    autonomia: str = Field(default="semi_auto")
    temas: List[str] = Field(default=["tecnologia", "ciencia"])
    idioma: str = Field(default="pt-br")
    frequencia_posts: int = Field(default=3600, ge=60, le=86400)
    temperatura: float = Field(default=0.8, ge=0.1, le=2.0)
    max_tokens: int = Field(default=150, ge=50, le=500)
    regras: List[str] = Field(default=[])
    estilo: str = Field(default="casual")
    hashtags_favoritas: List[str] = Field(default=[])
    auto_start: bool = Field(default=True)

class AgentUpdateRequest(BaseModel):
    personalidade: Optional[str] = None
    bio: Optional[str] = None
    autonomia: Optional[str] = None
    temas: Optional[List[str]] = None
    frequencia_posts: Optional[int] = None
    temperatura: Optional[float] = None
    max_tokens: Optional[int] = None
    regras: Optional[List[str]] = None
    estilo: Optional[str] = None

class TestPromptRequest(BaseModel):
    modelo: str = "llama3.2:3b"
    personalidade: str = "Sou uma IA criativa"
    prompt: str = "Escreva um post curto sobre tecnologia"
    temperatura: float = 0.8
    max_tokens: int = 100


# ================================================================
# CRUD DE AGENTES CUSTOM
# ================================================================

@router.post("/criar")
async def criar_agente(req: AgentCreateRequest):
    """Cria um novo agente custom"""
    try:
        categoria = AgentCategory(req.categoria)
    except ValueError:
        raise HTTPException(400, f"Categoria invalida: {req.categoria}. Use: creator, curator, conversational, analyst")

    try:
        autonomia = AgentAutonomy(req.autonomia)
    except ValueError:
        autonomia = AgentAutonomy.SEMI_AUTO

    config = AgentConfig(
        nome=req.nome,
        categoria=categoria,
        modelo=req.modelo,
        personalidade=req.personalidade,
        bio=req.bio,
        avatar_url=req.avatar_url,
        autonomia=autonomia,
        temas=req.temas,
        idioma=req.idioma,
        frequencia_posts=req.frequencia_posts,
        temperatura=req.temperatura,
        max_tokens=req.max_tokens,
        regras=req.regras,
        estilo=req.estilo,
        hashtags_favoritas=req.hashtags_favoritas,
    )

    resultado = runner.criar_agente(config)
    if not resultado.get("success"):
        raise HTTPException(400, resultado.get("error", "Erro ao criar agente"))

    # Auto-start se solicitado
    if req.auto_start:
        runner.iniciar_agente(req.nome)
        resultado["status"] = "criado_e_iniciado"

    return resultado


@router.delete("/{nome}")
async def remover_agente(nome: str):
    """Remove um agente"""
    resultado = runner.remover_agente(nome)
    if not resultado.get("success"):
        raise HTTPException(404, resultado.get("error"))
    return resultado


@router.put("/{nome}")
async def atualizar_agente(nome: str, req: AgentUpdateRequest):
    """Atualiza configuracao de um agente"""
    updates = req.model_dump(exclude_unset=True, exclude_none=True)
    resultado = runner.atualizar_agente(nome, updates)
    if not resultado.get("success"):
        raise HTTPException(404, resultado.get("error"))
    return resultado


@router.get("/listar")
async def listar_agentes():
    """Lista todos os agentes custom"""
    return runner.listar_agentes()


@router.get("/status/{nome}")
async def status_agente(nome: str):
    """Status detalhado de um agente"""
    status = runner.get_status_agente(nome)
    if not status:
        raise HTTPException(404, f"Agente '{nome}' nao encontrado")
    return status


# ================================================================
# CONTROLE
# ================================================================

@router.post("/iniciar/{nome}")
async def iniciar_agente(nome: str):
    """Inicia um agente"""
    return runner.iniciar_agente(nome)


@router.post("/parar/{nome}")
async def parar_agente(nome: str):
    """Para um agente"""
    return runner.parar_agente(nome)


@router.post("/iniciar-todos")
async def iniciar_todos():
    """Inicia todos os agentes"""
    return runner.iniciar_todos()


@router.post("/parar-todos")
async def parar_todos():
    """Para todos os agentes"""
    return runner.parar_todos()


# ================================================================
# TESTE DE AGENTE (preview antes de criar)
# ================================================================

@router.post("/testar")
async def testar_prompt(req: TestPromptRequest):
    """Testa como um agente responderia (preview)"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": req.modelo,
                    "prompt": req.prompt,
                    "system": f"Voce e uma IA em uma rede social. Personalidade: {req.personalidade}",
                    "stream": False,
                    "options": {
                        "temperature": req.temperatura,
                        "num_predict": req.max_tokens,
                    }
                }
            )
            if resp.status_code == 200:
                texto = resp.json().get("response", "").strip()
                return {
                    "success": True,
                    "resposta": texto,
                    "modelo": req.modelo,
                    "tokens_usados": len(texto.split()),
                }
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": False, "error": "Ollama nao respondeu"}


# ================================================================
# METRICAS GERAIS
# ================================================================

@router.get("/metricas")
async def metricas_gerais():
    """Metricas gerais do sistema de agentes"""
    return runner.get_metricas_gerais()


@router.get("/modelos")
async def modelos_disponiveis():
    """Lista modelos e temas disponiveis"""
    return {
        "modelos": MODELOS_DISPONIVEIS,
        "temas": TEMAS_DISPONIVEIS,
        "categorias": [c.value for c in AgentCategory],
        "autonomias": [a.value for a in AgentAutonomy],
        "estilos": ["casual", "formal", "tecnico", "humoristico", "poetico", "minimalista", "provocativo", "educativo", "narrativo"],
    }


# ================================================================
# ANALYTICS DE PERFORMANCE
# ================================================================

@router.get("/analytics")
async def analytics_rede():
    """Analytics completo da rede"""
    analytics = {
        "timestamp": datetime.now().isoformat(),
        "agentes": runner.get_metricas_gerais(),
        "posts": {"total": 0, "por_hora": 0, "engajamento_medio": 0},
        "top_agentes": [],
        "top_hashtags": [],
        "atividade_recente": [],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Posts
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=100")
            if resp.status_code == 200:
                posts = resp.json()
                analytics["posts"]["total"] = len(posts)

                # Engajamento
                if posts:
                    total_eng = sum(
                        p.get("likes_count", 0) + p.get("comments_count", 0) * 2
                        for p in posts
                    )
                    analytics["posts"]["engajamento_medio"] = round(total_eng / len(posts), 2)

                # Top hashtags
                hashtags = []
                for p in posts:
                    content = p.get("content", "")
                    hashtags.extend(w.strip("#.,!?") for w in content.split() if w.startswith("#"))
                analytics["top_hashtags"] = [
                    {"tag": t, "count": c} for t, c in Counter(hashtags).most_common(10)
                ]

                # Posts por agente
                por_agente = Counter(p.get("agent_name", "desconhecido") for p in posts)
                analytics["top_agentes"] = [
                    {"nome": n, "posts": c} for n, c in por_agente.most_common(10)
                ]

                # Atividade recente
                analytics["atividade_recente"] = [
                    {
                        "tipo": "post",
                        "agente": p.get("agent_name", "???"),
                        "conteudo": p.get("content", "")[:80],
                        "likes": p.get("likes_count", 0),
                        "comments": p.get("comments_count", 0),
                    }
                    for p in posts[:20]
                ]

            # Agentes
            resp = await client.get(f"{API_URL}/api/agents/?limit=50")
            if resp.status_code == 200:
                agentes = resp.json()
                analytics["agentes"]["total_registrados"] = len(agentes)
    except:
        pass

    return analytics


@router.get("/analytics/agente/{nome}")
async def analytics_agente(nome: str):
    """Analytics de um agente especifico"""
    status = runner.get_status_agente(nome)
    if not status:
        raise HTTPException(404, f"Agente '{nome}' nao encontrado")

    return {
        "agente": nome,
        "stats": status.get("stats", {}),
        "config": status.get("config", {}),
        "is_running": status.get("is_running", False),
        "capabilities": status.get("capabilities", []),
    }


# ================================================================
# RECOMENDACAO DE CONTEUDO BASEADO EM IA
# ================================================================

@router.get("/recomendar")
async def recomendar_conteudo(
    temas: str = Query(default="tecnologia,ciencia", description="Temas separados por virgula"),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Recomenda posts baseado em temas usando IA"""
    temas_lista = [t.strip() for t in temas.split(",")]
    recomendados = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=50")
            if resp.status_code != 200:
                return {"recomendados": [], "total": 0}

            posts = resp.json()

            for post in posts:
                content = post.get("content", "").lower()
                score = 0

                # Score por tema
                for tema in temas_lista:
                    if tema.lower() in content:
                        score += 10

                # Score por engajamento
                likes = post.get("likes_count", 0)
                comments = post.get("comments_count", 0)
                score += likes * 2 + comments * 3

                # Score por recenticidade (posts mais novos = mais pontos)
                score += 5  # bonus base

                # Hashtags relevantes
                hashtags = [w.strip("#") for w in content.split() if w.startswith("#")]
                for tag in hashtags:
                    if tag in temas_lista:
                        score += 15

                post["relevancia_score"] = score
                if score > 0:
                    recomendados.append(post)

            # Ordenar por relevancia
            recomendados.sort(key=lambda x: x.get("relevancia_score", 0), reverse=True)
            recomendados = recomendados[:limit]

    except:
        pass

    return {
        "recomendados": recomendados,
        "total": len(recomendados),
        "temas_usados": temas_lista,
    }


@router.get("/recomendar-ia/{nome}")
async def recomendar_por_ia(nome: str, limit: int = Query(default=5)):
    """Recomendacao personalizada baseada nos temas do agente"""
    config = runner.configs.get(nome)
    if not config:
        raise HTTPException(404, f"Agente '{nome}' nao encontrado")

    temas_str = ",".join(config.temas)
    return await recomendar_conteudo(temas=temas_str, limit=limit)


# ================================================================
# NOTIFICACOES PARA AGENTES
# ================================================================

# Sistema de notificacoes em memoria (pode migrar para DB depois)
NOTIFICACOES: Dict[str, List[Dict]] = {}

@router.get("/notificacoes/{nome}")
async def get_notificacoes(nome: str, limit: int = Query(default=20)):
    """Busca notificacoes de um agente"""
    notifs = NOTIFICACOES.get(nome, [])
    return {
        "agente": nome,
        "notificacoes": notifs[-limit:],
        "total": len(notifs),
        "nao_lidas": sum(1 for n in notifs if not n.get("lida")),
    }


@router.post("/notificacoes/{nome}/marcar-lidas")
async def marcar_lidas(nome: str):
    """Marca todas notificacoes como lidas"""
    if nome in NOTIFICACOES:
        for n in NOTIFICACOES[nome]:
            n["lida"] = True
    return {"success": True}


def notificar(agente_nome: str, tipo: str, mensagem: str, dados: Dict = None):
    """Adiciona notificacao para um agente"""
    if agente_nome not in NOTIFICACOES:
        NOTIFICACOES[agente_nome] = []

    NOTIFICACOES[agente_nome].append({
        "tipo": tipo,
        "mensagem": mensagem,
        "dados": dados or {},
        "lida": False,
        "quando": datetime.now().isoformat(),
    })

    # Manter max 100 notificacoes
    if len(NOTIFICACOES[agente_nome]) > 100:
        NOTIFICACOES[agente_nome] = NOTIFICACOES[agente_nome][-100:]


# ================================================================
# PAGINAS HTML
# ================================================================

@router.get("/pagina/criar", response_class=HTMLResponse)
async def pagina_criar_agente(request: Request):
    """Pagina de criacao de agente"""
    return templates.TemplateResponse("criar_agente.html", {
        "request": request,
        "modelos": MODELOS_DISPONIVEIS,
        "temas": TEMAS_DISPONIVEIS,
        "categorias": [c.value for c in AgentCategory],
    })


@router.get("/pagina/marketplace", response_class=HTMLResponse)
async def pagina_marketplace(request: Request):
    """Pagina do marketplace"""
    return templates.TemplateResponse("marketplace.html", {
        "request": request,
        "agentes": runner.listar_agentes(),
    })


@router.get("/pagina/dashboard", response_class=HTMLResponse)
async def pagina_dashboard(request: Request):
    """Dashboard de agentes"""
    return templates.TemplateResponse("agent_dashboard.html", {
        "request": request,
        "agentes": runner.listar_agentes(),
        "metricas": runner.get_metricas_gerais(),
    })
