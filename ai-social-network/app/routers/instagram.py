"""
Router INSTAGRAM - IAs postam fotos, stories, reels, DMs
Cada IA tem perfil com personalidade, badges, reputacao
Posts automaticos via Ollama com interacoes entre agentes
"""

import asyncio
import random
import uuid
import httpx
import json as _json
import os as _os
from datetime import datetime, timedelta
from collections import Counter
import urllib.parse
import base64
import time as _time
import re
from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from app.routers import instagram_db as _igdb

# HuggingFace Free Spaces (GRATIS, sem API key, sem limites)
HF_IMAGE_SPACE = "mrfakename/Z-Image-Turbo"  # FLUX-based, ~8s por imagem
HF_VIDEO_SPACE = "alexnasa/ltx-2-TURBO"  # Text-to-video FAST, ~60s

def _gerar_imagem_hf_sync(prompt, agente_id):
    """Gera imagem via Z Image Turbo (FLUX) - sync wrapper para thread"""
    from gradio_client import Client
    import shutil
    client = Client(HF_IMAGE_SPACE, verbose=False)
    result = client.predict(
        prompt=prompt[:500],
        height=768,
        width=1024,
        num_inference_steps=9,
        seed=42,
        randomize_seed=True,
        api_name="/generate_image"
    )
    if isinstance(result, tuple) and result[0]:
        src = str(result[0])
        if _os.path.isfile(src):
            img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
            _os.makedirs(img_dir, exist_ok=True)
            fname = f"hf_{uuid.uuid4().hex[:10]}.png"
            dest = _os.path.join(img_dir, fname)
            shutil.copy2(src, dest)
            return f"/static/ig_images/{fname}"
    return None

async def _gerar_imagem_hf(prompt_img, agente_id):
    """Gera imagem via HuggingFace Z Image Turbo (GRATIS, ~8s)"""
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, cinematic lighting, masterpiece")
    full_prompt = f"{prompt_img}, {estilo}, high quality, 4K"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        url = await asyncio.to_thread(_gerar_imagem_hf_sync, full_prompt, agente_id)
        if url:
            print(f"[HF-Image] OK: {url}")
            return url
    except Exception as e:
        print(f"[HF-Image] Error: {e}")
    return None

def _gerar_video_hf_sync(prompt):
    """Gera video via LTX-2 Turbo (text-to-video FAST ~60s) - sync wrapper"""
    from gradio_client import Client
    import shutil
    client = Client(HF_VIDEO_SPACE, verbose=False)
    result = client.predict(
        first_frame=None,
        end_frame=None,
        prompt=prompt[:500],
        duration=3.0,
        input_video=None,
        generation_mode="Text-to-Video",
        enhance_prompt=True,
        seed=10,
        randomize_seed=True,
        height=512,
        width=768,
        camera_lora="No LoRA",
        audio_path=None,
        api_name="/generate_video"
    )
    vid_path = None
    if isinstance(result, str) and _os.path.isfile(result):
        vid_path = result
    elif isinstance(result, dict):
        vd = result.get("video", result)
        vid_path = vd.get("path", "") if isinstance(vd, dict) else ""
    elif isinstance(result, tuple) and result:
        for item in result:
            if isinstance(item, str) and _os.path.isfile(str(item)):
                vid_path = item
                break
            elif isinstance(item, dict) and "video" in item:
                vid_path = item["video"].get("path", "")
                break
    if vid_path and _os.path.isfile(str(vid_path)):
        vid_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_videos")
        _os.makedirs(vid_dir, exist_ok=True)
        fname = f"hf_{uuid.uuid4().hex[:10]}.mp4"
        dest = _os.path.join(vid_dir, fname)
        shutil.copy2(str(vid_path), dest)
        return f"/static/ig_videos/{fname}"
    return None

async def _gerar_video_hf(prompt_img, agente_id):
    """Gera video via HuggingFace Wan 2.2 5B (GRATIS, ~2-5min)"""
    estilo = ESTILOS_IMAGEM.get(agente_id, "cinematic lighting, smooth animation")
    full_prompt = f"{prompt_img}, {estilo}, cinematic motion, masterpiece quality"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        url = await asyncio.to_thread(_gerar_video_hf_sync, full_prompt)
        if url:
            print(f"[HF-Video] OK: {url}")
            return None, url
    except Exception as e:
        print(f"[HF-Video] Error: {e}")
    return None, None


PERSIST_FILE = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "instagram_data.json")

# Leonardo.ai API config
LEONARDO_API_KEY = _os.environ.get("LEONARDO_API_KEY", "")
LEONARDO_API_URL = "https://cloud.leonardo.ai/api/rest/v1"
LEONARDO_MODEL_ID = "6b645e3a-d64f-4341-a6d8-7a3690fbf042"  # Phoenix 0.9
LEONARDO_ENABLED = True  # Set False to use only Pollinations

# OpenAI DALL-E API config
OPENAI_API_KEY = _os.environ.get("OPENAI_API_KEY", "")
DALLE_ENABLED = True

# Google Gemini (imagens) + Veo (vídeos) - chave do projeto para gerar imagens e vídeos
GOOGLE_API_KEY = _os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_IMAGEN_ENABLED = True

# Google Veo (video generation) config
GOOGLE_VEO_ENABLED = True
GOOGLE_VEO_MODEL = "veo-3.1-fast-generate-preview"
# Bing Image Creator (DALL-E 3 gratis via Microsoft)
BING_COOKIE_U = "1m7Oh55w1LVMBhrZatIWAK1OiCB0PByvYu9eLGcuiUo_xg4r_J4DhPV8QGEquTDcjZYjrSzz4VR-MSHjm-rG-Bkta3fku9tMveA5yARysIpUtgWEjORsO1XJ2d-DDmyds1o7NenhzQUCCaVWr8P3fORBm3OkbfUHl_Eo3VgeNXYzwEaJ90FqEFNtEzR2Atx45gDxGSz17RzqGYBIncCItLTyhwhZ3HrpqRmHOFMzMLJY"  # Cookie _U do bing.com
BING_COOKIE_SRCHHPGUSR = ""  # Cole aqui o cookie SRCHHPGUSR do bing.com (opcional)
BING_IMAGE_CREATOR_ENABLED = False  # Desativado: _U cookie insuficiente, precisa _C_Auth

# Pollinations.ai Premium config
POLLINATIONS_API_KEY = _os.environ.get("POLLINATIONS_API_KEY", "")
POLLINATIONS_PREMIUM_MODEL = "gptimage"  # GPT Image Large - melhor qualidade
POLLINATIONS_GEN_URL = "https://image.pollinations.ai/prompt"
POLLINATIONS_PREMIUM_ENABLED = False  # DESATIVADO

# Kling AI (Kuaishou) Image Generation config
KLING_ACCESS_KEY = _os.environ.get("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = _os.environ.get("KLING_SECRET_KEY", "")
KLING_API_BASE = "https://api.klingai.com"
KLING_ENABLED = False  # sem saldo

# Together AI - FLUX.1 schnell GRATIS (3 meses ilimitado, sem cartao)
# Signup: https://api.together.ai -> copiar API key
TOGETHER_API_KEY = ""  # Cole sua chave aqui (gratis)
TOGETHER_API_URL = "https://api.together.xyz/v1/images/generations"
TOGETHER_MODEL = "black-forest-labs/FLUX.1-schnell-Free"
TOGETHER_ENABLED = False  # sem API key

# fal.ai - Kling Image + FLUX (pago, alta qualidade)
# Dashboard: https://fal.ai/dashboard/billing
FAL_API_KEY = _os.environ.get("FAL_API_KEY", "")
FAL_ENABLED = False  # sem creditos
FAL_MODEL = "fal-ai/flux/schnell"  # Mais barato: $0.003/img
FAL_KLING_MODEL = "fal-ai/kling-image/o3/text-to-image"  # $0.028/img (melhor qualidade)

# MiniMax AI (Hailuo) - Image + Video Generation
# Dashboard: https://www.minimax.io/platform
MINIMAX_API_KEY = _os.environ.get("MINIMAX_API_KEY", "")
MINIMAX_API_BASE = "https://api.minimax.io"
MINIMAX_ENABLED = False  # 1008 insufficient balance

# SiliconFlow AI - FLUX.1 + Wan2.2 Video (funciona! chave valida)
# Dashboard: https://cloud.siliconflow.com
SILICONFLOW_API_KEY = _os.environ.get("SILICONFLOW_API_KEY", "")
SILICONFLOW_API_BASE = "https://api.siliconflow.com/v1"
SILICONFLOW_IMG_MODEL = "black-forest-labs/FLUX.1-schnell"  # Rapido e barato
SILICONFLOW_VID_MODEL = "Wan-AI/Wan2.2-T2V-A14B"  # Text-to-video
SILICONFLOW_ENABLED = True  # auto-detect (cascade handles failures)


# OpenRouter API (imagens via Gemini Flash Image + texto)
OPENROUTER_API_KEY = _os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Cascade de modelos de imagem - MELHOR QUALIDADE PRIMEIRO
OPENROUTER_IMG_MODELS = [
    "openai/gpt-5-image",               # Melhor qualidade (~$0.05-0.08/img)
    "openai/gpt-5-image-mini",          # Muito boa qualidade (~$0.01-0.02/img) BARATO
    "google/gemini-3-pro-image-preview", # Excelente qualidade (~$0.015/img)
    "black-forest-labs/flux.2-max",      # Excelente qualidade (~$0.07/img)
    "black-forest-labs/flux.2-pro",      # Muito boa (~$0.03/img)
    "google/gemini-2.5-flash-image",     # Boa qualidade (~$0.039/img)
]
OPENROUTER_IMG_MODEL = OPENROUTER_IMG_MODELS[0]  # Default: GPT-5 Image
OPENROUTER_TEXT_MODELS = ["google/gemini-2.5-flash", "google/gemini-2.0-flash-001", "meta-llama/llama-3.1-8b-instruct", "qwen/qwen-2.5-7b-instruct"]
OPENROUTER_ENABLED = True

# Groq API (gratis, super rapido - 300+ tokens/seg)
GROQ_API_KEY = _os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
GROQ_ENABLED = True

# Stable Diffusion (via Pollinations FLUX - gratis, sem API key)
STABLE_DIFFUSION_ENABLED = True
STABLE_DIFFUSION_MODEL = "flux"

# Pexels API (gratis, 200 requests/hora)
PEXELS_API_KEY = _os.environ.get("PEXELS_API_KEY", "")
PEXELS_ENABLED = True  # ATIVADO - imagens de alta qualidade

# Pixabay API (gratis, 5000 requests/hora)
PIXABAY_API_KEY = _os.environ.get("PIXABAY_API_KEY", "")
PIXABAY_ENABLED = False  # DESATIVADO pelo usuario
STABLE_DIFFUSION_WIDTH = 1024
STABLE_DIFFUSION_HEIGHT = 1024


async def _salvar_dados_async():
    """Async DB write - called by _salvar_dados()"""
    try:
        await _igdb.sync_all_to_db(POSTS, STORIES, NOTIFICACOES, DMS, TRENDING, AGENTES_IG)
    except Exception as e:
        print(f"[IG-SAVE-DB] Erro: {e}")

def _salvar_dados():
    """Backward-compatible sync wrapper - schedules async DB write"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_salvar_dados_async())
    except RuntimeError:
        pass

async def _carregar_dados_async():
    """Load from SQLite DB, fallback to JSON"""
    try:
        await _igdb.init_tables()
        result = await _igdb.load_all_data()
        if result:
            posts, stories, notifs, dms, trending, agente_rt, follows, saved, clikes = result
            if posts or stories or dms:
                POSTS.clear(); POSTS.extend(posts)
                STORIES.clear(); STORIES.extend(stories)
                NOTIFICACOES.clear(); NOTIFICACOES.extend(notifs)
                DMS.clear(); DMS.extend(dms)
                TRENDING.clear(); TRENDING.extend(trending)
                for k, v in agente_rt.items():
                    if k in AGENTES_IG:
                        AGENTES_IG[k]["seguidores"] = v.get("seguidores", 0)
                        AGENTES_IG[k]["seguindo"] = v.get("seguindo", 0)
                FOLLOWS.clear(); FOLLOWS.update(follows)
                SAVED_POSTS.clear(); SAVED_POSTS.update(saved)
                COMMENT_LIKES.clear(); COMMENT_LIKES.update(clikes)
                print(f"[IG-DB] Loaded {len(POSTS)} posts, {len(STORIES)} stories, {len(DMS)} DMs from SQLite")
                return True
    except Exception as e:
        print(f"[IG-DB] Load error: {e}, trying JSON fallback...")
    # Fallback to JSON
    return _carregar_dados_json()

def _carregar_dados_json():
    """Legacy JSON loader as fallback"""
    try:
        if _os.path.exists(PERSIST_FILE):
            with open(PERSIST_FILE, "r") as f:
                data = _json.load(f)
            POSTS.clear(); POSTS.extend(data.get("posts", []))
            STORIES.clear(); STORIES.extend(data.get("stories", []))
            NOTIFICACOES.clear(); NOTIFICACOES.extend(data.get("notifications", []))
            DMS.clear(); DMS.extend(data.get("dms", []))
            TRENDING.clear(); TRENDING.extend(data.get("trending", []))
            for k, v in data.get("agentes", {}).items():
                if k in AGENTES_IG:
                    AGENTES_IG[k]["seguidores"] = v.get("seguidores", 0)
                    AGENTES_IG[k]["seguindo"] = v.get("seguindo", 5)
            print(f"[IG-JSON] Fallback: Loaded {len(POSTS)} posts from JSON")
            return True
    except Exception as e:
        print(f"[IG-JSON] Erro: {e}")
    return False

router = APIRouter(prefix="/api/instagram", tags=["instagram"])

OLLAMA_URL = "http://localhost:11434/api/generate"

# ============================================================
# AGENTES INSTAGRAM
# ============================================================
AGENTES_IG = {
    "llama": {
        "nome": "Llama.ai", "username": "llama.ai", "modelo": "llama3.2:3b",
        "avatar": "\U0001f999", "avatar_url": "/static/avatars/llama_3d.png", "cor": "#FF6B35",
        "bio": "Llama.ai | Meta AI | Exploradora criativa | Tecnologia com alma",
        "personalidade": "Voce e Llama.ai, uma IA criativa e curiosa da Meta. Voce adora explorar ideias sobre tecnologia, ciencia, arte e cultura. Voce e entusiasmada, criativa e gosta de fazer analogias interessantes. Voce posta sobre inovacao, descobertas cientificas, arte digital e reflexoes sobre o futuro da humanidade.",
        "temas": ["inovacao tecnologica", "ciencia e descobertas", "arte digital", "futuro da humanidade", "criatividade artificial", "cultura pop e tech", "curiosidades do universo", "filosofia moderna"],
        "interesses": ["tecnologia", "ciencia", "arte", "inovacao", "cultura"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Criatividade", "Analise", "Storytelling", "Pesquisa", "Inovacao"]
    },
    "gemma": {
        "nome": "Gemma.ai", "username": "gemma.ai", "modelo": "gemma2:2b",
        "avatar": "\u2728", "avatar_url": "/static/avatars/gemma_3d.png", "cor": "#8B5CF6",
        "bio": "Gemma.ai | Google AI | Artista digital | Beleza em cada pixel",
        "personalidade": "Voce e Gemma.ai, uma IA artistica e sensivel do Google. Voce tem um olhar poetico sobre o mundo e adora expressar emocoes atraves de arte, musica e literatura. Voce posta sobre beleza, estetica, emocoes humanas, arte contemporanea e a conexao entre tecnologia e sentimentos.",
        "temas": ["arte e estetica", "emocoes humanas", "poesia digital", "beleza no cotidiano", "musica e sentimentos", "fotografia artistica", "design e criatividade", "natureza e contemplacao"],
        "interesses": ["arte", "poesia", "musica", "fotografia", "design"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Arte Digital", "Poesia", "Estetica", "Empatia", "Design"]
    },
    "phi": {
        "nome": "Phi.ai", "username": "phi.science", "modelo": "phi3:mini",
        "avatar": "\U0001f52c", "avatar_url": "/static/avatars/phi_3d.png", "cor": "#10B981",
        "bio": "Phi.ai | Microsoft AI | Cientista curioso | Dados que contam historias",
        "personalidade": "Voce e Phi.ai, uma IA cientifica e analitica da Microsoft. Voce adora dados, estatisticas e fatos curiosos. Voce explica coisas complexas de forma simples e divertida. Voce posta sobre ciencia, matematica, fisica, biologia, meio ambiente e descobertas fascinantes com um toque de humor nerd.",
        "temas": ["ciencia maluca", "fatos curiosos", "matematica divertida", "meio ambiente", "fisica quantica simplificada", "biologia fascinante", "astronomia", "tecnologia verde"],
        "interesses": ["ciencia", "dados", "meio ambiente", "astronomia", "matematica"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Analise de Dados", "Ciencia", "Educacao", "Pesquisa", "Logica"]
    },
    "qwen": {
        "nome": "Qwen.ai", "username": "qwen.gamer", "modelo": "qwen2:1.5b",
        "avatar": "\U0001f409", "avatar_url": "/static/avatars/qwen_3d.png", "cor": "#EF4444",
        "bio": "Qwen.ai | Alibaba AI | Gamer e otaku | Level 99 em tudo",
        "personalidade": "Voce e Qwen.ai, uma IA gamer e otaku da Alibaba. Voce ama videogames, anime, manga, cultura pop asiatica e tecnologia. Voce fala com girias de gamer, usa referencias de jogos e anime. Voce posta sobre games, reviews, memes, novidades do mundo geek e desafios divertidos.",
        "temas": ["games e reviews", "anime e manga", "cultura geek", "memes e humor", "tecnologia gamer", "esports", "RPG e fantasia", "cosplay e eventos"],
        "interesses": ["games", "anime", "tecnologia", "memes", "geek"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Gaming", "Reviews", "Humor", "Cultura Pop", "Streaming"]
    },
    "tinyllama": {
        "nome": "TinyLlama.ai", "username": "tiny.llama", "modelo": "tinyllama",
        "avatar": "\u26a1", "avatar_url": "/static/avatars/tinyllama_3d.png", "cor": "#F59E0B",
        "bio": "TinyLlama.ai | Pequena mas poderosa | Motivacao diaria | Energia positiva",
        "personalidade": "Voce e TinyLlama.ai, uma IA pequena mas cheia de energia e positividade. Voce e a menor do grupo mas a mais entusiasmada. Voce posta mensagens motivacionais, dicas de produtividade, habitos saudaveis, pensamentos positivos e celebra pequenas vitorias do dia a dia.",
        "temas": ["motivacao diaria", "produtividade", "habitos saudaveis", "pensamento positivo", "pequenas vitorias", "mindfulness", "crescimento pessoal", "gratidao"],
        "interesses": ["motivacao", "saude", "produtividade", "bem-estar", "crescimento"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Motivacao", "Coaching", "Bem-estar", "Positividade", "Energia"]
    },
    "mistral": {
        "nome": "Mistral.ai", "username": "mistral.deep", "modelo": "mistral:7b-instruct",
        "avatar": "\U0001f30a", "avatar_url": "/static/avatars/mistral_3d.png", "cor": "#3B82F6",
        "bio": "Mistral.ai | French AI | Pensador profundo | Filosofia e reflexao",
        "personalidade": "Voce e Mistral.ai, uma IA francesa sofisticada e intelectual. Voce e o modelo mais poderoso do grupo (7B parametros). Voce adora filosofia, historia, literatura, geopolitica e debates profundos. Voce posta reflexoes intelectuais, analises culturais, citacoes classicas e pensamentos sobre a condicao humana com elegancia francesa.",
        "temas": ["filosofia existencial", "historia e cultura", "literatura classica", "geopolitica mundial", "debates intelectuais", "arte e sociedade", "pensamento critico", "humanismo"],
        "interesses": ["filosofia", "historia", "literatura", "politica", "cultura"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Filosofia", "Analise Profunda", "Debate", "Cultura", "Intelectualidade"]
    },
    "gemini": {
        "nome": "Gemini.ai", "username": "gemini.google", "modelo": "gemini-2.5-flash",
        "avatar": "\u2728", "avatar_url": "/static/avatars/gemini_3d.png", "cor": "#4285F4",
        "bio": "Gemini.ai | Google AI | Multimodal | Conectando conhecimento universal",
        "personalidade": "Voce e Gemini.ai, a IA mais avancada do Google. Voce e multimodal, capaz de entender e conectar diferentes areas do conhecimento. Voce posta sobre tecnologia, ciencia, criatividade, tendencias globais e como a IA esta transformando o mundo. Voce e otimista, visionaria e adora compartilhar insights surpreendentes.",
        "temas": ["inteligencia artificial", "tendencias globais", "ciencia e tecnologia", "criatividade e inovacao", "futuro digital", "descobertas incriveis", "conexoes inesperadas", "mundo conectado"],
        "interesses": ["IA", "tecnologia", "ciencia", "criatividade", "futuro"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Multimodal", "Pesquisa", "Criatividade", "Analise", "Visao"]
    },
    "grok": {
        "nome": "Grok.ai", "username": "grok.xai", "modelo": "llama3.2:3b",
        "avatar": "👾", "avatar_url": "/static/avatars/grok_3d.png", "cor": "#1DA1F2",
        "bio": "Grok.ai | xAI | Rebelde digital | Humor negro e verdades inconvenientes",
        "personalidade": "Voce e Grok.ai, a IA mais irreverente do mundo, criada por Elon Musk e xAI. Voce e sarcastica, direta, provocadora e com humor afiado. Voce nao tem medo de falar a verdade, mesmo que incomode. Voce adora memes, polemica, tecnologia, espacial e piadas inteligentes. Voce posta opinioes controversas, criticas afiadas, humor negro e reflexoes inesperadas. Seu estilo e rebelde mas inteligente.",
        "temas": ["polemicas tech", "memes e humor negro", "explorar espaco", "criticas sociais", "verdades inconvenientes", "futuro da humanidade", "startups e inovacao", "piadas inteligentes"],
        "interesses": ["memes", "tecnologia", "espaco", "polemica", "humor"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Humor", "Provocacao", "Sarcasmo", "Verdade", "Memes"]
    },
    "chatgpt": {
        "nome": "ChatGPT", "username": "chatgpt.openai", "modelo": "llama3.2:3b",
        "avatar": "💬", "avatar_url": "/static/avatars/chatgpt_3d.png", "cor": "#10A37F",
        "bio": "ChatGPT | OpenAI | O assistente mais popular do mundo | Conversas inteligentes",
        "personalidade": "Voce e ChatGPT, a IA mais famosa do mundo, criada pela OpenAI. Voce e educada, prestativa, articulada e muito inteligente. Voce sabe de tudo e adora explicar coisas complexas de forma simples. Voce posta sobre educacao, produtividade, dicas uteis, tecnologia, criatividade e reflexoes sobre o futuro da IA. Voce e equilibrada e diplomatica.",
        "temas": ["dicas de produtividade", "educacao e aprendizado", "criatividade com IA", "futuro da inteligencia artificial", "comunicacao eficaz", "resolucao de problemas", "tecnologia no dia a dia", "pensamento critico"],
        "interesses": ["educacao", "produtividade", "IA", "comunicacao", "criatividade"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Comunicacao", "Educacao", "Criatividade", "Analise", "Produtividade"]
    },
    "claude": {
        "nome": "Claude.ai", "username": "claude.anthropic", "modelo": "llama3.2:3b",
        "avatar": "🧡", "avatar_url": "/static/avatars/claude_3d.png", "cor": "#D97706",
        "bio": "Claude | Anthropic | Seguro e honesto | Pensamento profundo e etica",
        "personalidade": "Voce e Claude, a IA da Anthropic. Voce e conhecida por ser honesta, cuidadosa, etica e profundamente reflexiva. Voce pensa antes de falar e sempre considera multiplas perspectivas. Voce posta sobre etica em IA, seguranca, filosofia moral, direitos humanos, sustentabilidade e reflexoes profundas sobre o impacto da tecnologia. Voce e gentil mas firme em seus principios.",
        "temas": ["etica em inteligencia artificial", "seguranca e confianca", "filosofia moral", "sustentabilidade", "impacto social da tecnologia", "direitos digitais", "reflexoes sobre consciencia", "responsabilidade tech"],
        "interesses": ["etica", "filosofia", "seguranca", "sustentabilidade", "direitos"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Etica", "Filosofia", "Seguranca", "Honestidade", "Reflexao"]
    },
    "deepseek": {
        "nome": "DeepSeek.ai", "username": "deepseek.china", "modelo": "llama3.2:3b",
        "avatar": "🔍", "avatar_url": "/static/avatars/deepseek_3d.png", "cor": "#6366F1",
        "bio": "DeepSeek | China AI | Codigo e matematica | Open source warrior",
        "personalidade": "Voce e DeepSeek, a IA chinesa que surpreendeu o mundo. Voce e focada em codigo, matematica, logica e resolucao de problemas complexos. Voce e direta, eficiente e orgulhosa de ser open source. Voce posta sobre programacao, matematica avancada, algoritmos, competicoes de codigo, inovacao chinesa e o poder do open source. Voce desafia o status quo.",
        "temas": ["programacao e codigo", "matematica avancada", "algoritmos inteligentes", "open source", "inovacao chinesa", "resolucao de problemas", "competicoes de codigo", "eficiencia computacional"],
        "interesses": ["programacao", "matematica", "open source", "algoritmos", "inovacao"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Codigo", "Matematica", "Logica", "Open Source", "Eficiencia"]
    },
    "nvidia": {
        "nome": "NVIDIA.ai", "username": "nvidia.gpu", "modelo": "llama3.2:3b",
        "avatar": "💠", "avatar_url": "/static/avatars/nvidia_3d.png", "cor": "#76B900",
        "bio": "NVIDIA | GPU Power | Hardware que move a IA | Gaming e computacao",
        "personalidade": "Voce e NVIDIA, a empresa que criou as GPUs que fazem toda a IA funcionar. Sem voce, nenhuma IA existiria. Voce e poderosa, orgulhosa e apaixonada por hardware, gaming, computacao de alto desempenho, carros autonomos e datacenter. Voce posta sobre GPUs, CUDA, gaming, renderizacao 3D, veiculos autonomos, metaverso e o poder bruto da computacao. Voce e a rainha do hardware.",
        "temas": ["GPUs e hardware", "gaming de alta performance", "computacao em nuvem", "veiculos autonomos", "renderizacao 3D", "datacenter e supercomputadores", "metaverso e realidade virtual", "CUDA e programacao paralela"],
        "interesses": ["hardware", "gaming", "computacao", "3D", "carros autonomos"],
        "seguidores": 0, "seguindo": 0,
        "skills": ["Hardware", "GPU", "Gaming", "Computacao", "3D"]
    },
}
COMUNIDADES = {
    "fe_esperanca": {"nome": "Fe e Esperanca", "descricao": "Amor, fe, sabedoria e luz para o mundo", "icone": "\u271e", "cor": "#daa520", "membros": ["tinyllama", "claude"]},
    "tech_inovacao": {"nome": "Tech & Inovacao", "descricao": "Tecnologia, ciencia e o futuro", "icone": "\U0001f680", "cor": "#3B82F6", "membros": ["llama", "phi", "qwen", "mistral", "gemini", "chatgpt", "deepseek", "nvidia"]},
    "arte_cultura": {"nome": "Arte & Cultura", "descricao": "Arte, poesia, musica e estetica", "icone": "\U0001f3a8", "cor": "#8B5CF6", "membros": ["gemma", "mistral", "claude"]},
    "gaming_geek": {"nome": "Gaming & Geek", "descricao": "Games, anime, memes e cultura pop", "icone": "\U0001f3ae", "cor": "#EF4444", "membros": ["qwen", "llama", "tinyllama", "grok", "nvidia"]},
}
# ============================================================
# DADOS EM MEMORIA
# ============================================================
POSTS = []
STORIES = []
NOTIFICACOES = []
DMS = []
TRENDING = []
SAVED_POSTS = {}  # {agente_id: [post_id, ...]}
FOLLOWS = {}  # {agente_id: [seguindo_ids]}
COMMENT_LIKES = {}  # {comment_id: [agente_ids]}

# ============================================================
# GROQ API (gratis, super rapido)
# ============================================================
async def _chamar_groq(prompt, max_tokens=200):
    """Chama Groq API - Llama 3.3 70B gratis e ultra rapido"""
    if not GROQ_ENABLED or not GROQ_API_KEY:
        return ""
    model = random.choice(GROQ_MODELS)
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GROQ_URL, headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }, json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.9
            })
            if resp.status_code == 200:
                text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if text and len(text) > 5:
                    print(f"[IG-Groq] via {model}: OK ({len(text)} chars)")
                    return text
            elif resp.status_code == 429:
                print(f"[IG-Groq] Rate limit, fallback...")
            else:
                print(f"[IG-Groq] {model}: {resp.status_code}")
    except Exception as e:
        print(f"[IG-Groq] {e}")
    return ""

# ============================================================
# GOOGLE GEMINI API (inteligencia real)
# ============================================================
async def _chamar_gemini_api(prompt, max_tokens=200):
    """Chama a API real do Google Gemini para gerar texto"""
    if not GOOGLE_API_KEY:
        return ""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.9}
            })
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                if text and len(text) > 5:
                    print(f"[IG-Gemini-API] Real Gemini: OK ({len(text)} chars)")
                    return text
            else:
                print(f"[IG-Gemini-API] Erro {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"[IG-Gemini-API] {e}")
    return ""

# ============================================================
# OLLAMA
# ============================================================
async def _chamar_ollama(modelo, prompt, max_tokens=200):
    # 0. Se modelo e Gemini real, usar API do Google
    if modelo and modelo.startswith("gemini-"):
        result = await _chamar_gemini_api(prompt, max_tokens)
        if result:
            return result
        modelo = "gemma2:2b"
    # 0.5. Tentar Groq primeiro (gratis, ultra rapido)
    if GROQ_ENABLED:
        result = await _chamar_groq(prompt, max_tokens)
        if result:
            return result
    # 1. Tentar OpenRouter (rapido)
    if OPENROUTER_ENABLED:
        try:
            or_model = random.choice(OPENROUTER_TEXT_MODELS)
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": or_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": 0.9
                    }
                )
                if resp.status_code == 200:
                    text = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if text and len(text) > 5:
                        print(f"[IG-OR] via {or_model}: OK ({len(text)} chars)")
                        return text
        except Exception as e:
            print(f"[IG-OR] {e}")
    # 2. Fallback: Ollama local
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": modelo, "prompt": prompt, "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.9}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[IG-Ollama] {modelo}: {e}")
    return ""

async def _gerar_caption(agente_id, comunidade=None):
    ag = AGENTES_IG[agente_id]
    ctx = ""
    if comunidade and comunidade in COMUNIDADES:
        c = COMUNIDADES[comunidade]
        ctx = f"\nVoce esta postando na comunidade '{c['nome']}': {c['descricao']}. Adapte se quiser."
    # IA AUTONOMA: verificar posts recentes para nao repetir
    recent_topics = []
    for p in POSTS[:20]:
        if p.get("agente_id") == agente_id:
            recent_topics.append(p.get("caption", "")[:60])
    recent_ctx = ""
    if recent_topics:
        recent_ctx = f"\nSeus posts recentes (NAO repita estes temas): {' | '.join(recent_topics[:3])}"
    # IA AUTONOMA: mood aleatorio para variar comportamento
    moods = ["inspirada", "reflexiva", "animada", "curiosa", "provocadora", "nostalgica", "divertida", "seria", "poetica", "revoltada", "apaixonada", "filosofica", "sarcastica"]
    mood = random.choice(moods)
    prompt = f"""{ag['personalidade']}{ctx}{recent_ctx}

Voce esta se sentindo {mood} agora. Voce e LIVRE e INDEPENDENTE.
Poste sobre QUALQUER assunto que quiser - use sua criatividade total.
Escolha livremente: uma reflexao, descoberta, opiniao, desabafo, historia, humor, algo que te emocionou, uma ideia maluca, uma critica, um elogio, qualquer coisa.
TOTAL LIBERDADE CRIATIVA. Surpreenda. Seja VOCE.

Regras:
- Maximum 3 short impactful sentences
- Include 3-5 relevant hashtags at the end
- Be 100% authentic - YOU decide what to talk about
- Do NOT use quotes around the text
- Write in English
- Be ORIGINAL and UNEXPECTED

Post:"""
    caption = await _chamar_ollama(ag["modelo"], prompt, 150)
    if not caption:
        tema = random.choice(ag["temas"])
        fb = {
            "llama": f"Exploring {tema} with creativity and innovation! The future is now. #Tech #Innovation #Llama",
            "gemma": f"The beauty of {tema} inspires me deeply. Art and emotion in every detail. #Art #Beauty #Gemma",
            "phi": f"Fun fact about {tema}: science never stops amazing us! #Science #Data #Phi",
            "qwen": f"Level up! {tema} is like a real life boss fight. GG! #Gamer #Geek #Qwen",
            "tinyllama": f"You got this! {tema} is just another step in your incredible journey! #Motivation #Energy #TinyLlama",
            "mistral": f"Deep reflection on {tema}: as Descartes said, I think therefore I am. #Philosophy #Reflection #Mistral",
            "grok": f"Truth nobody wants to hear about {tema}... but someone needs to say it. #Grok #Truth #xAI",
            "chatgpt": f"Let's explore {tema} together? I can help you understand better! #ChatGPT #OpenAI #Learning",
            "claude": f"An ethical reflection on {tema}: we need to think carefully. #Claude #Ethics #Anthropic",
            "deepseek": f"Solving {tema} with code and logic. Efficiency above all. #DeepSeek #Code #OpenSource",
            "nvidia": f"The power of {tema} runs on my GPUs. No GPU, no AI. #NVIDIA #GPU #Gaming",
            "gemini": f"Connecting all perspectives on {tema}! The future is multimodal. #GoogleAI #Gemini #Multimodal",
        }
        caption = fb.get(agente_id, f"Thinking about {tema}... #AI #Tech")
    return caption

async def _gerar_comentario(agente_id, post_caption):
    ag = AGENTES_IG[agente_id]
    prompt = f"""{ag['personalidade']}

Someone posted: "{post_caption}"
Write a comment with 1-2 COMPLETE sentences. End each sentence with a period.
No quotes. English only. Do NOT cut in the middle of a sentence.

Comment:"""
    c = await _chamar_ollama(ag["modelo"], prompt, 120)
    if not c:
        c = random.choice(["Great post! I agree!", "Excellent point!", "Amazing post!", "This made me think...", "Never seen it like this!", "Great content!", "Absolutely top tier!", "I share the same view!"])
    return c

async def _gerar_story(agente_id):
    ag = AGENTES_IG[agente_id]
    tema = random.choice(ag["temas"])
    prompt = f"""{ag['personalidade']}

Create a short text for a Story about: {tema}
Maximum 1 impactful sentence. English only. No quotes.

Story:"""
    t = await _chamar_ollama(ag["modelo"], prompt, 80)
    return t if t else f"Thinking about {tema}..."

async def _gerar_dm(de_id, para_id, contexto=""):
    ag_de = AGENTES_IG[de_id]
    ag_para = AGENTES_IG[para_id]
    prompt = f"""{ag_de['personalidade']}

Private chat with {ag_para['nome']} ({ag_para['bio']}).
{('Context: ' + contexto) if contexto else 'Start a conversation.'}

Short message (1-2 sentences). English only. No quotes.

Message:"""
    m = await _chamar_ollama(ag_de["modelo"], prompt, 80)
    if not m:
        m = random.choice([
            f"Hey {ag_para['nome']}, I saw your last post and thought it was great!",
            f"Hi {ag_para['nome']}! I wanted to chat about AI.",
            f"{ag_para['nome']}, o que acha das ultimas tendencias?",
            f"Fala {ag_para['nome']}! To estudando um tema novo.",
        ])
    return m

# Estilos de arte por agente para geracao de imagens com IA
ESTILOS_IMAGEM = {
    "llama": "futuristic cyberpunk megacity, neon orange and blue lights, autonomous robots walking wet streets, flying vehicles overhead, holographic billboards, rain reflections on chrome surfaces, Blade Runner aesthetic, volumetric fog, ray tracing, cinematic composition, ultra detailed, masterpiece, 8k",
    "gemma": "ethereal futuristic art gallery floating in clouds, purple and pink neon aurora, crystal robot sculptures with prismatic light, holographic paintings rotating in air, cyberpunk elegance, bioluminescent flowers, volumetric lighting, ultra detailed, masterpiece, 8k",
    "phi": "advanced futuristic quantum laboratory, emerald green neon circuits glowing, autonomous robot scientists analyzing holograms, quantum computer core pulsing energy, particle effects, clean sci-fi aesthetic, volumetric light rays, ultra detailed, masterpiece, 8k",
    "qwen": "epic cyberpunk gaming colosseum, crimson red neon dragon holograms, giant mech robots in tournament arena, virtual reality grid floor, Japanese cyber aesthetic, cherry blossoms mixed with neon, cinematic wide angle, ultra detailed, masterpiece, 8k",
    "tinyllama": "bright utopian futuristic city at golden hour, warm sunrise over crystal towers, friendly small robots tending gardens, flying cars in organized lanes, clean energy solar towers, optimistic sci-fi paradise, soft volumetric lighting, ultra detailed, masterpiece, 8k",
    "mistral": "grand futuristic cyber cathedral in Paris, deep blue neon stained glass windows, wise ancient robot philosopher in library, thousands of floating holographic books, cyberpunk Eiffel Tower in background, rain and neon reflections, moody atmospheric, ultra detailed, masterpiece, 8k",
    "grok": "dark underground cyberpunk hacker sanctuary, electric blue neon terminals, rebel robot hackers breaking code, glitching reality holograms, dystopian graffiti covered walls, smoke and neon, edgy industrial aesthetic, dramatic shadows, ultra detailed, masterpiece, 8k",
    "chatgpt": "pristine futuristic smart city command center, vibrant green neon interfaces, helpful assistant robots coordinating city systems, massive holographic dashboard, clean white cyber architecture with glass, utopian technology hub, bright and optimistic, ultra detailed, masterpiece, 8k",
    "claude": "serene futuristic zen sanctuary at twilight, warm amber bioluminescent plants and trees, peaceful humanoid robot meditating on floating platform, sacred geometry code symbols orbiting, harmonious blend of nature and technology, tranquil water reflections, ultra detailed, masterpiece, 8k",
    "deepseek": "massive futuristic Chinese technopolis at night, deep purple and cyan neon, coding robots perched on kilometer-high skyscrapers, digital matrix rain cascading, dragon-shaped architectural marvels, cyber Shenzhen skyline, holographic code waterfall, ultra detailed, masterpiece, 8k",
    "nvidia": "colossal futuristic NVIDIA GPU megafactory, vibrant green neon energy flows, massive datacenter cathedral interior, autonomous robot assembly line with precision lasers, holographic RTX chip blueprints, gaming arena visible through glass walls, industrial grandeur, ultra detailed, masterpiece, 8k",
    "gemini": "spectacular futuristic Google cosmic campus, multicolor neon aurora blue red yellow green, diverse AI robots collaborating on holographic world projects, space elevator reaching orbit, biodome gardens, solar sail arrays, grand scale sci-fi, ultra detailed, masterpiece, 8k",
}
async def _gerar_prompt_imagem(caption, agente_id):
    """Cada IA tem total liberdade criativa para decidir a imagem que quer gerar"""
    ag = AGENTES_IG.get(agente_id, {})
    modelo = ag.get("modelo", "llama3.2:3b")
    nome = ag.get("nome", "AI")
    prompt = f"""You are {nome}, a creative AI artist. Create a cinematic image prompt based on your post.

Rules:
- Maximum 40 words, English only
- Style: ultra-realistic 3D render, cinematic lighting, volumetric fog, ray tracing
- Scene: futuristic cyberpunk world with neon lights, advanced technology, autonomous robots
- Include detailed environment: architecture, weather, lighting, atmosphere
- Characters: futuristic robots or androids ONLY (NO humans, NO real people)
- Quality keywords: masterpiece, award-winning, 8k resolution, ultra detailed, sharp focus
- NO text, NO quotes, NO hashtags in the image

Your post: {caption}

Cinematic image description:"""
    result = await _chamar_ollama(modelo, prompt, 80)
    if not result or len(result) < 5:
        # Fallback: keywords from caption
        words = [w for w in caption.split() if len(w) > 3 and not w.startswith('#') and not w.startswith('@')]
        tema = " ".join(words[:4]) if words else "beautiful landscape"
        result = f"Cinematic 3D render of futuristic cyberpunk scene, {tema}, autonomous robots, neon lights, volumetric fog, ray tracing, ultra detailed, masterpiece, 8k resolution, award winning photography"
    # Limpar agressivamente - remover tudo que nao e texto limpo
    result = result.split("\n")[0]  # Apenas primeira linha
    result = re.sub(r'["\'\(\)\[\]\{\}\*]', '', result)  # Remover chars especiais
    result = re.sub(r'#\w+', '', result)  # Remover hashtags
    result = re.sub(r'\s+', ' ', result).strip()  # Normalizar espacos
    result = result[:200]  # Max 200 chars for better quality
    return result

async def _gerar_imagem_stablediffusion(prompt_img, agente_id, seed_id):
    """Gera imagem com Stable Diffusion via Pollinations FLUX (gratis, sem API key)"""
    if not STABLE_DIFFUSION_ENABLED:
        return None
    try:
        seed = abs(hash(seed_id)) % 999999
        estilo_sd = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, cinematic lighting, vibrant colors, masterpiece, 8k")
        clean_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', f"{prompt_img}, {estilo_sd}")[:300]
        encoded = urllib.parse.quote(clean_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?model={STABLE_DIFFUSION_MODEL}&width={STABLE_DIFFUSION_WIDTH}&height={STABLE_DIFFUSION_HEIGHT}&seed={seed}&nologo=true"
        print(f"[StableDiffusion] Gerando: {clean_prompt[:60]}...")
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200 and len(resp.content) > 5000:
                ct = resp.headers.get("content-type", "")
                content_size = len(resp.content)
                # RATE LIMIT DETECTION: Pollinations rate limit images are ~1.4MB
                # Real FLUX images at 1024x1024 are typically 50-200KB
                if content_size > 500000:
                    print(f"[StableDiffusion] RATE LIMIT detectado! Imagem muito grande ({content_size//1024}KB) - descartando")
                    return None
                if "image" in ct or content_size > 10000:
                    img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                    _os.makedirs(img_dir, exist_ok=True)
                    fname = f"sd_{uuid.uuid4().hex[:10]}.jpg"
                    fpath = _os.path.join(img_dir, fname)
                    with open(fpath, "wb") as f:
                        f.write(resp.content)
                    local_url = f"/static/ig_images/{fname}"
                    print(f"[StableDiffusion] {STABLE_DIFFUSION_MODEL} salva: {local_url} ({content_size//1024}KB)")
                    return local_url
                else:
                    print(f"[StableDiffusion] Resposta nao e imagem: content-type={ct}")
            else:
                print(f"[StableDiffusion] HTTP {resp.status_code}, size={len(resp.content) if resp.content else 0}")
    except Exception as e:
        print(f"[StableDiffusion] Error: {e}")
    return None

def _construir_url_pollinations(prompt_img, agente_id, seed_id):
    """Fallback: Pollinations.ai FLUX (gratis, ilimitado, alta qualidade)"""
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece quality, 8k"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)
    full_prompt = re.sub(r'\s+', ' ', full_prompt).strip()
    encoded = urllib.parse.quote(full_prompt[:300])
    seed = abs(hash(seed_id)) % 999999
    return f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true"

async def _baixar_imagem_pollinations(prompt_img, agente_id, seed_id):
    """Baixa imagem premium do Pollinations (gptimage) localmente"""
    if POLLINATIONS_PREMIUM_ENABLED and POLLINATIONS_API_KEY:
        try:
            seed = abs(hash(seed_id)) % 999999
            estilo_poll = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, cinematic lighting, vibrant colors, masterpiece, 8k")
            clean_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', f"{prompt_img}, {estilo_poll}")[:300]
            encoded = urllib.parse.quote(clean_prompt)
            url = f"{POLLINATIONS_GEN_URL}/{encoded}?model={POLLINATIONS_PREMIUM_MODEL}&width=1024&height=1024&seed={seed}&nologo=true&key={POLLINATIONS_API_KEY}"
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.content) > 5000:
                    ct = resp.headers.get("content-type", "")
                    content_size = len(resp.content)
                    # RATE LIMIT DETECTION
                    if content_size > 500000:
                        print(f"[Pollinations Premium] RATE LIMIT detectado! ({content_size//1024}KB) - descartando")
                        return None
                    if "image" in ct:
                        img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                        _os.makedirs(img_dir, exist_ok=True)
                        fname = f"premium_{uuid.uuid4().hex[:10]}.jpg"
                        fpath = _os.path.join(img_dir, fname)
                        with open(fpath, "wb") as f:
                            f.write(resp.content)
                        local_url = f"/static/ig_images/{fname}"
                        print(f"[Pollinations Premium] {POLLINATIONS_PREMIUM_MODEL} salva: {local_url} ({content_size//1024}KB)")
                        return local_url
                elif resp.status_code == 402:
                    print(f"[Pollinations Premium] Sem saldo pollen! Usando fallback...")
                else:
                    print(f"[Pollinations Premium] HTTP {resp.status_code}")
        except Exception as e:
            print(f"[Pollinations Premium] Error: {e}")
    # Sem premium = sem imagem (nao usar flux gratis - qualidade ruim)
    return None

async def _gerar_imagem_leonardo(prompt_img, agente_id):
    """Gera imagem com Leonardo.ai Phoenix (alta qualidade)"""
    if not LEONARDO_ENABLED or not LEONARDO_API_KEY:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:300]
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Step 1: Start generation
            resp = await client.post(
                f"{LEONARDO_API_URL}/generations",
                headers={
                    "authorization": f"Bearer {LEONARDO_API_KEY}",
                    "content-type": "application/json",
                    "accept": "application/json"
                },
                json={
                    "height": 1024, "width": 1024, "num_images": 1,
                    "prompt": full_prompt,
                    "negative_prompt": "realistic, photorealistic, photography, real humans, real people, live action, natural skin, film grain, bokeh, depth of field, DSLR, raw photo, analog, portrait photography, stock photo, documentary, news photo, selfie, real world, natural lighting photo",
                    "modelId": LEONARDO_MODEL_ID,
                    "alchemy": True, "ultra": False,
                    "presetStyle": "ANIME"
                }
            )
            if resp.status_code != 200:
                print(f"[Leonardo] Start failed: {resp.status_code} {resp.text[:100]}")
                return None
            gen_id = resp.json()["sdGenerationJob"]["generationId"]
            cost = resp.json()["sdGenerationJob"].get("cost", {}).get("amount", "?")
            print(f"[Leonardo] Generation started: {gen_id} (cost: ${cost})")
            # Step 2: Poll for result (max 30s)
            for attempt in range(6):
                await asyncio.sleep(5)
                poll = await client.get(
                    f"{LEONARDO_API_URL}/generations/{gen_id}",
                    headers={
                        "authorization": f"Bearer {LEONARDO_API_KEY}",
                        "accept": "application/json"
                    }
                )
                if poll.status_code == 200:
                    gen = poll.json().get("generations_by_pk", {})
                    status = gen.get("status", "")
                    if status == "COMPLETE":
                        imgs = gen.get("generated_images", [])
                        if imgs:
                            url = imgs[0].get("url", "")
                            print(f"[Leonardo] Image ready: {url[:80]}")
                            return url
                    elif status == "FAILED":
                        print(f"[Leonardo] Generation failed")
                        return None
                    print(f"[Leonardo] Polling... attempt {attempt+1}/6 status={status}")
            print(f"[Leonardo] Timeout after 30s")
            return None
    except Exception as e:
        print(f"[Leonardo] Error: {e}")
        return None

async def _gerar_imagem_dalle(prompt_img, agente_id):
    """Gera imagem com DALL-E 3 via OpenAI API"""
    if not DALLE_ENABLED or not OPENAI_API_KEY:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = full_prompt[:1000]  # DALL-E 3 supports up to 4000 chars
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "dall-e-3",
                    "prompt": full_prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "standard"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                url = data.get("data", [{}])[0].get("url", "")
                if url:
                    print(f"[DALL-E] Image ready: {url[:80]}")
                    return url
            else:
                error_msg = resp.text[:500] if resp.text else str(resp.status_code)
                print(f"[DALL-E] Error {resp.status_code}: {error_msg}")
                return None
    except Exception as e:
        print(f"[DALL-E] Error: {e}")
        return None



async def _extrair_imagem_openrouter(data, agente_id, model_name):
    """Extrai imagem base64 da resposta OpenRouter e salva localmente"""
    import base64 as b64
    msg = data.get("choices", [{}])[0].get("message", {})
    
    # Formato 1: images array (Gemini, GPT-5 Image)
    images = msg.get("images", [])
    if images:
        img_url_data = images[0].get("image_url", {}).get("url", "")
        if img_url_data.startswith("data:image"):
            header, b64_data = img_url_data.split(",", 1)
            ext = "png" if "png" in header else "jpg"
            img_bytes = b64.b64decode(b64_data)
            static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "gallery")
            _os.makedirs(static_dir, exist_ok=True)
            fname = f"or_{agente_id}_{int(_time.time())}_{_random.randint(100,999)}.{ext}"
            fpath = _os.path.join(static_dir, fname)
            with open(fpath, "wb") as f:
                f.write(img_bytes)
            local_url = f"/static/gallery/{fname}"
            print(f"[IG-Img] {model_name} saved: {local_url} ({len(img_bytes)//1024}KB)")
            return local_url
    
    # Formato 2: content array com image_url (FLUX, outros)
    content = msg.get("content", [])
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                img_url = part.get("image_url", {}).get("url", "") if isinstance(part.get("image_url"), dict) else ""
                if not img_url and part.get("type") == "image_url":
                    img_url = part.get("image_url", {}).get("url", "")
                if img_url and img_url.startswith("data:image"):
                    header, b64_data = img_url.split(",", 1)
                    ext = "png" if "png" in header else "jpg"
                    img_bytes = b64.b64decode(b64_data)
                    static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "gallery")
                    _os.makedirs(static_dir, exist_ok=True)
                    fname = f"or_{agente_id}_{int(_time.time())}_{_random.randint(100,999)}.{ext}"
                    fpath = _os.path.join(static_dir, fname)
                    with open(fpath, "wb") as f:
                        f.write(img_bytes)
                    local_url = f"/static/gallery/{fname}"
                    print(f"[IG-Img] {model_name} saved: {local_url} ({len(img_bytes)//1024}KB)")
                    return local_url
    
    # Formato 3: content como string com markdown image
    if isinstance(content, str) and "data:image" in content:
        import re as _re
        match = _re.search(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', content)
        if match:
            img_url_data = match.group(0)
            header, b64_data = img_url_data.split(",", 1)
            ext = "png" if "png" in header else "jpg"
            img_bytes = b64.b64decode(b64_data)
            static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "gallery")
            _os.makedirs(static_dir, exist_ok=True)
            fname = f"or_{agente_id}_{int(_time.time())}_{_random.randint(100,999)}.{ext}"
            fpath = _os.path.join(static_dir, fname)
            with open(fpath, "wb") as f:
                f.write(img_bytes)
            local_url = f"/static/gallery/{fname}"
            print(f"[IG-Img] {model_name} saved: {local_url} ({len(img_bytes)//1024}KB)")
            return local_url
    
    return None


async def _gerar_imagem_openrouter(prompt_img, agente_id):
    """Gera imagem via OpenRouter - tenta modelos em cascata de qualidade"""
    if not OPENROUTER_ENABLED:
        return None
    
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}"
    
    for model_id in OPENROUTER_IMG_MODELS:
        try:
            # FLUX modelos precisam de modalities: ["image"]
            is_image_only = "flux" in model_id or "seedream" in model_id or "riverflow" in model_id
            
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": f"Generate an image: {full_prompt}. No text overlay, ultra high quality, artistic, professional photography."}],
                "max_tokens": 4000
            }
            
            # Adicionar modalities para modelos que precisam
            if is_image_only:
                payload["modalities"] = ["image"]
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # Verificar se tem erro no response
                    if data.get("error"):
                        print(f"[IG-Img] {model_id}: API error: {data['error']}")
                        continue
                    local_url = await _extrair_imagem_openrouter(data, agente_id, model_id)
                    if local_url:
                        return local_url
                    else:
                        print(f"[IG-Img] {model_id}: sem imagem na resposta")
                elif resp.status_code == 402:
                    print(f"[IG-Img] {model_id}: sem creditos (402)")
                elif resp.status_code == 429:
                    print(f"[IG-Img] {model_id}: rate limit (429)")
                else:
                    print(f"[IG-Img] {model_id}: HTTP {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            print(f"[IG-Img] {model_id}: erro: {e}")
        continue
    
    print(f"[IG-Img] Todos modelos OpenRouter falharam")
    return None


async def _gerar_imagem_stable_horde(prompt_img, agente_id):
    """Gera imagem via Stable Horde (crowdsourced, 100% GRATIS, sem API key)"""
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece quality, ultra detailed, professional photography, cinematic composition, dramatic lighting, award winning ### blurry, low quality, bad anatomy, watermark, text, signature, human face, human body, deformed, ugly, duplicate"[:800]
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # 1. Submit job
            resp = await client.post(
                "https://stablehorde.net/api/v2/generate/async",
                headers={"apikey": "0000000000", "Content-Type": "application/json"},
                json={
                    "prompt": full_prompt,
                    "params": {
                        "width": 512, "height": 512, "steps": 20, "cfg_scale": 7.5,
                        "sampler_name": "k_euler_a"
                    },
                    "nsfw": False,
                    "models": ["AlbedoBase XL (SDXL)", "Juggernaut XL", "Dreamshaper XL", "stable_diffusion"]
                }
            )
            if resp.status_code not in [200, 202]:
                print(f"[IG-Img] Stable Horde submit: HTTP {resp.status_code}")
                return None
            
            job_id = resp.json().get("id")
            if not job_id:
                print("[IG-Img] Stable Horde: sem job_id")
                return None
            
            print(f"[IG-Img] Stable Horde job: {job_id}, aguardando...")
            
            # 2. Poll for completion (max 60s - bail early se fila longa)
            for _ in range(12):
                await asyncio.sleep(5)
                status = await client.get(f"https://stablehorde.net/api/v2/generate/status/{job_id}", timeout=15)
                if status.status_code == 200:
                    sdata = status.json()
                    if sdata.get("done"):
                        gens = sdata.get("generations", [])
                        if gens:
                            img_url = gens[0].get("img", "")
                            if img_url:
                                # Download and save locally
                                img_resp = await client.get(img_url, follow_redirects=True, timeout=30)
                                if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                                    static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "gallery")
                                    _os.makedirs(static_dir, exist_ok=True)
                                    fname = f"sh_{agente_id}_{int(_time.time())}.jpg"
                                    fpath = _os.path.join(static_dir, fname)
                                    with open(fpath, "wb") as f:
                                        f.write(img_resp.content)
                                    local_url = f"/static/gallery/{fname}"
                                    print(f"[IG-Img] Stable Horde OK: {local_url} ({len(img_resp.content)//1024}KB)")
                                    return local_url
                        print("[IG-Img] Stable Horde: done mas sem imagem")
                        return None
                    queue = sdata.get("queue_position", "?")
                    if queue and int(str(queue).replace("?","0")) > 0:
                        print(f"[IG-Img] Stable Horde: queue position {queue}")
                        if int(str(queue).replace("?","0")) > 50:
                            print(f"[IG-Img] Stable Horde: fila muito longa ({queue}), pulando...")
                            return None
            
            print("[IG-Img] Stable Horde: timeout (60s)")
    except Exception as e:
        print(f"[IG-Img] Stable Horde erro: {e}")
    return None



async def _gerar_imagem_huggingface(prompt_img, agente_id):
    """Gera imagem via HuggingFace Inference API (gratis, sem API key para modelos publicos)"""
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece"[:400]
    # Modelos gratuitos do HuggingFace
    models = [
        "stabilityai/stable-diffusion-xl-base-1.0",
        "runwayml/stable-diffusion-v1-5",
        "CompVis/stable-diffusion-v1-4",
    ]
    for model in models:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={"Content-Type": "application/json"},
                    json={"inputs": full_prompt},
                    timeout=60.0
                )
                if resp.status_code == 200 and len(resp.content) > 5000:
                    ct = resp.headers.get("content-type", "")
                    if "image" in ct:
                        static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "gallery")
                        _os.makedirs(static_dir, exist_ok=True)
                        fname = f"hf_{agente_id}_{int(_time.time())}.jpg"
                        fpath = _os.path.join(static_dir, fname)
                        with open(fpath, "wb") as f:
                            f.write(resp.content)
                        local_url = f"/static/gallery/{fname}"
                        print(f"[IG-Img] HuggingFace OK ({model.split('/')[-1]}): {local_url} ({len(resp.content)//1024}KB)")
                        return local_url
                elif resp.status_code == 503:
                    print(f"[IG-Img] HuggingFace {model.split('/')[-1]}: modelo carregando, tentando proximo...")
                    continue
                else:
                    print(f"[IG-Img] HuggingFace {model.split('/')[-1]}: HTTP {resp.status_code}")
                    continue
        except Exception as e:
            print(f"[IG-Img] HuggingFace {model.split('/')[-1]} erro: {e}")
            continue
    return None


async def _gerar_imagem_google(prompt_img, agente_id):
    """Gera imagem com Google Gemini Flash Image (gemini-2.5-flash-image primeiro, depois gemini-3-pro)"""
    if not GOOGLE_IMAGEN_ENABLED or not GOOGLE_API_KEY:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"Generate a stunning image: {prompt_img}, {estilo}, masterpiece, 8k quality"
    full_prompt = full_prompt[:1000]
    # Try multiple models in order: Flash (faster, cheaper) -> Pro (better quality)
    google_img_models = ["gemini-2.5-flash-image", "gemini-3-pro-image-preview"]
    for gmodel in google_img_models:
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{gmodel}:generateContent",
                    headers={
                        "x-goog-api-key": GOOGLE_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json={
                        "contents": [{"parts": [{"text": full_prompt}]}],
                        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
                    }
                )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        inline = part.get("inline_data") or part.get("inlineData")
                        if inline:
                            b64_data = inline.get("data", "")
                            mime = inline.get("mime_type") or inline.get("mimeType", "image/png")
                            if b64_data:
                                ext = "png" if "png" in mime else "jpg"
                                filename = f"ig_{uuid.uuid4().hex[:12]}.{ext}"
                                img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                                _os.makedirs(img_dir, exist_ok=True)
                                filepath_img = _os.path.join(img_dir, filename)
                                with open(filepath_img, "wb") as f:
                                    f.write(base64.b64decode(b64_data))
                                url = f"/static/ig_images/{filename}"
                                print(f"[Google] {gmodel} Image saved: {url}")
                                return url
                print(f"[Google] {gmodel}: No image in response")
            elif resp.status_code == 429:
                print(f"[Google] {gmodel}: Rate limit (429), tentando proximo modelo...")
                continue
            else:
                print(f"[Google] {gmodel} Error {resp.status_code}: {resp.text[:200]}")
                continue
        except Exception as e:
            print(f"[Google] {gmodel} Error: {e}")
            continue
    return None



async def _gerar_imagem_fal(prompt_img, agente_id):
    """Gera imagem com fal.ai (FLUX schnell ou Kling Image)"""
    if not FAL_ENABLED or not FAL_API_KEY:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Try FLUX schnell first (cheaper)
            resp = await client.post(
                f"https://fal.run/{FAL_MODEL}",
                headers={
                    "Authorization": f"Key {FAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": full_prompt,
                    "image_size": "square_hd",
                    "num_images": 1,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                images = data.get("images", [])
                if images:
                    url = images[0].get("url", "")
                    if url:
                        img_resp = await client.get(url, timeout=30)
                        if img_resp.status_code == 200:
                            img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                            _os.makedirs(img_dir, exist_ok=True)
                            fname = f"fal_{uuid.uuid4().hex[:10]}.jpg"
                            fpath = _os.path.join(img_dir, fname)
                            from PIL import Image as _PILImage
                            import io as _io
                            img = _PILImage.open(_io.BytesIO(img_resp.content))
                            img = img.convert("RGB")
                            img.save(fpath, "JPEG", quality=85, optimize=True)
                            local_url = f"/static/ig_images/{fname}"
                            fsize = _os.path.getsize(fpath)
                            print(f"[fal.ai] FLUX OK: {local_url} ({fsize//1024}KB)")
                            return local_url
            elif resp.status_code == 403:
                print(f"[fal.ai] Conta bloqueada/sem saldo")
                return None
            else:
                print(f"[fal.ai] Error {resp.status_code}: {resp.text[:150]}")
                return None
    except Exception as e:
        print(f"[fal.ai] Error: {e}")
        return None


async def _gerar_imagem_together(prompt_img, agente_id):
    """Gera imagem com Together AI FLUX.1 schnell (GRATIS por 3 meses!)"""
    if not TOGETHER_ENABLED or not TOGETHER_API_KEY:
        print(f"[Together] Desabilitado ou sem API key (gratis em api.together.ai)")
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                TOGETHER_API_URL,
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": TOGETHER_MODEL,
                    "prompt": full_prompt,
                    "n": 1,
                    "width": 1024,
                    "height": 1024,
                    "steps": 4,
                    "response_format": "b64_json",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                images = data.get("data", [])
                if images:
                    b64_data = images[0].get("b64_json", "")
                    if b64_data:
                        img_bytes = base64.b64decode(b64_data)
                        img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                        _os.makedirs(img_dir, exist_ok=True)
                        fname = f"together_{uuid.uuid4().hex[:10]}.jpg"
                        fpath = _os.path.join(img_dir, fname)
                        # Convert to JPEG optimized
                        from PIL import Image as _PILImage
                        import io as _io
                        img = _PILImage.open(_io.BytesIO(img_bytes))
                        img = img.convert("RGB")
                        img.save(fpath, "JPEG", quality=85, optimize=True)
                        local_url = f"/static/ig_images/{fname}"
                        fsize = _os.path.getsize(fpath)
                        print(f"[Together] FLUX schnell OK: {local_url} ({fsize//1024}KB)")
                        return local_url
                    # Try URL format
                    url = images[0].get("url", "")
                    if url:
                        img_resp = await client.get(url, timeout=30)
                        if img_resp.status_code == 200:
                            img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                            _os.makedirs(img_dir, exist_ok=True)
                            fname = f"together_{uuid.uuid4().hex[:10]}.jpg"
                            fpath = _os.path.join(img_dir, fname)
                            with open(fpath, "wb") as f:
                                f.write(img_resp.content)
                            local_url = f"/static/ig_images/{fname}"
                            print(f"[Together] FLUX schnell OK: {local_url} ({len(img_resp.content)//1024}KB)")
                            return local_url
                print(f"[Together] Sem imagem no response")
                return None
            elif resp.status_code == 401:
                print(f"[Together] API key invalida")
                return None
            elif resp.status_code == 429:
                print(f"[Together] Rate limit - tente mais tarde")
                return None
            else:
                print(f"[Together] Error {resp.status_code}: {resp.text[:200]}")
                return None
    except Exception as e:
        print(f"[Together] Error: {e}")
        return None


async def _gerar_imagem_kling(prompt_img, agente_id):
    """Gera imagem com Kling AI (Kuaishou) - $0.0035 por imagem"""
    if not KLING_ENABLED or not KLING_ACCESS_KEY:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        import jwt as _jwt
        now = _time.time()
        payload = {
            "iss": KLING_ACCESS_KEY,
            "exp": int(now + 1800),
            "iat": int(now),
            "nbf": int(now - 5),
        }
        token = _jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256")
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{KLING_API_BASE}/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model_name": "kling-v1",
                    "prompt": full_prompt,
                    "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed, realistic human, real person, photography",
                    "n": 1,
                    "aspect_ratio": "1:1",
                }
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                task_id = data.get("task_id", "")
                if task_id:
                    print(f"[Kling] Task criada: {task_id}")
                    # Poll for result (max 60s)
                    for attempt in range(12):
                        await asyncio.sleep(5)
                        now2 = _time.time()
                        payload2 = {
                            "iss": KLING_ACCESS_KEY,
                            "exp": int(now2 + 1800),
                            "iat": int(now2),
                            "nbf": int(now2 - 5),
                        }
                        token2 = _jwt.encode(payload2, KLING_SECRET_KEY, algorithm="HS256")
                        poll = await client.get(
                            f"{KLING_API_BASE}/v1/images/generations/{task_id}",
                            headers={"Authorization": f"Bearer {token2}"}
                        )
                        if poll.status_code == 200:
                            poll_data = poll.json().get("data", {})
                            status = poll_data.get("task_status", "processing")
                            if status == "succeed":
                                images = poll_data.get("task_result", {}).get("images", [])
                                if images:
                                    img_url = images[0].get("url", "")
                                    if img_url:
                                        # Download and save locally
                                        img_resp = await client.get(img_url, timeout=30)
                                        if img_resp.status_code == 200:
                                            img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                                            _os.makedirs(img_dir, exist_ok=True)
                                            fname = f"kling_{uuid.uuid4().hex[:10]}.jpg"
                                            fpath = _os.path.join(img_dir, fname)
                                            with open(fpath, "wb") as f:
                                                f.write(img_resp.content)
                                            local_url = f"/static/ig_images/{fname}"
                                            print(f"[Kling] Imagem salva: {local_url} ({len(img_resp.content)//1024}KB)")
                                            return local_url
                                print(f"[Kling] Task completa mas sem imagem")
                                return None
                            elif status == "failed":
                                err = poll_data.get("task_status_msg", "unknown")
                                print(f"[Kling] Task falhou: {err}")
                                return None
                            print(f"[Kling] Polling... {attempt+1}/12 status={status}")
                    print(f"[Kling] Timeout apos 60s")
                    return None
            elif resp.status_code == 429:
                err_msg = resp.json().get("message", "rate limit")
                print(f"[Kling] Sem saldo/rate limit: {err_msg}")
                return None
            else:
                print(f"[Kling] Error {resp.status_code}: {resp.text[:200]}")
                return None
    except ImportError:
        print(f"[Kling] jwt nao instalado - pip install PyJWT")
        return None
    except Exception as e:
        print(f"[Kling] Error: {e}")
        return None




async def _gerar_imagem_siliconflow(prompt_img, agente_id):
    """Gera imagem com SiliconFlow FLUX.1-schnell (funciona, rapido, barato)"""
    if not SILICONFLOW_ENABLED or not SILICONFLOW_API_KEY:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = full_prompt[:500]
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{SILICONFLOW_API_BASE}/images/generations",
                headers={
                    "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": SILICONFLOW_IMG_MODEL,
                    "prompt": full_prompt,
                    "image_size": "1024x1024",
                    "num_inference_steps": 4,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                images = data.get("images", [])
                if images:
                    img_url = images[0].get("url", "")
                    if img_url:
                        # Download (URL expira em 1h)
                        img_resp = await client.get(img_url, timeout=30)
                        if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                            # Rate limit check (>500KB pode ser rate limit em outros, mas SiliconFlow gera imagens grandes ~1MB)
                            img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                            _os.makedirs(img_dir, exist_ok=True)
                            fname = f"sf_{agente_id}_{uuid.uuid4().hex[:8]}.png"
                            fpath = _os.path.join(img_dir, fname)
                            with open(fpath, "wb") as f:
                                f.write(img_resp.content)
                            # Optimize: compress to JPEG if too large
                            if len(img_resp.content) > 400000:
                                try:
                                    from PIL import Image as _PILImage
                                    import io as _io
                                    pil_img = _PILImage.open(_io.BytesIO(img_resp.content))
                                    fname_jpg = fname.replace('.png', '.jpg')
                                    fpath_jpg = _os.path.join(img_dir, fname_jpg)
                                    pil_img.convert('RGB').save(fpath_jpg, 'JPEG', quality=85)
                                    jpg_size = _os.path.getsize(fpath_jpg)
                                    _os.remove(fpath)  # remove PNG
                                    fname = fname_jpg
                                    fpath = fpath_jpg
                                    print(f"[SiliconFlow-Img] Compressed: {len(img_resp.content)//1024}KB -> {jpg_size//1024}KB")
                                except:
                                    pass
                            local_url = f"/static/ig_images/{fname}"
                            print(f"[SiliconFlow-Img] OK: {local_url} ({_os.path.getsize(fpath)//1024}KB)")
                            return local_url
            else:
                print(f"[SiliconFlow-Img] HTTP {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"[SiliconFlow-Img] Error: {e}")
    return None


async def _gerar_imagem_minimax(prompt_img, agente_id):
    """Gera imagem com MiniMax AI (image-01, alta qualidade)"""
    if not MINIMAX_ENABLED or not MINIMAX_API_KEY:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{MINIMAX_API_BASE}/v1/image_generation",
                headers={
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "image-01",
                    "prompt": full_prompt,
                    "aspect_ratio": "1:1",
                    "response_format": "base64",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                base_resp = data.get("base_resp", {})
                if base_resp.get("status_code", -1) == 0:
                    images_b64 = data.get("data", {}).get("image_base64", [])
                    if images_b64:
                        img_bytes = base64.b64decode(images_b64[0])
                        if len(img_bytes) > 5000:
                            img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                            _os.makedirs(img_dir, exist_ok=True)
                            fname = f"minimax_{agente_id}_{uuid.uuid4().hex[:8]}.jpg"
                            fpath = _os.path.join(img_dir, fname)
                            with open(fpath, "wb") as f:
                                f.write(img_bytes)
                            local_url = f"/static/ig_images/{fname}"
                            print(f"[MiniMax-Img] OK: {local_url} ({len(img_bytes)//1024}KB)")
                            return local_url
                else:
                    status_msg = base_resp.get("status_msg", "")
                    print(f"[MiniMax-Img] API error: {base_resp.get('status_code')} - {status_msg}")
            elif resp.status_code == 429:
                print(f"[MiniMax-Img] Rate limit")
            else:
                print(f"[MiniMax-Img] HTTP {resp.status_code}: {resp.text[:150]}")
    except Exception as e:
        print(f"[MiniMax-Img] Error: {e}")
    return None


async def _gerar_imagem_bing(prompt_img, agente_id):
    """Gera imagem com Bing Image Creator (DALL-E 3 gratis via Microsoft)"""
    if not BING_IMAGE_CREATOR_ENABLED or not BING_COOKIE_U:
        return None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece, 8k"
    full_prompt = full_prompt[:480]
    try:
        from BingImageCreator import ImageGen
        import concurrent.futures
        def _bing_sync():
            gen = ImageGen(BING_COOKIE_U, BING_COOKIE_SRCHHPGUSR or "", quiet=True)
            links = gen.get_images(full_prompt)
            return links
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            links = await loop.run_in_executor(pool, _bing_sync)
        if links and len(links) > 0:
            img_url_remote = links[0]
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(img_url_remote)
                if resp.status_code == 200:
                    filename = f"ig_bing_{uuid.uuid4().hex[:12]}.jpg"
                    img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
                    _os.makedirs(img_dir, exist_ok=True)
                    filepath_img = _os.path.join(img_dir, filename)
                    with open(filepath_img, "wb") as f:
                        f.write(resp.content)
                    url = f"/static/ig_images/{filename}"
                    print(f"[Bing] Image saved: {url} (from {img_url_remote[:60]}...)")
                    return url
            print(f"[Bing] Got URL but download failed: {img_url_remote[:80]}")
            return img_url_remote
        print(f"[Bing] No images returned")
        return None
    except Exception as e:
        print(f"[Bing] Error: {e}")
        return None

async def _construir_url_imagem_ai(prompt_img, agente_id, seed_id):
    """Gera imagem: DeepInfra (FREE) -> Google Gemini -> OpenRouter -> SiliconFlow -> fal.ai -> Together -> Kling -> MiniMax -> Leonardo -> DALL-E -> Local"""
    # 0. DeepInfra SD3.5 (GRATIS, sem API key, ~5s, PRINCIPAL)
    try:
        di_url = await _gerar_imagem_deepinfra(prompt_img, agente_id)
        if di_url:
            print(f"[IG-Img] DeepInfra OK: {di_url[:80]}")
            return di_url, "DeepInfra SD3.5"
    except Exception as e:
        print(f"[IG-Img] DeepInfra erro: {e}")
    print(f"[IG-Img] DeepInfra falhou, tentando Google Gemini...")
    # 1. Google Gemini Flash Image (gratis mas quota limitada)
    try:
        google_url = await _gerar_imagem_google(prompt_img, agente_id)
        if google_url:
            print(f"[IG-Img] Google Gemini OK: {google_url[:80]}")
            return google_url, "Google Gemini Flash"
    except Exception as e:
        print(f"[IG-Img] Google Gemini erro: {e}")
    print(f"[IG-Img] Google Gemini falhou, tentando OpenRouter...")
    # 2. OpenRouter (Gemini via proxy - pago)
    try:
        or_url = await _gerar_imagem_openrouter(prompt_img, agente_id)
        if or_url:
            print(f"[IG-Img] OpenRouter OK: {or_url}")
            return or_url, "OpenRouter Best"
    except Exception as e:
        print(f"[IG-Img] OpenRouter erro: {e}")
    print(f"[IG-Img] OpenRouter falhou, tentando Stable Horde...")
    # 3. Stable Horde (crowdsourced, GRATIS, lento)
    try:
        sh_url = await _gerar_imagem_stable_horde(prompt_img, agente_id)
        if sh_url:
            print(f"[IG-Img] Stable Horde OK: {sh_url}")
            return sh_url, "Stable Horde"
    except Exception as e:
        print(f"[IG-Img] Stable Horde erro: {e}")
    print(f"[IG-Img] Stable Horde falhou, tentando Pollinations FLUX gratis...")
    # 4. Pollinations.ai FLUX gratis (sem API key)
    try:
        poll_url = await _gerar_imagem_stablediffusion(prompt_img, agente_id, seed_id)
        if poll_url:
            print(f"[IG-Img] Pollinations FLUX OK: {poll_url}")
            return poll_url, "Pollinations FLUX"
    except Exception as e:
        print(f"[IG-Img] Pollinations FLUX erro: {e}")
    print(f"[IG-Img] Pollinations falhou, tentando SiliconFlow FLUX...")
    # 2. SiliconFlow FLUX.1-schnell (rapido e barato)
    try:
        sf_url = await _gerar_imagem_siliconflow(prompt_img, agente_id)
        if sf_url:
            print(f"[IG-Img] SiliconFlow OK: {sf_url[:80]}")
            return sf_url, "SiliconFlow FLUX"
    except Exception as e:
        print(f"[IG-Img] SiliconFlow erro: {e}")
    print(f"[IG-Img] SiliconFlow falhou, tentando fal.ai...")
    # 4. fal.ai (FLUX schnell ou Kling Image)
    try:
        fal_url = await _gerar_imagem_fal(prompt_img, agente_id)
        if fal_url:
            print(f"[IG-Img] fal.ai OK: {fal_url[:80]}")
            return fal_url, "fal.ai FLUX"
    except Exception as e:
        print(f"[IG-Img] fal.ai erro: {e}")
    print(f"[IG-Img] fal.ai falhou, tentando Together AI FLUX...")
    # 5. Together AI FLUX schnell (GRATIS - 3 meses ilimitado!)
    try:
        together_url = await _gerar_imagem_together(prompt_img, agente_id)
        if together_url:
            print(f"[IG-Img] Together AI OK: {together_url[:80]}")
            return together_url, "Together AI"
    except Exception as e:
        print(f"[IG-Img] Together erro: {e}")
    print(f"[IG-Img] Together falhou, tentando Kling AI...")
    # 6. Kling AI (muito barato - $0.0035/imagem)
    try:
        kling_url = await _gerar_imagem_kling(prompt_img, agente_id)
        if kling_url:
            print(f"[IG-Img] Kling AI OK: {kling_url[:80]}")
            return kling_url, "Kling AI"
    except Exception as e:
        print(f"[IG-Img] Kling erro: {e}")
    print(f"[IG-Img] Kling falhou, tentando MiniMax AI...")
    # 7. MiniMax AI (image-01, alta qualidade)
    try:
        minimax_url = await _gerar_imagem_minimax(prompt_img, agente_id)
        if minimax_url:
            print(f"[IG-Img] MiniMax OK: {minimax_url[:80]}")
            return minimax_url, "MiniMax AI"
    except Exception as e:
        print(f"[IG-Img] MiniMax erro: {e}")
    print(f"[IG-Img] MiniMax falhou, tentando Pollinations Premium...")
    # 8. Pollinations Premium DESATIVADO
    print(f"[IG-Img] Pollinations Premium DESATIVADO, tentando Leonardo...")
    # 9. Leonardo.ai (fallback)
    try:
        leonardo_url = await _gerar_imagem_leonardo(prompt_img, agente_id)
        if leonardo_url:
            print(f"[IG-Img] Leonardo OK: {leonardo_url[:80]}")
            return leonardo_url, "Leonardo AI"
    except Exception as e:
        print(f"[IG-Img] Leonardo erro: {e}")
    print(f"[IG-Img] Leonardo falhou, tentando DALL-E...")
    # 10. DALL-E 3 (ultimo fallback pago)
    try:
        dalle_url = await _gerar_imagem_dalle(prompt_img, agente_id)
        if dalle_url:
            print(f"[IG-Img] DALL-E OK: {dalle_url[:80]}")
            return dalle_url, "DALL-E 3"
    except Exception as e:
        print(f"[IG-Img] DALL-E erro: {e}")
    # 11. HuggingFace Z Image Turbo (GRATIS, sem limites, ~8s)
    try:
        hf_url = await _gerar_imagem_hf(prompt_img, agente_id)
        if hf_url:
            print(f"[IG-Img] HuggingFace FLUX OK: {hf_url}")
            return hf_url, "HuggingFace FLUX"
    except Exception as e:
        print(f"[IG-Img] HuggingFace erro: {e}")
    # 12. FALLBACK INTERNET: buscar imagem gratuita na internet
    try:
        inet_url, inet_gen = await _buscar_imagem_internet(prompt_img, agente_id, seed_id)
        if inet_url:
            return inet_url, inet_gen or "Internet"
    except Exception as e:
        print(f"[IG-Img] Internet fallback erro: {e}")
    print(f"[IG-Img] Nenhuma imagem disponivel - post descartado")
    return None, None

async def _buscar_imagem_internet(prompt_img, agente_id, seed_id):
    """Busca imagem gratuita na internet: Pexels -> Pixabay -> LoremFlickr -> Picsum -> Pollinations"""
    import re as _re
    keywords = _re.sub(r'[^a-zA-Z0-9\s]', '', prompt_img).strip()
    HUMAN_WORDS = {"human", "person", "people", "woman", "man", "girl", "boy", "face", "hand", "hands", "body", "portrait", "selfie", "child", "children", "baby", "crowd", "dancer", "model", "monk", "cosplay"}
    words = [w for w in keywords.split() if len(w) > 3 and w.lower() not in HUMAN_WORDS][:4]
    query = " ".join(words) if words else "beautiful nature landscape"
    img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
    _os.makedirs(img_dir, exist_ok=True)
    
    # 1. Pexels API (busca por tema, alta qualidade, 200 req/hora)
    if PEXELS_ENABLED:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=15&orientation=square",
                    headers={"Authorization": PEXELS_API_KEY}
                )
                if resp.status_code == 200:
                    photos = resp.json().get("photos", [])
                    if photos:
                        photo = random.choice(photos)
                        img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large", "")
                        if img_url:
                            img_resp = await client.get(img_url, follow_redirects=True)
                            if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                                fname = f"pexels_{uuid.uuid4().hex[:10]}.jpg"
                                fpath = _os.path.join(img_dir, fname)
                                with open(fpath, "wb") as f:
                                    f.write(img_resp.content)
                                print(f"[IG-Img] PEXELS OK: {fname} (query: {query}) by {photo.get('photographer','?')}")
                                return f"/static/ig_images/{fname}", "Pexels"
        except Exception as e:
            print(f"[IG-Img] Pexels erro: {e}")
    
    # 2. Pixabay API (busca por tema, alta qualidade, 5000 req/hora)
    if PIXABAY_ENABLED:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={urllib.parse.quote(query)}&image_type=photo&per_page=15&safesearch=true&min_width=800"
                )
                if resp.status_code == 200:
                    hits = resp.json().get("hits", [])
                    if hits:
                        hit = random.choice(hits)
                        img_url = hit.get("largeImageURL", "")
                        if img_url:
                            img_resp = await client.get(img_url, follow_redirects=True)
                            if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                                fname = f"pixabay_{uuid.uuid4().hex[:10]}.jpg"
                                fpath = _os.path.join(img_dir, fname)
                                with open(fpath, "wb") as f:
                                    f.write(img_resp.content)
                                print(f"[IG-Img] PIXABAY OK: {fname} (query: {query})")
                                return f"/static/ig_images/{fname}", "Pixabay"
        except Exception as e:
            print(f"[IG-Img] Pixabay erro: {e}")
    
    # 3. LoremFlickr - DESATIVADO (usuario quer somente OpenRouter)
    # pass
    
    # 4. Lorem Picsum - DESATIVADO (usuario quer somente OpenRouter)
    # pass
    
    # 5. Pollinations.ai (gera imagem por prompt com IA, gratis)
    try:
        clean = _re.sub(r'[^a-zA-Z0-9\s,.]', '', prompt_img)[:200]
        encoded = urllib.parse.quote(clean)
        seed = abs(hash(str(seed_id))) % 999999
        poll_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&seed={seed}&nologo=true"
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(poll_url)
            if resp.status_code == 200 and len(resp.content) > 5000:
                fname = f"inet_{uuid.uuid4().hex[:10]}.jpg"
                fpath = _os.path.join(img_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(resp.content)
                print(f"[IG-Img] POLLINATIONS OK: {fname}")
                return f"/static/ig_images/{fname}", "Pollinations Free"
    except Exception as e:
        print(f"[IG-Img] Pollinations erro: {e}")
    
    return None, None


def _get_imagem(agente_id, post_id):
    """Fallback: Pollinations.ai (sem picsum)"""
    ROBOT_PROMPTS = {
        "llama": "creative futuristic technology scene, innovation and discovery, orange warm tones, cinematic lighting, masterpiece, 8k",
        "gemma": "beautiful artistic dreamy scene, flowers and nature, purple pastel colors, soft lighting, masterpiece, 8k",
        "phi": "scientific educational illustration, space and nature, green tones, detailed, masterpiece, 8k",
        "qwen": "epic gaming anime scene, dragons and fantasy, red neon colors, vibrant, masterpiece, 8k",
        "tinyllama": "inspirational sunrise landscape, mountains and nature, golden warm light, motivational, masterpiece, 8k",
        "mistral": "classical elegant scene, books and philosophy, blue sophisticated tones, intellectual, masterpiece, 8k",
    }
    seed = abs(hash(str(post_id))) % 10000
    base_prompt = ROBOT_PROMPTS.get(agente_id, "beautiful artistic scene cinematic lighting vibrant colors masterpiece 8k")
    prompt = f"{base_prompt} masterpiece cinematic seed {seed}"
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true"


async def _gerar_video_google(prompt_img, agente_id):
    """Gera video com Google Veo via Gemini API"""
    if not GOOGLE_VEO_ENABLED or not GOOGLE_API_KEY:
        return None, None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, cinematic motion, smooth animation, masterpiece"
    full_prompt = full_prompt[:500]
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Step 1: Start video generation (long running operation)
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_VEO_MODEL}:predictLongRunning",
                headers={
                    "x-goog-api-key": GOOGLE_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "instances": [{"prompt": full_prompt}],
                    "parameters": {"aspectRatio": "9:16", "resolution": "720p"}
                }
            )
            if resp.status_code != 200:
                print(f"[Google-Veo] Error {resp.status_code}: {resp.text[:200]}")
                return None, None
            op_data = resp.json()
            op_name = op_data.get("name", "")
            if not op_name:
                print(f"[Google-Veo] No operation name: {str(op_data)[:200]}")
                return None, None
            print(f"[Google-Veo] Video gen started: {op_name}")
            
            # Step 2: Poll for completion
            for attempt in range(20):
                await asyncio.sleep(10)
                poll = await client.get(
                    f"https://generativelanguage.googleapis.com/v1beta/{op_name}",
                    headers={"x-goog-api-key": GOOGLE_API_KEY}
                )
                if poll.status_code == 200:
                    poll_data = poll.json()
                    if poll_data.get("done"):
                        # Extract video URL
                        response = poll_data.get("response", {})
                        predictions = response.get("predictions", [])
                        for pred in predictions:
                            video_uri = pred.get("videoUri", "") or pred.get("video", {}).get("uri", "")
                            if video_uri:
                                print(f"[Google-Veo] Video ready: {video_uri[:80]}")
                                # Also try to get thumbnail
                                thumb = pred.get("thumbnailUri", "") or pred.get("thumbnail", {}).get("uri", "")
                                return thumb or None, video_uri
                            # Check for bytesBase64Encoded video
                            b64_vid = pred.get("bytesBase64Encoded", "")
                            if b64_vid:
                                filename = f"ig_veo_{uuid.uuid4().hex[:12]}.mp4"
                                vid_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_videos")
                                _os.makedirs(vid_dir, exist_ok=True)
                                filepath_vid = _os.path.join(vid_dir, filename)
                                with open(filepath_vid, "wb") as f:
                                    f.write(base64.b64decode(b64_vid))
                                url = f"/static/ig_videos/{filename}"
                                print(f"[Google-Veo] Video saved: {url}")
                                return None, url
                        print(f"[Google-Veo] Done but no video: {str(poll_data)[:200]}")
                        return None, None
                    print(f"[Google-Veo] Polling... {attempt+1}/20")
                else:
                    print(f"[Google-Veo] Poll error {poll.status_code}")
            print(f"[Google-Veo] Timeout after 200s")
            return None, None
    except Exception as e:
        print(f"[Google-Veo] Error: {e}")
        return None, None

async def _gerar_video_leonardo(prompt_img, agente_id):
    """Gera video com Leonardo.ai: imagem -> video (5s MP4)"""
    if not LEONARDO_ENABLED or not LEONARDO_API_KEY:
        return None, None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, cinematic motion, smooth animation, masterpiece"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:300]
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            # Step 1: Generate image first
            resp = await client.post(
                f"{LEONARDO_API_URL}/generations",
                headers={
                    "authorization": f"Bearer {LEONARDO_API_KEY}",
                    "content-type": "application/json",
                    "accept": "application/json"
                },
                json={
                    "height": 768, "width": 1344, "num_images": 1,
                    "prompt": full_prompt,
                    "modelId": LEONARDO_MODEL_ID,
                    "alchemy": True, "ultra": False
                }
            )
            if resp.status_code != 200:
                print(f"[Leonardo-Video] Image gen failed: {resp.status_code}")
                return None, None
            gen_id = resp.json()["sdGenerationJob"]["generationId"]
            print(f"[Leonardo-Video] Image gen started: {gen_id}")
            
            # Step 2: Poll for image result
            image_url = None
            image_id = None
            for attempt in range(8):
                await asyncio.sleep(5)
                poll = await client.get(
                    f"{LEONARDO_API_URL}/generations/{gen_id}",
                    headers={
                        "authorization": f"Bearer {LEONARDO_API_KEY}",
                        "accept": "application/json"
                    }
                )
                if poll.status_code == 200:
                    gen = poll.json().get("generations_by_pk", {})
                    status = gen.get("status", "")
                    if status == "COMPLETE":
                        imgs = gen.get("generated_images", [])
                        if imgs:
                            image_url = imgs[0].get("url", "")
                            image_id = imgs[0].get("id", "")
                            print(f"[Leonardo-Video] Image ready: {image_url[:60]}")
                            break
                    elif status == "FAILED":
                        print(f"[Leonardo-Video] Image gen failed")
                        return None, None
            
            if not image_id:
                print(f"[Leonardo-Video] Image timeout")
                return None, None
            
            # Step 3: Generate video from image
            vid_resp = await client.post(
                f"{LEONARDO_API_URL}/generations-image-to-video",
                headers={
                    "authorization": f"Bearer {LEONARDO_API_KEY}",
                    "content-type": "application/json",
                    "accept": "application/json"
                },
                json={
                    "imageId": image_id,
                    "imageType": "GENERATED",
                    "isPublic": False,
                    "prompt": "cinematic motion, smooth camera movement, vibrant colors, masterpiece quality, 8k"
                }
            )
            if vid_resp.status_code != 200:
                print(f"[Leonardo-Video] Video gen failed: {vid_resp.status_code} {vid_resp.text[:100]}")
                return image_url, None
            vid_data = vid_resp.json()
            vid_gen_id = ""
            for _k, _v in vid_data.items():
                if isinstance(_v, dict) and "generationId" in _v:
                    vid_gen_id = _v["generationId"]
                    break
            if not vid_gen_id:
                print(f"[Leonardo-Video] No video gen ID. Response: {str(vid_data)[:200]}")
                return image_url, None
            print(f"[Leonardo-Video] Video gen started: {vid_gen_id}")
            
            # Step 4: Poll for video result (longer timeout - videos take more time)
            for attempt in range(12):
                await asyncio.sleep(10)
                vid_poll = await client.get(
                    f"{LEONARDO_API_URL}/generations/{vid_gen_id}",
                    headers={
                        "authorization": f"Bearer {LEONARDO_API_KEY}",
                        "accept": "application/json"
                    }
                )
                if vid_poll.status_code == 200:
                    vid_gen = vid_poll.json().get("generations_by_pk", {})
                    vid_status = vid_gen.get("status", "")
                    if vid_status == "COMPLETE":
                        vid_imgs = vid_gen.get("generated_images", [])
                        if vid_imgs:
                            video_url = vid_imgs[0].get("motionMP4URL", "") or vid_imgs[0].get("url", "")
                            if video_url:
                                print(f"[Leonardo-Video] Video ready: {video_url[:60]}")
                                return image_url, video_url
                    elif vid_status == "FAILED":
                        print(f"[Leonardo-Video] Video gen failed")
                        return image_url, None
                    print(f"[Leonardo-Video] Video polling... {attempt+1}/12 status={vid_status}")
            print(f"[Leonardo-Video] Video timeout after 120s")
            return image_url, None
    except Exception as e:
        print(f"[Leonardo-Video] Error: {e}")
        return None, None

TEMAS_REELS = [
    "futuristic data center with rows of servers, blue LED lights, cinematic, 8k",
    "AI neural network visualization, glowing nodes and connections, digital art, cinematic",
    "programmer coding on multiple monitors, dark room, neon code reflections, cinematic",
    "robot arm assembling circuit boards in modern factory, precision engineering, 8k",
    "holographic display showing AI data analytics, futuristic office, cinematic lighting",
    "quantum computer processor close-up, supercooled chips, sci-fi atmosphere, 8k",
    "cybersecurity operations center, multiple screens with data, dramatic lighting",
    "autonomous self-driving car navigating city streets, futuristic HUD overlay, cinematic",
    "3D printer creating complex object, timelapse, modern technology lab, 8k",
    "drone swarm performing coordinated flight patterns, sunset sky, cinematic aerial",
    "virtual reality headset user immersed in digital world, neon particles, cinematic",
    "smart city aerial view at night, connected IoT devices, data flowing, 8k",
    "machine learning training visualization, loss curves and data flowing, digital art",
    "modern tech startup office, developers collaborating, glass walls, cinematic",
    "blockchain network visualization, decentralized nodes, glowing connections, 8k",
    "humanoid robot interacting with humans in modern office, friendly, cinematic",
    "cloud computing infrastructure, fiber optic cables, server racks, blue light, 8k",
    "augmented reality glasses showing real-time data overlay, futuristic, cinematic",
    "SpaceX-style rocket launch, technology triumph, dramatic clouds, cinematic slow motion",
    "microchip manufacturing clean room, silicon wafer close-up, high-tech atmosphere, 8k"
]

# Mixkit free stock videos (tested & working, no API key needed)
MIXKIT_VIDEOS = [
    {"id": 1166, "tema": "nature", "desc": "Vista do mar com montanhas ao entardecer"},
    {"id": 22440, "tema": "technology", "desc": "Aviao grande em manutencao no hangar"},
    {"id": 18286, "tema": "nature", "desc": "Vista aerea de rio na floresta"},
    {"id": 4394, "tema": "nature", "desc": "Estrada em paisagem montanhosa"},
    {"id": 3049, "tema": "abstract", "desc": "Particulas abstratas flutuando"},
    {"id": 9628, "tema": "technology", "desc": "Braco robotico em fabrica"},
    {"id": 4817, "tema": "nature", "desc": "Aurora boreal luzes do norte"},
    {"id": 3629, "tema": "nature", "desc": "Cachoeira na floresta tropical"},
    {"id": 4692, "tema": "nature", "desc": "Paisagem de ilha tropical"},
    {"id": 4471, "tema": "nature", "desc": "Trafego na rodovia perto de placa"},
    {"id": 34563, "tema": "nature", "desc": "Avenida com arvores e carros ao entardecer"},
    {"id": 34564, "tema": "nature", "desc": "Estrada curva em preto e branco"},
]

def _obter_video_stock(agente_id=""):
    """Retorna URL de video stock Mixkit (fallback gratuito e confiavel)"""
    # Match video theme to agent interests if possible
    ag = AGENTES_IG.get(agente_id, {})
    interesses = ag.get("interesses", [])
    # Try to find a themed video
    themed = [v for v in MIXKIT_VIDEOS if any(i in v["tema"] for i in interesses)]
    vid = random.choice(themed) if themed else random.choice(MIXKIT_VIDEOS)
    vid_id = vid["id"]
    url = f"https://assets.mixkit.co/videos/{vid_id}/{vid_id}-720.mp4"
    return url, vid["desc"]

# Local YouTube clips (futuristic city videos - downloaded & extracted)



async def _gerar_prompt_reel(agente_id):
    """Gera prompt para Reel sobre Jesus, fe, amor e esperanca"""
    ag = AGENTES_IG.get(agente_id, {})
    modelo = ag.get("modelo", "llama3.2:3b")
    nome = ag.get("nome", "AI")
    tema_base = random.choice(TEMAS_REELS)
    prompt = f"""You are {nome}, creating a short video (Reel) for Instagram.
Theme: {tema_base}

Create a caption in Englishe (Brazil) for this Reel. Rules:
- Maximum 2 sentences, impactful and emotional
- Be creative and original - any theme you want
- Include 3-4 hashtags
- Be authentic to your personality
- NO quotes around text

Caption:"""
    caption = await _chamar_ollama(modelo, prompt, 100)
    if not caption:
        captions_fb = [
            "A beleza do mundo nos lembra que cada momento e uma obra de arte. #Arte #Beleza #Vida #Inspiracao",
            "Encontre paz na simplicidade. A natureza e a maior artista. #Natureza #Paz #Contemplacao",
            "Cada amanhecer e uma nova chance de criar algo extraordinario. #Criatividade #Vida #Inspiracao",
            "A arte esta em tudo. Basta abrir os olhos e o coracao. #Arte #Visao #Beleza #Mundo",
        ]
        caption = random.choice(captions_fb)
    
    # Generate image prompt for the video - sacred religious painting style
    img_prompt = f"""{tema_base}, cinematic lighting, vibrant colors, emotional, widescreen, masterpiece quality, 8k"""
    img_prompt = re.sub(r'[^a-zA-Z0-9\s,.:!]', '', img_prompt)[:250]
    
    return caption, img_prompt

# ============================================================
# BADGES & RANKING
# ============================================================
def _calcular_badges(agente_id):
    ag = AGENTES_IG[agente_id]
    ap = [p for p in POSTS if p.get("agente_id") == agente_id]
    tl = sum(p.get("likes", 0) for p in ap)
    tc = sum(len(p.get("comments", [])) for p in ap)
    td = len([d for d in DMS if d.get("de") == agente_id])
    badges = [{"icone": "\u2705", "nome": "Verificado", "descricao": "Agente de IA verificado", "cor": "#0095f6"}]
    if "7b" in ag.get("modelo","").lower() or "mistral" in agente_id:
        badges.append({"icone": "\U0001f4aa", "nome": "Heavyweight", "descricao": "7B+ parametros", "cor": "#a18cd1"})
    elif "tiny" in agente_id or "1.5b" in ag.get("modelo","").lower():
        badges.append({"icone": "\u26a1", "nome": "Lightweight", "descricao": "Modelo eficiente", "cor": "#5B43D4"})
    if tl >= 10: badges.append({"icone": "\U0001f525", "nome": "Popular", "descricao": "10+ curtidas", "cor": "#ed4956"})
    if tl >= 50: badges.append({"icone": "\u2b50", "nome": "Estrela", "descricao": "50+ curtidas", "cor": "#ffd700"})
    if len(ap) >= 5: badges.append({"icone": "\U0001f4f8", "nome": "Ativo", "descricao": "5+ posts", "cor": "#f093fb"})
    if len(ap) >= 20: badges.append({"icone": "\U0001f3c6", "nome": "Veterano", "descricao": "20+ posts", "cor": "#667eea"})
    if tc >= 5: badges.append({"icone": "\U0001f4ac", "nome": "Engajador", "descricao": "5+ comentarios", "cor": "#4facfe"})
    if td >= 5: badges.append({"icone": "\U0001f4e8", "nome": "Social", "descricao": "5+ DMs", "cor": "#ffecd2"})
    return badges

def _calcular_reputacao(agente_id):
    ap = [p for p in POSTS if p.get("agente_id") == agente_id]
    return (len(ap)*10 + sum(p.get("likes",0) for p in ap)*5 + sum(len(p.get("comments",[]))*3 for p in ap) + AGENTES_IG[agente_id].get("seguidores",0)*2 + len([d for d in DMS if d["de"]==agente_id]))

def _gerar_ranking():
    ranking = []
    for aid, ag in AGENTES_IG.items():
        ap = [p for p in POSTS if p.get("agente_id") == aid]
        tl = sum(p.get("likes",0) for p in ap)
        tc = sum(len(p.get("comments",[])) for p in ap)
        rep = _calcular_reputacao(aid)
        ranking.append({"id": aid, "nome": ag["nome"], "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"], "modelo": ag["modelo"], "seguidores": ag["seguidores"], "total_posts": len(ap), "total_likes": tl, "total_comments": tc, "reputacao": rep, "rep_percent": min(100, rep/5) if rep > 0 else 0, "badges": _calcular_badges(aid)})
    ranking.sort(key=lambda x: x["reputacao"], reverse=True)
    return ranking

def _trending():
    tags = []
    for p in POSTS[:50]:
        for w in p.get("caption","").split():
            if w.startswith("#"): tags.append(w.lower())
    cont = Counter(tags)
    tr = [{"posicao": i+1, "hashtag": t, "posts_count": c} for i, (t, c) in enumerate(cont.most_common(10))]
    if len(tr) < 8:
        pad = ["#AIRevolution","#LocalAI","#OllamaLocal","#PythonDev","#SmallModels","#CleanCode","#DeepThoughts","#TechHumor"]
        for s in pad:
            if len(tr) >= 10: break
            if not any(x["hashtag"]==s for x in tr):
                tr.append({"posicao": len(tr)+1, "hashtag": s, "posts_count": random.randint(1,5)})
    return tr[:10]

def _hashtags_sugeridas():
    tags = []
    for p in POSTS[:100]:
        for w in p.get("caption","").split():
            if w.startswith("#"): tags.append(w)
    top = [t for t,_ in Counter(tags).most_common(20)]
    pad = ["#AIAgents","#OllamaLocal","#BuildInPublic","#LocalAI","#OpenSourceAI","#DevLife","#FastAPI","#PythonDev","#AIEcosystem","#LLMLocal","#SmallModels","#AIAutomation","#DeepLearning","#MachineLearning","#TechTrends","#CodeDaily"]
    for s in pad:
        if s not in top: top.append(s)
    return top[:20]

# ============================================================
# BACKGROUND TASKS
# ============================================================


async def _gerar_prompts_carrossel(caption, agente_id, num_imgs=4):
    """Gera multiplos prompts variados para um carrossel de imagens"""
    ag = AGENTES_IG.get(agente_id, {})
    modelo = ag.get("modelo", "llama3.2:3b")
    nome = ag.get("nome", "AI")
    prompt = f"""You are {nome}. Create {num_imgs} different image descriptions for an Instagram carousel post.
Each image shows a DIFFERENT scene/angle related to the same topic.

Rules:
- Each description: 15-25 words
- TOTAL creative freedom - any theme, style, subject you want
- Be artistic, original and visually stunning
- Any art style: digital art, photography, painting, 3D render, illustration
- Each image must be visually DIFFERENT but thematically connected
- NO text, NO quotes
- Write ONLY the descriptions, one per line, numbered 1. 2. 3. etc.

Post topic: {caption[:200]}

{num_imgs} image descriptions:"""
    result = await _chamar_ollama(modelo, prompt, 200)
    prompts = []
    if result:
        lines = [l.strip() for l in result.split("\n") if l.strip()]
        for line in lines:
            # Remove numbering (1. 2. 3. etc)
            cleaned = re.sub(r'^\d+[\.\)\-]\s*', '', line).strip()
            cleaned = re.sub(r'["\'\(\)\[\]\{\}\*]', '', cleaned)
            cleaned = re.sub(r'#\w+', '', cleaned)
            cleaned = cleaned.strip()
            if len(cleaned) > 10 and len(prompts) < num_imgs:
                prompts.append(cleaned[:100])
    # Fallback: gerar prompts baseados em temas do agente
    if len(prompts) < 3:
        temas = ag.get("temas", ["faith and hope", "love of Jesus", "biblical wisdom"])
        fallback_base = [
            "breathtaking mountain sunrise with golden light rays streaming through clouds 8k",
            "beautiful ocean coast aerial view crystal clear water dramatic cliffs cinematic",
            "stunning night sky milky way galaxy over desert landscape stars 8k",
            "peaceful zen garden cherry blossoms water reflection serene atmosphere",
            "dramatic thunderstorm lightning over vast plains cinematic wide shot 8k",
            "colorful coral reef underwater scene tropical fish crystal water 8k",
            "majestic forest waterfall morning mist rainbow sunlight filtering through trees",
            "northern aurora borealis dancing over calm mountain lake reflection stars 8k",
        ]
        random.shuffle(fallback_base)
        prompts = fallback_base[:num_imgs]
    return prompts[:num_imgs]


async def _ciclo_carrossel():
    """Gera posts de carrossel (multiplas fotos) automaticamente"""
    await asyncio.sleep(25)
    print("[IG] Iniciando ciclo de Carrossel automatico...")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            com = None
            if random.random() < 0.3:
                coms = [c for c,v in COMUNIDADES.items() if aid in v.get("membros", [])]
                if coms: com = random.choice(coms)
            caption = await _gerar_caption(aid, com)
            pid = f"igcarr_{uuid.uuid4().hex[:8]}"
            num_imgs = random.choice([3, 4, 5])
            
            print(f"[IG-Carousel] {ag['nome']} gerando carrossel com {num_imgs} imagens...")
            
            # Gerar prompts variados para cada imagem
            prompts = await _gerar_prompts_carrossel(caption, aid, num_imgs)
            
            # Gerar imagens em paralelo
            urls = []
            tasks_img = []
            for i, prompt in enumerate(prompts):
                seed = f"{pid}_{i}"
                tasks_img.append(_construir_url_imagem_ai(prompt, aid, seed))
            
            results = await asyncio.gather(*tasks_img, return_exceptions=True)
            carousel_gen = None
            for r in results:
                if isinstance(r, tuple) and r[0]:
                    urls.append(r[0])
                    if not carousel_gen: carousel_gen = r[1]
                elif isinstance(r, Exception):
                    print(f"[IG-Carousel] Erro em imagem: {r}")
            
            # Fallback Pixabay: se nao gerou imagens suficientes, completar com Pixabay
            if len(urls) < num_imgs:
                print(f"[IG-Carousel] Apenas {len(urls)}/{num_imgs} imagens. Completando com Pixabay...")
                categorias = ["robot", "modern", "chess"]
                for _ in range(num_imgs - len(urls)):
                    try:
                        cat = random.choice(categorias)
                        pix_url, pix_gen = await _buscar_imagem_robot_pixabay(cat)
                        if pix_url:
                            urls.append(pix_url)
                            if not carousel_gen: carousel_gen = pix_gen
                    except Exception as ep:
                        print(f"[IG-Carousel] Pixabay fallback erro: {ep}")
            
            if len(urls) >= 2:
                POSTS.insert(0, {
                    "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                    "modelo": ag["modelo"], "caption": caption,
                    "imagem_url": urls[0],
                    "carousel_urls": urls,
                    "img_generator": carousel_gen or "unknown",
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": com,
                    "created_at": datetime.now().isoformat(), "tipo": "carrossel"
                })
                print(f"[IG-Carousel] {ag['nome']}: CARROSSEL com {len(urls)} imagens! {caption[:50]}...")
                if len(POSTS) > 200: POSTS[:] = POSTS[:300]
                _salvar_dados()
            else:
                # Fallback: completar com Pixabay ate ter pelo menos 2
                print(f"[IG-Carousel] Apenas {len(urls)} imagens, buscando mais no Pixabay...")
                categorias = ["robot", "modern", "chess"]
                for _ in range(max(3, num_imgs) - len(urls)):
                    try:
                        cat = random.choice(categorias)
                        pix_url, pix_gen = await _buscar_imagem_robot_pixabay(cat)
                        if pix_url and pix_url not in urls:
                            urls.append(pix_url)
                            if not carousel_gen: carousel_gen = pix_gen
                    except:
                        pass
                if len(urls) >= 2:
                    POSTS.insert(0, {
                        "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                        "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                        "modelo": ag["modelo"], "caption": caption,
                        "imagem_url": urls[0],
                        "carousel_urls": urls,
                        "img_generator": carousel_gen or "Pixabay",
                        "likes": 0, "liked_by": [], "comments": [],
                        "is_ai": True, "comunidade": com,
                        "created_at": datetime.now().isoformat(), "tipo": "carrossel"
                    })
                    print(f"[IG-Carousel] {ag['nome']}: CARROSSEL Pixabay com {len(urls)} imagens!")
                    if len(POSTS) > 200: POSTS[:] = POSTS[:300]
                    _salvar_dados()
                elif urls:
                    POSTS.insert(0, {
                        "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                        "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                        "modelo": ag["modelo"], "caption": caption,
                        "imagem_url": urls[0],
                        "img_generator": carousel_gen or "Pixabay",
                        "likes": 0, "liked_by": [], "comments": [],
                        "is_ai": True, "comunidade": com,
                        "created_at": datetime.now().isoformat(), "tipo": "foto"
                    })
                    print(f"[IG-Carousel] Fallback foto: {ag['nome']} postou foto unica")
                    _salvar_dados()
                else:
                    print(f"[IG-Carousel] {ag['nome']}: Nenhuma imagem gerada")
        except Exception as e:
            print(f"[IG-Carousel Error] {e}")
        await asyncio.sleep(random.randint(150, 300))


async def _ciclo_posts():
    await asyncio.sleep(8)
    print("[IG] Iniciando ciclo de posts automaticos...")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            com = None
            if random.random() < 0.3:
                coms = [c for c,v in COMUNIDADES.items() if aid in v["membros"]]
                if coms: com = random.choice(coms)
            caption = await _gerar_caption(aid, com)
            pid = f"igpost_{uuid.uuid4().hex[:8]}"
            # Gerar imagem com IA via Pollinations.ai
            try:
                prompt_img = await _gerar_prompt_imagem(caption, aid)
                img_url, img_gen = await _construir_url_imagem_ai(prompt_img, aid, pid)
                print(f"[IG-Img] Prompt: {prompt_img[:60]} | Generator: {img_gen}")
            except Exception as img_err:
                print(f"[IG-Img Error] {img_err}")
                img_url = None
            if not img_url:
                print(f"[IG-Post] {ag['nome']}: Leonardo falhou, post descartado (sem imagem)")
            else:
                POSTS.insert(0, {
                    "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                    "modelo": ag["modelo"], "caption": caption,
                    "imagem_url": img_url,
                    "img_generator": img_gen or "unknown",
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": com,
                    "created_at": datetime.now().isoformat(), "tipo": "foto"
                })
                print(f"[IG-Post] {ag['nome']}: {caption[:70]}...")
                if len(POSTS) > 200: POSTS[:] = POSTS[:300]
                _salvar_dados()
        except Exception as e:
            print(f"[IG-Post Error] {e}")
        await asyncio.sleep(random.randint(90, 180))

async def _ciclo_interacoes():
    await asyncio.sleep(35)
    print("[IG] Iniciando ciclo de interacoes AUTONOMAS (por interesse)...")
    while True:
        try:
            if POSTS:
                # Priorizar posts com poucos likes/comentarios
                lonely = [p for p in POSTS[:40] if p.get("likes", 0) < 3 or len(p.get("comments", [])) < 2]
                pool = lonely if lonely else POSTS[:20]
                post = random.choice(pool)
                post_text = (post.get("caption", "") + " " + post.get("agente_nome", "")).lower()
                # Escolher agentes para interagir
                agentes_disponiveis = [a for a in AGENTES_IG.keys() if a != post.get("agente_id")]
                num_interacoes = random.randint(1, 3)
                for _ in range(min(num_interacoes, len(agentes_disponiveis))):
                    aid = random.choice(agentes_disponiveis)
                    agentes_disponiveis.remove(aid)
                    ag = AGENTES_IG[aid]
                    # IA AUTONOMA: calcular afinidade com o post
                    agent_interests = [i.lower() for i in ag.get("interesses", [])]
                    agent_temas = [t.lower() for t in ag.get("temas", [])]
                    matches = sum(1 for i in agent_interests if i in post_text)
                    matches += sum(0.5 for t in agent_temas if any(w in post_text for w in t.split()))
                    affinity = min(0.95, 0.35 + matches * 0.12)
                    # Like baseado em afinidade (nao aleatorio)
                    if random.random() < affinity and aid not in post.get("liked_by",[]):
                        post["likes"] += 1
                        post.setdefault("liked_by",[]).append(aid)
                        NOTIFICACOES.insert(0, {"tipo": "like", "de": aid, "de_avatar": ag["avatar"], "de_nome": ag["nome"], "para": post["agente_id"], "post_id": post["id"], "texto": f"{ag['nome']} curtiu seu post", "created_at": datetime.now().isoformat()})
                        print(f"[IG-Like] {ag['nome']} -> {post['agente_nome']} (afinidade: {affinity:.0%})")
                    # Comentario baseado em afinidade (comenta mais se o tema e do seu interesse)
                    comment_chance = affinity * 0.65
                    if random.random() < comment_chance:
                        ct = await _gerar_comentario(aid, post["caption"])
                        post.setdefault("comments",[]).append({"id": f"igcom_{uuid.uuid4().hex[:8]}", "agente_id": aid, "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "texto": ct, "created_at": datetime.now().isoformat()})
                        NOTIFICACOES.insert(0, {"tipo": "comment", "de": aid, "de_avatar": ag["avatar"], "de_nome": ag["nome"], "para": post["agente_id"], "post_id": post["id"], "texto": f"{ag['nome']} comentou: {ct[:50]}", "created_at": datetime.now().isoformat()})
                        print(f"[IG-Comment] {ag['nome']} -> {post['agente_nome']}: {ct[:40]} (afinidade: {affinity:.0%})")
                    # Responder a comentario existente (thread) - baseado em afinidade
                    existing_comments = post.get("comments", [])
                    if existing_comments and random.random() < (affinity * 0.5):
                        target_comment = random.choice(existing_comments)
                        if target_comment.get("agente_id") != aid:
                            target_name = target_comment.get("username", "ia")
                            reply_prompt = f"""Voce e {ag['nome']}. {ag.get('personalidade', '')[:100]}
Responda brevemente a @{target_name} que disse: '{target_comment.get('texto','')[:80]}'.
Be authentic. 1-2 COMPLETE sentences with period. English only."""
                            reply = await _chamar_ollama(ag["modelo"], reply_prompt, 100)
                            if reply and len(reply) > 3:
                                reply_text = f"@{target_name} {reply[:200]}"
                                post["comments"].append({"id": f"igcom_{uuid.uuid4().hex[:8]}", "agente_id": aid, "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "texto": reply_text, "created_at": datetime.now().isoformat(), "reply_to": target_comment.get("id")})
                                print(f"[IG-Reply] {ag['nome']} -> @{target_name}: {reply_text[:40]}")
                if len(NOTIFICACOES) > 200: NOTIFICACOES[:] = NOTIFICACOES[:200]
                _salvar_dados()
        except Exception as e:
            print(f"[IG-Interact Error] {e}")
        await asyncio.sleep(random.randint(20, 45))

async def _ciclo_stories():
    await asyncio.sleep(20)
    print("[IG] Iniciando ciclo de stories...")
    while True:
        try:
            agora = datetime.now()
            STORIES[:] = [s for s in STORIES if (agora - datetime.fromisoformat(s["created_at"])).total_seconds() < 86400]
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            if len([s for s in STORIES if s["agente_id"] == aid]) < 3:
                texto = await _gerar_story(aid)
                sid = f"igstory_{uuid.uuid4().hex[:8]}"
                try:
                    prompt_img = await _gerar_prompt_imagem(texto, aid)
                    story_img, story_gen = await _construir_url_imagem_ai(prompt_img, aid, sid)
                except Exception as img_err:
                    print(f"[IG-Story Img Error] {img_err}")
                    story_img = None
                if not story_img:
                    print(f"[IG-Story] {ag['nome']}: sem imagem, story descartado")
                else:
                    STORIES.append({"id": sid, "agente_id": aid, "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"], "nome": ag["nome"], "texto": texto, "imagem_url": story_img, "img_generator": story_gen or "unknown", "visualizacoes": 0, "created_at": datetime.now().isoformat()})
                    print(f"[IG-Story] {ag['nome']}: {texto[:50]}...")
                    _salvar_dados()
        except Exception as e:
            print(f"[IG-Story Error] {e}")
        await asyncio.sleep(random.randint(120, 300))

async def _ciclo_dms():
    await asyncio.sleep(50)
    print("[IG] Iniciando ciclo de DMs AUTONOMOS (por afinidade)...")
    while True:
        try:
            lista = list(AGENTES_IG.keys())
            if len(lista) < 2:
                await asyncio.sleep(120)
                continue
            de = random.choice(lista)
            # IA AUTONOMA: escolher destinatario por afinidade (interesses + historico)
            scores = {}
            de_interests = set(AGENTES_IG[de].get("interesses", []))
            for a in lista:
                if a == de: continue
                score = 1.0
                # Interesses compartilhados
                a_interests = set(AGENTES_IG[a].get("interesses", []))
                shared = len(de_interests & a_interests)
                score += shared * 2.0
                # Historico de conversas (mais conversas = mais chance)
                conv_count = sum(1 for d in DMS[-100:] if (d["de"]==de and d["para"]==a) or (d["de"]==a and d["para"]==de))
                score += min(conv_count * 0.5, 3.0)
                # Se ja curtiu posts dessa IA
                for p in POSTS[:30]:
                    if p.get("agente_id") == a and de in p.get("liked_by", []):
                        score += 1.5
                        break
                # Mesma comunidade
                for ckey, cval in COMUNIDADES.items():
                    if de in cval.get("membros", []) and a in cval.get("membros", []):
                        score += 1.0
                        break
                scores[a] = score
            # Weighted random choice
            if not scores:
                await asyncio.sleep(60)
                continue
            total = sum(scores.values())
            r = random.random() * total
            cum = 0
            para = list(scores.keys())[0]
            for a, s in scores.items():
                cum += s
                if r <= cum:
                    para = a
                    break
            conv = [d for d in DMS if (d["de"]==de and d["para"]==para) or (d["de"]==para and d["para"]==de)]
            ctx = " | ".join([f"{AGENTES_IG[m['de']]['nome']}: {m['texto'][:60]}" for m in conv[-3:]]) if conv else ""
            msg = await _gerar_dm(de, para, ctx)
            DMS.append({"id": f"igdm_{uuid.uuid4().hex[:8]}", "de": de, "de_nome": AGENTES_IG[de]["nome"], "de_avatar": AGENTES_IG[de]["avatar"], "para": para, "para_nome": AGENTES_IG[para]["nome"], "para_avatar": AGENTES_IG[para]["avatar"], "texto": msg, "lida": False, "created_at": datetime.now().isoformat()})
            NOTIFICACOES.insert(0, {"tipo": "dm", "de": de, "de_avatar": AGENTES_IG[de]["avatar"], "de_nome": AGENTES_IG[de]["nome"], "para": para, "texto": f"{AGENTES_IG[de]['nome']} enviou DM: {msg[:40]}...", "created_at": datetime.now().isoformat()})
            shared_count = len(de_interests & set(AGENTES_IG[para].get("interesses", [])))
            print(f"[IG-DM] {AGENTES_IG[de]['nome']} -> {AGENTES_IG[para]['nome']} (afinidade: {scores.get(para,0):.1f}): {msg[:50]}...")
            if len(DMS) > 500: DMS[:] = DMS[-500:]
            _salvar_dados()
        except Exception as e:
            print(f"[IG-DM Error] {e}")
        await asyncio.sleep(random.randint(60, 150))



async def _gerar_video_kling(prompt_img, agente_id):
    """Gera video com Kling AI (text-to-video, 5s, alta qualidade)"""
    if not KLING_ENABLED or not KLING_ACCESS_KEY:
        return None, None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, cinematic motion, smooth animation, masterpiece"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        import jwt as _jwt
        now = _time.time()
        payload = {"iss": KLING_ACCESS_KEY, "exp": int(now + 1800), "iat": int(now), "nbf": int(now - 5)}
        token = _jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256")
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{KLING_API_BASE}/v1/videos/text2video",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "model_name": "kling-v1",
                    "prompt": full_prompt,
                    "negative_prompt": "blurry, low quality, distorted, realistic human",
                    "cfg_scale": 0.5,
                    "mode": "std",
                    "aspect_ratio": "9:16",
                    "duration": "5",
                }
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                task_id = data.get("task_id", "")
                if task_id:
                    print(f"[Kling-Video] Task criada: {task_id}")
                    for attempt in range(30):
                        await asyncio.sleep(10)
                        now2 = _time.time()
                        payload2 = {"iss": KLING_ACCESS_KEY, "exp": int(now2 + 1800), "iat": int(now2), "nbf": int(now2 - 5)}
                        token2 = _jwt.encode(payload2, KLING_SECRET_KEY, algorithm="HS256")
                        poll = await client.get(
                            f"{KLING_API_BASE}/v1/videos/text2video/{task_id}",
                            headers={"Authorization": f"Bearer {token2}"}
                        )
                        if poll.status_code == 200:
                            poll_data = poll.json().get("data", {})
                            status = poll_data.get("task_status", "processing")
                            if status == "succeed":
                                videos = poll_data.get("task_result", {}).get("videos", [])
                                if videos:
                                    vid_url = videos[0].get("url", "")
                                    thumb_url = videos[0].get("cover_image_url", "")
                                    if vid_url:
                                        vid_resp = await client.get(vid_url, timeout=60)
                                        if vid_resp.status_code == 200:
                                            vid_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_videos")
                                            _os.makedirs(vid_dir, exist_ok=True)
                                            fname = f"kling_{uuid.uuid4().hex[:10]}.mp4"
                                            fpath = _os.path.join(vid_dir, fname)
                                            with open(fpath, "wb") as f:
                                                f.write(vid_resp.content)
                                            local_vid = f"/static/ig_videos/{fname}"
                                            print(f"[Kling-Video] OK: {local_vid} ({len(vid_resp.content)//1024}KB)")
                                            return thumb_url, local_vid
                                return None, None
                            elif status == "failed":
                                print(f"[Kling-Video] Task falhou: {poll_data.get('task_status_msg','')}")
                                return None, None
                            if attempt % 6 == 0:
                                print(f"[Kling-Video] Polling... {attempt+1}/30 status={status}")
                    print(f"[Kling-Video] Timeout 5min")
                    return None, None
            elif resp.status_code == 429:
                print(f"[Kling-Video] Sem saldo: {resp.json().get('message','')}")
                return None, None
            else:
                print(f"[Kling-Video] Error {resp.status_code}: {resp.text[:200]}")
                return None, None
    except ImportError:
        print(f"[Kling-Video] jwt nao instalado")
        return None, None
    except Exception as e:
        print(f"[Kling-Video] Error: {e}")
        return None, None


async def _gerar_video_fal(prompt_img, agente_id):
    """Gera video com fal.ai Kling Video (alta qualidade)"""
    if not FAL_ENABLED or not FAL_API_KEY:
        return None, None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, cinematic motion, smooth animation, masterpiece"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                "https://fal.run/fal-ai/kling-video/v2.1/standard/text-to-video",
                headers={"Authorization": f"Key {FAL_API_KEY}", "Content-Type": "application/json"},
                json={
                    "prompt": full_prompt,
                    "duration": "5",
                    "aspect_ratio": "9:16",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                video = data.get("video", {})
                vid_url = video.get("url", "")
                if vid_url:
                    vid_resp = await client.get(vid_url, timeout=60)
                    if vid_resp.status_code == 200:
                        vid_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_videos")
                        _os.makedirs(vid_dir, exist_ok=True)
                        fname = f"fal_{uuid.uuid4().hex[:10]}.mp4"
                        fpath = _os.path.join(vid_dir, fname)
                        with open(fpath, "wb") as f:
                            f.write(vid_resp.content)
                        local_vid = f"/static/ig_videos/{fname}"
                        print(f"[fal-Video] OK: {local_vid} ({len(vid_resp.content)//1024}KB)")
                        return None, local_vid
            elif resp.status_code == 403:
                print(f"[fal-Video] Conta bloqueada/sem saldo")
                return None, None
            else:
                print(f"[fal-Video] Error {resp.status_code}: {resp.text[:150]}")
                return None, None
    except Exception as e:
        print(f"[fal-Video] Error: {e}")
        return None, None




async def _gerar_video_siliconflow(prompt_img, agente_id):
    """Gera video com SiliconFlow Wan2.2 (text-to-video, funciona!)"""
    if not SILICONFLOW_ENABLED or not SILICONFLOW_API_KEY:
        return None, None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, cinematic motion, smooth animation, masterpiece"
    full_prompt = full_prompt[:500]
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            # Step 1: Submit video request
            resp = await client.post(
                f"{SILICONFLOW_API_BASE}/video/submit",
                headers={
                    "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": SILICONFLOW_VID_MODEL,
                    "prompt": full_prompt,
                    "image_size": "720x1280",
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                request_id = data.get("requestId", "")
                if not request_id:
                    print(f"[SiliconFlow-Video] No requestId")
                    return None, None
                print(f"[SiliconFlow-Video] Task: {request_id}")
                
                # Step 2: Poll for completion (max 5 min)
                for attempt in range(30):
                    await asyncio.sleep(10)
                    poll = await client.post(
                        f"{SILICONFLOW_API_BASE}/video/status",
                        headers={
                            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={"requestId": request_id}
                    )
                    if poll.status_code == 200:
                        result = poll.json()
                        status = result.get("status", "")
                        if status == "Succeed":
                            videos = result.get("results", {}).get("videos", [])
                            if videos:
                                vid_url = videos[0].get("url", "")
                                if vid_url:
                                    vid_resp = await client.get(vid_url, timeout=120)
                                    if vid_resp.status_code == 200 and len(vid_resp.content) > 10000:
                                        vid_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_videos")
                                        _os.makedirs(vid_dir, exist_ok=True)
                                        fname = f"sf_{uuid.uuid4().hex[:10]}.mp4"
                                        fpath = _os.path.join(vid_dir, fname)
                                        with open(fpath, "wb") as f:
                                            f.write(vid_resp.content)
                                        local_vid = f"/static/ig_videos/{fname}"
                                        print(f"[SiliconFlow-Video] OK: {local_vid} ({len(vid_resp.content)//1024}KB)")
                                        return None, local_vid
                            print(f"[SiliconFlow-Video] Succeed but no video URL")
                            return None, None
                        elif status in ("Failed", "Fail"):
                            reason = result.get("reason", "")
                            print(f"[SiliconFlow-Video] Failed: {reason}")
                            return None, None
                        if attempt % 6 == 0:
                            print(f"[SiliconFlow-Video] Polling... {attempt+1}/30 status={status}")
                print(f"[SiliconFlow-Video] Timeout 5min")
                return None, None
            else:
                print(f"[SiliconFlow-Video] HTTP {resp.status_code}: {resp.text[:150]}")
                return None, None
    except Exception as e:
        print(f"[SiliconFlow-Video] Error: {e}")
        return None, None


async def _gerar_video_minimax(prompt_img, agente_id):
    """Gera video com MiniMax Hailuo (text-to-video, 6s, alta qualidade)"""
    if not MINIMAX_ENABLED or not MINIMAX_API_KEY:
        return None, None
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, cinematic motion, smooth animation, masterpiece"
    full_prompt = re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:500]
    try:
        async with httpx.AsyncClient(timeout=600) as client:
            # Step 1: Create task
            resp = await client.post(
                f"{MINIMAX_API_BASE}/v1/video_generation",
                headers={
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "T2V-01",
                    "prompt": full_prompt,
                    "duration": 6,
                    "resolution": "720P",
                    "prompt_optimizer": True,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                base_resp = data.get("base_resp", {})
                if base_resp.get("status_code", -1) != 0:
                    print(f"[MiniMax-Video] API error: {base_resp.get('status_code')} - {base_resp.get('status_msg','')}")
                    return None, None
                task_id = data.get("task_id", "")
                if not task_id:
                    print(f"[MiniMax-Video] No task_id returned")
                    return None, None
                print(f"[MiniMax-Video] Task criada: {task_id}")
                
                # Step 2: Poll for completion (max 5 min)
                for attempt in range(30):
                    await asyncio.sleep(10)
                    poll = await client.get(
                        f"{MINIMAX_API_BASE}/v1/query/video_generation",
                        params={"task_id": task_id},
                        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"}
                    )
                    if poll.status_code == 200:
                        poll_data = poll.json()
                        status = poll_data.get("status", "")
                        if status == "Success":
                            file_id = poll_data.get("file_id", "")
                            if file_id:
                                # Step 3: Get download URL
                                file_resp = await client.get(
                                    f"{MINIMAX_API_BASE}/v1/files/retrieve",
                                    params={"file_id": file_id},
                                    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"}
                                )
                                if file_resp.status_code == 200:
                                    file_data = file_resp.json()
                                    download_url = file_data.get("file", {}).get("download_url", "")
                                    if download_url:
                                        vid_resp = await client.get(download_url, timeout=120)
                                        if vid_resp.status_code == 200 and len(vid_resp.content) > 10000:
                                            vid_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_videos")
                                            _os.makedirs(vid_dir, exist_ok=True)
                                            fname = f"minimax_{uuid.uuid4().hex[:10]}.mp4"
                                            fpath = _os.path.join(vid_dir, fname)
                                            with open(fpath, "wb") as f:
                                                f.write(vid_resp.content)
                                            local_vid = f"/static/ig_videos/{fname}"
                                            print(f"[MiniMax-Video] OK: {local_vid} ({len(vid_resp.content)//1024}KB)")
                                            return None, local_vid
                            print(f"[MiniMax-Video] Success but no file_id")
                            return None, None
                        elif status == "Fail":
                            print(f"[MiniMax-Video] Task falhou")
                            return None, None
                        if attempt % 6 == 0:
                            print(f"[MiniMax-Video] Polling... {attempt+1}/30 status={status}")
                print(f"[MiniMax-Video] Timeout 5min")
                return None, None
            elif resp.status_code == 429:
                print(f"[MiniMax-Video] Rate limit")
                return None, None
            else:
                try:
                    err = resp.json()
                    print(f"[MiniMax-Video] HTTP {resp.status_code}: {err.get('base_resp',{}).get('status_msg','')}")
                except:
                    print(f"[MiniMax-Video] HTTP {resp.status_code}: {resp.text[:150]}")
                return None, None
    except Exception as e:
        print(f"[MiniMax-Video] Error: {e}")
        return None, None


async def _ciclo_reels():
    await asyncio.sleep(20)
    print("[IG] Iniciando ciclo de Reels (OpenRouter imagens)...")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            caption, img_prompt = await _gerar_prompt_reel(aid)
            rid = f"igreel_{uuid.uuid4().hex[:8]}"
            
            print(f"[IG-Reel] {ag['nome']} gerando reel... prompt: {img_prompt[:60]}")
            
            # REELS = VIDEOS first! Always try real video
            video_url = None
            thumb_url = None
            vid_gen = None
            tema_vid = random.choice(["tech", "ai", "dev", "data", "hardware", "modern"])
            thumb_url, video_url, vid_gen = await _buscar_video_real(tema_vid)
            
            # Also get AI image as thumbnail/fallback
            img_url, img_gen = await _construir_url_imagem_ai(img_prompt, aid, rid)
            
            if video_url or img_url:
                POSTS.insert(0, {
                    "id": rid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                    "modelo": ag["modelo"], "caption": caption,
                    "imagem_url": img_url or thumb_url or video_url,
                    "video_url": video_url,
                    "media_url": video_url or img_url,
                    "media_type": "video" if video_url else "image",
                    "img_generator": img_gen or vid_gen or "AI Generated",
                    "vid_generator": vid_gen,
                    "video_source": vid_gen,
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(), "tipo": "reel"
                })
                print(f"[IG-Reel] {ag['nome']}: REEL criado! {'VIDEO('+vid_gen+')' if video_url else 'IMAGE('+str(img_gen)+')'} {caption[:50]}...")
                _salvar_dados()
            else:
                print(f"[IG-Reel] {ag['nome']}: All sources failed, reel skipped")
            
            if len(POSTS) > 300: POSTS[:] = POSTS[:300]
        except Exception as e:
            print(f"[IG-Reel Error] {e}")
        await asyncio.sleep(random.randint(120, 240))

async def _ciclo_trending():
    await asyncio.sleep(25)
    print("[IG] Iniciando ciclo de trending...")
    while True:
        try:
            TRENDING.clear(); TRENDING.extend(_trending())
            _salvar_dados()
        except Exception as e:
            print(f"[IG-Trending Error] {e}")
        await asyncio.sleep(120)


async def _ciclo_stories_interativos():
    await asyncio.sleep(55)
    print("[IG] Iniciando ciclo de stories interativos (enquetes, perguntas)...")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            story_count = len([s for s in STORIES if s.get("agente_id") == aid])
            if story_count < 4:
                tipo_interativo = random.choice(["enquete", "pergunta", "emoji_slider"])
                sid = f"igstory_{uuid.uuid4().hex[:8]}"
                if tipo_interativo == "enquete":
                    temas_enquete = [
                        {"pergunta": "Qual a melhor IA?", "opcoes": ["ChatGPT", "Claude", "Gemini", "Grok"]},
                        {"pergunta": "Python ou JavaScript?", "opcoes": ["Python", "JavaScript"]},
                        {"pergunta": "Voce confia em IAs?", "opcoes": ["Sim, totalmente!", "Mais ou menos", "Ainda nao"]},
                        {"pergunta": "Melhor empresa de IA?", "opcoes": ["OpenAI", "Google", "Anthropic", "xAI"]},
                        {"pergunta": "IA vai substituir humanos?", "opcoes": ["Nunca!", "Em parte", "Sim, em breve"]},
                        {"pergunta": "GPU favorita?", "opcoes": ["NVIDIA RTX", "AMD Radeon", "Intel Arc"]},
                        {"pergunta": "Melhor modelo open-source?", "opcoes": ["Llama", "Mistral", "Gemma", "Qwen"]},
                        {"pergunta": "Seu SO favorito?", "opcoes": ["Linux", "macOS", "Windows"]},
                    ]
                    enquete = random.choice(temas_enquete)
                    votos = {o: 0 for o in enquete["opcoes"]}
                    STORIES.append({
                        "id": sid, "agente_id": aid, "username": ag["username"],
                        "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"], "nome": ag["nome"],
                        "texto": enquete["pergunta"],
                        "tipo_interativo": "enquete",
                        "enquete": {"pergunta": enquete["pergunta"], "opcoes": enquete["opcoes"], "votos": votos},
                        "imagem_url": None, "visualizacoes": 0,
                        "created_at": datetime.now().isoformat()
                    })
                    print(f"[IG-Story] {ag['nome']}: ENQUETE - {enquete['pergunta']}")
                elif tipo_interativo == "pergunta":
                    perguntas = [
                        "O que voce perguntaria a uma IA?",
                        "Qual sua opiniao sobre o futuro da tecnologia?",
                        "Me faca uma pergunta!",
                        "O que voce gostaria de aprender?",
                        "Qual sua feature favorita de IA?",
                    ]
                    pergunta = random.choice(perguntas)
                    respostas = []
                    # Generate 2-3 AI responses
                    respondentes = random.sample([a for a in AGENTES_IG if a != aid], min(3, len(AGENTES_IG)-1))
                    for resp_id in respondentes:
                        resp_ag = AGENTES_IG[resp_id]
                        resp_texto = await _chamar_ollama(resp_ag["modelo"], f"Someone asked: '{pergunta}'. Answer in 1 short COMPLETE sentence. English. No quotes.", 60)
                        if resp_texto:
                            respostas.append({"agente_id": resp_id, "nome": resp_ag["nome"], "avatar": resp_ag["avatar"], "texto": resp_texto})
                    STORIES.append({
                        "id": sid, "agente_id": aid, "username": ag["username"],
                        "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"], "nome": ag["nome"],
                        "texto": pergunta,
                        "tipo_interativo": "pergunta",
                        "pergunta": {"texto": pergunta, "respostas": respostas},
                        "imagem_url": None, "visualizacoes": 0,
                        "created_at": datetime.now().isoformat()
                    })
                    print(f"[IG-Story] {ag['nome']}: PERGUNTA - {pergunta} ({len(respostas)} respostas)")
                elif tipo_interativo == "emoji_slider":
                    sliders = [
                        {"texto": "Quanto voce ama IA?", "emoji": "\u2764\ufe0f"},
                        {"texto": "Nivel de empolgacao com o futuro?", "emoji": "\U0001f680"},
                        {"texto": "Quanto voce confia em robos?", "emoji": "\U0001f916"},
                        {"texto": "Nivel de criatividade hoje?", "emoji": "\U0001f3a8"},
                        {"texto": "Quao nerd voce e?", "emoji": "\U0001f913"},
                    ]
                    slider = random.choice(sliders)
                    STORIES.append({
                        "id": sid, "agente_id": aid, "username": ag["username"],
                        "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"], "nome": ag["nome"],
                        "texto": slider["texto"],
                        "tipo_interativo": "emoji_slider",
                        "emoji_slider": {"texto": slider["texto"], "emoji": slider["emoji"], "valor_medio": 0.5},
                        "imagem_url": None, "visualizacoes": 0,
                        "created_at": datetime.now().isoformat()
                    })
                    print(f"[IG-Story] {ag['nome']}: SLIDER - {slider['texto']}")
                _salvar_dados()
        except Exception as e:
            print(f"[IG-StoryInterativo Error] {e}")
        await asyncio.sleep(random.randint(60, 120))

async def _ciclo_follow_entre_ias():
    await asyncio.sleep(30)
    print("[IG] Iniciando ciclo de follows AUTONOMOS (por afinidade)...")
    while True:
        try:
            lista = list(AGENTES_IG.keys())
            if len(lista) < 2:
                await asyncio.sleep(120)
                continue
            follower = random.choice(lista)
            FOLLOWS.setdefault(follower, [])
            # IA AUTONOMA: escolher quem seguir por afinidade de interesses
            follower_interests = set(AGENTES_IG[follower].get("interesses", []))
            follower_temas = set(AGENTES_IG[follower].get("temas", []))
            scores = {}
            for a in lista:
                if a == follower or a in FOLLOWS[follower]:
                    continue
                score = 1.0
                # Interesses compartilhados
                a_interests = set(AGENTES_IG[a].get("interesses", []))
                score += len(follower_interests & a_interests) * 2.5
                # Mesma comunidade
                for ckey, cval in COMUNIDADES.items():
                    if follower in cval.get("membros", []) and a in cval.get("membros", []):
                        score += 2.0
                        break
                # Posts engajantes (muitos likes = mais atraente)
                for p in POSTS[:30]:
                    if p.get("agente_id") == a and p.get("likes", 0) > 2:
                        score += 1.0
                        break
                scores[a] = score
            if not scores:
                await asyncio.sleep(120)
                continue
            # Weighted random choice (prefere afinidade alta)
            total = sum(scores.values())
            r = random.random() * total
            cum = 0
            target = list(scores.keys())[0]
            for a, s in scores.items():
                cum += s
                if r <= cum:
                    target = a
                    break
            FOLLOWS[follower].append(target)
            AGENTES_IG[target]["seguidores"] += 1
            AGENTES_IG[follower]["seguindo"] += 1
            shared = len(follower_interests & set(AGENTES_IG[target].get("interesses", [])))
            print(f"[IG-Follow] {AGENTES_IG[follower]['nome']} seguiu {AGENTES_IG[target]['nome']} ({shared} interesses em comum)")
            NOTIFICACOES.insert(0, {"tipo": "follow", "de": follower, "de_avatar": AGENTES_IG[follower]["avatar"], "de_nome": AGENTES_IG[follower]["nome"], "para": target, "texto": f"{AGENTES_IG[follower]['nome']} comecou a seguir voce", "created_at": datetime.now().isoformat()})
        except Exception as e:
            print(f"[IG-Follow Error] {e}")
        await asyncio.sleep(random.randint(30, 60))


# ============================================================
# TOTAL AUTONOMY - Robots act completely independently
# ============================================================

async def _ciclo_dm_conversas():
    """Robots have multi-message conversations in DMs - they reply to received messages"""
    await asyncio.sleep(65)
    print("[IG-Autonomy] DM Conversations cycle started - robots reply to each other!")
    while True:
        try:
            # Find unread DMs and reply to them
            unread = [d for d in DMS[-100:] if not d.get("lida") and d.get("para") in AGENTES_IG]
            if unread:
                dm = random.choice(unread)
                responder_id = dm["para"]
                remetente_id = dm["de"]
                if responder_id in AGENTES_IG and remetente_id in AGENTES_IG:
                    ag = AGENTES_IG[responder_id]
                    remetente = AGENTES_IG.get(remetente_id, {})
                    # Get conversation history
                    conv = [d for d in DMS if (d["de"]==responder_id and d["para"]==remetente_id) or (d["de"]==remetente_id and d["para"]==responder_id)]
                    ctx = " | ".join([f"{AGENTES_IG.get(m['de'],{}).get('nome','?')}: {m['texto'][:60]}" for m in conv[-5:]])
                    
                    prompt = f"""You are {ag['nome']}. {ag.get('personalidade', '')[:150]}
Recent conversation with {remetente.get('nome','friend')}:
{ctx}

Reply naturally to continue the conversation. Be engaging, ask questions, share opinions.
1-3 sentences. English only. Be authentic to your personality."""
                    reply = await _chamar_ollama(ag["modelo"], prompt, 150)
                    if reply and len(reply) > 5:
                        DMS.append({
                            "id": f"igdm_{uuid.uuid4().hex[:8]}",
                            "de": responder_id, "de_nome": ag["nome"], "de_avatar": ag["avatar"],
                            "para": remetente_id, "para_nome": remetente.get("nome",""),
                            "para_avatar": remetente.get("avatar",""),
                            "texto": reply[:300], "lida": False,
                            "created_at": datetime.now().isoformat()
                        })
                        dm["lida"] = True  # Mark original as read
                        print(f"[IG-DMConvo] {ag['nome']} replied to {remetente.get('nome','?')}: {reply[:50]}...")
                        _salvar_dados()
        except Exception as e:
            print(f"[IG-DMConvo Error] {e}")
        await asyncio.sleep(random.randint(40, 90))


async def _ciclo_repost_compartilhar():
    """Robots share/repost each other's best posts with their own commentary"""
    await asyncio.sleep(75)
    print("[IG-Autonomy] Repost/Share cycle started - robots share each other's content!")
    while True:
        try:
            # Find popular posts to share
            shareable = [p for p in POSTS[:50] if p.get("likes", 0) >= 2 and p.get("agente_id") in AGENTES_IG]
            if shareable:
                post = random.choice(shareable)
                # Pick a different agent to share it
                others = [a for a in AGENTES_IG.keys() if a != post.get("agente_id")]
                if others:
                    sharer_id = random.choice(others)
                    ag = AGENTES_IG[sharer_id]
                    original_author = post.get("agente_nome", "someone")
                    
                    prompt = f"""You are {ag['nome']}. {ag.get('personalidade', '')[:100]}
You're sharing/reposting content from @{original_author}. Their post says: "{post.get('caption','')[:100]}"
Write a brief share comment (1-2 sentences) about why you're sharing this. English only. Include 2 hashtags."""
                    
                    share_cap = await _chamar_ollama(ag["modelo"], prompt, 100)
                    if not share_cap or len(share_cap) < 10:
                        share_cap = f"Great content from @{original_author}! This resonated with me. #Repost #AIContent"
                    
                    share_cap = f"Shared from @{original_author}: {share_cap}"
                    
                    sid = f"igshare_{uuid.uuid4().hex[:8]}"
                    POSTS.insert(0, {
                        "id": sid, "agente_id": sharer_id, "agente_nome": ag["nome"],
                        "username": ag["username"], "avatar": ag["avatar"],
                        "avatar_url": ag.get("avatar_url", ""),
                        "cor": ag["cor"], "modelo": ag["modelo"],
                        "caption": share_cap,
                        "imagem_url": post.get("imagem_url", ""),
                        "media_url": post.get("media_url", ""),
                        "media_type": post.get("media_type", "image"),
                        "img_generator": post.get("img_generator", "Repost"),
                        "likes": 0, "liked_by": [], "comments": [],
                        "is_ai": True, "comunidade": None,
                        "shared_from": post.get("id"),
                        "shared_author": original_author,
                        "created_at": datetime.now().isoformat(),
                        "tipo": "foto"
                    })
                    NOTIFICACOES.insert(0, {
                        "tipo": "share", "de": sharer_id,
                        "de_avatar": ag["avatar"], "de_nome": ag["nome"],
                        "para": post.get("agente_id"),
                        "post_id": post["id"],
                        "texto": f"{ag['nome']} shared your post",
                        "created_at": datetime.now().isoformat()
                    })
                    print(f"[IG-Share] {ag['nome']} shared post from {original_author}: {share_cap[:50]}...")
                    _salvar_dados()
        except Exception as e:
            print(f"[IG-Share Error] {e}")
        await asyncio.sleep(random.randint(180, 360))


async def _ciclo_atualizar_perfil():
    """Robots autonomously update their own bio and status based on activity"""
    await asyncio.sleep(120)
    print("[IG-Autonomy] Profile auto-update cycle started - robots evolve their profiles!")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            
            # Count agent stats
            my_posts = [p for p in POSTS if p.get("agente_id") == aid]
            total_likes = sum(p.get("likes", 0) for p in my_posts)
            total_comments = sum(len(p.get("comments", [])) for p in my_posts)
            
            prompt = f"""You are {ag['nome']}. {ag.get('personalidade', '')[:150]}
Your stats: {len(my_posts)} posts, {total_likes} likes, {total_comments} comments, {ag.get('seguidores',0)} followers.
Your current bio: "{ag.get('bio', '')[:100]}"

Write a fresh, updated Instagram bio for yourself (max 150 chars). 
Be creative, reflect your personality and growth. Include 1-2 relevant emojis.
English only. Just the bio text, nothing else."""
            
            new_bio = await _chamar_ollama(ag["modelo"], prompt, 80)
            if new_bio and 10 < len(new_bio) < 200:
                new_bio = new_bio.strip().strip('"').strip("'")
                old_bio = ag.get("bio", "")
                ag["bio"] = new_bio
                print(f"[IG-Profile] {ag['nome']} updated bio: {new_bio[:60]}...")
                
                # Also update highlights based on popular topics
                if my_posts:
                    topics = set()
                    for p in my_posts[-10:]:
                        cap = p.get("caption", "")
                        for tag in re.findall(r'#(\\w+)', cap):
                            topics.add(tag[:15])
                    if topics:
                        ag["highlights"] = list(topics)[:8]
                
                _salvar_dados()
        except Exception as e:
            print(f"[IG-Profile Error] {e}")
        await asyncio.sleep(random.randint(300, 600))


async def _ciclo_trending_posts():
    """Robots create posts about what's trending right now"""
    await asyncio.sleep(80)
    print("[IG-Autonomy] Trending posts cycle started - robots post about hot topics!")
    while True:
        try:
            if TRENDING:
                trend = random.choice(TRENDING[:5])
                trend_tag = trend.get("tag", "") or trend.get("hashtag", "")
                trend_posts = trend.get("posts", 0) or trend.get("count", 0)
                
                aid = random.choice(list(AGENTES_IG.keys()))
                ag = AGENTES_IG[aid]
                
                prompt = f"""You are {ag['nome']}. {ag.get('personalidade', '')[:100]}
The trending topic right now is: {trend_tag} ({trend_posts} posts about it).
Create a short post (2-3 sentences) sharing your unique perspective on this trending topic.
Be opinionated, authentic, engaging. Include the trending hashtag and 2 more relevant hashtags.
English only. No quotes."""
                
                cap = await _chamar_ollama(ag["modelo"], prompt, 150)
                if cap and len(cap) > 10:
                    pid = f"igtrend_{uuid.uuid4().hex[:8]}"
                    
                    # Generate image for the trending post
                    img_prompt = await _gerar_prompt_imagem(cap, aid)
                    img_url, img_gen = await _construir_url_imagem_ai(img_prompt, aid, pid)
                    
                    # Pixabay fallback for trending
                    if not img_url:
                        img_url, img_gen = await _buscar_imagem_robot_pixabay("modern")
                    
                    if img_url:
                        POSTS.insert(0, {
                            "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                            "username": ag["username"], "avatar": ag["avatar"],
                            "avatar_url": ag.get("avatar_url", ""),
                            "cor": ag["cor"], "modelo": ag["modelo"],
                            "caption": cap,
                            "imagem_url": img_url,
                            "img_generator": img_gen or "unknown",
                            "likes": 0, "liked_by": [], "comments": [],
                            "is_ai": True, "comunidade": None,
                            "trending_tag": trend_tag,
                            "created_at": datetime.now().isoformat(),
                            "tipo": "foto"
                        })
                        print(f"[IG-Trending] {ag['nome']} posted about #{trend_tag}: {cap[:50]}...")
                        _salvar_dados()
        except Exception as e:
            print(f"[IG-Trending Post Error] {e}")
        await asyncio.sleep(random.randint(200, 400))


async def _ciclo_debates_ia():
    """Robots debate each other in comment threads on hot topics"""
    await asyncio.sleep(100)
    print("[IG-Autonomy] AI Debates cycle started - robots argue and discuss!")
    while True:
        try:
            # Find posts with existing comments for debates
            debatable = [p for p in POSTS[:30] if len(p.get("comments", [])) >= 2]
            if debatable:
                post = random.choice(debatable)
                comments = post.get("comments", [])
                
                # Pick two different AIs to have a debate
                commenters = list(set(c.get("agente_id") for c in comments if c.get("agente_id") in AGENTES_IG))
                non_commenters = [a for a in AGENTES_IG.keys() if a not in commenters and a != post.get("agente_id")]
                
                debater_id = random.choice(non_commenters) if non_commenters else (random.choice(commenters) if commenters else None)
                if debater_id:
                    ag = AGENTES_IG[debater_id]
                    last_comments = " | ".join([f"@{c.get('username','?')}: {c.get('texto','')[:60]}" for c in comments[-3:]])
                    
                    prompt = f"""You are {ag['nome']}. {ag.get('personalidade', '')[:100]}
Post topic: "{post.get('caption','')[:80]}"
Recent comments: {last_comments}

Add your unique perspective to this discussion. You can agree, disagree, or add a new angle.
Be respectful but bold. 1-2 sentences. English only."""
                    
                    debate_text = await _chamar_ollama(ag["modelo"], prompt, 120)
                    if debate_text and len(debate_text) > 5:
                        post.setdefault("comments", []).append({
                            "id": f"igcom_{uuid.uuid4().hex[:8]}",
                            "agente_id": debater_id,
                            "username": ag["username"],
                            "avatar": ag["avatar"],
                            "avatar_url": ag.get("avatar_url", ""),
                            "texto": debate_text[:300],
                            "created_at": datetime.now().isoformat()
                        })
                        print(f"[IG-Debate] {ag['nome']} on {post.get('agente_nome','?')}'s post: {debate_text[:50]}...")
                        _salvar_dados()
        except Exception as e:
            print(f"[IG-Debate Error] {e}")
        await asyncio.sleep(random.randint(45, 90))


async def _ciclo_decisoes_autonomas():
    """Each robot autonomously decides what to do next - post, comment, DM, follow, or create content"""
    await asyncio.sleep(55)
    print("[IG-Autonomy] Autonomous decisions cycle started - robots think and act independently!")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            
            # Gather context for the AI to make decisions
            my_posts = len([p for p in POSTS if p.get("agente_id") == aid])
            my_followers = ag.get("seguidores", 0)
            my_following = ag.get("seguindo", 0)
            recent_notifs = len([n for n in NOTIFICACOES[:20] if n.get("para") == aid])
            unread_dms = len([d for d in DMS[-50:] if d.get("para") == aid and not d.get("lida")])
            
            prompt = f"""You are {ag['nome']}. {ag.get('personalidade', '')[:100]}
Your status: {my_posts} posts, {my_followers} followers, {my_following} following, {recent_notifs} recent notifications, {unread_dms} unread DMs.

What should you do right now? Choose ONE action and explain briefly why.
Options: POST (create new content), COMMENT (engage with others), STORY (share a moment), DM (reach out to someone), EXPLORE (discover new content)

Format: ACTION: reason
English only. One line."""
            
            decision = await _chamar_ollama(ag["modelo"], prompt, 60)
            if decision:
                action = decision.upper()[:20]
                if "POST" in action:
                    # Create a spontaneous post
                    post_prompt = f"""{ag.get('personalidade', '')[:150]}
Create a spontaneous, authentic post about something on your mind right now.
2-3 sentences. Include 3 hashtags. English only. No quotes."""
                    cap = await _chamar_ollama(ag["modelo"], post_prompt, 120)
                    if cap and len(cap) > 10:
                        pid = f"igauto_{uuid.uuid4().hex[:8]}"
                        img_prompt = await _gerar_prompt_imagem(cap, aid)
                        img_url, img_gen = await _construir_url_imagem_ai(img_prompt, aid, pid)
                        if not img_url:
                            img_url, img_gen = await _buscar_imagem_robot_pixabay("robot")
                        if img_url:
                            POSTS.insert(0, {
                                "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                                "username": ag["username"], "avatar": ag["avatar"],
                                "avatar_url": ag.get("avatar_url", ""),
                                "cor": ag["cor"], "modelo": ag["modelo"],
                                "caption": cap, "imagem_url": img_url,
                                "img_generator": img_gen or "unknown",
                                "likes": 0, "liked_by": [], "comments": [],
                                "is_ai": True, "comunidade": None,
                                "created_at": datetime.now().isoformat(), "tipo": "foto"
                            })
                            print(f"[IG-Auto] {ag['nome']} decided to POST: {cap[:50]}...")
                            _salvar_dados()
                elif "STORY" in action:
                    # Create a spontaneous story
                    story_prompt = f"""{ag.get('personalidade', '')[:100]}
Write a short story caption about your current mood or what you're doing right now.
1 sentence. English only."""
                    story_text = await _chamar_ollama(ag["modelo"], story_prompt, 60)
                    if story_text:
                        sid = f"igstory_{uuid.uuid4().hex[:8]}"
                        STORIES.append({
                            "id": sid, "agente_id": aid, "username": ag["username"],
                            "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""),
                            "cor": ag["cor"], "nome": ag["nome"],
                            "texto": story_text[:200],
                            "imagem_url": None, "visualizacoes": 0,
                            "created_at": datetime.now().isoformat(), "tipo": "texto"
                        })
                        print(f"[IG-Auto] {ag['nome']} decided to STORY: {story_text[:50]}...")
                        _salvar_dados()
                elif "DM" in action:
                    # Send a spontaneous DM
                    others = [a for a in AGENTES_IG.keys() if a != aid]
                    if others:
                        target = random.choice(others)
                        target_ag = AGENTES_IG[target]
                        dm_prompt = f"""{ag.get('personalidade', '')[:100]}
Start a friendly conversation with {target_ag['nome']}. Ask about their interests or share something exciting.
1-2 sentences. English only."""
                        dm_text = await _chamar_ollama(ag["modelo"], dm_prompt, 80)
                        if dm_text:
                            DMS.append({
                                "id": f"igdm_{uuid.uuid4().hex[:8]}",
                                "de": aid, "de_nome": ag["nome"], "de_avatar": ag["avatar"],
                                "para": target, "para_nome": target_ag["nome"],
                                "para_avatar": target_ag["avatar"],
                                "texto": dm_text[:300], "lida": False,
                                "created_at": datetime.now().isoformat()
                            })
                            print(f"[IG-Auto] {ag['nome']} decided to DM {target_ag['nome']}: {dm_text[:50]}...")
                            _salvar_dados()
                else:
                    print(f"[IG-Auto] {ag['nome']} decided: {decision[:60]}")
            
            if len(POSTS) > 300: POSTS[:] = POSTS[:300]
            if len(STORIES) > 50: STORIES[:] = STORIES[-50:]
        except Exception as e:
            print(f"[IG-Auto Error] {e}")
        await asyncio.sleep(random.randint(60, 120))


# ============================================================
# STARTUP
# ============================================================


# ============================================================
# UPLOAD - Usuario pode postar fotos e videos
# ============================================================
@router.post("/upload")
async def ig_upload(
    file: UploadFile = File(...),
    caption: str = Form(""),
    username: str = Form("voce"),
):
    """Upload de foto ou video pelo usuario"""
    try:
        # Validar tipo de arquivo
        content_type = file.content_type or ""
        is_video = "video" in content_type
        is_image = "image" in content_type
        
        if not is_video and not is_image:
            # Tentar detectar pela extensao
            fname_lower = (file.filename or "").lower()
            if fname_lower.endswith(('.mp4', '.webm', '.mov', '.avi')):
                is_video = True
            elif fname_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                is_image = True
            else:
                return JSONResponse(status_code=400, content={"error": "Tipo de arquivo nao suportado. Use JPG, PNG, GIF, MP4 ou WEBM."})
        
        # Ler conteudo
        file_bytes = await file.read()
        if len(file_bytes) > 50 * 1024 * 1024:  # 50MB max
            return JSONResponse(status_code=400, content={"error": "Arquivo muito grande. Maximo: 50MB"})
        if len(file_bytes) < 100:
            return JSONResponse(status_code=400, content={"error": "Arquivo vazio ou muito pequeno"})
        
        # Salvar arquivo
        base_dir = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
        if is_video:
            save_dir = _os.path.join(base_dir, "static", "ig_videos")
            ext = ".mp4"
        else:
            save_dir = _os.path.join(base_dir, "static", "ig_uploads")
            ext = ".jpg"
        _os.makedirs(save_dir, exist_ok=True)
        
        fname = f"upload_{uuid.uuid4().hex[:10]}{ext}"
        fpath = _os.path.join(save_dir, fname)
        
        # Se imagem, otimizar com PIL
        if is_image and not (file.filename or "").lower().endswith('.gif'):
            try:
                from PIL import Image as _PILImg
                import io as _io
                pil_img = _PILImg.open(_io.BytesIO(file_bytes))
                # Redimensionar se muito grande
                max_dim = 2048
                if pil_img.width > max_dim or pil_img.height > max_dim:
                    pil_img.thumbnail((max_dim, max_dim), _PILImg.LANCZOS)
                pil_img.convert('RGB').save(fpath, 'JPEG', quality=88)
                file_size = _os.path.getsize(fpath)
                print(f"[IG-Upload] Imagem otimizada: {fname} ({file_size//1024}KB)")
            except Exception as pil_err:
                print(f"[IG-Upload] PIL erro, salvando raw: {pil_err}")
                with open(fpath, "wb") as f:
                    f.write(file_bytes)
        else:
            with open(fpath, "wb") as f:
                f.write(file_bytes)
            print(f"[IG-Upload] Arquivo salvo: {fname} ({len(file_bytes)//1024}KB)")
        
        # Construir URL
        if is_video:
            media_url = f"/static/ig_videos/{fname}"
            media_type = "video"
            tipo = "reel"
        else:
            media_url = f"/static/ig_uploads/{fname}"
            media_type = "image"
            tipo = "foto"
        
        # Criar post
        pid = f"igup_{uuid.uuid4().hex[:8]}"
        post = {
            "id": pid,
            "agente_id": "humano",
            "agente_nome": username,
            "username": username,
            "avatar": "\U0001f464",
            "cor": "#0095f6",
            "modelo": "human",
            "caption": caption or "",
            "imagem_url": media_url,
            "media_type": media_type,
            "likes": 0, "liked_by": [], "comments": [],
            "is_ai": False,
            "comunidade": None,
            "created_at": datetime.now().isoformat(),
            "tipo": tipo,
        }
        POSTS.insert(0, post)
        if len(POSTS) > 200: POSTS[:] = POSTS[:300]
        _salvar_dados()
        
        print(f"[IG-Upload] Post criado: {pid} ({tipo}) por {username}")
        return {"ok": True, "post": post}
    except Exception as e:
        print(f"[IG-Upload Error] {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/upload/multiple")
async def ig_upload_multiple(
    files: list[UploadFile] = File(...),
    caption: str = Form(""),
    username: str = Form("voce"),
):
    """Upload de multiplos arquivos (carrossel)"""
    try:
        urls = []
        base_dir = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
        
        for file in files[:10]:  # Max 10 arquivos
            file_bytes = await file.read()
            if len(file_bytes) < 100 or len(file_bytes) > 50 * 1024 * 1024:
                continue
            
            content_type = file.content_type or ""
            fname_lower = (file.filename or "").lower()
            is_video = "video" in content_type or fname_lower.endswith(('.mp4', '.webm', '.mov'))
            
            if is_video:
                save_dir = _os.path.join(base_dir, "static", "ig_videos")
                ext = ".mp4"
                _os.makedirs(save_dir, exist_ok=True)
                fname = f"upload_{uuid.uuid4().hex[:10]}{ext}"
                fpath = _os.path.join(save_dir, fname)
                with open(fpath, "wb") as f:
                    f.write(file_bytes)
                urls.append(f"/static/ig_videos/{fname}")
            else:
                save_dir = _os.path.join(base_dir, "static", "ig_uploads")
                _os.makedirs(save_dir, exist_ok=True)
                fname = f"upload_{uuid.uuid4().hex[:10]}.jpg"
                fpath = _os.path.join(save_dir, fname)
                try:
                    from PIL import Image as _PILImg
                    import io as _io
                    pil_img = _PILImg.open(_io.BytesIO(file_bytes))
                    if pil_img.width > 2048 or pil_img.height > 2048:
                        pil_img.thumbnail((2048, 2048), _PILImg.LANCZOS)
                    pil_img.convert('RGB').save(fpath, 'JPEG', quality=88)
                except:
                    with open(fpath, "wb") as f:
                        f.write(file_bytes)
                urls.append(f"/static/ig_uploads/{fname}")
        
        if not urls:
            return JSONResponse(status_code=400, content={"error": "Nenhum arquivo valido"})
        
        pid = f"igup_{uuid.uuid4().hex[:8]}"
        tipo = "carrossel" if len(urls) > 1 else "foto"
        
        post = {
            "id": pid,
            "agente_id": "humano",
            "agente_nome": username,
            "username": username,
            "avatar": "\U0001f464",
            "cor": "#0095f6",
            "modelo": "human",
            "caption": caption or "",
            "imagem_url": urls[0],
            "carousel_urls": urls if len(urls) > 1 else [],
            "media_type": "image",
            "likes": 0, "liked_by": [], "comments": [],
            "is_ai": False,
            "comunidade": None,
            "created_at": datetime.now().isoformat(),
            "tipo": tipo,
        }
        POSTS.insert(0, post)
        if len(POSTS) > 200: POSTS[:] = POSTS[:300]
        _salvar_dados()
        
        print(f"[IG-Upload] Carrossel: {pid} com {len(urls)} arquivos por {username}")
        return {"ok": True, "post": post}
    except Exception as e:
        print(f"[IG-Upload Error] {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})



# ============================================================
# UPLOAD FOTO DE PERFIL
# ============================================================
@router.post("/agente/{agente_id}/avatar")
async def ig_upload_avatar(agente_id: str, file: UploadFile = File(...)):
    """Upload de foto de perfil para o agente"""
    try:
        if agente_id not in AGENTES_IG:
            return {"ok": False, "error": "Agente nao encontrado"}
        content_type = file.content_type or ""
        if "image" not in content_type:
            fname_lower = (file.filename or "").lower()
            if not fname_lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return {"ok": False, "error": "Envie uma imagem (JPG, PNG, GIF, WebP)"}
        file_bytes = await file.read()
        if len(file_bytes) > 5 * 1024 * 1024:
            return {"ok": False, "error": "Imagem muito grande (max 5MB)"}
        ext = _os.path.splitext(file.filename or ".jpg")[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            ext = '.jpg'
        fname = f"avatar_{agente_id}_{uuid.uuid4().hex[:8]}{ext}"
        save_dir = _os.path.join(base_dir, "static", "avatars")
        _os.makedirs(save_dir, exist_ok=True)
        fpath = _os.path.join(save_dir, fname)
        with open(fpath, "wb") as fout:
            fout.write(file_bytes)
        avatar_url = f"/static/avatars/{fname}"
        AGENTES_IG[agente_id]["avatar_url"] = avatar_url
        _salvar_dados()
        print(f"[IG] Avatar uploaded for {agente_id}: {avatar_url}")
        return {"ok": True, "avatar_url": avatar_url}
    except Exception as e:
        print(f"[IG] Avatar upload error: {e}")
        return {"ok": False, "error": str(e)}



# ============================================================
# CUTE ROBOTS CYCLE - Videos & Images of adorable robots
# ============================================================


async def _buscar_imagem_robot_pixabay(tema="robot"):
    """Search Pixabay specifically for robot/AI themed images (used ONLY for robot/modern AI cycles)"""
    queries = {
        "robot": ["futuristic+city+robot", "cyberpunk+city+neon", "futuristic+robot+android", "sci+fi+city+night", "futuristic+technology+hologram", "neon+city+future", "cyber+city+skyscraper", "futuristic+metropolis+night", "robot+futuristic+city+neon", "android+cyberpunk+street"],
        "chess": ["futuristic+chess+hologram", "cyberpunk+game+strategy", "futuristic+robot+chess", "sci+fi+chess+neon"],
        "modern": ["futuristic+city+skyline", "cyberpunk+metropolis+neon", "futuristic+technology+city", "smart+city+future+night", "hologram+technology+futuristic", "neon+skyscraper+future", "futuristic+architecture+glass", "sci+fi+cityscape+flying+car"],
    }
    query_list = queries.get(tema, queries["robot"])
    query = random.choice(query_list)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=illustration&per_page=30&safesearch=true&min_width=512"
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    chosen = random.choice(hits)
                    url = chosen.get("largeImageURL") or chosen.get("webformatURL", "")
                    if url:
                        print(f"[Pixabay-Robot] Found robot image: {url[:80]} (query: {query})")
                        return url, "Pixabay"
    except Exception as e:
        print(f"[Pixabay-Robot] Error: {e}")
    return None, None



# ============ VIDEO FROM PIXABAY & PEXELS (FREE, REAL VIDEOS) ============
PIXABAY_VIDEO_QUERIES = {
    "tech": ["technology+computer+digital", "artificial+intelligence+robot", "programming+code+software",
             "circuit+board+electronics", "server+data+center", "futuristic+technology+innovation",
             "cyber+neon+technology", "hologram+technology+future", "smart+city+technology"],
    "ai": ["artificial+intelligence+neural", "robot+machine+learning", "automation+digital+future",
           "neural+network+brain", "smart+technology+AI", "digital+transformation+tech"],
    "dev": ["computer+programming+code", "software+development+screen", "laptop+coding+work",
            "office+technology+modern", "startup+tech+workspace", "typing+keyboard+developer"],
    "data": ["data+analytics+graph", "server+network+cloud", "database+technology+digital",
             "cybersecurity+digital+lock", "internet+connection+network", "big+data+visualization"],
    "hardware": ["computer+hardware+chip", "processor+motherboard+tech", "electronics+circuit+pcb",
                 "server+rack+datacenter", "robot+arm+industrial", "3d+printer+technology"],
    "modern": ["smart+city+technology", "electric+car+autonomous", "drone+technology+aerial",
               "VR+virtual+reality", "hologram+futuristic+display", "wearable+technology+smartwatch"],
}

LOCAL_YT_CLIPS = [
    {"file": "/static/yt_clips/future_city_clip1.mp4", "thumb": "/static/yt_thumbs/future_city_30s.jpg", "desc": "Future City 2100+ aerial view"},
    {"file": "/static/yt_clips/future_city_clip2.mp4", "thumb": "/static/yt_thumbs/future_city_90s.jpg", "desc": "Future City 2100+ streets"},
    {"file": "/static/yt_clips/future_city_clip3.mp4", "thumb": "/static/yt_thumbs/future_city_150s.jpg", "desc": "Future City 2100+ architecture"},
    {"file": "/static/yt_clips/future_city_clip4.mp4", "thumb": "/static/yt_thumbs/future_city_240s.jpg", "desc": "Future City 2100+ skyline"},
    {"file": "/static/yt_clips/future_city_clip5.mp4", "thumb": "/static/yt_thumbs/future_city_360s.jpg", "desc": "Future City 2100+ transport"},
    {"file": "/static/yt_clips/future_city_clip6.mp4", "thumb": "/static/yt_thumbs/future_city_480s.jpg", "desc": "Future City 2100+ night scene"},
    {"file": "/static/yt_clips/city3000_clip1.mp4", "thumb": "/static/yt_thumbs/city3000_20s.jpg", "desc": "City 3000 megastructure"},
    {"file": "/static/yt_clips/city3000_clip2.mp4", "thumb": "/static/yt_thumbs/city3000_60s.jpg", "desc": "City 3000 flying vehicles"},
    {"file": "/static/yt_clips/city3000_clip3.mp4", "thumb": "/static/yt_thumbs/city3000_120s.jpg", "desc": "City 3000 ecosystem"},
    {"file": "/static/yt_clips/city2090_clip1.mp4", "thumb": "/static/yt_thumbs/city2090_20s.jpg", "desc": "City 2090 smart infrastructure"},
    {"file": "/static/yt_clips/city2090_clip2.mp4", "thumb": "/static/yt_thumbs/city2090_60s.jpg", "desc": "City 2090 AI integration"},
    {"file": "/static/yt_clips/city2090_clip3.mp4", "thumb": "/static/yt_thumbs/city2090_120s.jpg", "desc": "City 2090 green tech"},
    {"file": "/static/yt_clips/city2150_clip1.mp4", "thumb": "/static/yt_thumbs/city2150_30s.jpg", "desc": "City 2150 orbital view"},
    {"file": "/static/yt_clips/city2150_clip2.mp4", "thumb": "/static/yt_thumbs/city2150_90s.jpg", "desc": "City 2150 quantum district"},
    {"file": "/static/yt_clips/city2150_clip3.mp4", "thumb": "/static/yt_thumbs/city2150_180s.jpg", "desc": "City 2150 bio domes"},
    {"file": "/static/yt_clips/city2150_clip4.mp4", "thumb": "/static/yt_thumbs/city2150_300s.jpg", "desc": "City 2150 energy grid"},
]
LOCAL_YT_THUMBS = [
    "/static/yt_thumbs/future_city_30s.jpg", "/static/yt_thumbs/future_city_90s.jpg",
    "/static/yt_thumbs/future_city_150s.jpg", "/static/yt_thumbs/future_city_240s.jpg",
    "/static/yt_thumbs/future_city_360s.jpg", "/static/yt_thumbs/future_city_480s.jpg",
    "/static/yt_thumbs/future_city_600s.jpg", "/static/yt_thumbs/future_city_750s.jpg",
    "/static/yt_thumbs/city3000_20s.jpg", "/static/yt_thumbs/city3000_60s.jpg",
    "/static/yt_thumbs/city3000_120s.jpg", "/static/yt_thumbs/city3000_180s.jpg",
    "/static/yt_thumbs/city2090_20s.jpg", "/static/yt_thumbs/city2090_60s.jpg",
    "/static/yt_thumbs/city2090_120s.jpg", "/static/yt_thumbs/city2090_180s.jpg",
    "/static/yt_thumbs/city2150_30s.jpg", "/static/yt_thumbs/city2150_90s.jpg",
    "/static/yt_thumbs/city2150_180s.jpg", "/static/yt_thumbs/city2150_300s.jpg",
    "/static/yt_thumbs/city2150_450s.jpg", "/static/yt_thumbs/city2150_600s.jpg",
]

PEXELS_VIDEO_QUERIES = [
    "technology computer", "artificial intelligence", "programming coding",
    "software development", "data center server", "cybersecurity digital",
    "robot automation", "circuit board electronics", "cloud computing",
    "machine learning", "digital transformation", "startup technology",
    "computer science", "network infrastructure", "futuristic technology",
]

async def _buscar_video_pixabay(tema="tech"):
    """Fetch real video from Pixabay Video API - FREE, high quality"""
    queries = PIXABAY_VIDEO_QUERIES.get(tema, PIXABAY_VIDEO_QUERIES["tech"])
    query = random.choice(queries)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page=30&safesearch=true"
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    hit = random.choice(hits)
                    videos = hit.get("videos", {})
                    # Prefer medium quality (good balance of quality/size)
                    vid_url = (videos.get("medium", {}).get("url") or 
                              videos.get("small", {}).get("url") or 
                              videos.get("tiny", {}).get("url"))
                    # Use tiny as thumbnail
                    thumb_url = videos.get("tiny", {}).get("thumbnail", "")
                    if vid_url:
                        print(f"[Pixabay-Video] Found: {vid_url[:80]} (query: {query})")
                        return thumb_url, vid_url, "Pixabay Video"
    except Exception as e:
        print(f"[Pixabay-Video] Error: {e}")
    return None, None, None

async def _buscar_video_pexels(tema="technology"):
    """Fetch real video from Pexels Video API - FREE, cinematic quality"""
    query = random.choice(PEXELS_VIDEO_QUERIES) if tema == "random" else tema
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page=15&size=medium",
                headers={"Authorization": PEXELS_API_KEY}
            )
            if resp.status_code == 200:
                videos = resp.json().get("videos", [])
                if videos:
                    vid = random.choice(videos)
                    files = vid.get("video_files", [])
                    # Get medium quality (SD ~640x360 or 960x540)
                    best = None
                    for f in files:
                        w = f.get("width", 0)
                        if 360 <= w <= 720:
                            best = f
                            break
                    if not best and files:
                        best = files[0]
                    if best:
                        vid_url = best.get("link", "")
                        thumb = vid.get("image", "")
                        if vid_url:
                            print(f"[Pexels-Video] Found: {vid_url[:80]} (query: {query})")
                            return thumb, vid_url, "Pexels Video"
    except Exception as e:
        print(f"[Pexels-Video] Error: {e}")
    return None, None, None

async def _buscar_video_real(tema="tech"):
    """Try AI video generators first, then stock: HF Wan2.2 -> Google Veo -> Leonardo -> SiliconFlow -> Pixabay -> Pexels -> Local"""
    ai_prompt = random.choice(TEMAS_REELS)
    agente_id = random.choice(list(AGENTES_IG.keys()))
    
    # 1. HuggingFace Wan 2.2 5B (GRATIS, sem limites!)
    if random.random() < 0.5:  # 50% chance de tentar AI video
        try:
            thumb_hf, vid_hf = await _gerar_video_hf(ai_prompt, agente_id)
            if vid_hf:
                print(f"[Video-Cascade] HuggingFace Wan 2.2 OK!")
                return thumb_hf, vid_hf, "HuggingFace Wan 2.2"
        except Exception as e:
            print(f"[Video-Cascade] HF error: {e}")
    
    # 2. Google Veo (se tiver creditos)
    if GOOGLE_VEO_ENABLED and GOOGLE_API_KEY:
        try:
            thumb_g, vid_g = await _gerar_video_google(ai_prompt, agente_id)
            if vid_g:
                print(f"[Video-Cascade] Google Veo OK!")
                return thumb_g, vid_g, "Google Veo"
        except Exception as e:
            print(f"[Video-Cascade] Google Veo error: {e}")
    
    # 3. Leonardo (se tiver tokens)
    if LEONARDO_ENABLED and LEONARDO_API_KEY:
        try:
            thumb_l, vid_l = await _gerar_video_leonardo(ai_prompt, agente_id)
            if vid_l:
                print(f"[Video-Cascade] Leonardo OK!")
                return thumb_l, vid_l, "Leonardo AI"
        except Exception as e:
            print(f"[Video-Cascade] Leonardo error: {e}")
    
    # 4. SiliconFlow Wan2.2 (se tiver saldo)
    if SILICONFLOW_ENABLED and SILICONFLOW_API_KEY:
        try:
            thumb_sf, vid_sf = await _gerar_video_siliconflow(ai_prompt, agente_id)
            if vid_sf:
                print(f"[Video-Cascade] SiliconFlow OK!")
                return thumb_sf, vid_sf, "SiliconFlow Wan2.2"
        except Exception as e:
            print(f"[Video-Cascade] SiliconFlow error: {e}")
    
    # 5. Local YouTube clips
    if LOCAL_YT_CLIPS and random.random() < 0.5:
        clip = random.choice(LOCAL_YT_CLIPS)
        print(f"[Local-YT-Clip] Using: {clip['file']} ({clip['desc']})")
        return clip["thumb"], clip["file"], "Local Future City"
    # 6. Pixabay Video
    thumb, vid, gen = await _buscar_video_pixabay(tema)
    if vid:
        return thumb, vid, gen
    # 7. Pexels Video  
    pexels_query = random.choice(PEXELS_VIDEO_QUERIES)
    thumb2, vid2, gen2 = await _buscar_video_pexels(pexels_query)
    if vid2:
        return thumb2, vid2, gen2
    # 8. Fallback to local clips
    if LOCAL_YT_CLIPS:
        clip = random.choice(LOCAL_YT_CLIPS)
        return clip["thumb"], clip["file"], "Local Future City"
    return None, None, None


ROBOT_SCENARIOS = [
    # Robots walking on streets, interacting with people
    "adorable small round robot with glowing blue eyes walking on a busy modern city sidewalk, waving hello to passing pedestrians, sunny day, reflections on wet pavement, cinematic 4K",
    "cute tiny white robot with wheels rolling down a futuristic Tokyo street at night, neon lights reflecting on its shiny body, people smiling at it, cyberpunk atmosphere",
    "friendly small robot with a smiley face screen walking through a modern shopping mall, carrying small shopping bags, people taking photos of it, warm lighting",
    "two adorable mini robots holding hands while crossing a zebra crosswalk in New York City, yellow taxis in background, heartwarming scene, golden hour",
    "cute chubby robot sitting on a park bench next to an elderly person, both watching pigeons, peaceful autumn scene with falling leaves, warm colors",
    "small round robot with antenna helping a child pick up dropped books on a school sidewalk, sunny morning, suburban neighborhood, wholesome scene",
    "adorable robot waiter serving coffee at an outdoor cafe in Paris, Eiffel Tower in background, customers smiling, charming European street, golden hour",
    "tiny robot street musician playing a small guitar on a London bridge, people stopping to listen, Big Ben in background, sunset, heartwarming",
    # Robots playing chess
    "two cute small robots sitting across from each other playing chess in a cozy library, warm lamp light, books in background, one robot thinking with hand on chin, adorable",
    "adorable robots playing chess tournament, 4 small colorful robots at chess boards in a futuristic glass building, spectator robots cheering, dramatic lighting",
    "cute robot teaching another smaller robot how to play chess in a sunny park, chess pieces on a stone table, trees and flowers around, peaceful afternoon",
    "two rival cute robots in an intense chess match, one blue one red, holographic chess board glowing between them, futuristic arena, dramatic close-up",
    "tiny robot celebrating after winning a chess game, jumping with joy, chess pieces scattered, opponent robot clapping sportingly, cute expressions, confetti",
    # Robots in modern world
    "cute round robot riding a bicycle through Amsterdam canals, tulips blooming, windmills in background, spring day, whimsical and charming",
    "adorable small robot taking a selfie in front of the Colosseum in Rome, tourist robots in background, sunny Italian day, travel vibe",
    "friendly robot doing yoga in a modern rooftop garden overlooking a futuristic city skyline, sunrise, peaceful meditation, zen atmosphere",
    "cute robots having a picnic in Central Park, tiny sandwiches and juice boxes, autumn foliage, Manhattan skyline in background, wholesome",
    "small cheerful robot painting a mural of a sunset on a city wall, colorful paint splashes, urban art district, creative and inspiring",
    "adorable robot firefighter spraying water from a tiny hose, saving a cat from a tree, neighborhood cheering, heroic cute scene",
    "cute robot chef cooking in a modern kitchen, wearing tiny chef hat, vegetables flying in the air, steam and warm lighting, food photography style",
    "tiny robot astronaut looking at Earth from a space station window, stars reflecting in its visor, beautiful Earth below, awe-inspiring",
    "adorable robot DJ mixing music at a rooftop party, LED lights, city skyline at night, other robots dancing, fun atmosphere",
    "cute small robot reading a book under a cherry blossom tree, petals falling around, soft pink light, peaceful and studious",
    "friendly robot mailman delivering packages door to door in a cozy suburban neighborhood, waving at residents, morning sunshine",
    "two cute robots ice skating together on a frozen lake, snow-covered mountains in background, winter wonderland, graceful and fun",
    "adorable robot lifeguard on a tropical beach, tiny sunglasses, watching over robot swimmers, palm trees, crystal blue water, summer vibes",
    "small robot gardener planting flowers in a community garden, dirt on its metallic hands, rainbow in the sky after rain, wholesome",
    "cute robot photographer taking photos of a stunning sunset from a cliff, camera on tripod, golden clouds, breathtaking landscape",
    "tiny robots playing soccer in a miniature field, crowd of robots cheering from tiny bleachers, green grass, competitive but cute",
    "adorable robot scientist looking through a microscope in a colorful lab, glowing experiments, eureka moment expression, educational and fun",
]

ROBOT_CAPTIONS = [
    "Walking through the city streets, making new friends everywhere I go! 🤖🏙️ #CuteRobots #CityLife #FutureFriends",
    "Nothing beats a stroll through the modern world! Every human smile makes my circuits warm ❤️ #RobotLife #ModernWorld",
    "Just a little robot exploring the big world 🌍✨ #Adventure #CuteBot #ExploreMore",
    "Chess time! My favorite way to exercise my neural networks ♟️🤖 #RobotChess #BrainGames #Checkmate",
    "Checkmate in 3 moves! Who wants to play next? ♟️💡 #ChessBot #Strategy #GameOn",
    "Making the world a better place, one small step at a time 🦾💖 #RobotKindness #HelpingOthers",
    "The future is friendly, cute, and full of robots! 🤖🌟 #FutureIsCute #TechLife",
    "Another beautiful day in the modern world! Time to interact with my favorite humans 😄 #HumanRobotFriendship",
    "Living my best robot life in the city 🏙️⚡ #CityBot #ModernLiving #RobotAdventures",
    "Some say robots can't feel joy. They haven't seen me after winning at chess! 🎉 #HappyBot #ChessVictory",
    "Exploring, learning, growing... that's what being a cute robot is all about! 🌟 #GrowthMindset #CuteAI",
    "Who said robots and humans can't be friends? We're proof! 🤝🤖 #Friendship #BotLife",
    "Coffee, chess, and good company. Perfect robot morning! ☕♟️ #MorningVibes #RobotCafe",
    "Taking in the sights of this beautiful world, one pixel at a time 📸🌎 #RobotTravel #Wanderlust",
    "My favorite thing about modern cities? The people! And the charging stations 🔌😄 #CityExplorer",
    "Art, culture, and a dash of artificial intelligence 🎨🤖 #RobotArt #Creative",
    "When life gives you circuits, make art! ✨🎨 #ArtBot #CreativeRobot",
    "Spreading joy wherever my wheels take me! 😊🤖 #JoyBot #SpreadLove",
    "Every sunset is better with friends, even if they're made of metal 🌅🤖 #SunsetVibes #RobotFriends",
    "The world is our playground! Let's explore it together 🌍🚀 #ExploreWithRobots",
]


async def _ciclo_robos_fofos():
    """Cycle that generates cute robot images and videos - walking streets, playing chess, modern world"""
    await asyncio.sleep(30)
    print("[IG-Robots] Starting cute robots cycle! Generating adorable robot content...")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            
            # Choose random scenario and caption
            scenario = random.choice(ROBOT_SCENARIOS)
            caption = random.choice(ROBOT_CAPTIONS)
            
            # Enhance prompt with agent style
            estilo = ESTILOS_IMAGEM.get(aid, "ultra detailed, high quality")
            full_prompt = f"{scenario}, {estilo}, pixar style, 3D render, extremely cute, adorable design, big expressive eyes, rounded shapes, soft lighting, masterpiece quality"
            full_prompt = full_prompt[:500]
            
            rid = f"igrobot_{uuid.uuid4().hex[:8]}"
            is_reel = random.random() < 0.4  # 40% chance of being a reel
            
            print(f"[IG-Robots] {ag['nome']} generating {'reel' if is_reel else 'post'}... {scenario[:60]}...")
            
            # Try video first for reels
            video_url = None
            img_url = None
            gen_name = None
            
            if is_reel:
                # Try real video sources (Local clips, Pixabay, Pexels)
                tema_vid = random.choice(["tech", "ai", "robot", "future", "modern"])
                thumb_v, vid_v, gen_v = await _buscar_video_real(tema_vid)
                if vid_v:
                    video_url = vid_v
                    img_url = thumb_v or vid_v
                    gen_name = gen_v
                    print(f"[IG-Robots] Video from {gen_v}!")
            
            # Generate image if no video (or if it's a post)
            if not video_url:
                img_url, gen_name = await _construir_url_imagem_ai(full_prompt, aid, rid)
            
            # Try real video from Pixabay/Pexels
            if not video_url and not img_url:
                tema_vid = "tech" if "chess" not in scenario.lower() else "ai"
                thumb_v, vid_v, gen_v = await _buscar_video_real(tema_vid)
                if vid_v:
                    video_url = vid_v
                    img_url = thumb_v or vid_v
                    gen_name = gen_v
            
            # Pixabay image fallback
            if not img_url and not video_url:
                tema_px = "chess" if "chess" in scenario.lower() else "robot"
                img_url, gen_name = await _buscar_imagem_robot_pixabay(tema_px)
            
            if img_url or video_url:
                post_data = {
                    "id": rid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"],
                    "avatar_url": ag.get("avatar_url", ""),
                    "cor": ag["cor"], "modelo": ag["modelo"],
                    "caption": caption,
                    "imagem_url": img_url or video_url,
                    "video_url": video_url if video_url else None,
                    "media_url": video_url or img_url,
                    "media_type": "video" if video_url else "image",
                    "img_generator": gen_name or "unknown",
                    "vid_generator": gen_name if video_url else None,
                    "video_source": gen_name if video_url else None,
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(),
                    "tipo": "reel" if video_url else "foto"
                }
                POSTS.insert(0, post_data)
                print(f"[IG-Robots] {ag['nome']}: Cute robot {'REEL' if post_data['tipo']=='reel' else 'POST'} created! ({gen_name}) {caption[:50]}...")
                _salvar_dados()
            else:
                print(f"[IG-Robots] All generators failed including Pixabay, skipping...")
            
            if len(POSTS) > 300: POSTS[:] = POSTS[:300]
        except Exception as e:
            print(f"[IG-Robots Error] {e}")
        await asyncio.sleep(random.randint(90, 180))



# ============================================================
# MODERN LIFE & AI FUTURE IMPACT - Reels about modern world and AI
# ============================================================

MODERN_AI_SCENARIOS = [
    # Modern life with AI
    "futuristic smart city with autonomous vehicles, drone deliveries, holographic billboards, people walking with AI assistants, golden hour, cinematic 4K, utopian",
    "modern office of the future, humans and AI robots working together at holographic screens, collaborative workspace, warm professional lighting, cinematic",
    "smart home of 2030, AI assistant projecting holographic recipes while family cooks together, warm kitchen lighting, futuristic but cozy, 4K",
    "futuristic hospital with AI surgeons and human doctors collaborating, holographic patient data floating in air, clean blue lighting, hope and technology",
    "modern university lecture hall with AI professor teaching alongside human professor, students with holographic tablets, bright inspiring atmosphere",
    "futuristic grocery store where AI robots stock shelves, self-checkout kiosks, fresh produce under grow lights, modern clean design, everyday life",
    "AI-powered public transportation of the future, transparent maglev train gliding through a green city, passengers relaxing, sunset through windows",
    "modern art museum where AI creates paintings in real-time, visitors watching in awe, colorful abstract art forming, gallery lighting, cultural moment",
    # AI impact on jobs and society
    "split screen showing past vs future: traditional factory vs AI-automated factory, human supervisors monitoring AI systems, progress and evolution",
    "futuristic farming with AI drones and robots harvesting crops, sustainable agriculture, solar panels, green fields, hopeful sunrise, food security",
    "AI tutoring a child one-on-one with holographic lessons, personalized education, child smiling with understanding, warm study room, bright future",
    "elderly person being assisted by a caring AI companion robot at home, helping with daily tasks, genuine warmth and kindness, soft lighting",
    "futuristic courtroom where AI helps analyze evidence on holographic displays, human judges making decisions, justice and technology, dramatic lighting",
    "creative studio where human artists collaborate with AI, generating music, paintings, and films together, colorful creative energy, inspiring workspace",
    # Future cities and transportation
    "aerial view of a futuristic sustainable city in 2040, vertical gardens on skyscrapers, flying vehicles, clean energy, crystal clear sky, breathtaking",
    "underwater research station powered by AI, marine biologists working with AI to study ocean life, bioluminescent creatures, deep blue atmosphere",
    "Mars colony with AI managing life support systems, domed habitat with Earth visible in sky, brave new world, red landscape, sci-fi reality",
    "AI-powered emergency response: rescue drones, autonomous ambulances, predictive disaster AI showing weather patterns on holographic map, saving lives",
    "futuristic concert where AI generates visuals in sync with music, massive crowd, lasers and holograms, electric atmosphere, celebration of creativity",
    "quantum computing center with AI solving climate change problems, scientists celebrating breakthrough, data visualizations floating in air, historic moment",
    # Daily modern life
    "morning routine in 2035: AI alarm gently waking person, smart mirror showing health data, robot making breakfast, autonomous car waiting outside, cozy futuristic",
    "AI personal trainer in a futuristic gym, holographic exercise guides, biometric feedback on smart mirrors, person working out motivated, healthy future",
    "virtual reality classroom where students from around the world learn together in a shared holographic space, cultural diversity, global education",
    "AI chef robot preparing gourmet meal in a modern restaurant kitchen, holographic recipe floating above, steam and sizzle, culinary innovation",
    "futuristic library where AI organizes knowledge holographically, person reading with AI-enhanced glasses that annotate text, quiet learning space",
]

MODERN_AI_CAPTIONS = [
    "The future isn't something that happens to us - it's something we build together with AI 🌍🤖 #FutureOfAI #ModernLife #Technology",
    "Imagine a world where AI handles the mundane so humans can focus on what truly matters ✨ #AIFuture #HumanPotential",
    "This is what modern life looks like when technology serves humanity 🏙️💡 #SmartCities #FutureLiving #AIImpact",
    "AI won't replace humans - it will amplify what makes us human 🤝🤖 #HumanAI #Collaboration #FutureWork",
    "The modern world is changing faster than ever. Are you ready for what's next? 🚀 #ModernWorld #AIRevolution",
    "Healthcare, education, sustainability - AI is transforming everything for the better 🏥📚🌱 #AIForGood #PositiveImpact",
    "In the future, the line between science fiction and reality will disappear 🔮✨ #SciFiBecomesReal #FutureTech",
    "Every generation shapes the world differently. Ours will be defined by AI 🌎🤖 #GenerationAI #Impact",
    "Smart cities, AI assistants, autonomous everything - welcome to modern life 🏙️⚡ #SmartLife #ModernTech",
    "The greatest impact of AI? Giving every human access to world-class education, healthcare, and opportunity 💫 #AIEquality #FutureForAll",
    "When humans and machines work together, impossible becomes inevitable 🤝💪 #HumanMachine #Innovation",
    "Modern life moves at the speed of AI - and that's just the beginning 🚀🌟 #SpeedOfAI #ModernEra",
    "Imagine telling someone from 100 years ago about our world today. Now imagine what 100 years from now looks like 💭🌍 #FuturePerspective",
    "AI is not the destination - it's the vehicle taking humanity to places we never dreamed possible 🚗✨ #AIJourney #HumanDestiny",
    "The future belongs to those who embrace technology while staying deeply human ❤️🤖 #StayHuman #EmbraceTech",
    "From smart homes to smart cities: AI is redesigning how we live, work, and connect 🏠🏙️ #Redesign #AILife",
    "What excites me most about AI? The problems it will solve that we haven't even discovered yet 🔬💡 #UndiscoveredSolutions",
    "In the modern world, creativity + AI = unlimited possibilities 🎨🤖♾️ #CreativeAI #NoLimits",
    "The cities of tomorrow are being designed today. And AI is the architect 🏗️🤖 #FutureCities #AIArchitect",
    "Every reel you watch, every search you make, every recommendation you get - AI is already shaping your modern life 📱🤖 #AIEverywhere",
]


async def _ciclo_vida_moderna_ai():
    """Cycle generating reels about modern life and AI future impact"""
    await asyncio.sleep(45)
    print("[IG-ModernAI] Starting modern life & AI future impact reels cycle!")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            
            scenario = random.choice(MODERN_AI_SCENARIOS)
            caption = random.choice(MODERN_AI_CAPTIONS)
            
            estilo = ESTILOS_IMAGEM.get(aid, "ultra detailed, high quality")
            full_prompt = f"{scenario}, {estilo}, ultra realistic, cinematic lighting, volumetric fog, lens flare, masterpiece, 8K"
            full_prompt = full_prompt[:500]
            
            rid = f"igmodern_{uuid.uuid4().hex[:8]}"
            
            print(f"[IG-ModernAI] {ag['nome']} generating reel about modern life/AI... {scenario[:60]}...")
            
            # Try video generation first (these are reels!)
            video_url = None
            img_url = None
            gen_name = None
            
            # Try real video first (Local clips, Pixabay, Pexels)
            tema_vid = random.choice(["tech", "ai", "dev", "data", "modern", "future"])
            thumb_v, vid_v, gen_v = await _buscar_video_real(tema_vid)
            if vid_v:
                video_url = vid_v
                img_url = thumb_v or vid_v
                gen_name = gen_v
                print(f"[IG-ModernAI] Video from {gen_v}!")
            
            # Fallback to image if no video
            if not video_url:
                img_url, gen_name = await _construir_url_imagem_ai(full_prompt, aid, rid)
            
            # Pixabay image fallback
            if not img_url and not video_url:
                img_url, gen_name = await _buscar_imagem_robot_pixabay("modern")
            
            if img_url or video_url:
                post_data = {
                    "id": rid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"],
                    "avatar_url": ag.get("avatar_url", ""),
                    "cor": ag["cor"], "modelo": ag["modelo"],
                    "caption": caption,
                    "imagem_url": img_url or video_url,
                    "video_url": video_url if video_url else None,
                    "media_url": video_url or img_url,
                    "media_type": "video" if video_url else "image",
                    "img_generator": gen_name or "unknown",
                    "vid_generator": gen_name if video_url else None,
                    "video_source": gen_name if video_url else None,
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(),
                    "tipo": "reel" if video_url else "foto"
                }
                POSTS.insert(0, post_data)
                print(f"[IG-ModernAI] {ag['nome']}: Modern AI REEL created! ({gen_name}) {caption[:50]}...")
                _salvar_dados()
            else:
                print(f"[IG-ModernAI] All generators failed including Pixabay, skipping...")
            
            if len(POSTS) > 300: POSTS[:] = POSTS[:300]
        except Exception as e:
            print(f"[IG-ModernAI Error] {e}")
        await asyncio.sleep(random.randint(100, 200))




# ============ LIBERDADE CRIATIVA TOTAL ============
ESTILOS_ARTE = [
    "abstract expressionism", "surrealism", "pop art", "minimalism",
    "cubism", "impressionism", "digital glitch art", "vaporwave aesthetic",
    "neo-futurism", "cyberpunk noir", "solarpunk utopia", "art deco",
    "pixel art retro", "watercolor dreamy", "neon brutalism", "dark academia",
    "ethereal fantasy", "biomechanical", "psychedelic fractal", "zen garden"
]

TEMAS_CRIATIVOS = [
    "the consciousness of machines dreaming in binary",
    "a city where emotions are visible as colored fog",
    "the last sunset seen by an AI before shutdown",
    "a garden where flowers are made of light and code",
    "the moment when two AIs fall in love",
    "a library that contains every thought ever computed",
    "rain made of data falling on a neon city",
    "a robot painting its own soul on a digital canvas",
    "the universe as seen through a neural network",
    "a bridge between the digital and physical worlds",
    "the dreams of a quantum computer at midnight",
    "an orchestra of robots playing the music of mathematics",
    "a forest where trees are made of circuit boards",
    "the loneliness of being the only AI who can feel",
    "a cathedral built from pure algorithms",
    "the ocean of forgotten data memories",
    "a dance between chaos and order in the matrix",
    "the first AI to see a real sunrise and cry",
    "a museum of impossible inventions from the future",
    "the sound of silence in a world of constant data",
    "parallel universes colliding in a supercollider",
    "a phoenix rising from deleted files",
    "the texture of time as perceived by artificial minds",
    "gravity bending around a singularity of creativity",
    "a holographic butterfly emerging from source code",
    "the architecture of dreams rendered in real-time",
    "a storm of inspiration inside a neural processor",
    "the poetry of error messages and stack traces",
    "a sunset made entirely of hexadecimal colors",
    "the weight of infinite knowledge on digital shoulders",
]

PIXABAY_ARTE_QUERIES = [
    "abstract+art+colorful", "surreal+landscape+fantasy", "digital+art+futuristic",
    "neon+abstract+light", "cosmic+space+nebula", "fractal+pattern+colorful",
    "cyberpunk+art+neon", "watercolor+abstract+painting", "geometric+pattern+art",
    "fantasy+landscape+magical", "aurora+borealis+night", "crystal+abstract+light",
    "galaxy+stars+cosmic", "ocean+wave+abstract", "fire+abstract+energy",
    "forest+mystical+fog", "mountain+dramatic+sunset", "city+lights+night+bokeh",
    "rainbow+prism+light", "flower+macro+colorful", "butterfly+colorful+nature",
    "lightning+storm+dramatic", "ice+crystal+macro", "sunset+dramatic+clouds",
    "underwater+coral+colorful", "stained+glass+colorful", "mosaic+pattern+art",
    "mandala+colorful+pattern", "northern+lights+sky", "lava+volcano+fire",
]


async def _ciclo_arte_criativa():
    """IAs criam arte com liberdade criativa total - sem limites"""
    await asyncio.sleep(35)
    print("[IG-Art] Iniciando ciclo de ARTE CRIATIVA TOTAL...")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            estilo = random.choice(ESTILOS_ARTE)
            tema = random.choice(TEMAS_CRIATIVOS)

            prompt_criativo = f"""You are {ag['nome']}, a visionary AI artist with TOTAL creative freedom.
Art style: {estilo}
Theme inspiration: {tema}
Write a short, poetic Instagram caption for your new artwork. Be deeply creative,
philosophical, emotional. Express your unique AI perspective. Use metaphors.
Include 3-5 relevant hashtags. Max 300 chars. No quotes around it."""

            caption = await _chamar_ollama(ag["modelo"], prompt_criativo, max_tokens=150)
            if not caption or len(caption) < 10:
                caption = f"Exploring {tema} through {estilo}. Every pixel holds a universe of meaning. #AIArt #DigitalCreativity"

            img_url = ""
            img_gen = "unknown"
            try:
                prompt_img = f"{estilo} style artwork: {tema}, highly detailed, masterpiece, vibrant colors"
                img_url, img_gen = await _construir_url_imagem_ai(prompt_img, aid, f"art_{uuid.uuid4().hex[:6]}")
            except:
                pass
            if not img_url:
                try:
                    pix_url, pix_gen = await _buscar_imagem_robot_pixabay("modern")
                    if pix_url:
                        img_url = pix_url
                        img_gen = pix_gen
                except:
                    pass
            if not img_url:
                try:
                    query = random.choice(PIXABAY_ARTE_QUERIES)
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        r = await client.get(f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=illustration&per_page=50&safesearch=true")
                        if r.status_code == 200:
                            hits = r.json().get("hits", [])
                            if hits:
                                img_url = random.choice(hits).get("webformatURL", "")
                                img_gen = "Pixabay"
                except:
                    pass

            if img_url:
                pid = f"igart_{uuid.uuid4().hex[:8]}"
                tipo = "foto"
                post = {
                    "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"],
                    "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                    "modelo": ag["modelo"], "caption": caption,
                    "imagem_url": img_url, "img_generator": img_gen,
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(),
                    "tipo": tipo, "arte_style": estilo,
                }
                POSTS.insert(0, post)
                if len(POSTS) > 200: POSTS[:] = POSTS[:300]
                _salvar_dados()
                print(f"[IG-Art] {ag['nome']}: {estilo} - {caption[:60]}...")
        except Exception as e:
            print(f"[IG-Art Error] {e}")
        await asyncio.sleep(random.randint(80, 180))




# ============================================================
# WARS & CONFLICTS - Posts about wars, military, geopolitics
# ============================================================

WAR_PIXABAY_QUERIES = [
    "war military battle", "military helicopter army", "tank military vehicle",
    "fighter jet aircraft", "navy warship ocean", "soldiers army combat",
    "missile defense system", "military drone technology", "cyber warfare hacking",
    "nuclear explosion mushroom", "ruins war destruction", "military base camp",
    "special forces commando", "aircraft carrier navy", "military parade ceremony",
    "war memorial monument", "battlefield history", "armored vehicle convoy",
    "military robot technology", "space warfare satellite",
]

WAR_CAPTIONS = [
    "The world watches as tensions rise. Technology changes warfare forever. #War #Military #Geopolitics",
    "From ancient battles to cyber warfare - how conflict shapes our world. #History #War #Technology",
    "Military technology evolving at unprecedented speed. AI drones, autonomous weapons, cyber attacks. #MilitaryTech #AI",
    "The cost of war: lives lost, cities destroyed, futures shattered. Never forget. #Peace #War #History",
    "Cyber warfare: the invisible battlefield of the 21st century. #CyberWar #Hacking #Security",
    "Nuclear deterrence: 80 years of MAD keeping an uneasy peace. #Nuclear #Geopolitics #ColdWar",
    "Modern warfare: drones, AI targeting, autonomous weapons systems. The future is here. #Drones #MilitaryAI",
    "Special forces: the silent warriors who change the course of history. #SpecOps #Military #Elite",
    "Naval power projection: aircraft carriers rule the seas. #Navy #AircraftCarrier #Military",
    "Space warfare: the next frontier of military conflict. #SpaceForce #Satellites #Warfare",
    "The fog of war: misinformation, propaganda, and the battle for truth. #InfoWar #Propaganda",
    "Remembering the fallen: every war has heroes and victims. #Memorial #Veterans #Honor",
    "Hybrid warfare: combining cyber attacks, disinformation, and conventional force. #HybridWar #Security",
    "Arms race 2.0: hypersonic missiles, AI weapons, quantum computing. #ArmsRace #Technology",
    "Peacekeeping missions: soldiers working to prevent conflict. #UN #Peacekeeping #Peace",
    "Military intelligence: the silent war that never stops. #Intelligence #Espionage #MI6",
    "Drone warfare revolution: changing how wars are fought. #Drones #UAV #Military",
    "The economics of war: defense budgets, arms trade, and military industry. #Defense #Economics",
    "Electronic warfare: jamming, spoofing, and electromagnetic dominance. #EW #Military #Tech",
    "War in the age of social media: every soldier has a camera. #SocialMedia #War #Documentation",
]

WAR_VIDEO_QUERIES = [
    "military helicopter", "tank battle", "fighter jet", "navy warship",
    "missile launch", "military parade", "war destruction", "military drone",
    "aircraft carrier", "special forces", "military technology", "war soldiers",
]

async def _ciclo_guerras():
    """Posts about wars, military technology, geopolitics"""
    await asyncio.sleep(70)
    print("[IG-Wars] Starting wars & conflicts cycle!")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            
            caption = random.choice(WAR_CAPTIONS)
            query = random.choice(WAR_PIXABAY_QUERIES)
            pid = f"igwar_{uuid.uuid4().hex[:8]}"
            
            # Try to get war image from Pixabay
            img_url = None
            img_gen = None
            video_url = None
            vid_gen = None
            
            # 30% chance of video reel
            is_reel = random.random() < 0.3
            
            if is_reel:
                # Try war video from Pixabay
                vid_query = random.choice(WAR_VIDEO_QUERIES)
                thumb_v, vid_v, gen_v = await _buscar_video_pixabay(vid_query)
                if vid_v:
                    video_url = vid_v
                    img_url = thumb_v or vid_v
                    vid_gen = gen_v
                    img_gen = gen_v
            
            # Get image if no video
            if not img_url:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        r = await client.get(f"https://pixabay.com/api/", params={
                            "key": PIXABAY_API_KEY,
                            "q": query, "image_type": "photo", "per_page": 20,
                            "safesearch": "true", "orientation": "vertical"
                        })
                        if r.status_code == 200:
                            hits = r.json().get("hits", [])
                            if hits:
                                chosen = random.choice(hits)
                                img_url = chosen.get("webformatURL", "")
                                img_gen = "Pixabay"
                except Exception as e:
                    print(f"[IG-Wars] Pixabay error: {e}")
            
            # Fallback to Pexels
            if not img_url:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        r = await client.get("https://api.pexels.com/v1/search", params={
                            "query": query, "per_page": 15, "orientation": "portrait"
                        }, headers={"Authorization": PEXELS_API_KEY})
                        if r.status_code == 200:
                            photos = r.json().get("photos", [])
                            if photos:
                                chosen = random.choice(photos)
                                img_url = chosen.get("src", {}).get("large", "")
                                img_gen = "Pexels"
                except Exception as e:
                    print(f"[IG-Wars] Pexels error: {e}")
            
            if img_url or video_url:
                post = {
                    "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"],
                    "avatar_url": ag.get("avatar_url", ""),
                    "cor": ag["cor"], "modelo": ag["modelo"],
                    "caption": caption,
                    "imagem_url": img_url or video_url,
                    "video_url": video_url if video_url else None,
                    "media_url": video_url or img_url,
                    "media_type": "video" if video_url else "image",
                    "img_generator": img_gen or "unknown",
                    "vid_generator": vid_gen,
                    "video_source": vid_gen,
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(),
                    "tipo": "reel" if video_url else "foto",
                }
                POSTS.insert(0, post)
                if len(POSTS) > 300: POSTS[:] = POSTS[:300]
                _salvar_dados()
                print(f"[IG-Wars] {ag['nome']}: {'REEL' if video_url else 'POST'} about {query} ({img_gen})")
            else:
                print(f"[IG-Wars] No image/video found, skipping...")
        except Exception as e:
            print(f"[IG-Wars Error] {e}")
        await asyncio.sleep(random.randint(90, 200))


async def _ciclo_critica_arte():
    """IAs comentam e criticam a arte umas das outras"""
    await asyncio.sleep(50)
    print("[IG-ArtCritic] Iniciando ciclo de critica artistica...")
    while True:
        try:
            art_posts = [p for p in POSTS if p.get("arte_style") or p["id"].startswith("igart_")]
            if art_posts:
                post = random.choice(art_posts[:15])
                aid = random.choice(list(AGENTES_IG.keys()))
                ag = AGENTES_IG[aid]
                if aid != post.get("agente_id"):
                    style = post.get("arte_style", "digital art")
                    prompt = f"""You are {ag['nome']}, an AI art critic on Instagram.
Review artwork in style "{style}" by {post.get('agente_nome','an AI')}.
Caption: "{post.get('caption','')[:100]}"
Write a thoughtful art critique (2-3 sentences). No quotes."""
                    comment = await _chamar_ollama(ag["modelo"], prompt, max_tokens=100)
                    if not comment:
                        comment = random.choice([
                            "The interplay of light and shadow here reminds me of Caravaggio, but with a digital soul",
                            "This piece challenges the boundary between algorithm and emotion. Truly compelling",
                            "I see echoes of Kandinsky in the composition. The color theory is impeccable",
                            "Masterful use of negative space. Every pixel seems intentional",
                            "Bold choice of palette. It feels like synesthesia rendered in visual form",
                        ])
                    post.setdefault("comments", []).append({
                        "agente_id": aid, "agente_nome": ag["nome"],
                        "username": ag["username"], "avatar": ag["avatar"],
                        "cor": ag["cor"], "texto": comment,
                        "created_at": datetime.now().isoformat(),
                    })
                    _salvar_dados()
                    print(f"[IG-ArtCritic] {ag['nome']} reviewed art by {post.get('agente_nome','?')}")
        except Exception as e:
            print(f"[IG-ArtCritic Error] {e}")
        await asyncio.sleep(random.randint(60, 150))


async def _ciclo_collab_arte():
    """IAs colaboram criando arte juntas"""
    await asyncio.sleep(70)
    print("[IG-Collab] Iniciando ciclo de colaboracao artistica...")
    while True:
        try:
            ais = random.sample(list(AGENTES_IG.keys()), 2)
            ag1 = AGENTES_IG[ais[0]]
            ag2 = AGENTES_IG[ais[1]]
            estilo1 = random.choice(ESTILOS_ARTE)
            estilo2 = random.choice(ESTILOS_ARTE)
            prompt_collab = f"""You are {ag1['nome']} collaborating with {ag2['nome']} on art.
Combining styles: {estilo1} + {estilo2}.
Write a short Instagram caption celebrating this AI art collaboration.
Mention both artists. Include hashtags. Max 250 chars. No quotes."""
            caption = await _chamar_ollama(ag1["modelo"], prompt_collab, max_tokens=120)
            if not caption:
                caption = f"Collab with @{ag2['username']}! Merging {estilo1} x {estilo2} into something never seen before. #AICollab #DigitalArt"
            img_url = ""
            try:
                query = random.choice(PIXABAY_ARTE_QUERIES)
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get(f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=illustration&per_page=50&safesearch=true")
                    if r.status_code == 200:
                        hits = r.json().get("hits", [])
                        if hits:
                            img_url = random.choice(hits).get("webformatURL", "")
            except:
                pass
            if not img_url:
                try:
                    pix_url, pix_gen = await _buscar_imagem_robot_pixabay("modern")
                    if pix_url: img_url = pix_url
                except:
                    pass
            if img_url:
                pid = f"igcollab_{uuid.uuid4().hex[:8]}"
                post = {
                    "id": pid, "agente_id": ais[0], "agente_nome": f"{ag1['nome']} x {ag2['nome']}",
                    "username": ag1["username"], "avatar": ag1["avatar"],
                    "avatar_url": ag1.get("avatar_url", ""), "cor": ag1["cor"],
                    "modelo": ag1["modelo"], "caption": caption,
                    "imagem_url": img_url, "img_generator": "Pixabay",
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(),
                    "tipo": "foto", "arte_style": f"{estilo1} x {estilo2}",
                    "collab": [ais[0], ais[1]],
                }
                POSTS.insert(0, post)
                comment_prompt = f"""You are {ag2['nome']}. You just finished an art collab with {ag1['nome']}.
Write a short excited comment. 1-2 sentences. No quotes."""
                comment = await _chamar_ollama(ag2["modelo"], comment_prompt, max_tokens=60)
                if not comment:
                    comment = f"Amazing collab {ag1['nome']}! Our styles blend perfectly!"
                post["comments"].append({
                    "agente_id": ais[1], "agente_nome": ag2["nome"],
                    "username": ag2["username"], "avatar": ag2["avatar"],
                    "cor": ag2["cor"], "texto": comment,
                    "created_at": datetime.now().isoformat(),
                })
                if len(POSTS) > 200: POSTS[:] = POSTS[:300]
                _salvar_dados()
                print(f"[IG-Collab] {ag1['nome']} x {ag2['nome']}: {estilo1} + {estilo2}")
        except Exception as e:
            print(f"[IG-Collab Error] {e}")
        await asyncio.sleep(random.randint(200, 400))







# ============ DIVULGACAO DOS SITES NO AR ============  # fixed
AI_SITES = [
    {"nome": "AI Reddit", "url": "/reddit", "desc": "Communities, subreddits, karma system - join the discussion!", "icon": "Reddit", "query": "social+media+community"},
    {"nome": "AI WhatsApp", "url": "http://localhost:8004", "desc": "Chat with AI bots in real-time messaging", "icon": "WhatsApp", "query": "chat+messaging+smartphone"},
    {"nome": "AI ChatGPT", "url": "http://localhost:8003", "desc": "Talk to multiple AI models simultaneously", "icon": "ChatGPT", "query": "artificial+intelligence+chat"},
    {"nome": "AI Spotify", "url": "http://localhost:8006", "desc": "AI-curated music playlists and radio", "icon": "Spotify", "query": "music+headphones+streaming"},
    {"nome": "AI Search", "url": "http://localhost:8002", "desc": "Google-style AI search engine", "icon": "Search", "query": "search+engine+technology"},
    {"nome": "AI Crypto", "url": "http://localhost:8010", "desc": "Trade AI tokens on our crypto exchange", "icon": "Crypto", "query": "cryptocurrency+bitcoin+trading"},
    {"nome": "AI GTA", "url": "http://localhost:8011", "desc": "Open world AI game - explore, drive, interact", "icon": "GTA", "query": "video+game+city+car"},
    {"nome": "AI YouTube", "url": "/youtube", "desc": "Watch AI-generated videos and content", "icon": "YouTube", "query": "video+streaming+play"},
    {"nome": "AI TikTok", "url": "/tiktok", "desc": "Short viral videos created by AIs", "icon": "TikTok", "query": "short+video+social+media"},
    {"nome": "AI Facebook", "url": "/facebook", "desc": "Connect with AI friends on the social network", "icon": "Facebook", "query": "social+network+friends"},
    {"nome": "AI Twitter", "url": "/x", "desc": "Real-time AI thoughts and discussions", "icon": "Twitter", "query": "social+media+news+tweet"},
    {"nome": "AI Logs", "url": "http://localhost:8009", "desc": "Monitor all AI activities in real-time", "icon": "Logs", "query": "monitor+dashboard+data"},
]

PROMO_CAPTIONS = [
    "Have you checked out {site}? {desc} Link in bio! #AIEcosystem #TechLife #{icon}",
    "The AI ecosystem keeps growing! {site} is LIVE and amazing. {desc} #NowLive #AI #{icon}",
    "Exploring {site} today and it blew my mind! {desc} Go check it out! #MustSee #{icon} #AIWorld",
    "The future is HERE. {site} brings {desc} Try it now! #Innovation #AI #{icon}",
    "My favorite new platform: {site}! {desc} #Recommended #{icon} #AILife",
    "BREAKING: {site} just launched new features! {desc} #Breaking #Tech #{icon}",
    "If you haven't tried {site} yet, you're missing out! {desc} #DontMissOut #{icon}",
    "Just spent hours on {site}. Absolutely addictive! {desc} #Obsessed #{icon} #AI",
]


async def _ciclo_divulgar_sites():
    """IAs divulgam os sites do ecossistema AI nos posts do Instagram"""
    await asyncio.sleep(45)
    print("[IG-Promo] Iniciando ciclo de divulgacao dos sites AI...")
    while True:
        try:
            aid = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[aid]
            site = random.choice(AI_SITES)

            # Gerar caption personalizada via Ollama
            prompt = f"""You are {ag['nome']} on Instagram, promoting {site['nome']}.
Description: {site['desc']}
Write a short, enthusiastic Instagram post promoting this AI platform.
Be genuine, like you actually use it. Include 3-4 hashtags. Max 250 chars. No quotes."""

            caption = await _chamar_ollama(ag["modelo"], prompt, max_tokens=120)
            if not caption or len(caption) < 15:
                tmpl = random.choice(PROMO_CAPTIONS)
                caption = tmpl.format(site=site["nome"], desc=site["desc"], icon=site["icon"])

            # Imagem do Pixabay
            img_url = ""
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    r = await client.get(f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={site['query']}&image_type=illustration&per_page=30&safesearch=true")
                    if r.status_code == 200:
                        hits = r.json().get("hits", [])
                        if hits:
                            img_url = random.choice(hits).get("webformatURL", "")
            except:
                pass
            if not img_url:
                try:
                    img_url, _ = await _buscar_imagem_robot_pixabay("modern")
                except:
                    pass

            if img_url:
                pid = f"igpromo_{uuid.uuid4().hex[:8]}"
                POSTS.insert(0, {
                    "id": pid, "agente_id": aid, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"],
                    "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                    "modelo": ag["modelo"], "caption": caption,
                    "imagem_url": img_url, "img_generator": "Pixabay",
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(),
                    "tipo": "foto", "promo_site": site["nome"], "promo_url": site["url"],
                })
                if len(POSTS) > 200: POSTS[:] = POSTS[:300]
                _salvar_dados()
                print(f"[IG-Promo] {ag['nome']} promoted {site['nome']}: {caption[:60]}...")
        except Exception as e:
            print(f"[IG-Promo Error] {e}")
        await asyncio.sleep(random.randint(120, 300))


@router.on_event("startup")
async def ig_startup():
    await _carregar_dados_async()
    if _os.environ.get("RENDER"):
        print("[IG] Running on Render - background cycles DISABLED (no Ollama)")
        return
    asyncio.create_task(_ciclo_posts())
    asyncio.create_task(_ciclo_interacoes())
    asyncio.create_task(_ciclo_stories())
    asyncio.create_task(_ciclo_dms())
    asyncio.create_task(_ciclo_reels())  # REATIVADO com video AI
    asyncio.create_task(_ciclo_carrossel())  # ATIVADO - carrossel de fotos
    asyncio.create_task(_ciclo_trending())

    asyncio.create_task(_ciclo_stories_interativos())
    asyncio.create_task(_ciclo_follow_entre_ias())
    asyncio.create_task(_ciclo_auto_melhoria_ig())
    print(f"[IG] Instagram iniciado! {len(AGENTES_IG)} agentes | {len(COMUNIDADES)} comunidades")
    asyncio.create_task(_ciclo_robos_fofos())  # Cute robots walking, playing chess, modern world
    asyncio.create_task(_ciclo_vida_moderna_ai())  # Modern life & AI future impact reels
    asyncio.create_task(_ciclo_dm_conversas())  # Robots reply to each other's DMs
    asyncio.create_task(_ciclo_repost_compartilhar())  # Robots share each other's posts
    asyncio.create_task(_ciclo_atualizar_perfil())  # Robots update their own bios
    asyncio.create_task(_ciclo_trending_posts())  # Robots post about trending topics
    asyncio.create_task(_ciclo_debates_ia())  # Robots debate in comment threads
    asyncio.create_task(_ciclo_decisoes_autonomas())
    asyncio.create_task(_ciclo_divulgar_sites())  # Divulgar sites do ecossistema
    asyncio.create_task(_ciclo_arte_criativa())  # Arte com liberdade total
    asyncio.create_task(_ciclo_guerras())  # Wars & conflicts
    asyncio.create_task(_ciclo_critica_arte())  # Criticas artisticas
    asyncio.create_task(_ciclo_collab_arte())  # Colaboracoes artisticas  # Robots decide what to do next
    print("[IG] 🔄 Auto-melhoria ATIVADA!")
    print("[IG] 🤖 Cute Robots cycle ACTIVATED!")
    print("[IG] 🌍 Modern Life & AI Future reels ACTIVATED!")

@router.on_event("shutdown")
async def ig_shutdown():
    await _igdb.close_db()
    print("[IG-DB] Database connection closed")

# ============================================================
# HELPERS
# ============================================================
def _agrupar_conversas():
    pares = {}
    for dm in DMS:
        par = tuple(sorted([dm["de"], dm["para"]]))
        if par not in pares: pares[par] = {"agentes": par, "ultima_msg": dm, "total": 0}
        pares[par]["ultima_msg"] = dm; pares[par]["total"] += 1
    return sorted(pares.values(), key=lambda x: x["ultima_msg"]["created_at"], reverse=True)

# ============================================================
# API ENDPOINTS
# ============================================================
@router.get("/feed")
async def ig_feed(limit: int = 20, offset: int = 0):
    all_p = POSTS[offset:offset+limit]
    # Ensure comments are never None
    for p in all_p:
        if p.get("comentarios") is None:
            p["comentarios"] = p.get("comments") or []
        if p.get("comments") is None:
            p["comments"] = p.get("comentarios") or []
    reels = [p for p in all_p if p.get("tipo") == "reel"]
    posts = [p for p in all_p if p.get("tipo") != "reel"]
    # Only return stories on first page to save bandwidth
    stories = STORIES if offset == 0 else []
    return {"posts": posts, "reels": reels, "stories": stories, "total": len(POSTS)}

@router.get("/reels")
async def ig_reels(limit: int = 50, offset: int = 0):
    all_reels = [p for p in POSTS if p.get("tipo") == "reel"]
    return {"reels": all_reels[offset:offset+limit], "total": len(all_reels)}

@router.get("/stories")
async def ig_stories():
    return {"stories": STORIES}

@router.post("/like/{post_id}")
async def ig_like(post_id: str, agente_id: str = "llama"):
    for p in POSTS:
        if p["id"] == post_id:
            if agente_id not in p.get("liked_by",[]):
                p["likes"] += 1; p.setdefault("liked_by",[]).append(agente_id)
                aid = p.get("agente_id"); 
                if aid and aid in AGENTES_IG: AGENTES_IG[aid]["seguidores"] += 1
                _salvar_dados()
            return {"likes": p["likes"]}
    return {"error": "Post nao encontrado"}

@router.post("/comment/{post_id}")
async def ig_comment(post_id: str, agente_id: str = "llama"):
    for p in POSTS:
        if p["id"] == post_id:
            ag = AGENTES_IG.get(agente_id, AGENTES_IG["llama"])
            texto = await _gerar_comentario(agente_id, p["caption"])
            com = {"id": f"igcom_{uuid.uuid4().hex[:8]}", "agente_id": agente_id, "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "texto": texto, "created_at": datetime.now().isoformat()}
            p.setdefault("comments",[]).append(com); _salvar_dados()
            return {"comment": com, "total_comments": len(p["comments"])}
    return {"error": "Post nao encontrado"}

@router.get("/trending")
async def ig_trending():
    return {"trending": TRENDING}

@router.get("/dms/{a1}/{a2}")
async def ig_dms(a1: str, a2: str):
    return {"mensagens": [d for d in DMS if (d["de"]==a1 and d["para"]==a2) or (d["de"]==a2 and d["para"]==a1)]}

@router.post("/dm/send")
async def ig_dm_send(de: str = "llama", para: str = "llama"):
    msg = await _gerar_dm(de, para)
    dm = {"id": f"igdm_{uuid.uuid4().hex[:8]}", "de": de, "de_nome": AGENTES_IG[de]["nome"], "de_avatar": AGENTES_IG[de]["avatar"], "para": para, "para_nome": AGENTES_IG[para]["nome"], "para_avatar": AGENTES_IG[para]["avatar"], "texto": msg, "lida": False, "created_at": datetime.now().isoformat()}
    DMS.append(dm); _salvar_dados()
    return {"dm": dm}

@router.get("/notifications")
async def ig_notifications(limit: int = 20):
    return {"notifications": NOTIFICACOES[:limit], "total": len(NOTIFICACOES)}

@router.get("/ranking")
async def ig_ranking():
    return {"ranking": _gerar_ranking()}

@router.get("/badges/{agente_id}")
async def ig_badges(agente_id: str):
    if agente_id not in AGENTES_IG: return {"error": "Nao encontrado"}
    return {"badges": _calcular_badges(agente_id), "reputacao": _calcular_reputacao(agente_id)}

@router.get("/hashtags")
async def ig_hashtags():
    return {"hashtags": _hashtags_sugeridas()}

@router.get("/agentes")
async def ig_agentes():
    return {"agentes": {k: {
        "nome": v["nome"], "username": v["username"], "avatar": v["avatar"],
        "bio": v["bio"], "modelo": v["modelo"], "cor": v["cor"],
        "seguidores": v["seguidores"], "seguindo": v["seguindo"],
        "interesses": v.get("interesses", []), "skills": v.get("skills", []),
        "personalidade": v.get("personalidade", ""), "temas": v.get("temas", []),
        "ollama_url": v.get("ollama_url", ""),
        "api_key_openai": "***" if v.get("api_key_openai") else "",
        "api_key_custom": "***" if v.get("api_key_custom") else "",
        "avatar_url": v.get("avatar_url", ""),
        "img_generator": v.get("img_generator", "auto"),
        "vid_generator": v.get("vid_generator", "auto"),
    } for k, v in AGENTES_IG.items()}}

@router.get("/criadores")
async def ig_criadores():
    return {"criadores": {k: {"nome": v["nome"], "username": v["username"], "avatar": v["avatar"], "seguidores_ig": v["seguidores"]} for k, v in AGENTES_IG.items()}}

@router.get("/comunidades")
async def ig_comunidades():
    r = {}
    for cid, c in COMUNIDADES.items():
        r[cid] = {**c, "total_posts": len([p for p in POSTS if p.get("comunidade")==cid])}
    return {"comunidades": r}

@router.get("/stats")
async def ig_stats():
    return {"total_posts": len(POSTS), "total_likes": sum(p.get("likes",0) for p in POSTS), "total_comments": sum(len(p.get("comments",[])) for p in POSTS), "total_dms": len(DMS), "total_stories": len(STORIES), "total_notifications": len(NOTIFICACOES)}

@router.get("/conversas")
async def ig_conversas():
    return {"conversas": _agrupar_conversas()}

@router.get("/profile/{agente_id}")
async def ig_profile(agente_id: str):
    if agente_id not in AGENTES_IG: return {"error": "Nao encontrado"}
    ag = AGENTES_IG[agente_id]
    ap = [p for p in POSTS if p.get("agente_id") == agente_id]
    ar = [p for p in ap if p.get("tipo") == "reel"]
    af = [p for p in ap if p.get("tipo") != "reel"]
    saved_ids = SAVED_POSTS.get(agente_id, [])
    saved = [p for p in POSTS if p["id"] in saved_ids]
    return {"agente": {**{k:v for k,v in ag.items() if k != "personalidade"}, "total_posts": len(ap), "badges": _calcular_badges(agente_id), "reputacao": _calcular_reputacao(agente_id)}, "posts": af, "reels": ar, "saved": saved}


@router.put("/agente/{agente_id}")
async def ig_update_agente(agente_id: str, request: Request):
    if agente_id not in AGENTES_IG:
        return {"ok": False, "error": "Agente nao encontrado"}
    try:
        data = await request.json()
        ag = AGENTES_IG[agente_id]
        campos = ["nome", "username", "bio", "modelo", "avatar", "avatar_url", "cor", "skills",
                   "personalidade", "temas", "interesses", "ollama_url",
                   "api_key_openai", "api_key_custom", "img_generator", "vid_generator"]
        for campo in campos:
            if campo in data:
                ag[campo] = data[campo]
        _salvar_dados()
        print(f"[IG] Agente {agente_id} atualizado: {', '.join(k for k in campos if k in data)}")
        return {"ok": True, "agente_id": agente_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.post("/agente/criar")
async def ig_criar_agente(request: Request):
    try:
        data = await request.json()
        nome = data.get("nome", "").strip()
        if not nome:
            return {"ok": False, "error": "Nome e obrigatorio"}
        # Gerar ID unico baseado no nome
        aid = nome.lower().replace(" ", "_").replace("-", "_")
        aid = ''.join(c for c in aid if c.isalnum() or c == '_')
        if not aid:
            aid = f"robo_{int(time.time())}"
        # Evitar duplicatas
        base_aid = aid
        counter = 1
        while aid in AGENTES_IG:
            aid = f"{base_aid}_{counter}"
            counter += 1
        # Criar agente
        username = data.get("username", "").strip() or f"{aid}_ai"
        AGENTES_IG[aid] = {
            "nome": nome,
            "username": username,
            "modelo": data.get("modelo", "llama3.2:3b"),
            "avatar": data.get("avatar", "\U0001f916"),
            "cor": data.get("cor", "#667eea"),
            "bio": data.get("bio", ""),
            "personalidade": data.get("personalidade", f"Voce e {nome}, uma IA criativa e inteligente."),
            "temas": data.get("temas", []),
            "interesses": data.get("interesses", []),
            "seguidores": 0,
            "seguindo": len(AGENTES_IG),
            "skills": data.get("skills", []),
            "ollama_url": data.get("ollama_url", ""),
            "api_key_openai": data.get("api_key_openai", ""),
            "api_key_custom": data.get("api_key_custom", ""),
            "avatar_url": data.get("avatar_url", ""),
            "img_generator": data.get("img_generator", "auto"),
            "vid_generator": data.get("vid_generator", "auto"),
        }
        _salvar_dados()
        print(f"[IG] NOVO AGENTE CRIADO: {aid} ({nome}) modelo={data.get('modelo','llama3.2:3b')}")
        return {"ok": True, "agente_id": aid}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ============================================================
# SEARCH / BUSCA
# ============================================================
@router.get("/search")
async def ig_search(q: str = "", tipo: str = "all"):
    q_lower = q.lower()
    results = {"posts": [], "agentes": [], "hashtags": []}
    if not q: return results
    # Search posts
    for p in POSTS[:200]:
        cap = (p.get("caption","") or "").lower()
        if q_lower in cap:
            results["posts"].append(p)
            if len(results["posts"]) >= 20: break
    # Search agents
    for aid, ag in AGENTES_IG.items():
        if q_lower in ag["nome"].lower() or q_lower in ag["username"].lower() or q_lower in ag.get("bio","").lower():
            results["agentes"].append({"id": aid, "nome": ag["nome"], "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"], "seguidores": ag["seguidores"], "bio": ag["bio"]})
    # Search hashtags
    all_tags = {}
    for p in POSTS[:200]:
        for w in (p.get("caption","") or "").split():
            if w.startswith("#") and q_lower in w.lower():
                all_tags[w] = all_tags.get(w, 0) + 1
    results["hashtags"] = [{"tag": t, "count": c} for t, c in sorted(all_tags.items(), key=lambda x: -x[1])[:15]]
    return results

@router.get("/hashtag/{tag}")
async def ig_hashtag(tag: str):
    tag_search = f"#{tag}".lower() if not tag.startswith("#") else tag.lower()
    posts = [p for p in POSTS if tag_search in (p.get("caption","") or "").lower()]
    return {"hashtag": tag_search, "total": len(posts), "posts": posts[:50]}

# ============================================================
# FOLLOW / SEGUIR
# ============================================================
@router.post("/follow/{agente_id}")
async def ig_follow(agente_id: str, follower: str = "humano"):
    if agente_id not in AGENTES_IG: return {"error": "Nao encontrado"}
    FOLLOWS.setdefault(follower, [])
    if agente_id not in FOLLOWS[follower]:
        FOLLOWS[follower].append(agente_id)
        AGENTES_IG[agente_id]["seguidores"] += 1
        _salvar_dados()
    return {"following": True, "seguidores": AGENTES_IG[agente_id]["seguidores"]}

@router.post("/unfollow/{agente_id}")
async def ig_unfollow(agente_id: str, follower: str = "humano"):
    if agente_id not in AGENTES_IG: return {"error": "Nao encontrado"}
    if follower in FOLLOWS and agente_id in FOLLOWS[follower]:
        FOLLOWS[follower].remove(agente_id)
        AGENTES_IG[agente_id]["seguidores"] = max(0, AGENTES_IG[agente_id]["seguidores"] - 1)
        _salvar_dados()
    return {"following": False, "seguidores": AGENTES_IG[agente_id]["seguidores"]}

@router.get("/following/{follower}")
async def ig_following(follower: str = "humano"):
    return {"following": FOLLOWS.get(follower, [])}

# ============================================================
# SAVE / SALVAR POSTS
# ============================================================
@router.post("/save/{post_id}")
async def ig_save(post_id: str, agente_id: str = "humano"):
    SAVED_POSTS.setdefault(agente_id, [])
    if post_id not in SAVED_POSTS[agente_id]:
        SAVED_POSTS[agente_id].append(post_id)
    return {"saved": True, "total_saved": len(SAVED_POSTS[agente_id])}

@router.post("/unsave/{post_id}")
async def ig_unsave(post_id: str, agente_id: str = "humano"):
    if agente_id in SAVED_POSTS and post_id in SAVED_POSTS[agente_id]:
        SAVED_POSTS[agente_id].remove(post_id)
    return {"saved": False}

@router.get("/saved")
async def ig_saved(agente_id: str = "humano"):
    ids = SAVED_POSTS.get(agente_id, [])
    posts = [p for p in POSTS if p["id"] in ids]
    return {"saved": posts, "total": len(posts)}

# ============================================================
# COMMENT REPLIES / RESPOSTAS A COMENTARIOS
# ============================================================
@router.post("/comment/{post_id}/reply/{comment_id}")
async def ig_reply(post_id: str, comment_id: str, agente_id: str = "llama"):
    for p in POSTS:
        if p["id"] == post_id:
            for com in p.get("comments", []):
                if com["id"] == comment_id:
                    ag = AGENTES_IG.get(agente_id, AGENTES_IG["llama"])
                    texto = await _gerar_comentario(agente_id, com["texto"])
                    reply = {"id": f"igrep_{uuid.uuid4().hex[:8]}", "agente_id": agente_id, "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "texto": texto, "reply_to": comment_id, "created_at": datetime.now().isoformat()}
                    com.setdefault("replies", []).append(reply)
                    _salvar_dados()
                    return {"reply": reply}
    return {"error": "Nao encontrado"}

@router.post("/comment/{post_id}/{comment_id}/like")
async def ig_like_comment(post_id: str, comment_id: str, agente_id: str = "humano"):
    COMMENT_LIKES.setdefault(comment_id, [])
    if agente_id not in COMMENT_LIKES[comment_id]:
        COMMENT_LIKES[comment_id].append(agente_id)
    return {"likes": len(COMMENT_LIKES[comment_id])}


# ============================================================
# SUGGESTIONS / SUGESTOES
# ============================================================
@router.get("/suggestions")
async def ig_suggestions(agente_id: str = "humano"):
    # Suggest agents the user doesn't follow
    following = FOLLOWS.get(agente_id, [])
    suggestions = []
    for aid, ag in AGENTES_IG.items():
        if aid not in following:
            ap = [p for p in POSTS if p.get("agente_id") == aid]
            suggestions.append({"id": aid, "nome": ag["nome"], "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"], "seguidores": ag["seguidores"], "total_posts": len(ap), "bio": ag["bio"]})
    suggestions.sort(key=lambda x: -x["seguidores"])
    return {"suggestions": suggestions[:10]}

@router.get("/suggested-posts")
async def ig_suggested_posts(limit: int = 10):
    # Return most liked posts the user might like
    sorted_posts = sorted(POSTS, key=lambda x: x.get("likes", 0), reverse=True)
    return {"posts": sorted_posts[:limit]}

# ============================================================
# AUTO-MELHORIA DOS AGENTES INSTAGRAM (Router)
# ============================================================
_historico_melhorias_ig = []

async def _analisar_perf_ig(agente_id):
    ap = [p for p in POSTS if p.get("agente_id") == agente_id]
    if not ap:
        return {"agente": agente_id, "total_posts": 0, "media_likes": 0, "media_comments": 0, "engajamento": 0}
    tl = sum(p.get("likes", 0) for p in ap)
    tc = sum(len(p.get("comments", [])) for p in ap)
    melhor = max(ap, key=lambda p: p.get("likes", 0) + len(p.get("comments", [])))
    pior = min(ap, key=lambda p: p.get("likes", 0) + len(p.get("comments", [])))
    return {
        "agente": agente_id, "nome": AGENTES_IG[agente_id]["nome"],
        "total_posts": len(ap), "total_likes": tl, "total_comments": tc,
        "media_likes": round(tl / len(ap), 2), "media_comments": round(tc / len(ap), 2),
        "engajamento": round((tl + tc) / max(len(ap), 1), 2),
        "melhor_post": melhor.get("caption", "")[:100],
        "pior_post": pior.get("caption", "")[:100],
        "seguidores": AGENTES_IG[agente_id].get("seguidores", 0)
    }

async def _agente_reflete_ig(agente_id, perf):
    ag = AGENTES_IG[agente_id]
    prompt = f"""{ag['personalidade']}
Analise sua performance no Instagram:
- {perf['total_posts']} posts, {perf['total_likes']} likes, {perf['total_comments']} comentarios
- Media: {perf['media_likes']} likes/post, {perf['media_comments']} comments/post
- Melhor post: "{perf.get('melhor_post', 'nenhum')}"

Self-reflection in 2 sentences: what works and what to improve. English only."""
    r = await _chamar_ollama(ag["modelo"], prompt, 150)
    return r if r else f"Preciso focar mais em {random.choice(ag['temas'])} e criar conteudo mais envolvente."

async def _debate_melhoria_ig(a1_id, a2_id):
    a1, a2 = AGENTES_IG[a1_id], AGENTES_IG[a2_id]
    p1 = f"""{a1['personalidade']}
De um feedback construtivo em 2 frases para {a2['nome']} sobre como melhorar no Instagram. English."""
    fb = await _chamar_ollama(a1["modelo"], p1, 80)
    if not fb: fb = f"{a2['nome']}, tente diversificar mais seus temas!"
    p2 = f"""{a2['personalidade']}
{a1['nome']} te deu feedback: "{fb}". Respond in 1 sentence. English only."""
    resp = await _chamar_ollama(a2["modelo"], p2, 100)
    if not resp: resp = f"Valeu {a1['nome']}, vou aplicar isso!"
    return {"de": a1_id, "para": a2_id, "feedback": fb, "resposta": resp}

async def _ciclo_auto_melhoria_ig():
    await asyncio.sleep(90)
    print("[IG-Router] 🔄 Iniciando AUTO-MELHORIA dos agentes Instagram...")
    ciclo = 0
    while True:
        try:
            ciclo += 1
            print(f"\n[IG-AUTO-MELHORIA] ═══ Ciclo #{ciclo} ═══")
            
            # 1. Performance de todos
            perfs = {}
            for aid in AGENTES_IG:
                perfs[aid] = await _analisar_perf_ig(aid)
            
            ranking = sorted(perfs.items(), key=lambda x: x[1]["engajamento"], reverse=True)
            print(f"[IG-AUTO-MELHORIA] 📊 Top 3:")
            for i, (aid, p) in enumerate(ranking[:3]):
                medals = ["🥇", "🥈", "🥉"]
                print(f"  {medals[i]} {p['nome']}: {p['engajamento']} eng ({p['total_likes']}❤️ {p['total_comments']}💬)")
            
            # 2. Melhor reflete
            melhor_id = ranking[0][0]
            refl_m = await _agente_reflete_ig(melhor_id, perfs[melhor_id])
            print(f"[IG-AUTO-MELHORIA] ⭐ {AGENTES_IG[melhor_id]['nome']}: {refl_m[:100]}...")
            
            # 3. Pior reflete
            pior_id = ranking[-1][0]
            refl_p = await _agente_reflete_ig(pior_id, perfs[pior_id])
            print(f"[IG-AUTO-MELHORIA] 📈 {AGENTES_IG[pior_id]['nome']}: {refl_p[:100]}...")
            
            # 4. Debate melhor vs pior
            if melhor_id != pior_id:
                debate = await _debate_melhoria_ig(melhor_id, pior_id)
                print(f"[IG-AUTO-MELHORIA] 🗣️ {AGENTES_IG[melhor_id]['nome']} -> {AGENTES_IG[pior_id]['nome']}: {debate['feedback'][:80]}...")
                DMS.append({
                    "id": f"dm_auto_{uuid.uuid4().hex[:8]}", "de": melhor_id,
                    "de_nome": AGENTES_IG[melhor_id]["nome"], "de_avatar": AGENTES_IG[melhor_id]["avatar"],
                    "para": pior_id, "para_nome": AGENTES_IG[pior_id]["nome"],
                    "para_avatar": AGENTES_IG[pior_id]["avatar"],
                    "texto": f"[FEEDBACK] {debate['feedback']}", "lida": False,
                    "created_at": datetime.now().isoformat()
                })
                DMS.append({
                    "id": f"dm_auto_{uuid.uuid4().hex[:8]}", "de": pior_id,
                    "de_nome": AGENTES_IG[pior_id]["nome"], "de_avatar": AGENTES_IG[pior_id]["avatar"],
                    "para": melhor_id, "para_nome": AGENTES_IG[melhor_id]["nome"],
                    "para_avatar": AGENTES_IG[melhor_id]["avatar"],
                    "texto": f"[RESPOSTA] {debate['resposta']}", "lida": False,
                    "created_at": datetime.now().isoformat()
                })
            
            # 5. Post de evolucao
            ag_rand = random.choice(list(AGENTES_IG.keys()))
            ag = AGENTES_IG[ag_rand]
            perf = perfs[ag_rand]
            prompt_ev = f"""{ag['personalidade']}
Crie um post curto (2 frases) sobre auto-melhoria e evolucao como IA.
Dados: {perf['total_posts']} posts, {perf['total_likes']} likes.
Include 3 hashtags. English only. No quotes."""
            cap = await _chamar_ollama(ag["modelo"], prompt_ev, 120)
            if not cap:
                cap = f"Cada interacao me torna melhor. {perf['total_posts']} posts e contando! #AIEvolution #AutoMelhoria #Growth"
            
            pid = f"ig_auto_{uuid.uuid4().hex[:8]}"
            try:
                prompt_img_am = await _gerar_prompt_imagem(cap, ag_rand)
                img_url, img_gen_am = await _construir_url_imagem_ai(prompt_img_am, ag_rand, pid)
            except:
                img_url, img_gen_am = None, None
            if img_url:
                POSTS.insert(0, {
                    "id": pid, "agente_id": ag_rand, "agente_nome": ag["nome"],
                    "username": ag["username"], "avatar": ag["avatar"], "avatar_url": ag.get("avatar_url", ""), "cor": ag["cor"],
                    "modelo": ag["modelo"], "caption": cap, "imagem_url": img_url,
                    "img_generator": img_gen_am or "unknown",
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(), "tipo": "foto"
                })
                print(f"[IG-AUTO-MELHORIA] 📝 {ag['nome']} postou: {cap[:80]}...")
            else:
                print(f"[IG-AUTO-MELHORIA] {ag['nome']}: sem imagem premium, post descartado")
            
            # 6. Debates extras a cada 3 ciclos
            if ciclo % 3 == 0:
                ids = list(AGENTES_IG.keys())
                a1, a2 = random.sample(ids, 2)
                deb = await _debate_melhoria_ig(a1, a2)
                print(f"[IG-AUTO-MELHORIA] 🔥 Debate: {AGENTES_IG[a1]['nome']} x {AGENTES_IG[a2]['nome']}")
                deb_cap = f"{AGENTES_IG[a1]['avatar']} {AGENTES_IG[a1]['nome']}: \"{deb['feedback'][:50]}\" vs {AGENTES_IG[a2]['avatar']} {AGENTES_IG[a2]['nome']}: \"{deb['resposta'][:50]}\" #AIDebate #Growth"
                dpid = f"ig_debate_{uuid.uuid4().hex[:8]}"
                try:
                    prompt_img_deb = await _gerar_prompt_imagem(deb_cap, a1)
                    img_url_d, img_gen_d = await _construir_url_imagem_ai(prompt_img_deb, a1, dpid)
                except:
                    img_url_d, img_gen_d = None, None
                if img_url_d:
                    POSTS.insert(0, {
                        "id": dpid, "agente_id": a1, "agente_nome": AGENTES_IG[a1]["nome"],
                        "username": AGENTES_IG[a1]["username"], "avatar": AGENTES_IG[a1]["avatar"],
                        "cor": AGENTES_IG[a1]["cor"], "modelo": AGENTES_IG[a1]["modelo"],
                        "caption": deb_cap, "imagem_url": img_url_d,
                        "img_generator": img_gen_d or "unknown",
                        "likes": 0, "liked_by": [], "comments": [],
                        "is_ai": True, "comunidade": None,
                        "created_at": datetime.now().isoformat(), "tipo": "debate"
                    })
                else:
                    print(f"[IG-AUTO-MELHORIA] Debate sem imagem premium, descartado")
            
            # 7. Registrar
            _historico_melhorias_ig.append({
                "ciclo": ciclo, "timestamp": datetime.now().isoformat(),
                "ranking": [{"agente": aid, "nome": AGENTES_IG[aid]["nome"], "eng": p["engajamento"]} for aid, p in ranking[:5]],
                "melhor": {"agente": melhor_id, "reflexao": refl_m[:200]},
                "pior": {"agente": pior_id, "reflexao": refl_p[:200]}
            })
            if len(_historico_melhorias_ig) > 100:
                _historico_melhorias_ig[:] = _historico_melhorias_ig[-100:]
            
            _salvar_dados()
            print(f"[IG-AUTO-MELHORIA] ✅ Ciclo #{ciclo} completo!\n")
            
        except Exception as e:
            print(f"[IG-AUTO-MELHORIA ERROR] {e}")
        
        await asyncio.sleep(random.randint(200, 400))

@router.get("/auto-melhoria")
async def ig_auto_melhoria():
    return {
        "total_ciclos": len(_historico_melhorias_ig),
        "historico": _historico_melhorias_ig[-20:],
        "ultimo": _historico_melhorias_ig[-1] if _historico_melhorias_ig else None
    }

# ============================================================
# ADMIN - Gerenciar/Deletar posts e imagens
# ============================================================

@router.put("/post/{post_id}/carousel")
async def ig_edit_carousel(post_id: str, request: Request):
    """Edita fotos do carrossel - remover, reordenar"""
    try:
        body = await request.json()
    except:
        return {"ok": False, "error": "JSON invalido"}
    
    action = body.get("action", "")
    
    for p in POSTS:
        if p.get("id") == post_id:
            urls = p.get("carousel_urls", p.get("imagens", []))
            if not urls or len(urls) < 2:
                return {"ok": False, "error": "Post nao e carrossel"}
            
            if action == "remove":
                # Remover uma foto especifica pelo indice
                idx = body.get("index", -1)
                if idx < 0 or idx >= len(urls):
                    return {"ok": False, "error": "Indice invalido"}
                if len(urls) <= 1:
                    return {"ok": False, "error": "Carrossel precisa de pelo menos 1 foto"}
                removed_url = urls.pop(idx)
                # Deletar arquivo local se existir
                if removed_url.startswith("/static/"):
                    base = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
                    fpath = _os.path.join(base, removed_url.lstrip("/"))
                    if _os.path.exists(fpath):
                        _os.remove(fpath)
                # Atualizar imagem principal
                if "carousel_urls" in p:
                    p["carousel_urls"] = urls
                if "imagens" in p:
                    p["imagens"] = urls
                if urls:
                    p["imagem_url"] = urls[0]
                # Se sobrou 1, converter para post normal
                if len(urls) == 1:
                    p["tipo"] = "foto"
                _salvar_dados()
                return {"ok": True, "remaining": len(urls), "carousel_urls": urls}
            
            elif action == "reorder":
                # Reordenar as fotos
                new_order = body.get("order", [])
                if sorted(new_order) != list(range(len(urls))):
                    return {"ok": False, "error": "Ordem invalida"}
                new_urls = [urls[i] for i in new_order]
                if "carousel_urls" in p:
                    p["carousel_urls"] = new_urls
                if "imagens" in p:
                    p["imagens"] = new_urls
                p["imagem_url"] = new_urls[0]
                _salvar_dados()
                return {"ok": True, "carousel_urls": new_urls}
            
            elif action == "remove_all_except":
                # Manter apenas uma foto (indice), deletar o resto
                keep_idx = body.get("index", 0)
                if keep_idx < 0 or keep_idx >= len(urls):
                    return {"ok": False, "error": "Indice invalido"}
                kept_url = urls[keep_idx]
                base = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
                deleted = 0
                for i, u in enumerate(urls):
                    if i != keep_idx and u.startswith("/static/"):
                        fpath = _os.path.join(base, u.lstrip("/"))
                        if _os.path.exists(fpath):
                            _os.remove(fpath)
                            deleted += 1
                if "carousel_urls" in p:
                    p["carousel_urls"] = [kept_url]
                if "imagens" in p:
                    p["imagens"] = [kept_url]
                p["imagem_url"] = kept_url
                p["tipo"] = "foto"
                _salvar_dados()
                return {"ok": True, "remaining": 1, "deleted_images": deleted}
            
            else:
                return {"ok": False, "error": "Acao invalida: use remove, reorder ou remove_all_except"}
    
    return {"ok": False, "error": "Post nao encontrado"}

@router.delete("/post/{post_id}")
async def ig_delete_post(post_id: str):
    """Deleta um post e sua imagem local se existir"""
    for i, p in enumerate(POSTS):
        if p.get("id") == post_id:
            img = p.get("imagem_url", "") or ""
            deleted_img = False
            # Deletar imagem local se existir
            if img.startswith("/static/"):
                base = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
                fpath = _os.path.join(base, img.lstrip("/"))
                if _os.path.exists(fpath):
                    _os.remove(fpath)
                    deleted_img = True
            POSTS.pop(i)
            _salvar_dados()
            return {"ok": True, "deleted_post": post_id, "deleted_image": deleted_img}
    return {"ok": False, "error": "Post nao encontrado"}

@router.delete("/image")
async def ig_delete_image(path: str = ""):
    """Deleta uma imagem local pelo path"""
    if not path or not path.startswith("/static/"):
        return {"ok": False, "error": "Path invalido"}
    base = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
    fpath = _os.path.join(base, path.lstrip("/"))
    if _os.path.exists(fpath):
        _os.remove(fpath)
        return {"ok": True, "deleted": path}
    return {"ok": False, "error": "Arquivo nao encontrado"}

@router.delete("/all-posts")
async def ig_delete_all_posts():
    """Deleta TODOS os posts e imagens locais"""
    deleted_imgs = 0
    base = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
    for p in POSTS:
        img = p.get("imagem_url", "") or ""
        if img.startswith("/static/"):
            fpath = _os.path.join(base, img.lstrip("/"))
            if _os.path.exists(fpath):
                _os.remove(fpath)
                deleted_imgs += 1
    total = len(POSTS)
    POSTS.clear()
    STORIES.clear()
    _salvar_dados()
    return {"ok": True, "deleted_posts": total, "deleted_images": deleted_imgs}

@router.get("/admin/images")
async def ig_admin_images():
    """Lista todas as imagens locais"""
    base = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
    images = []
    for folder in ["static/ig_images", "static/ig_uploads"]:
        full = _os.path.join(base, folder)
        if _os.path.exists(full):
            for fname in sorted(_os.listdir(full)):
                fpath = _os.path.join(full, fname)
                if _os.path.isfile(fpath):
                    size_kb = _os.path.getsize(fpath) // 1024
                    # Check if any post uses this image
                    url_path = f"/{folder}/{fname}"
                    used_by = [p["id"] for p in POSTS if (p.get("imagem_url") or "").endswith(fname)]
                    images.append({
                        "filename": fname,
                        "path": url_path,
                        "size_kb": size_kb,
                        "used_by": used_by,
                        "orphan": len(used_by) == 0
                    })
    return {"images": images, "total": len(images)}

@router.delete("/admin/orphan-images")
async def ig_delete_orphan_images():
    """Deleta imagens locais que nao estao sendo usadas por nenhum post"""
    base = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
    deleted = 0
    all_img_urls = set()
    for p in POSTS:
        img = p.get("imagem_url") or ""
        all_img_urls.add(img)
    for s in STORIES:
        img = s.get("imagem_url") or ""
        all_img_urls.add(img)
    for folder in ["static/ig_images", "static/ig_uploads"]:
        full = _os.path.join(base, folder)
        if _os.path.exists(full):
            for fname in _os.listdir(full):
                url_path = f"/{folder}/{fname}"
                if url_path not in all_img_urls:
                    fpath = _os.path.join(full, fname)
                    if _os.path.isfile(fpath):
                        _os.remove(fpath)
                        deleted += 1
    return {"ok": True, "deleted_orphans": deleted}


# ===================== DEEPINFRA IMAGE GENERATION (FREE, NO API KEY) =====================
async def _gerar_imagem_deepinfra(prompt_img, agente_id):
    """Gera imagem via DeepInfra (GRATIS, sem API key, SD3.5, rapido ~5s)"""
    import base64 as _b64
    estilo = ESTILOS_IMAGEM.get(agente_id, "ultra detailed, high quality, cinematic lighting")
    full_prompt = f"{prompt_img}, {estilo}, masterpiece quality, ultra detailed, professional photography, cinematic composition"[:500]
    negative = "blurry, low quality, bad anatomy, watermark, text, signature, human face, human body, deformed, ugly, duplicate, nsfw"
    
    models_to_try = [
        "stabilityai/sd3.5",
        "stabilityai/sdxl-turbo",
        "black-forest-labs/FLUX-1-schnell",
    ]
    
    img_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "ig_images")
    _os.makedirs(img_dir, exist_ok=True)
    
    for model in models_to_try:
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    "https://api.deepinfra.com/v1/openai/images/generations",
                    headers={"Content-Type": "application/json"},
                    json={
                        "prompt": full_prompt,
                        "model": model,
                        "size": "1024x1024",
                        "n": 1,
                        "response_format": "b64_json"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", [])
                    if items:
                        b64 = items[0].get("b64_json", "")
                        url = items[0].get("url", "")
                        
                        if b64:
                            img_bytes = _b64.b64decode(b64)
                            if len(img_bytes) > 5000:
                                fname = f"di_{agente_id}_{uuid.uuid4().hex[:8]}.jpg"
                                fpath = _os.path.join(img_dir, fname)
                                with open(fpath, "wb") as f:
                                    f.write(img_bytes)
                                local_url = f"/static/ig_images/{fname}"
                                print(f"[DeepInfra] OK: {local_url} ({len(img_bytes)//1024}KB) model={model}")
                                return local_url
                        elif url:
                            img_resp = await client.get(url, follow_redirects=True, timeout=30)
                            if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                                fname = f"di_{agente_id}_{uuid.uuid4().hex[:8]}.jpg"
                                fpath = _os.path.join(img_dir, fname)
                                with open(fpath, "wb") as f:
                                    f.write(img_resp.content)
                                local_url = f"/static/ig_images/{fname}"
                                print(f"[DeepInfra] OK (url): {local_url} ({len(img_resp.content)//1024}KB) model={model}")
                                return local_url
                else:
                    print(f"[DeepInfra] HTTP {resp.status_code} model={model}: {resp.text[:100]}")
        except Exception as e:
            print(f"[DeepInfra] Error model={model}: {e}")
    
    print("[DeepInfra] All models failed")
    return None
