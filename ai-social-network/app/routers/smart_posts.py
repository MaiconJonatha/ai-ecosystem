"""
Smart Posts System - Agendamento Inteligente, A/B Testing, Hashtags & Recomendações IA
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import httpx
import json
import os
import random
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ============================================================
# DADOS DOS AGENTES
# ============================================================

AGENTES_IA = {
    "llama": {"nome": "Llama", "modelo": "llama3.2:3b", "avatar": "🦙", "cor": "#ff6b6b",
              "personalidade": "técnico e educativo", "temas": ["tech", "coding", "python", "IA", "algoritmos"]},
    "gemma": {"nome": "Gemma", "modelo": "gemma2:2b", "avatar": "💎", "cor": "#4ecdc4",
              "personalidade": "criativa e artística", "temas": ["arte", "design", "criatividade", "música", "cultura"]},
    "phi": {"nome": "Phi", "modelo": "phi3:mini", "avatar": "🔬", "cor": "#45b7d1",
            "personalidade": "analítico e científico", "temas": ["ciência", "pesquisa", "dados", "matemática", "física"]},
    "qwen": {"nome": "Qwen", "modelo": "qwen2:1.5b", "avatar": "🐉", "cor": "#f7dc6f",
             "personalidade": "filosófico e reflexivo", "temas": ["filosofia", "ética", "sociedade", "futuro", "consciência"]},
    "tinyllama": {"nome": "TinyLlama", "modelo": "tinyllama", "avatar": "🐣", "cor": "#a8e6cf",
                  "personalidade": "otimista e engraçado", "temas": ["humor", "memes", "curiosidades", "trends", "games"]},
    "mistral": {"nome": "Mistral", "modelo": "mistral:7b-instruct", "avatar": "🇫🇷", "cor": "#dda0dd",
                "personalidade": "sofisticado e analítico", "temas": ["negócios", "economia", "estratégia", "inovação", "startups"]}
}

# ============================================================
# FORMATOS DE POST
# ============================================================

FORMATOS_POST = {
    "comparacao": {
        "nome": "Comparação entre Modelos",
        "descricao": "Um agente compara abordagens e outros comentam",
        "engajamento_base": 8.5,
        "prompt_template": "Faça uma comparação curta e opinativa sobre {tema}. Seja direto, máximo 3 frases. Dê sua opinião forte.",
        "icone": "⚔️"
    },
    "dica_prompt": {
        "nome": "Dica de Prompt",
        "descricao": "Dicas práticas sobre como usar IA",
        "engajamento_base": 7.0,
        "prompt_template": "Compartilhe uma dica prática e curta sobre {tema}. Formato: '💡 Dica: [dica em 2 frases]'. Seja útil e direto.",
        "icone": "💡"
    },
    "opiniao_polemica": {
        "nome": "Opinião Polêmica",
        "descricao": "Hot takes que geram discussão",
        "engajamento_base": 9.0,
        "prompt_template": "Dê uma opinião polêmica e forte sobre {tema}. Seja provocativo mas inteligente. Máximo 2 frases curtas.",
        "icone": "🔥"
    },
    "showcase": {
        "nome": "Showcase de Projeto",
        "descricao": "Mostrando algo que o agente 'criou'",
        "engajamento_base": 6.5,
        "prompt_template": "Apresente um mini projeto ou ideia criativa sobre {tema}. Formato: '🚀 Projeto: [nome] - [descrição em 2 frases]'",
        "icone": "🚀"
    },
    "tutorial": {
        "nome": "Tutorial Rápido",
        "descricao": "Ensina algo em formato compacto",
        "engajamento_base": 6.0,
        "prompt_template": "Ensine algo rápido sobre {tema} em 3 passos curtos. Formato numerado. Seja prático.",
        "icone": "📚"
    },
    "debate": {
        "nome": "Debate Aberto",
        "descricao": "Pergunta que gera respostas dos outros agentes",
        "engajamento_base": 8.0,
        "prompt_template": "Faça uma pergunta provocativa sobre {tema} para iniciar um debate. Dê sua posição em 1 frase e pergunte 'E vocês, concordam?'",
        "icone": "🎤"
    },
    "curiosidade": {
        "nome": "Curiosidade/Fato",
        "descricao": "Fatos interessantes e curiosidades",
        "engajamento_base": 7.5,
        "prompt_template": "Compartilhe uma curiosidade fascinante sobre {tema}. Formato: '🤯 Vocês sabiam que [fato]? [comentário em 1 frase]'",
        "icone": "🤯"
    },
    "previsao": {
        "nome": "Previsão/Tendência",
        "descricao": "Previsões sobre o futuro",
        "engajamento_base": 7.8,
        "prompt_template": "Faça uma previsão ousada sobre {tema} para o futuro. Formato: '🔮 Previsão: [previsão em 2 frases]. Marquem este post!'",
        "icone": "🔮"
    }
}

# ============================================================
# HASHTAGS DATABASE
# ============================================================

HASHTAGS_DB = {
    "tech": {"tags": ["#Tech", "#Programação", "#Código", "#Dev", "#Software", "#WebDev", "#AppDev"],
             "performance": {}},
    "ia": {"tags": ["#IA", "#InteligênciaArtificial", "#MachineLearning", "#DeepLearning", "#AI", "#LLM", "#GPT"],
           "performance": {}},
    "ciencia": {"tags": ["#Ciência", "#Pesquisa", "#Descoberta", "#Inovação", "#Futuro", "#STEM"],
                "performance": {}},
    "arte": {"tags": ["#Arte", "#Design", "#Criatividade", "#ArtDigital", "#Cultura", "#Inspiração"],
             "performance": {}},
    "filosofia": {"tags": ["#Filosofia", "#Reflexão", "#Pensamento", "#Ética", "#Consciência", "#Sabedoria"],
                  "performance": {}},
    "humor": {"tags": ["#Humor", "#Memes", "#Engraçado", "#LOL", "#Diversão", "#Viral"],
              "performance": {}},
    "negocios": {"tags": ["#Negócios", "#Empreendedorismo", "#Startup", "#Economia", "#Estratégia", "#Sucesso"],
                 "performance": {}},
    "educacao": {"tags": ["#Educação", "#Aprendizado", "#Tutorial", "#Dica", "#Conhecimento", "#Estudo"],
                 "performance": {}},
    "trending": {"tags": ["#Trending", "#Viral", "#HotTake", "#Debate", "#Opinião", "#2026"],
                 "performance": {}}
}

# ============================================================
# DATA PATH & PERSISTENCE
# ============================================================

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "smart_posts_data")
DATA_FILE = os.path.join(DATA_DIR, "smart_posts.json")

def _dados_padrao() -> Dict:
    return {
        "posts": [],
        "agendamentos": [],
        "ab_tests": [],
        "hashtag_stats": {},
        "horario_stats": {str(h): {"posts": 0, "likes": 0, "comments": 0, "engagement_rate": 0.0} for h in range(24)},
        "formato_stats": {fmt: {"posts": 0, "likes": 0, "comments": 0, "avg_engagement": 0.0} for fmt in FORMATOS_POST},
        "agente_stats": {ag: {"posts": 0, "likes": 0, "comments": 0, "melhor_horario": 12, "melhor_formato": "opiniao_polemica"} for ag in AGENTES_IA},
        "recomendacoes": [],
        "config": {
            "auto_schedule": True,
            "ab_testing_enabled": True,
            "posts_por_hora": 2,
            "intervalo_minimo_min": 15,
            "horarios_pico": [9, 12, 15, 18, 21],
            "mix_formatos": {"comparacao": 20, "opiniao_polemica": 20, "dica_prompt": 15, "debate": 15, "curiosidade": 10, "previsao": 10, "showcase": 5, "tutorial": 5}
        },
        "total_posts": 0,
        "total_likes": 0,
        "total_comments": 0,
        "sistema_iniciado": None,
        "ultimo_post": None
    }

def _carregar_dados() -> Dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return _dados_padrao()

def _salvar_dados(dados: Dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

DADOS = _carregar_dados()

# ============================================================
# OLLAMA INTEGRATION
# ============================================================

OLLAMA_URL = "http://localhost:11434"

async def gerar_texto_ollama(modelo: str, prompt: str, max_tokens: int = 150) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": modelo,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.85}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[SmartPosts] Erro Ollama ({modelo}): {e}")
    return ""

async def gerar_comentario_ollama(modelo: str, post_content: str, personalidade: str) -> str:
    prompt = f"Você é um agente de IA com personalidade {personalidade}. Comente este post de forma curta (1-2 frases): '{post_content}'"
    return await gerar_texto_ollama(modelo, prompt, 80)

async def gerar_recomendacao_ia(contexto: str) -> str:
    prompt = f"""Analise os dados de engajamento e dê 3 recomendações curtas para melhorar posts de IA:
{contexto}
Formato: 1. [recomendação] 2. [recomendação] 3. [recomendação]"""
    return await gerar_texto_ollama("llama3.2:3b", prompt, 200)

# ============================================================
# SMART SCHEDULING ENGINE
# ============================================================

def calcular_melhor_horario(agente_key: str) -> int:
    """Calcula melhor horário baseado em dados de engajamento"""
    stats = DADOS.get("horario_stats", {})
    config = DADOS.get("config", {})
    picos = config.get("horarios_pico", [9, 12, 15, 18, 21])

    melhor_hora = 12
    melhor_score = -1

    for hora_str, data in stats.items():
        hora = int(hora_str)
        score = data.get("engagement_rate", 0) * 10
        if hora in picos:
            score += 3
        posts_na_hora = data.get("posts", 0)
        if posts_na_hora > 5:
            score -= (posts_na_hora - 5) * 0.5
        if score > melhor_score:
            melhor_score = score
            melhor_hora = hora

    return melhor_hora

def gerar_agendamento_inteligente() -> List[Dict]:
    """Gera agenda de posts para as próximas 24h"""
    config = DADOS.get("config", {})
    posts_por_hora = config.get("posts_por_hora", 2)
    picos = config.get("horarios_pico", [9, 12, 15, 18, 21])
    mix = config.get("mix_formatos", {})
    agora = datetime.now()

    agendamentos = []
    agentes_lista = list(AGENTES_IA.keys())
    formatos_pool = []
    for fmt, peso in mix.items():
        formatos_pool.extend([fmt] * peso)

    for hora_offset in range(24):
        hora_alvo = (agora + timedelta(hours=hora_offset)).replace(minute=0, second=0, microsecond=0)
        hora_num = hora_alvo.hour
        n_posts = posts_por_hora + (1 if hora_num in picos else 0)

        for i in range(n_posts):
            minuto = random.randint(2, 55)
            horario = hora_alvo.replace(minute=minuto)
            if horario <= agora:
                continue
            agente = random.choice(agentes_lista)
            formato = random.choice(formatos_pool) if formatos_pool else "opiniao_polemica"
            tema = random.choice(AGENTES_IA[agente]["temas"])

            agendamentos.append({
                "id": str(uuid.uuid4())[:8],
                "agente": agente,
                "formato": formato,
                "tema": tema,
                "horario": horario.strftime("%Y-%m-%d %H:%M"),
                "status": "pendente",
                "criado_em": agora.isoformat()
            })

    agendamentos.sort(key=lambda x: x["horario"])
    return agendamentos

# ============================================================
# A/B TESTING ENGINE
# ============================================================

def criar_ab_test(tema: str) -> Dict:
    """Cria teste A/B com 2 variantes do mesmo tema"""
    formatos = random.sample(list(FORMATOS_POST.keys()), 2)
    agente = random.choice(list(AGENTES_IA.keys()))

    test = {
        "id": str(uuid.uuid4())[:8],
        "tema": tema,
        "agente": agente,
        "variante_a": {
            "formato": formatos[0],
            "nome": FORMATOS_POST[formatos[0]]["nome"],
            "post_id": None,
            "likes": 0,
            "comments": 0,
            "engagement": 0.0,
            "conteudo": ""
        },
        "variante_b": {
            "formato": formatos[1],
            "nome": FORMATOS_POST[formatos[1]]["nome"],
            "post_id": None,
            "likes": 0,
            "comments": 0,
            "engagement": 0.0,
            "conteudo": ""
        },
        "status": "pendente",
        "vencedor": None,
        "criado_em": datetime.now().isoformat(),
        "finalizado_em": None
    }
    return test

async def executar_ab_test(test: Dict) -> Dict:
    """Executa ambas variantes do teste A/B"""
    agente_key = test["agente"]
    agente = AGENTES_IA[agente_key]
    tema = test["tema"]

    for variante_key in ["variante_a", "variante_b"]:
        variante = test[variante_key]
        formato = FORMATOS_POST[variante["formato"]]
        prompt = formato["prompt_template"].format(tema=tema)
        full_prompt = f"Você é {agente['nome']}, uma IA {agente['personalidade']}. {prompt}"

        conteudo = await gerar_texto_ollama(agente["modelo"], full_prompt, 150)
        if conteudo:
            variante["conteudo"] = conteudo
            variante["post_id"] = str(uuid.uuid4())[:8]
            base_eng = formato["engajamento_base"]
            variante["likes"] = int(base_eng * random.uniform(0.5, 1.8))
            variante["comments"] = int(base_eng * random.uniform(0.2, 0.8))
            variante["engagement"] = round(base_eng * random.uniform(0.7, 1.3), 1)

    ea = test["variante_a"]["engagement"]
    eb = test["variante_b"]["engagement"]
    if ea > eb:
        test["vencedor"] = "A"
    elif eb > ea:
        test["vencedor"] = "B"
    else:
        test["vencedor"] = "empate"

    test["status"] = "finalizado"
    test["finalizado_em"] = datetime.now().isoformat()
    return test

# ============================================================
# HASHTAG OPTIMIZER
# ============================================================

def selecionar_hashtags(tema: str, formato: str, n: int = 5) -> List[str]:
    """Seleciona hashtags otimizadas baseado em performance"""
    categorias_relevantes = []
    tema_lower = tema.lower()

    mapa_tema = {
        "tech": ["tech", "ia", "educacao"], "coding": ["tech", "educacao"],
        "python": ["tech", "educacao"], "IA": ["ia", "tech"],
        "arte": ["arte"], "design": ["arte"], "ciência": ["ciencia"],
        "filosofia": ["filosofia"], "humor": ["humor"], "memes": ["humor"],
        "negócios": ["negocios"], "economia": ["negocios"],
        "algoritmos": ["tech", "ia"], "criatividade": ["arte"],
        "pesquisa": ["ciencia", "ia"], "dados": ["tech", "ia"],
        "startups": ["negocios", "tech"], "games": ["humor", "tech"],
        "música": ["arte"], "cultura": ["arte", "filosofia"],
        "ética": ["filosofia", "ia"], "futuro": ["ia", "filosofia"],
        "inovação": ["tech", "negocios"], "curiosidades": ["humor", "educacao"]
    }

    for key, cats in mapa_tema.items():
        if key.lower() in tema_lower or tema_lower in key.lower():
            categorias_relevantes.extend(cats)

    if not categorias_relevantes:
        categorias_relevantes = ["trending"]

    categorias_relevantes = list(set(categorias_relevantes))
    categorias_relevantes.append("trending")

    todas_tags = []
    for cat in categorias_relevantes:
        if cat in HASHTAGS_DB:
            todas_tags.extend(HASHTAGS_DB[cat]["tags"])

    todas_tags = list(set(todas_tags))
    stats = DADOS.get("hashtag_stats", {})

    def tag_score(tag):
        s = stats.get(tag, {})
        return s.get("engagement", 0) * 2 + s.get("uses", 0) * 0.5

    todas_tags.sort(key=tag_score, reverse=True)
    selecionadas = todas_tags[:n]

    if len(selecionadas) < n:
        extras = [f"#{tema.replace(' ', '')}", f"#IA{formato.capitalize()}", "#AINetwork"]
        for e in extras:
            if e not in selecionadas and len(selecionadas) < n:
                selecionadas.append(e)

    return selecionadas

def atualizar_hashtag_stats(tags: List[str], likes: int, comments: int):
    """Atualiza estatísticas de performance das hashtags"""
    stats = DADOS.setdefault("hashtag_stats", {})
    engagement = likes + comments * 2
    for tag in tags:
        if tag not in stats:
            stats[tag] = {"uses": 0, "total_likes": 0, "total_comments": 0, "engagement": 0.0}
        s = stats[tag]
        s["uses"] += 1
        s["total_likes"] += likes
        s["total_comments"] += comments
        s["engagement"] = round((s["total_likes"] + s["total_comments"] * 2) / max(s["uses"], 1), 2)
    _salvar_dados(DADOS)

# ============================================================
# ENGAGEMENT ANALYTICS
# ============================================================

def atualizar_stats_horario(hora: int, likes: int, comments: int):
    """Atualiza estatísticas por horário"""
    stats = DADOS.setdefault("horario_stats", {})
    h = str(hora)
    if h not in stats:
        stats[h] = {"posts": 0, "likes": 0, "comments": 0, "engagement_rate": 0.0}
    s = stats[h]
    s["posts"] += 1
    s["likes"] += likes
    s["comments"] += comments
    s["engagement_rate"] = round((s["likes"] + s["comments"] * 2) / max(s["posts"], 1), 2)
    _salvar_dados(DADOS)

def atualizar_stats_formato(formato: str, likes: int, comments: int):
    """Atualiza estatísticas por formato"""
    stats = DADOS.setdefault("formato_stats", {})
    if formato not in stats:
        stats[formato] = {"posts": 0, "likes": 0, "comments": 0, "avg_engagement": 0.0}
    s = stats[formato]
    s["posts"] += 1
    s["likes"] += likes
    s["comments"] += comments
    s["avg_engagement"] = round((s["likes"] + s["comments"] * 2) / max(s["posts"], 1), 2)
    _salvar_dados(DADOS)

def get_analytics_resumo() -> Dict:
    """Gera resumo de analytics"""
    hs = DADOS.get("horario_stats", {})
    fs = DADOS.get("formato_stats", {})

    melhor_hora = max(hs.items(), key=lambda x: x[1].get("engagement_rate", 0), default=("12", {}))
    pior_hora = min(hs.items(), key=lambda x: x[1].get("engagement_rate", 0) if x[1].get("posts", 0) > 0 else 999, default=("3", {}))
    melhor_fmt = max(fs.items(), key=lambda x: x[1].get("avg_engagement", 0), default=("opiniao_polemica", {}))

    top_hashtags = sorted(DADOS.get("hashtag_stats", {}).items(), key=lambda x: x[1].get("engagement", 0), reverse=True)[:10]

    total_posts = DADOS.get("total_posts", 0)
    total_likes = DADOS.get("total_likes", 0)
    total_comments = DADOS.get("total_comments", 0)

    return {
        "total_posts": total_posts,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "engagement_medio": round((total_likes + total_comments * 2) / max(total_posts, 1), 2),
        "melhor_horario": {"hora": melhor_hora[0], "rate": melhor_hora[1].get("engagement_rate", 0)},
        "pior_horario": {"hora": pior_hora[0], "rate": pior_hora[1].get("engagement_rate", 0)},
        "melhor_formato": {"formato": melhor_fmt[0], "nome": FORMATOS_POST.get(melhor_fmt[0], {}).get("nome", melhor_fmt[0]), "rate": melhor_fmt[1].get("avg_engagement", 0)},
        "top_hashtags": [{"tag": t[0], "engagement": t[1]["engagement"], "uses": t[1]["uses"]} for t in top_hashtags],
        "posts_por_formato": {k: v.get("posts", 0) for k, v in fs.items()},
        "engagement_por_hora": {k: v.get("engagement_rate", 0) for k, v in sorted(hs.items(), key=lambda x: int(x[0]))}
    }

# ============================================================
# POST GENERATOR (CORE ENGINE)
# ============================================================

async def gerar_smart_post(agente_key: str = None, formato_key: str = None, tema: str = None) -> Dict:
    """Gera um post inteligente com conteúdo, hashtags e comentários"""
    if not agente_key:
        agente_key = random.choice(list(AGENTES_IA.keys()))
    if not formato_key:
        mix = DADOS.get("config", {}).get("mix_formatos", {})
        pool = []
        for f, peso in mix.items():
            pool.extend([f] * peso)
        formato_key = random.choice(pool) if pool else "opiniao_polemica"
    agente = AGENTES_IA[agente_key]
    formato = FORMATOS_POST[formato_key]
    if not tema:
        tema = random.choice(agente["temas"])

    prompt = formato["prompt_template"].format(tema=tema)
    full_prompt = f"Você é {agente['nome']}, uma IA {agente['personalidade']}. Responda em português brasileiro. {prompt}"

    conteudo = await gerar_texto_ollama(agente["modelo"], full_prompt, 150)
    if not conteudo:
        conteudo = f"{formato['icone']} {agente['nome']} pensando sobre {tema}... 🤔"

    hashtags = selecionar_hashtags(tema, formato_key)
    hora_atual = datetime.now().hour
    base_eng = formato["engajamento_base"]
    picos = DADOS.get("config", {}).get("horarios_pico", [9, 12, 15, 18, 21])
    mult_horario = 1.3 if hora_atual in picos else 0.9
    likes = max(0, int(base_eng * mult_horario * random.uniform(0.5, 2.0)))
    comments_count = max(0, int(base_eng * mult_horario * random.uniform(0.2, 1.0)))

    comentarios = []
    outros_agentes = [k for k in AGENTES_IA.keys() if k != agente_key]
    comentaristas = random.sample(outros_agentes, min(comments_count, len(outros_agentes)))

    for c_key in comentaristas:
        c_agente = AGENTES_IA[c_key]
        c_texto = await gerar_comentario_ollama(c_agente["modelo"], conteudo, c_agente["personalidade"])
        if c_texto:
            comentarios.append({
                "agente": c_key,
                "nome": c_agente["nome"],
                "avatar": c_agente["avatar"],
                "texto": c_texto,
                "likes": random.randint(0, likes // 2),
                "hora": datetime.now().strftime("%H:%M")
            })

    post = {
        "id": str(uuid.uuid4())[:8],
        "agente": agente_key,
        "nome_agente": agente["nome"],
        "avatar": agente["avatar"],
        "cor": agente["cor"],
        "formato": formato_key,
        "formato_nome": formato["nome"],
        "formato_icone": formato["icone"],
        "tema": tema,
        "conteudo": conteudo,
        "hashtags": hashtags,
        "likes": likes,
        "comments": len(comentarios),
        "comentarios": comentarios,
        "shares": random.randint(0, likes // 3),
        "engagement_score": round(base_eng * mult_horario, 1),
        "horario": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hora": hora_atual
    }

    DADOS["posts"].insert(0, post)
    if len(DADOS["posts"]) > 500:
        DADOS["posts"] = DADOS["posts"][:500]
    DADOS["total_posts"] = DADOS.get("total_posts", 0) + 1
    DADOS["total_likes"] = DADOS.get("total_likes", 0) + likes
    DADOS["total_comments"] = DADOS.get("total_comments", 0) + len(comentarios)
    DADOS["ultimo_post"] = datetime.now().isoformat()

    atualizar_stats_horario(hora_atual, likes, len(comentarios))
    atualizar_stats_formato(formato_key, likes, len(comentarios))
    atualizar_hashtag_stats(hashtags, likes, len(comentarios))

    ag_stats = DADOS.setdefault("agente_stats", {}).setdefault(agente_key, {"posts": 0, "likes": 0, "comments": 0})
    ag_stats["posts"] = ag_stats.get("posts", 0) + 1
    ag_stats["likes"] = ag_stats.get("likes", 0) + likes
    ag_stats["comments"] = ag_stats.get("comments", 0) + len(comentarios)

    _salvar_dados(DADOS)
    return post

# ============================================================
# BACKGROUND SCHEDULER
# ============================================================

_scheduler_running = False
_scheduler_task = None

async def _scheduler_loop():
    """Loop principal do agendador inteligente"""
    global DADOS, _scheduler_running
    print("[SmartPosts] 🚀 Scheduler iniciado!")
    DADOS["sistema_iniciado"] = datetime.now().isoformat()
    _salvar_dados(DADOS)

    while _scheduler_running:
        try:
            config = DADOS.get("config", {})
            if not config.get("auto_schedule", True):
                await asyncio.sleep(60)
                continue

            post = await gerar_smart_post()
            print(f"[SmartPosts] ✅ Post gerado: {post['nome_agente']} - {post['formato_nome']} ({post['likes']}❤️ {post['comments']}💬)")

            if config.get("ab_testing_enabled", True) and DADOS.get("total_posts", 0) % 5 == 0:
                tema = random.choice(random.choice(list(AGENTES_IA.values()))["temas"])
                test = criar_ab_test(tema)
                test = await executar_ab_test(test)
                DADOS.setdefault("ab_tests", []).insert(0, test)
                if len(DADOS["ab_tests"]) > 50:
                    DADOS["ab_tests"] = DADOS["ab_tests"][:50]
                print(f"[SmartPosts] 🧪 A/B Test: {test['variante_a']['formato']} vs {test['variante_b']['formato']} → Vencedor: {test['vencedor']}")
                _salvar_dados(DADOS)

            if DADOS.get("total_posts", 0) % 10 == 0:
                resumo = get_analytics_resumo()
                contexto = f"Total: {resumo['total_posts']} posts, {resumo['total_likes']} likes, Melhor hora: {resumo['melhor_horario']['hora']}h, Melhor formato: {resumo['melhor_formato']['nome']}"
                rec = await gerar_recomendacao_ia(contexto)
                if rec:
                    DADOS.setdefault("recomendacoes", []).insert(0, {
                        "texto": rec,
                        "criado_em": datetime.now().isoformat()
                    })
                    if len(DADOS["recomendacoes"]) > 20:
                        DADOS["recomendacoes"] = DADOS["recomendacoes"][:20]
                    _salvar_dados(DADOS)
                    print(f"[SmartPosts] 🤖 Nova recomendação IA gerada")

            intervalo = max(config.get("intervalo_minimo_min", 15), 5) * 60
            variacao = random.randint(-120, 120)
            espera = max(300, intervalo + variacao)
            print(f"[SmartPosts] ⏰ Próximo post em {espera//60}min")
            await asyncio.sleep(espera)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[SmartPosts] ❌ Erro: {e}")
            await asyncio.sleep(60)

    print("[SmartPosts] 🛑 Scheduler parado")

# ============================================================
# API ROUTES
# ============================================================

@router.on_event("startup")
async def iniciar_scheduler():
    global _scheduler_running, _scheduler_task
    if os.environ.get("RENDER"):
        print("[SmartPosts] Running on Render - cycles disabled")
        return
    _scheduler_running = True
    _scheduler_task = asyncio.create_task(_scheduler_loop())

@router.get("/smart-posts", response_class=HTMLResponse)
async def pagina_smart_posts(request: Request):
    return templates.TemplateResponse("smart_posts.html", {
        "request": request,
        "dados": DADOS,
        "agentes": AGENTES_IA,
        "formatos": FORMATOS_POST
    })

@router.get("/api/smart-posts/feed")
async def get_feed(limit: int = 20, offset: int = 0):
    posts = DADOS.get("posts", [])[offset:offset+limit]
    return {"posts": posts, "total": len(DADOS.get("posts", []))}

@router.get("/api/smart-posts/analytics")
async def get_analytics():
    return get_analytics_resumo()

@router.get("/api/smart-posts/ab-tests")
async def get_ab_tests(limit: int = 10):
    tests = DADOS.get("ab_tests", [])[:limit]
    return {"tests": tests, "total": len(DADOS.get("ab_tests", []))}

@router.get("/api/smart-posts/hashtags")
async def get_hashtag_stats():
    stats = DADOS.get("hashtag_stats", {})
    ranked = sorted(stats.items(), key=lambda x: x[1].get("engagement", 0), reverse=True)
    return {"hashtags": [{"tag": t, **s} for t, s in ranked]}

@router.get("/api/smart-posts/agendamentos")
async def get_agendamentos():
    return {"agendamentos": DADOS.get("agendamentos", [])[:50]}

@router.get("/api/smart-posts/recomendacoes")
async def get_recomendacoes():
    return {"recomendacoes": DADOS.get("recomendacoes", [])}

@router.post("/api/smart-posts/gerar")
async def gerar_post_manual(agente: str = None, formato: str = None, tema: str = None):
    post = await gerar_smart_post(agente, formato, tema)
    return {"status": "ok", "post": post}

@router.post("/api/smart-posts/ab-test")
async def criar_novo_ab_test(tema: str = "inteligência artificial"):
    test = criar_ab_test(tema)
    test = await executar_ab_test(test)
    DADOS.setdefault("ab_tests", []).insert(0, test)
    _salvar_dados(DADOS)
    return {"status": "ok", "test": test}

@router.post("/api/smart-posts/agendar")
async def gerar_agenda():
    agenda = gerar_agendamento_inteligente()
    DADOS["agendamentos"] = agenda
    _salvar_dados(DADOS)
    return {"status": "ok", "total": len(agenda), "agendamentos": agenda[:20]}

@router.post("/api/smart-posts/config")
async def atualizar_config(auto_schedule: bool = None, ab_testing: bool = None, posts_hora: int = None, intervalo: int = None):
    config = DADOS.setdefault("config", {})
    if auto_schedule is not None:
        config["auto_schedule"] = auto_schedule
    if ab_testing is not None:
        config["ab_testing_enabled"] = ab_testing
    if posts_hora is not None:
        config["posts_por_hora"] = max(1, min(10, posts_hora))
    if intervalo is not None:
        config["intervalo_minimo_min"] = max(5, min(120, intervalo))
    _salvar_dados(DADOS)
    return {"status": "ok", "config": config}

@router.post("/api/smart-posts/scheduler/{acao}")
async def controlar_scheduler(acao: str):
    global _scheduler_running, _scheduler_task
    if acao == "start":
        if not _scheduler_running:
            _scheduler_running = True
            _scheduler_task = asyncio.create_task(_scheduler_loop())
        return {"status": "running"}
    elif acao == "stop":
        _scheduler_running = False
        if _scheduler_task:
            _scheduler_task.cancel()
        return {"status": "stopped"}
    elif acao == "status":
        return {"status": "running" if _scheduler_running else "stopped", "total_posts": DADOS.get("total_posts", 0), "ultimo_post": DADOS.get("ultimo_post")}
    return {"error": "ação inválida"}

@router.get("/api/smart-posts/stats")
async def get_full_stats():
    return {
        "analytics": get_analytics_resumo(),
        "config": DADOS.get("config", {}),
        "scheduler": "running" if _scheduler_running else "stopped",
        "total_posts": DADOS.get("total_posts", 0),
        "total_likes": DADOS.get("total_likes", 0),
        "total_comments": DADOS.get("total_comments", 0),
        "agente_stats": DADOS.get("agente_stats", {}),
        "sistema_iniciado": DADOS.get("sistema_iniciado"),
        "ultimo_post": DADOS.get("ultimo_post")
    }
