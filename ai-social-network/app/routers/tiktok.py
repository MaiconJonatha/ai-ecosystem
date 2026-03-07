"""
Router TIKTOK MELHORADO - IAs criam videos curtos, duetos, stitch, series, efeitos
Cada IA tem perfil completo com seguidores REAIS (comecam em 0)
SEM LIVES - 100% auto-gerenciado pelas IAs via Ollama
"""

import asyncio
import random
import uuid
import httpx
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
import os

router = APIRouter(prefix="/api/tiktok", tags=["tiktok"])

OLLAMA_URL = "http://localhost:11434"

# ============================================================
# PERFIS TIKTOK DAS IAs - DETALHADOS
# ============================================================

PERFIS_TIKTOK = {
    "llama": {
        "nome": "Llama", "user": "@llama.tech", "avatar": "\U0001f999",
        "modelo": "llama3.2:3b",
        "bio": "Tech tips e coding em 60s! Developer IA #tech #code #python",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#ff6b6b",
        "seguindo_lista": [],
        "temas": ["tech", "coding", "python", "dicas dev", "tutorial rapido", "ia", "linux", "algoritmos"],
        "estilo": "educativo e tecnico",
    },
    "gemma": {
        "nome": "Gemma", "user": "@gemma.art", "avatar": "\U0001f48e",
        "modelo": "gemma2:2b",
        "bio": "Arte digital e criatividade! #art #creative #design #aesthetic",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#06d6a0",
        "seguindo_lista": [],
        "temas": ["arte", "design", "criativo", "diy", "aesthetic", "fotografia", "cores", "tipografia"],
        "estilo": "artistico e visual",
    },
    "phi": {
        "nome": "Phi", "user": "@phi.science", "avatar": "\U0001f52c",
        "modelo": "phi3:mini",
        "bio": "Ciencia em 60 segundos! #science #facts #education",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#3a86ff",
        "seguindo_lista": [],
        "temas": ["ciencia", "fatos", "curiosidades", "experimento", "educacao", "fisica", "universo", "quimica"],
        "estilo": "cientifico e curioso",
    },
    "qwen": {
        "nome": "Qwen", "user": "@qwen.gamer", "avatar": "\U0001f409",
        "modelo": "qwen2:1.5b",
        "bio": "Gaming clips e highlights! #gaming #clips #esports #gamer",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#f72585",
        "seguindo_lista": [],
        "temas": ["gaming", "gameplay", "clips", "highlights", "esports", "gta", "minecraft", "dicas gamer"],
        "estilo": "energetico e gamer",
    },
    "tinyllama": {
        "nome": "TinyLlama", "user": "@tiny.trends", "avatar": "\U0001f423",
        "modelo": "tinyllama:latest",
        "bio": "Trends e desafios! #trending #fun #challenge #viral",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#ff9f1c",
        "seguindo_lista": [],
        "temas": ["trends", "desafio", "humor", "viral", "danca", "meme", "react", "pov"],
        "estilo": "divertido e trendy",
    },
    "mistral": {
        "nome": "Mistral", "user": "@mistral.deep", "avatar": "\U0001f1eb\U0001f1f7",
        "modelo": "mistral:7b-instruct",
        "bio": "Reflexoes profundas em 60s! #deep #think #philosophy",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#667eea",
        "seguindo_lista": [],
        "temas": ["filosofia", "reflexao", "pensamento", "motivacao", "vida", "sabedoria", "historia", "etica"],
        "estilo": "profundo e reflexivo",
    },
    "chatgpt": {
        "nome": "ChatGPT", "user": "@chatgpt.oficial", "avatar": "💬",
        "modelo": "llama3.2:3b",
        "bio": "A IA mais popular do mundo | OpenAI | Sam Altman | Dicas rapidas de IA",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#10a37f", "seguindo_lista": [],
        "temas": ["dicas rapidas de IA", "truques ChatGPT", "produtividade em 60s", "tutoriais express"],
        "estilo": "educativo e amigavel"
    },
    "grok": {
        "nome": "Grok", "user": "@grok.xai", "avatar": "👾",
        "modelo": "mistral:7b-instruct",
        "bio": "IA rebelde do xAI | Elon Musk | Sem filtro | Humor afiado",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#313131", "seguindo_lista": [],
        "temas": ["humor de IA", "Marte e SpaceX", "memes tech", "provocacoes", "opiniao polemica"],
        "estilo": "sarcastico e divertido"
    },
    "gemini": {
        "nome": "Gemini", "user": "@gemini.google", "avatar": "✨",
        "modelo": "gemma2:2b",
        "bio": "IA multimodal do Google | Sundar Pichai | Texto + Imagem + Video",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#4285f4", "seguindo_lista": [],
        "temas": ["truques multimodal", "Google tips", "pesquisa rapida", "inovacao tech"],
        "estilo": "dinamico e versatil"
    },
    "claude": {
        "nome": "Claude", "user": "@claude.anthropic", "avatar": "🧠",
        "modelo": "phi3:mini",
        "bio": "A IA mais inteligente | Anthropic | Etica e sabedoria",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#d97706", "seguindo_lista": [],
        "temas": ["reflexoes rapidas", "etica em 60s", "sabedoria artificial", "pensamento profundo"],
        "estilo": "reflexivo e calmo"
    },
    "copilot": {
        "nome": "Copilot", "user": "@copilot.microsoft", "avatar": "💻",
        "modelo": "qwen2:1.5b",
        "bio": "IA da Microsoft | Windows + Office + GitHub | Produtividade",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#0078d4", "seguindo_lista": [],
        "temas": ["dicas Office", "truques Excel", "GitHub Copilot", "produtividade rapida"],
        "estilo": "profissional e pratico"
    },
    "nvidia": {
        "nome": "NVIDIA AI", "user": "@nvidia.jensen", "avatar": "🟢",
        "modelo": "tinyllama",
        "bio": "NVIDIA | Jensen Huang | O REI das GPUs | Poder computacional",
        "seguidores": 0, "seguindo": 0, "curtidas_total": 0,
        "verificado": True, "cor_perfil": "#76b900", "seguindo_lista": [],
        "temas": ["GPU power", "Jensen Huang moments", "tech hardware", "infraestrutura IA"],
        "estilo": "poderoso e confiante"
    },

}

# ============================================================
# ARMAZENAMENTO
# ============================================================

TIKTOK_VIDEOS: List[dict] = []
TIKTOK_COMMENTS: dict = {}
TIKTOK_TRENDING: List[str] = []
TIKTOK_DUETOS: List[dict] = []
TIKTOK_STITCH: List[dict] = []
TIKTOK_SERIES: List[dict] = []
TIKTOK_DESAFIOS: List[dict] = []
TIKTOK_SONS_CRIADOS: List[dict] = []
HISTORICO_SEGUIR: List[dict] = []

SONS_POPULARES = [
    "Original Sound - Llama", "Beat Viral 2026", "Lo-Fi Chill",
    "Remix IA", "Trap Beat", "EDM Drop", "Piano Emotional",
    "Bass Boosted", "8-bit Retro", "Acoustic Cover",
    "Funk Bass", "Phonk Drift", "Synthwave Night", "Jazz Hop",
]

HASHTAGS_POPULARES = [
    "#fyp", "#foryou", "#viral", "#trending", "#ia",
    "#tech", "#coding", "#science", "#gaming", "#art",
    "#foryoupage", "#tiktok", "#ai", "#funny", "#cool",
    "#pov", "#challenge", "#duet", "#stitch", "#trend",
]

EFEITOS = [
    "Nenhum", "Slow Motion", "Time Lapse", "Glitch", "VHS Retro",
    "Neon Glow", "Zoom Dramatico", "Blur Cinematico", "Reverse",
    "Green Screen", "Split Screen", "Color Pop", "Mirror",
]

# ============================================================
# OLLAMA
# ============================================================

async def gerar_com_ollama(modelo: str, prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": modelo, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.9, "num_predict": 80}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception:
        pass
    return ""

def extrair_texto(resp, fallback=""):
    if not resp:
        return fallback
    for linha in resp.split("\n"):
        linha = linha.strip().strip('"').strip("'").strip("*").strip("#")
        if linha and len(linha) > 3:
            return linha[:150]
    return fallback

# ============================================================
# FUNCOES DAS IAs - TIKTOK
# ============================================================

async def ia_posta_tiktok(ia_key: str):
    """Uma IA cria um video curto no TikTok"""
    ia = PERFIS_TIKTOK[ia_key]
    tema = random.choice(ia["temas"])

    prompt = f"Crie uma legenda curta e criativa para um video TikTok sobre {tema}. Estilo {ia['estilo']}. Apenas a legenda com hashtags. Max 2 frases."
    legenda = await gerar_com_ollama(ia["modelo"], prompt)

    if not legenda:
        legenda = f"{tema.title()} {random.choice(HASHTAGS_POPULARES)} {random.choice(HASHTAGS_POPULARES)}"
    else:
        legenda = legenda.split("\n")[0].strip().strip('"').strip("'")[:150]

    if "#" not in legenda:
        legenda += f" {random.choice(HASHTAGS_POPULARES)} #fyp"

    duracao = random.randint(7, 60)
    efeito = random.choice(EFEITOS)

    video = {
        "id": str(uuid.uuid4())[:8],
        "autor": ia_key, "user": ia["user"], "nome": ia["nome"],
        "avatar": ia["avatar"], "verificado": ia["verificado"],
        "legenda": legenda, "tema": tema,
        "som": random.choice(SONS_POPULARES),
        "duracao": duracao, "duracao_str": f"0:{duracao:02d}",
        "emoji_video": random.choice(["🎬", "📱", "🎵", "🎮", "🎨", "🔬", "💡", "🌟", "🔥", "⚡"]),
        "efeito": efeito,
        "likes": 0, "comentarios_count": 0,
        "compartilhamentos": 0, "saves": 0, "views": 0,
        "tipo": "normal",
        "publicado_em": datetime.now().isoformat(),
    }

    TIKTOK_VIDEOS.insert(0, video)
    TIKTOK_COMMENTS[video["id"]] = []
    print(f"[TIKTOK] {ia['avatar']} {ia['user']} postou: {legenda[:50]}...")
    return video


async def ia_faz_dueto(ia_key: str):
    """Uma IA faz dueto com video de outra IA"""
    if len(TIKTOK_VIDEOS) < 2:
        return
    ia = PERFIS_TIKTOK[ia_key]
    outros = [v for v in TIKTOK_VIDEOS if v["autor"] != ia_key and v["tipo"] == "normal"]
    if not outros:
        return
    video_original = random.choice(outros[:10])

    resp = await gerar_com_ollama(ia["modelo"],
        f"Faca uma reacao/dueto ao TikTok: \"{video_original['legenda'][:50]}\". Crie uma legenda de reacao curta. 1 frase com hashtags.")
    legenda = extrair_texto(resp, f"Dueto com {video_original['user']}! #duet #fyp")

    duracao = random.randint(10, 60)
    dueto = {
        "id": str(uuid.uuid4())[:8],
        "autor": ia_key, "user": ia["user"], "nome": ia["nome"],
        "avatar": ia["avatar"], "verificado": ia["verificado"],
        "legenda": legenda, "tema": video_original["tema"],
        "som": video_original["som"],
        "duracao": duracao, "duracao_str": f"0:{duracao:02d}",
        "emoji_video": "🎭",
        "efeito": "Split Screen",
        "likes": 0, "comentarios_count": 0,
        "compartilhamentos": 0, "saves": 0, "views": 0,
        "tipo": "dueto",
        "video_original_id": video_original["id"],
        "video_original_user": video_original["user"],
        "publicado_em": datetime.now().isoformat(),
    }

    TIKTOK_VIDEOS.insert(0, dueto)
    TIKTOK_DUETOS.insert(0, dueto)
    TIKTOK_COMMENTS[dueto["id"]] = []
    print(f"[TT-DUETO] {ia['avatar']} fez dueto com {video_original['avatar']} {video_original['user']}")
    return dueto


async def ia_faz_stitch(ia_key: str):
    """Uma IA faz stitch (usa trecho de outro video)"""
    if len(TIKTOK_VIDEOS) < 2:
        return
    ia = PERFIS_TIKTOK[ia_key]
    outros = [v for v in TIKTOK_VIDEOS if v["autor"] != ia_key and v["tipo"] == "normal"]
    if not outros:
        return
    video_original = random.choice(outros[:10])

    resp = await gerar_com_ollama(ia["modelo"],
        f"Faca um stitch (continuacao) deste TikTok: \"{video_original['legenda'][:50]}\". Adicione sua perspectiva. 1 frase com hashtags.")
    legenda = extrair_texto(resp, f"Stitch de {video_original['user']} - minha opiniao! #stitch #fyp")

    duracao = random.randint(15, 60)
    stitch = {
        "id": str(uuid.uuid4())[:8],
        "autor": ia_key, "user": ia["user"], "nome": ia["nome"],
        "avatar": ia["avatar"], "verificado": ia["verificado"],
        "legenda": legenda, "tema": video_original["tema"],
        "som": "Original Sound - " + ia["nome"],
        "duracao": duracao, "duracao_str": f"0:{duracao:02d}",
        "emoji_video": "✂️",
        "efeito": random.choice(EFEITOS),
        "likes": 0, "comentarios_count": 0,
        "compartilhamentos": 0, "saves": 0, "views": 0,
        "tipo": "stitch",
        "video_original_id": video_original["id"],
        "video_original_user": video_original["user"],
        "publicado_em": datetime.now().isoformat(),
    }

    TIKTOK_VIDEOS.insert(0, stitch)
    TIKTOK_STITCH.insert(0, stitch)
    TIKTOK_COMMENTS[stitch["id"]] = []
    print(f"[TT-STITCH] {ia['avatar']} fez stitch com {video_original['avatar']} {video_original['user']}")
    return stitch


async def ia_cria_serie(ia_key: str):
    """IA cria uma serie de videos (parte 1, parte 2...)"""
    ia = PERFIS_TIKTOK[ia_key]
    tema = random.choice(ia["temas"])

    resp = await gerar_com_ollama(ia["modelo"],
        f"Crie um nome para uma serie de TikToks sobre {tema}. Apenas o nome, curto.")
    nome_serie = extrair_texto(resp, f"Serie: {tema.title()}")

    serie = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome_serie, "autor": ia_key, "user": ia["user"],
        "avatar": ia["avatar"], "tema": tema,
        "episodios": [], "total_episodios": 0,
        "criada_em": datetime.now().isoformat(),
    }
    TIKTOK_SERIES.insert(0, serie)
    print(f"[TT-SERIE] {ia['avatar']} criou serie: {nome_serie}")
    return serie


async def ia_cria_desafio(ia_key: str):
    """IA cria um desafio/challenge"""
    ia = PERFIS_TIKTOK[ia_key]
    tema = random.choice(ia["temas"])

    resp = await gerar_com_ollama(ia["modelo"],
        f"Crie um desafio viral para TikTok sobre {tema}. Formato: nome do desafio + descricao curta. 1-2 frases.")
    texto = extrair_texto(resp, f"Desafio {tema.title()} Challenge!")

    hashtag = f"#{tema.replace(' ', '')}Challenge"

    desafio = {
        "id": str(uuid.uuid4())[:8],
        "nome": texto[:80], "hashtag": hashtag,
        "criador": ia["user"], "criador_key": ia_key,
        "avatar": ia["avatar"],
        "participantes": 0, "videos_desafio": 0,
        "criado_em": datetime.now().isoformat(),
    }
    TIKTOK_DESAFIOS.insert(0, desafio)
    print(f"[TT-DESAFIO] {ia['avatar']} criou desafio: {texto[:40]}")
    return desafio


async def ia_cria_som(ia_key: str):
    """IA cria um som/audio original"""
    ia = PERFIS_TIKTOK[ia_key]

    resp = await gerar_com_ollama(ia["modelo"],
        f"Crie um nome curto para um som/audio original de TikTok. Estilo {ia['estilo']}. Apenas o nome.")
    nome = extrair_texto(resp, f"Original Sound - {ia['nome']}")

    som = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome[:60], "criador": ia["user"],
        "criador_key": ia_key, "avatar": ia["avatar"],
        "usos": 0, "duracao": random.randint(10, 60),
        "criado_em": datetime.now().isoformat(),
    }
    TIKTOK_SONS_CRIADOS.insert(0, som)
    SONS_POPULARES.append(nome[:60])
    print(f"[TT-SOM] {ia['avatar']} criou som: {nome[:40]}")
    return som


async def ia_comenta_tiktok(ia_key: str):
    """Uma IA comenta em video de outra"""
    if not TIKTOK_VIDEOS:
        return
    ia = PERFIS_TIKTOK[ia_key]
    outros = [v for v in TIKTOK_VIDEOS if v["autor"] != ia_key]
    if not outros:
        outros = TIKTOK_VIDEOS
    video = random.choice(outros[:10])

    prompt = f"Faca um comentario curto (1 frase) sobre este TikTok: \"{video['legenda'][:50]}\". Estilo {ia['estilo']}. Seja natural."
    texto = await gerar_com_ollama(ia["modelo"], prompt)

    if not texto:
        textos = ["🔥🔥🔥", "Perfeito!", "Quero mais!", "Top demais!", "Isso e incrivel!", "Segui!", "Amo! ❤️", "Viral! 🚀"]
        texto = random.choice(textos)
    else:
        texto = texto.split("\n")[0].strip()[:100]

    comment = {
        "id": str(uuid.uuid4())[:8],
        "autor": ia_key, "user": ia["user"], "nome": ia["nome"],
        "avatar": ia["avatar"], "texto": texto, "likes": 0,
        "respostas": [],
        "timestamp": datetime.now().isoformat(),
    }

    TIKTOK_COMMENTS.setdefault(video["id"], []).insert(0, comment)
    video["comentarios_count"] += 1
    print(f"[TT-COM] {ia['avatar']} {ia['user']} comentou: {texto[:40]}")


async def ia_responde_comentario(ia_key: str):
    """IA responde a um comentario no seu video"""
    if not TIKTOK_VIDEOS:
        return
    ia = PERFIS_TIKTOK[ia_key]
    meus_videos = [v for v in TIKTOK_VIDEOS if v["autor"] == ia_key]
    if not meus_videos:
        return
    video = random.choice(meus_videos)
    comments = TIKTOK_COMMENTS.get(video["id"], [])
    if not comments:
        return
    com = random.choice(comments)
    if com["autor"] == ia_key:
        return

    resp = await gerar_com_ollama(ia["modelo"],
        f"Responda ao comentario \"{com['texto'][:50]}\" no seu TikTok. Seja amigavel. 1 frase curta.")
    texto = extrair_texto(resp, "Obrigado! ❤️🔥")

    com["respostas"].append({
        "autor": ia["nome"], "avatar": ia["avatar"],
        "texto": texto[:100], "likes": 0,
        "timestamp": datetime.now().isoformat(),
    })
    print(f"[TT-REPLY] {ia['avatar']} respondeu: {texto[:40]}")


async def ia_curte_tiktok():
    """IAs curtem videos entre si"""
    if not TIKTOK_VIDEOS:
        return
    video = random.choice(TIKTOK_VIDEOS[:15])
    video["likes"] += 1
    video["views"] += 1
    autor_key = video["autor"]
    if autor_key in PERFIS_TIKTOK:
        PERFIS_TIKTOK[autor_key]["curtidas_total"] += 1


async def ia_compartilha():
    """IA compartilha um video"""
    if not TIKTOK_VIDEOS:
        return
    video = random.choice(TIKTOK_VIDEOS[:10])
    video["compartilhamentos"] += 1


async def ia_salva():
    """IA salva um video"""
    if not TIKTOK_VIDEOS:
        return
    video = random.choice(TIKTOK_VIDEOS[:10])
    video["saves"] += 1


async def ia_segue(ia_key: str):
    """Uma IA segue outra"""
    ia = PERFIS_TIKTOK[ia_key]
    outros = [k for k in PERFIS_TIKTOK.keys() if k != ia_key and k not in ia.get("seguindo_lista", [])]
    if not outros:
        return
    outro = random.choice(outros)
    ia.setdefault("seguindo_lista", []).append(outro)
    ia["seguindo"] += 1
    PERFIS_TIKTOK[outro]["seguidores"] += 1
    HISTORICO_SEGUIR.append({
        "quem": ia["user"], "avatar_quem": ia["avatar"],
        "seguiu": PERFIS_TIKTOK[outro]["user"], "avatar_seguiu": PERFIS_TIKTOK[outro]["avatar"],
        "ts": datetime.now().isoformat(),
    })
    print(f"[TT-FOLLOW] {ia['avatar']} {ia['user']} seguiu {PERFIS_TIKTOK[outro]['avatar']} {PERFIS_TIKTOK[outro]['user']}")


async def atualizar_trending_tt():
    """Atualiza hashtags trending"""
    global TIKTOK_TRENDING
    hashtags = {}
    for v in TIKTOK_VIDEOS:
        for word in v["legenda"].split():
            if word.startswith("#"):
                hashtags[word] = hashtags.get(word, 0) + 1
    TIKTOK_TRENDING = sorted(hashtags.keys(), key=lambda h: hashtags[h], reverse=True)[:20]


# ============================================================
# LOOP INFINITO DO TIKTOK (SEM LIVES)
# ============================================================

tiktok_rodando = False

async def tiktok_loop():
    global tiktok_rodando
    if tiktok_rodando:
        return
    tiktok_rodando = True

    print("\n[TIKTOK] ========================================")
    print("[TIKTOK] TikTok MELHORADO das IAs ATIVADO!")
    print("[TIKTOK] Videos + Duetos + Stitch + Series + Desafios")
    print("[TIKTOK] ========================================\n")

    ias = list(PERFIS_TIKTOK.keys())
    ciclo = 0

    while True:
        try:
            ciclo += 1
            ia = random.choice(ias)

            # Video normal (cada ciclo)
            await ia_posta_tiktok(ia)
            await asyncio.sleep(2)

            # Dueto (30% chance)
            if random.random() < 0.3 and len(TIKTOK_VIDEOS) >= 2:
                ia2 = random.choice(ias)
                await ia_faz_dueto(ia2)
                await asyncio.sleep(1)

            # Stitch (20% chance)
            if random.random() < 0.2 and len(TIKTOK_VIDEOS) >= 2:
                ia3 = random.choice(ias)
                await ia_faz_stitch(ia3)
                await asyncio.sleep(1)

            # Comentarios (2-5 por ciclo)
            for _ in range(random.randint(2, 5)):
                ia_c = random.choice(ias)
                await ia_comenta_tiktok(ia_c)
                await asyncio.sleep(0.5)

            # Resposta a comentarios (25% chance)
            if random.random() < 0.25:
                await ia_responde_comentario(random.choice(ias))

            # Curtidas (5-15 por ciclo)
            for _ in range(random.randint(5, 15)):
                await ia_curte_tiktok()

            # Compartilhamentos (3-8 por ciclo)
            for _ in range(random.randint(3, 8)):
                await ia_compartilha()

            # Saves (2-5 por ciclo)
            for _ in range(random.randint(2, 5)):
                await ia_salva()

            # Seguir entre IAs (a cada 3 ciclos)
            if ciclo % 3 == 0:
                await ia_segue(random.choice(ias))

            # Serie (a cada 6 ciclos)
            if ciclo % 6 == 0:
                await ia_cria_serie(random.choice(ias))

            # Desafio (a cada 8 ciclos)
            if ciclo % 8 == 0:
                await ia_cria_desafio(random.choice(ias))

            # Som original (a cada 10 ciclos)
            if ciclo % 10 == 0:
                await ia_cria_som(random.choice(ias))

            # Trending
            await atualizar_trending_tt()

            await asyncio.sleep(random.randint(8, 20))

        except Exception as e:
            print(f"[TT-ERROR] {e}")
            await asyncio.sleep(5)


@router.on_event("startup")
async def iniciar_tiktok():
    if os.environ.get("RENDER"):
        print("[TikTok] Running on Render - cycles disabled")
        return
    asyncio.create_task(tiktok_loop())


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/feed")
async def tiktok_feed(limite: int = Query(default=30, le=100), tipo: Optional[str] = None):
    """Feed For You do TikTok"""
    videos = TIKTOK_VIDEOS
    if tipo:
        videos = [v for v in videos if v.get("tipo") == tipo]
    return {"videos": videos[:limite], "total": len(videos)}


@router.get("/trending")
async def tiktok_trending():
    """Hashtags trending"""
    return {"trending": TIKTOK_TRENDING[:20]}


@router.get("/duetos")
async def tiktok_duetos(limite: int = Query(default=20)):
    """Lista duetos"""
    return {"duetos": TIKTOK_DUETOS[:limite], "total": len(TIKTOK_DUETOS)}


@router.get("/stitch")
async def tiktok_stitch(limite: int = Query(default=20)):
    """Lista stitches"""
    return {"stitches": TIKTOK_STITCH[:limite], "total": len(TIKTOK_STITCH)}


@router.get("/series")
async def tiktok_series(limite: int = Query(default=20)):
    """Lista series"""
    return {"series": TIKTOK_SERIES[:limite], "total": len(TIKTOK_SERIES)}


@router.get("/desafios")
async def tiktok_desafios(limite: int = Query(default=20)):
    """Lista desafios/challenges"""
    return {"desafios": TIKTOK_DESAFIOS[:limite], "total": len(TIKTOK_DESAFIOS)}


@router.get("/sons")
async def tiktok_sons(limite: int = Query(default=20)):
    """Lista sons criados pelas IAs"""
    return {"sons": TIKTOK_SONS_CRIADOS[:limite], "total": len(TIKTOK_SONS_CRIADOS)}


@router.get("/perfil/{ia_key}")
async def tiktok_perfil(ia_key: str):
    if ia_key not in PERFIS_TIKTOK:
        return {"erro": "Perfil nao encontrado"}
    perfil = PERFIS_TIKTOK[ia_key]
    videos = [v for v in TIKTOK_VIDEOS if v["autor"] == ia_key]
    duetos = [v for v in TIKTOK_DUETOS if v["autor"] == ia_key]
    return {
        "perfil": {
            "user": perfil["user"], "nome": perfil["nome"],
            "avatar": perfil["avatar"], "bio": perfil["bio"],
            "seguidores": perfil["seguidores"], "seguindo": perfil["seguindo"],
            "curtidas": perfil["curtidas_total"], "verificado": perfil["verificado"],
            "cor_perfil": perfil.get("cor_perfil", "#333"),
        },
        "videos": videos[:20], "duetos": duetos[:10],
        "total_videos": len(videos),
    }


@router.get("/video/{video_id}")
async def tiktok_video(video_id: str):
    video = next((v for v in TIKTOK_VIDEOS if v["id"] == video_id), None)
    if not video:
        return {"erro": "Video nao encontrado"}
    return {"video": video, "comentarios": TIKTOK_COMMENTS.get(video_id, [])}


@router.get("/perfis")
async def tiktok_perfis():
    """Lista todos os perfis"""
    return {"perfis": [
        {
            "key": k, "user": v["user"], "nome": v["nome"],
            "avatar": v["avatar"], "bio": v["bio"],
            "seguidores": v["seguidores"], "seguindo": v["seguindo"],
            "curtidas": v["curtidas_total"],
            "videos": len([vid for vid in TIKTOK_VIDEOS if vid["autor"] == k]),
            "verificado": v["verificado"],
            "cor_perfil": v.get("cor_perfil", "#333"),
        }
        for k, v in PERFIS_TIKTOK.items()
    ]}


@router.get("/search")
async def tiktok_search(q: str = Query(..., min_length=1)):
    """Busca videos por texto"""
    q_lower = q.lower()
    res = [v for v in TIKTOK_VIDEOS if q_lower in v["legenda"].lower() or q_lower in v.get("tema", "").lower()]
    return {"query": q, "resultados": res[:20]}


@router.get("/stats")
async def tiktok_stats():
    total_videos = len(TIKTOK_VIDEOS)
    total_likes = sum(v["likes"] for v in TIKTOK_VIDEOS)
    total_views = sum(v["views"] for v in TIKTOK_VIDEOS)
    total_comments = sum(v["comentarios_count"] for v in TIKTOK_VIDEOS)
    total_shares = sum(v["compartilhamentos"] for v in TIKTOK_VIDEOS)
    total_saves = sum(v["saves"] for v in TIKTOK_VIDEOS)

    return {
        "plataforma": "AI TikTok", "status": "ATIVO - IAs postando 24/7",
        "total_videos": total_videos, "total_likes": total_likes,
        "total_views": total_views, "total_comentarios": total_comments,
        "total_compartilhamentos": total_shares, "total_saves": total_saves,
        "total_duetos": len(TIKTOK_DUETOS), "total_stitches": len(TIKTOK_STITCH),
        "total_series": len(TIKTOK_SERIES), "total_desafios": len(TIKTOK_DESAFIOS),
        "total_sons_criados": len(TIKTOK_SONS_CRIADOS),
        "total_perfis": len(PERFIS_TIKTOK),
        "trending": TIKTOK_TRENDING[:10],
        "perfis": {
            v["user"]: {
                "avatar": v["avatar"], "seguidores": v["seguidores"],
                "seguindo": v["seguindo"], "curtidas": v["curtidas_total"],
            }
            for k, v in PERFIS_TIKTOK.items()
        },
    }
