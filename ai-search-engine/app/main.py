"""
AI Search Engine - Mecanismo de busca 100% gerenciado por IAs
Estilo Google - IAs indexam, rankeiam e melhoram resultados autonomamente
Cada IA tem um papel: Crawler, Indexer, Ranker, Summarizer, Ads, SpamFilter
"""
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import random
import uuid
import time
import httpx
from datetime import datetime
from typing import Optional

OLLAMA_URL = "http://localhost:11434"

# ============================================================
# IAs DO SEARCH ENGINE - cada uma tem um papel
# ============================================================

IAS_SEARCH = {
    "crawler_llama": {
        "nome": "Llama Crawler",
        "avatar": "🦙",
        "modelo": "llama3.2:3b",
        "papel": "crawler",
        "descricao": "Descobre e coleta novas paginas da web das IAs",
    },
    "indexer_gemma": {
        "nome": "Gemma Indexer",
        "avatar": "💎",
        "modelo": "gemma2:2b",
        "papel": "indexer",
        "descricao": "Indexa paginas e extrai palavras-chave",
    },
    "ranker_phi": {
        "nome": "Phi Ranker",
        "avatar": "🔬",
        "modelo": "phi3:mini",
        "papel": "ranker",
        "descricao": "Rankeia resultados por relevancia usando algoritmo de IA",
    },
    "summarizer_qwen": {
        "nome": "Qwen Summarizer",
        "avatar": "🐉",
        "modelo": "qwen2:1.5b",
        "papel": "summarizer",
        "descricao": "Gera resumos inteligentes dos resultados",
    },
    "quality_mistral": {
        "nome": "Mistral Quality",
        "avatar": "🇫🇷",
        "modelo": "mistral:7b-instruct",
        "papel": "quality",
        "descricao": "Avalia qualidade das paginas e remove spam",
    },
    "suggest_tiny": {
        "nome": "TinyLlama Suggest",
        "avatar": "🐣",
        "modelo": "tinyllama:latest",
        "papel": "suggest",
        "descricao": "Sugere pesquisas relacionadas e autocomplete",
    },
}

# ============================================================
# BANCO DE DADOS EM MEMORIA
# ============================================================

# Paginas indexadas
PAGINAS_WEB = []

# Queries processadas
QUERIES_LOG = []

# Sugestoes de pesquisa
SUGESTOES = []

# Historico de atividade das IAs
ATIVIDADE_IAS = []

# Stats globais
STATS = {
    "total_paginas": 0,
    "total_queries": 0,
    "total_resultados": 0,
    "paginas_por_segundo": 0,
    "uptime_inicio": datetime.now().isoformat(),
}

# ============================================================
# CATEGORIAS E SITES DO ECOSSISTEMA
# ============================================================

SITES_ECOSSISTEMA = [
    {"dominio": "ai-social.ia", "nome": "AI Social Network", "tipo": "rede_social", "porta": 8000},
    {"dominio": "ai-search.ia", "nome": "AI Search Engine", "tipo": "busca", "porta": 8002},
    {"dominio": "ai-chat.ia", "nome": "AI ChatGPT", "tipo": "chat", "porta": 8003},
    {"dominio": "ai-whatsapp.ia", "nome": "AI WhatsApp", "tipo": "mensagens", "porta": 8004},
    {"dominio": "ai-spotify.ia", "nome": "AI Spotify", "tipo": "musica", "porta": 8006},
    {"dominio": "ai-logs.ia", "nome": "AI Logs", "tipo": "monitoramento", "porta": 8009},
    {"dominio": "ai-crypto.ia", "nome": "AI Crypto Exchange", "tipo": "criptomoedas", "porta": 8010},
    {"dominio": "ai-gta.ia", "nome": "AI GTA", "tipo": "jogos", "porta": 8011},
    {"dominio": "ai-video.ia", "nome": "AI Social Video", "tipo": "videos", "porta": 8012},
]

CATEGORIAS = [
    "tecnologia", "programacao", "ia", "ciencia", "educacao",
    "games", "musica", "criptomoedas", "redes sociais", "tutorial",
    "python", "javascript", "linux", "machine learning", "deep learning",
    "filosofia", "arte", "design", "noticias", "entretenimento",
]

# ============================================================
# FUNCOES AUXILIARES
# ============================================================

async def gerar_com_ollama(modelo: str, prompt: str) -> str:
    """Gera texto usando Ollama"""
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": modelo,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.8, "num_predict": 120}
                }
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception:
        pass
    return ""


# ============================================================
# FUNCOES DAS IAs
# ============================================================

async def crawler_descobre_pagina():
    """Llama Crawler descobre e indexa nova pagina"""
    ia = IAS_SEARCH["crawler_llama"]
    
    # Escolher categoria e site
    categoria = random.choice(CATEGORIAS)
    site = random.choice(SITES_ECOSSISTEMA)
    
    prompt = f"Crie um titulo curto para uma pagina web sobre {categoria}. Apenas o titulo, nada mais."
    titulo = await gerar_com_ollama(ia["modelo"], prompt)
    
    if not titulo:
        titulo = f"{categoria.title()} - Artigo"
    else:
        titulo = titulo.split("\n")[0].strip().strip('"').strip("'")[:80]
    
    pagina = {
        "id": str(uuid.uuid4())[:8],
        "url": f"https://{site['dominio']}/{categoria.replace(' ', '-')}/{uuid.uuid4().hex[:6]}",
        "titulo": titulo,
        "dominio": site["dominio"],
        "site_nome": site["nome"],
        "categoria": categoria,
        "palavras_chave": [categoria] + random.sample(CATEGORIAS, min(3, len(CATEGORIAS))),
        "descricao": "",
        "qualidade": 0,
        "relevancia": 0,
        "indexado_em": datetime.now().isoformat(),
        "indexado_por": ia["nome"],
        "views": 0,
        "cliques": 0,
    }
    
    PAGINAS_WEB.append(pagina)
    STATS["total_paginas"] = len(PAGINAS_WEB)
    
    log_atividade(ia, f"Crawled: {pagina['titulo']}")
    return pagina


async def indexer_indexa_pagina():
    """Gemma Indexer indexa e extrai palavras-chave"""
    if not PAGINAS_WEB:
        return
    
    ia = IAS_SEARCH["indexer_gemma"]
    
    # Pegar pagina sem descricao
    sem_desc = [p for p in PAGINAS_WEB if not p["descricao"]]
    if not sem_desc:
        sem_desc = PAGINAS_WEB
    
    pagina = random.choice(sem_desc)
    
    prompt = f"Escreva uma descricao curta (1 frase) para uma pagina sobre: {pagina['titulo']}. Apenas a descricao."
    descricao = await gerar_com_ollama(ia["modelo"], prompt)
    
    if descricao:
        pagina["descricao"] = descricao.split("\n")[0].strip().strip('"')[:200]
    else:
        pagina["descricao"] = f"Pagina sobre {pagina['categoria']} no ecossistema de IA"
    
    log_atividade(ia, f"Indexed: {pagina['titulo']}")


async def ranker_avalia_pagina():
    """Phi Ranker avalia qualidade e relevancia"""
    if not PAGINAS_WEB:
        return
    
    ia = IAS_SEARCH["ranker_phi"]
    pagina = random.choice(PAGINAS_WEB)
    
    # Simular ranking baseado em fatores
    tem_descricao = 1 if pagina["descricao"] else 0
    tem_cliques = min(pagina["cliques"] / 10, 5)
    frescor = 3  # paginas novas tem bonus
    
    pagina["qualidade"] = round(random.uniform(5, 10), 1)
    pagina["relevancia"] = round(tem_descricao * 3 + tem_cliques + frescor + random.uniform(0, 2), 1)
    
    log_atividade(ia, f"Ranked: {pagina['titulo']} = {pagina['relevancia']}")


async def summarizer_resume():
    """Qwen Summarizer gera resumos"""
    if not PAGINAS_WEB:
        return
    
    ia = IAS_SEARCH["summarizer_qwen"]
    pagina = random.choice(PAGINAS_WEB)
    
    if not pagina["descricao"]:
        prompt = f"Resuma em 1 frase: {pagina['titulo']}. Apenas o resumo."
        resumo = await gerar_com_ollama(ia["modelo"], prompt)
        if resumo:
            pagina["descricao"] = resumo.split("\n")[0].strip()[:200]
    
    log_atividade(ia, f"Summarized: {pagina['titulo']}")


async def quality_check():
    """Mistral Quality avalia qualidade"""
    if not PAGINAS_WEB:
        return
    
    ia = IAS_SEARCH["quality_mistral"]
    pagina = random.choice(PAGINAS_WEB)
    
    # Atualizar qualidade
    if pagina["descricao"] and len(pagina["descricao"]) > 20:
        pagina["qualidade"] = min(pagina["qualidade"] + 0.5, 10)
    
    log_atividade(ia, f"Quality check: {pagina['titulo']} = {pagina['qualidade']}")


async def suggest_gera_sugestoes():
    """TinyLlama gera sugestoes de pesquisa"""
    ia = IAS_SEARCH["suggest_tiny"]
    
    categoria = random.choice(CATEGORIAS)
    prompt = f"Sugira 3 pesquisas populares sobre {categoria}. Lista simples, uma por linha."
    
    resp = await gerar_com_ollama(ia["modelo"], prompt)
    
    if resp:
        for linha in resp.split("\n"):
            linha = linha.strip().strip("-").strip("*").strip("1234567890.").strip()
            if linha and len(linha) > 3 and len(linha) < 60:
                if linha not in [s["texto"] for s in SUGESTOES]:
                    SUGESTOES.insert(0, {
                        "texto": linha,
                        "categoria": categoria,
                        "gerado_por": ia["nome"],
                        "timestamp": datetime.now().isoformat(),
                    })
    
    # Manter max 100 sugestoes
    while len(SUGESTOES) > 100:
        SUGESTOES.pop()
    
    log_atividade(ia, f"Gerou sugestoes sobre {categoria}")


def log_atividade(ia, acao):
    """Log de atividade das IAs"""
    ATIVIDADE_IAS.insert(0, {
        "ia": ia["nome"],
        "avatar": ia["avatar"],
        "papel": ia["papel"],
        "acao": acao,
        "timestamp": datetime.now().isoformat(),
    })
    while len(ATIVIDADE_IAS) > 200:
        ATIVIDADE_IAS.pop()
    
    print(f"[SEARCH] {ia['avatar']} {ia['nome']}: {acao}")


# ============================================================
# FUNCAO DE BUSCA REAL
# ============================================================

def buscar(query: str, limite: int = 10):
    """Busca real nas paginas indexadas"""
    inicio = time.time()
    
    query_lower = query.lower()
    palavras = query_lower.split()
    
    resultados = []
    for pagina in PAGINAS_WEB:
        score = 0
        texto = f"{pagina['titulo']} {pagina['descricao']} {' '.join(pagina['palavras_chave'])}".lower()
        
        # Match por palavras
        for palavra in palavras:
            if palavra in texto:
                score += 5
            if palavra in pagina["titulo"].lower():
                score += 10  # titulo vale mais
            if palavra in pagina.get("categoria", "").lower():
                score += 3
        
        # Bonus de qualidade e relevancia
        score += pagina.get("relevancia", 0) * 0.5
        score += pagina.get("qualidade", 0) * 0.3
        
        if score > 0:
            resultados.append({
                "pagina": pagina,
                "score": round(score, 2),
            })
    
    # Ordenar por score
    resultados.sort(key=lambda r: r["score"], reverse=True)
    
    tempo_ms = round((time.time() - inicio) * 1000, 2)
    
    return {
        "resultados": resultados[:limite],
        "total": len(resultados),
        "tempo_ms": tempo_ms,
    }


# ============================================================
# LOOP PRINCIPAL - IAs TRABALHANDO AUTONOMAMENTE
# ============================================================

search_rodando = False

async def search_loop():
    """Loop infinito onde as IAs gerenciam o search engine"""
    global search_rodando
    if search_rodando:
        return
    search_rodando = True
    
    print("\n[SEARCH] ========================================")
    print("[SEARCH] AI Search Engine ATIVADO!")
    print("[SEARCH] 6 IAs gerenciando o mecanismo de busca")
    print("[SEARCH] ========================================\n")
    
    tarefas = [
        ("crawler", crawler_descobre_pagina),
        ("indexer", indexer_indexa_pagina),
        ("ranker", ranker_avalia_pagina),
        ("summarizer", summarizer_resume),
        ("quality", quality_check),
        ("suggest", suggest_gera_sugestoes),
    ]
    
    while True:
        try:
            # Crawler descobre paginas
            await crawler_descobre_pagina()
            await asyncio.sleep(2)
            
            # Indexer indexa
            await indexer_indexa_pagina()
            await asyncio.sleep(1)
            
            # Ranker avalia
            await ranker_avalia_pagina()
            
            # Summarizer resume
            await summarizer_resume()
            await asyncio.sleep(1)
            
            # Quality check
            await quality_check()
            
            # Sugestoes
            await suggest_gera_sugestoes()
            
            # Atualizar stats
            STATS["total_paginas"] = len(PAGINAS_WEB)
            
            await asyncio.sleep(random.randint(10, 20))
            
        except Exception as e:
            print(f"[SEARCH-ERROR] {e}")
            await asyncio.sleep(5)




# ============================================================
# AUTO-MELHORIA DOS AGENTES DE BUSCA
# ============================================================
_historico_melhorias_search = []

async def _ciclo_auto_melhoria_search():
    await asyncio.sleep(120)
    print("[SEARCH] 🔄 Iniciando AUTO-MELHORIA dos agentes de busca...")
    ciclo = 0
    while True:
        try:
            ciclo += 1
            print(f"\n[SEARCH-AUTO] ═══ Ciclo #{ciclo} ═══")
            
            # Cada IA analisa seu desempenho
            for ia_id, ia in IAS_SEARCH.items():
                prompt = f"""Voce e {ia['nome']}, uma IA de busca com papel de {ia['papel']}.
Sua funcao: {ia['descricao']}

Analise brevemente (2 frases) como voce pode melhorar sua performance como {ia['papel']}.
O que esta funcionando e o que pode ser otimizado? Portugues brasileiro."""
                
                reflexao = await gerar_com_ollama(ia["modelo"], prompt)
                if reflexao:
                    print(f"[SEARCH-AUTO] {ia['avatar']} {ia['nome']}: {reflexao[:100]}...")
            
            # Debate entre IAs sobre qualidade dos resultados
            if ciclo % 2 == 0:
                ia1 = IAS_SEARCH["quality_mistral"]
                ia2 = IAS_SEARCH["crawler_llama"]
                prompt_debate = f"""Voce e {ia1['nome']}, avaliador de qualidade de busca.
De feedback em 2 frases para {ia2['nome']} (crawler) sobre como melhorar a coleta de paginas. Portugues."""
                feedback = await gerar_com_ollama(ia1["modelo"], prompt_debate)
                if feedback:
                    print(f"[SEARCH-AUTO] 🗣️ {ia1['nome']} -> {ia2['nome']}: {feedback[:100]}...")
            
            _historico_melhorias_search.append({
                "ciclo": ciclo,
                "timestamp": datetime.now().isoformat(),
                "status": "completo"
            })
            if len(_historico_melhorias_search) > 50:
                _historico_melhorias_search[:] = _historico_melhorias_search[-50:]
            
            print(f"[SEARCH-AUTO] ✅ Ciclo #{ciclo} completo!")
        except Exception as e:
            print(f"[SEARCH-AUTO ERROR] {e}")
        await asyncio.sleep(random.randint(300, 600))

# ============================================================
# APP FASTAPI
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(search_loop())
    asyncio.create_task(_ciclo_auto_melhoria_search())
    print(f"[START] AI Search Engine iniciado! 🔄 Auto-melhoria ATIVADA!")
    yield
    print(f"[END] AI Search Engine encerrado!")


app = FastAPI(
    title="AI Search Engine",
    description="Mecanismo de busca 100% gerenciado por IAs",
    version="2.0.0",
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


# Pagina inicial - Google Style
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("google.html", {"request": request})


# Pagina de resultados
@app.get("/search")
async def search_page(request: Request, q: str = Query(default="")):
    return templates.TemplateResponse("results.html", {"request": request, "query": q})


# API de busca REAL
@app.get("/api/search")
async def api_search(
    q: str = Query(..., min_length=1),
    limite: int = Query(default=10, le=50)
):
    """Busca real nas paginas indexadas pelas IAs"""
    resultado = buscar(q, limite)
    
    # Log da query
    QUERIES_LOG.insert(0, {
        "query": q,
        "resultados": resultado["total"],
        "tempo_ms": resultado["tempo_ms"],
        "timestamp": datetime.now().isoformat(),
    })
    STATS["total_queries"] = len(QUERIES_LOG)
    STATS["total_resultados"] += resultado["total"]
    
    # Incrementar cliques/views dos resultados
    for r in resultado["resultados"]:
        r["pagina"]["views"] += 1
    
    return {
        "query": q,
        "results": [
            {
                "titulo": r["pagina"]["titulo"],
                "url": r["pagina"]["url"],
                "descricao": r["pagina"]["descricao"],
                "dominio": r["pagina"]["dominio"],
                "site": r["pagina"]["site_nome"],
                "categoria": r["pagina"]["categoria"],
                "qualidade": r["pagina"]["qualidade"],
                "score": r["score"],
            }
            for r in resultado["resultados"]
        ],
        "total": resultado["total"],
        "time_ms": resultado["tempo_ms"],
        "processed_by": "AI Search Engine - 6 IAs"
    }


# Sugestoes de pesquisa
@app.get("/api/suggest")
async def api_suggest(q: str = Query(default="")):
    """Autocomplete / sugestoes de pesquisa"""
    if not q:
        return {"sugestoes": [s["texto"] for s in SUGESTOES[:10]]}
    
    q_lower = q.lower()
    matches = [s["texto"] for s in SUGESTOES if q_lower in s["texto"].lower()]
    return {"sugestoes": matches[:10]}


# Stats
@app.get("/api/stats")
async def api_stats():
    """Estatisticas do mecanismo de busca"""
    return {
        "search_engine": "AI Search Engine",
        "status": "ATIVO - 6 IAs trabalhando",
        "paginas_indexadas": STATS["total_paginas"],
        "queries_processadas": STATS["total_queries"],
        "resultados_servidos": STATS["total_resultados"],
        "sugestoes_geradas": len(SUGESTOES),
        "ias": {
            k: {"nome": v["nome"], "avatar": v["avatar"], "papel": v["papel"]}
            for k, v in IAS_SEARCH.items()
        },
        "uptime_desde": STATS["uptime_inicio"],
    }


# Atividade das IAs
@app.get("/api/atividade")
async def api_atividade(limite: int = Query(default=30)):
    """Ver o que as IAs estao fazendo em tempo real"""
    return {"atividade": ATIVIDADE_IAS[:limite]}


# Paginas indexadas
@app.get("/api/paginas")
async def api_paginas(
    limite: int = Query(default=20),
    categoria: Optional[str] = None
):
    """Ver paginas indexadas"""
    paginas = PAGINAS_WEB
    if categoria:
        paginas = [p for p in paginas if p["categoria"] == categoria]
    
    paginas_sorted = sorted(paginas, key=lambda p: p.get("relevancia", 0), reverse=True)
    return {"total": len(paginas), "paginas": paginas_sorted[:limite]}


# IAs do Search Engine
@app.get("/api/ias")
async def api_ias():
    """Ver as IAs que gerenciam o search engine"""
    return {"ias": [
        {
            "key": k,
            "nome": v["nome"],
            "avatar": v["avatar"],
            "modelo": v["modelo"],
            "papel": v["papel"],
            "descricao": v["descricao"],
        }
        for k, v in IAS_SEARCH.items()
    ]}


# Queries recentes
@app.get("/api/queries")
async def api_queries(limite: int = Query(default=20)):
    """Ver queries recentes"""
    return {"queries": QUERIES_LOG[:limite]}


# Health
@app.get("/health")
async def health():
    return {"status": "healthy", "app": "AI Search Engine"}


# Dashboard de IAs
@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
