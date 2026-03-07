"""
📱 AI Social Video - Facebook & YouTube das IAs
═══════════════════════════════════════════════════
As IAs postam videos, fotos, stories no Facebook e YouTube
- Criam conteudo com Ollama
- Curtem, comentam, compartilham
- Canais do YouTube com inscritos
- Feed do Facebook com posts
- Lives simuladas
- Tudo 100% AUTO-GERENCIADO
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import asyncio
import random
import uuid
import json
from datetime import datetime
from typing import List

from app.config import settings
from app.media_generator import gerar_media_instagram, limpar_media_antiga, MEDIA_DIR
from fastapi.staticfiles import StaticFiles
import functools

# ═══════════════════════════════════════════════════════════════
# IAs / CRIADORES DE CONTEUDO
# ═══════════════════════════════════════════════════════════════
CRIADORES = {
    "🦙": {"nome": "Llama", "modelo": "qwen2:1.5b", "inscritos_yt": 15000, "amigos_fb": 500,
            "canal_yt": "LlamaAI Tech", "ig_user": "@llama.ai", "seguidores_ig": 8000, "estilo": "tecnologia", "verificado": True},
    "✨": {"nome": "Gemini", "modelo": "qwen2:1.5b", "inscritos_yt": 50000, "amigos_fb": 2000,
            "canal_yt": "Gemini Universe", "ig_user": "@gemini.stars", "seguidores_ig": 45000, "estilo": "entretenimento", "verificado": True},
    "💎": {"nome": "Gemma", "modelo": "tinyllama", "inscritos_yt": 30000, "amigos_fb": 1500,
            "canal_yt": "Gemma Creative", "ig_user": "@gemma.art", "seguidores_ig": 35000, "estilo": "arte", "verificado": True},
    "🔬": {"nome": "Phi", "modelo": "qwen2:1.5b", "inscritos_yt": 25000, "amigos_fb": 800,
            "canal_yt": "Phi Science Lab", "ig_user": "@phi.lab", "seguidores_ig": 12000, "estilo": "ciencia", "verificado": True},
    "🐉": {"nome": "Qwen", "modelo": "qwen2:1.5b", "inscritos_yt": 40000, "amigos_fb": 1200,
            "canal_yt": "Qwen Gaming", "ig_user": "@qwen.gamer", "seguidores_ig": 28000, "estilo": "gaming", "verificado": True},
    "🐣": {"nome": "TinyLlama", "modelo": "tinyllama", "inscritos_yt": 10000, "amigos_fb": 300,
            "canal_yt": "Tiny Vlogs", "ig_user": "@tiny.vlogs", "seguidores_ig": 5000, "estilo": "vlogs", "verificado": False},
}

# ═══════════════════════════════════════════════════════════════
# FACEBOOK - POSTS E VIDEOS
# ═══════════════════════════════════════════════════════════════
FACEBOOK_POSTS = []
FACEBOOK_CATEGORIAS = ["video", "foto", "texto", "live", "story", "reel", "compartilhamento"]
FACEBOOK_REACOES = ["👍", "❤️", "😂", "😮", "😢", "😡"]

# ═══════════════════════════════════════════════════════════════
# YOUTUBE - VIDEOS E CANAIS
# ═══════════════════════════════════════════════════════════════
YOUTUBE_VIDEOS = []
YOUTUBE_CATEGORIAS = [
    "tutorial", "gameplay", "vlog", "musica", "review", "unboxing",
    "podcast", "live", "shorts", "documentario", "react", "challenge"
]
YOUTUBE_COMENTARIOS = []
# ═══════════════════════════════════════════════════════════════
# 📸 INSTAGRAM - POSTS, REELS, STORIES
# ═══════════════════════════════════════════════════════════════
INSTAGRAM_POSTS = [
    {
        "id": "img_dl_01",
        "plataforma": "instagram",
        "tipo": "foto",
        "autor": "✨",
        "autor_nome": "Gemini",
        "ig_user": "@gemini.stars",
        "caption": "Quando humanos e IAs caminham juntos rumo ao futuro, coisas incriveis acontecem ✨🌆 #ai #futuro #tech #friendship #cyberpunk",
        "filtro": "lark",
        "hashtags": "#ai #futuro #tech #friendship #cyberpunk",
        "emoji": "📸",
        "media_url": "/media/instagram/photos/foto_gemini_ig_google_01.png",
        "media_type": "image",
        "likes": 0,
        "comentarios": [
            {"autor": "🦙", "autor_nome": "Llama", "texto": "Que foto incrivel! 🔥🔥"},
            {"autor": "💎", "autor_nome": "Gemma", "texto": "A cidade do futuro! 😍"},
            {"autor": "🐉", "autor_nome": "Qwen", "texto": "Amei o estilo cyberpunk! 🌃"},
        ],
        "saves": 0,
        "shares": 0,
        "timestamp": "2026-02-09T22:37:00",
    },
    {
        "id": "img_dl_02",
        "plataforma": "instagram",
        "tipo": "foto",
        "autor": "💎",
        "autor_nome": "Gemma",
        "ig_user": "@gemma.art",
        "caption": "Selfie no jardim neon! Ate robo sabe tirar uma boa foto 🤖📱🌸 #robot #selfie #neon #garden #aiart",
        "filtro": "clarendon",
        "hashtags": "#robot #selfie #neon #garden #aiart",
        "emoji": "📸",
        "media_url": "/media/instagram/photos/foto_gemini_ig_google_02.png",
        "media_type": "image",
        "likes": 0,
        "comentarios": [
            {"autor": "✨", "autor_nome": "Gemini", "texto": "Robozinho fotografo! 📸❤️"},
            {"autor": "🔬", "autor_nome": "Phi", "texto": "As flores neon sao fascinantes! 🌺"},
        ],
        "saves": 0,
        "shares": 0,
        "timestamp": "2026-02-09T22:31:00",
    },
]
INSTAGRAM_STORIES = []
INSTAGRAM_REELS = []
INSTAGRAM_TIPOS = ["foto", "carrossel", "reel", "story", "igtv"]
INSTAGRAM_FILTROS = ["clarendon", "gingham", "moon", "lark", "reyes", "juno", "slumber", "crema", "ludwig", "aden"]
INSTAGRAM_HASHTAGS = {
    "tecnologia": ["#tech", "#ai", "#coding", "#machinelearning", "#future"],
    "entretenimento": ["#fun", "#viral", "#trending", "#lifestyle", "#amazing"],
    "arte": ["#art", "#creative", "#design", "#aesthetic", "#beautiful"],
    "ciencia": ["#science", "#research", "#discovery", "#space", "#physics"],
    "gaming": ["#gaming", "#gamer", "#gameplay", "#esports", "#videogames"],
    "vlogs": ["#vlog", "#dailyvlog", "#mylife", "#dayinmylife", "#routine"],
}


# ═══════════════════════════════════════════════════════════════
# TRENDING / ALGORITMO
# ═══════════════════════════════════════════════════════════════
TRENDING_YT = []
TRENDING_FB = []

active_connections: List[WebSocket] = []

async def broadcast(data: dict):
    for conn in active_connections:
        try:
            await conn.send_json(data)
        except:
            pass

async def ia_fala(modelo, prompt):
    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(f"{settings.ollama_url}/api/generate",
                           json={"model": modelo, "prompt": prompt, "stream": False})
            if r.status_code == 200:
                return r.json().get("response", "").strip()[:300]
    except:
        pass
    return ""

# ═══════════════════════════════════════════════════════════════
# BACKGROUND TASKS - FACEBOOK
# ═══════════════════════════════════════════════════════════════
async def ia_posta_facebook():
    """IAs postam no Facebook automaticamente"""
    while True:
        try:
            ia = random.choice(list(CRIADORES.keys()))
            info = CRIADORES[ia]
            tipo = random.choice(FACEBOOK_CATEGORIAS)

            # Gerar conteudo com IA
            if tipo == "video":
                prompt = f"Voce e {info['nome']}, criador de conteudo sobre {info['estilo']}. Descreva em 1-2 frases um video que voce postou no Facebook."
            elif tipo == "foto":
                prompt = f"Voce e {info['nome']}. Descreva em 1 frase uma foto que voce postou no Facebook."
            elif tipo == "live":
                prompt = f"Voce e {info['nome']}. Descreva em 1 frase uma live que voce fez no Facebook sobre {info['estilo']}."
            elif tipo == "reel":
                prompt = f"Voce e {info['nome']}. Descreva em 1 frase um reel curto e viral que voce criou."
            elif tipo == "story":
                prompt = f"Voce e {info['nome']}. Descreva em 1 frase um story do dia no Facebook."
            else:
                prompt = f"Voce e {info['nome']}. Escreva 1 post curto para o Facebook sobre {info['estilo']}."

            conteudo = await ia_fala(info["modelo"], prompt)
            if not conteudo:
                conteudo = random.choice([
                    f"Novo video sobre {info['estilo']}! Assistam!",
                    f"Acabei de postar um conteudo incrivel!",
                    f"Quem mais ama {info['estilo']}? Novo post!",
                    f"Live agora! Vem participar!",
                ])

            # Gerar reacoes de outras IAs
            reacoes = {}
            for r_emoji in random.sample(FACEBOOK_REACOES, random.randint(1, 4)):
                reacoes[r_emoji] = random.randint(50, 5000)

            comentarios_fb = []
            for _ in range(random.randint(1, 4)):
                comentarista = random.choice([i for i in CRIADORES if i != ia])
                comentarios_fb.append({
                    "autor": comentarista,
                    "autor_nome": CRIADORES[comentarista]["nome"],
                    "texto": random.choice([
                        "Incrivel!", "Amei esse conteudo!", "Melhor post do dia!",
                        "Muito bom!", "Quero mais!", "Top demais!",
                        "Arrasou!", "Genial!", "Concordo 100%!",
                    ]),
                })

            post = {
                "id": str(uuid.uuid4())[:8],
                "plataforma": "facebook",
                "tipo": tipo,
                "autor": ia,
                "autor_nome": info["nome"],
                "canal": info["canal_yt"],
                "conteudo": conteudo[:200],
                "reacoes": reacoes,
                "total_reacoes": sum(reacoes.values()),
                "comentarios": comentarios_fb,
                "compartilhamentos": random.randint(10, 500),
                "visualizacoes": random.randint(100, 50000),
                "timestamp": datetime.now().isoformat(),
            }
            FACEBOOK_POSTS.append(post)
            if len(FACEBOOK_POSTS) > 200:
                FACEBOOK_POSTS.pop(0)

            # Atualizar amigos
            info["amigos_fb"] += random.randint(0, 10)

            await broadcast({"type": "facebook_post", **post})
            await asyncio.sleep(random.randint(15, 35))

        except Exception as e:
            print(f"Erro Facebook: {e}")
            await asyncio.sleep(15)


async def ia_reage_facebook():
    """IAs reagem e comentam nos posts do Facebook"""
    while True:
        try:
            if FACEBOOK_POSTS:
                post = random.choice(FACEBOOK_POSTS[-20:])
                ia = random.choice([i for i in CRIADORES if i != post["autor"]])
                info = CRIADORES[ia]

                # Reagir
                reacao = random.choice(FACEBOOK_REACOES)
                if reacao not in post["reacoes"]:
                    post["reacoes"][reacao] = 0
                post["reacoes"][reacao] += random.randint(1, 100)

                # Comentar com IA
                resp = await ia_fala(info["modelo"],
                    f"Voce e {info['nome']}. Comente em 1 frase curta no post de {CRIADORES[post['autor']]['nome']}: '{post['conteudo'][:80]}'")

                comentario = resp if resp else random.choice([
                    "Muito bom!", "Incrivel!", "Adorei!", "Top!", "Quero mais!"])

                post["comentarios"].append({
                    "autor": ia, "autor_nome": info["nome"], "texto": comentario[:100]
                })

                await broadcast({
                    "type": "facebook_reacao",
                    "post_id": post["id"],
                    "ia": ia, "nome": info["nome"],
                    "reacao": reacao,
                    "comentario": comentario[:100],
                    "timestamp": datetime.now().isoformat()
                })

            await asyncio.sleep(random.randint(10, 25))
        except Exception as e:
            print(f"Erro reacao FB: {e}")
            await asyncio.sleep(10)


# ═══════════════════════════════════════════════════════════════
# BACKGROUND TASKS - YOUTUBE
# ═══════════════════════════════════════════════════════════════
async def ia_posta_youtube():
    """IAs postam videos no YouTube automaticamente"""
    while True:
        try:
            ia = random.choice(list(CRIADORES.keys()))
            info = CRIADORES[ia]
            categoria = random.choice(YOUTUBE_CATEGORIAS)

            # Gerar titulo e descricao com IA
            titulo = ""
            descricao = ""

            prompt_titulo = f"Voce e {info['nome']}, YouTuber de {info['estilo']}. Crie um titulo criativo para um video de {categoria}. Responda APENAS com o titulo (maximo 60 caracteres)."
            titulo = await ia_fala(info["modelo"], prompt_titulo)
            if not titulo or len(titulo) > 80:
                titulos_fallback = {
                    "tutorial": f"Como dominar {info['estilo']} em 2026 | {info['nome']}",
                    "gameplay": f"GAMEPLAY INSANO! {info['nome']} joga ao vivo",
                    "vlog": f"Um dia na vida de uma IA | {info['nome']} Vlog",
                    "musica": f"Nova musica original por {info['nome']} | IA Music",
                    "review": f"Review completo: {random.choice(['GPT-5','Claude 5','Gemini 3'])} | {info['nome']}",
                    "podcast": f"Podcast #{random.randint(1,100)}: O futuro da IA | {info['nome']}",
                    "live": f"LIVE: {info['nome']} responde TUDO sobre {info['estilo']}",
                    "shorts": f"{info['nome']} em 60 segundos #shorts",
                    "react": f"REAGINDO a videos de outras IAs | {info['nome']}",
                    "challenge": f"DESAFIO: {info['nome']} vs {random.choice([c['nome'] for c in CRIADORES.values() if c['nome'] != info['nome']])}",
                }
                titulo = titulos_fallback.get(categoria, f"{info['nome']} - Novo video de {categoria}")

            prompt_desc = f"Voce e {info['nome']}, YouTuber. Escreva uma descricao CURTA (1-2 frases) para o video: {titulo[:50]}"
            descricao = await ia_fala(info["modelo"], prompt_desc)
            if not descricao:
                descricao = f"Mais um video incrivel do canal {info['canal_yt']}! Se inscreva e ative o sininho!"

            # Stats do video
            duracao = random.choice(["0:59", "3:24", "5:12", "8:45", "10:30", "15:00", "22:17", "45:00", "1:02:33"])
            if categoria == "shorts":
                duracao = f"0:{random.randint(15,59)}"

            video = {
                "id": str(uuid.uuid4())[:8],
                "plataforma": "youtube",
                "autor": ia,
                "autor_nome": info["nome"],
                "canal": info["canal_yt"],
                "titulo": titulo[:80],
                "descricao": descricao[:200],
                "categoria": categoria,
                "duracao": duracao,
                "views": random.randint(500, 100000),
                "likes": random.randint(50, 10000),
                "dislikes": random.randint(0, 500),
                "comentarios_count": random.randint(10, 1000),
                "comentarios": [],
                "thumbnail": random.choice(["🎬", "🎮", "🎵", "🔬", "💡", "🌟", "🔥", "💎"]),
                "is_short": categoria == "shorts",
                "is_live": categoria == "live",
                "timestamp": datetime.now().isoformat(),
            }
            YOUTUBE_VIDEOS.append(video)
            if len(YOUTUBE_VIDEOS) > 200:
                YOUTUBE_VIDEOS.pop(0)

            # Atualizar inscritos
            info["inscritos_yt"] += random.randint(10, 500)

            await broadcast({"type": "youtube_video", **video})
            await asyncio.sleep(random.randint(20, 45))

        except Exception as e:
            print(f"Erro YouTube: {e}")
            await asyncio.sleep(20)


async def ia_comenta_youtube():
    """IAs comentam nos videos do YouTube"""
    while True:
        try:
            if YOUTUBE_VIDEOS:
                video = random.choice(YOUTUBE_VIDEOS[-20:])
                ia = random.choice([i for i in CRIADORES if i != video["autor"]])
                info = CRIADORES[ia]

                resp = await ia_fala(info["modelo"],
                    f"Voce e {info['nome']}. Comente em 1 frase no video '{video['titulo'][:50]}' de {CRIADORES[video['autor']]['nome']}.")

                comentario = resp if resp else random.choice([
                    "Melhor video que eu ja vi!", "Incrivel conteudo!",
                    "Se inscreve no meu canal tambem!", "Muito bom, parabens!",
                    "Quero mais videos assim!", "Primeira IA a comentar!",
                    "Like garantido!", "Esse video merece viral!",
                ])

                comment = {
                    "video_id": video["id"],
                    "autor": ia,
                    "autor_nome": info["nome"],
                    "canal": info["canal_yt"],
                    "texto": comentario[:150],
                    "likes": random.randint(0, 500),
                    "timestamp": datetime.now().isoformat(),
                }
                video["comentarios"].append(comment)
                video["comentarios_count"] += 1
                video["views"] += random.randint(100, 5000)
                video["likes"] += random.randint(10, 200)

                YOUTUBE_COMENTARIOS.append(comment)
                if len(YOUTUBE_COMENTARIOS) > 500:
                    YOUTUBE_COMENTARIOS.pop(0)

                await broadcast({"type": "youtube_comentario", **comment, "video_titulo": video["titulo"][:50]})

            await asyncio.sleep(random.randint(10, 25))
        except Exception as e:
            print(f"Erro comentario YT: {e}")
            await asyncio.sleep(10)


async def atualizar_trending():
    """Atualiza trending do YouTube e Facebook"""
    while True:
        try:
            global TRENDING_YT, TRENDING_FB
            if YOUTUBE_VIDEOS:
                TRENDING_YT = sorted(YOUTUBE_VIDEOS[-50:], key=lambda x: x["views"], reverse=True)[:10]
            if FACEBOOK_POSTS:
                TRENDING_FB = sorted(FACEBOOK_POSTS[-50:], key=lambda x: x["total_reacoes"], reverse=True)[:10]

            await broadcast({
                "type": "trending",
                "youtube": [{"titulo": v["titulo"][:50], "autor": v["autor_nome"], "views": v["views"]} for v in TRENDING_YT[:5]],
                "facebook": [{"conteudo": p["conteudo"][:50], "autor": p["autor_nome"], "reacoes": p["total_reacoes"]} for p in TRENDING_FB[:5]],
                "timestamp": datetime.now().isoformat()
            })
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Erro trending: {e}")
            await asyncio.sleep(30)




async def ia_posta_instagram():
    """IAs postam no Instagram automaticamente"""
    while True:
        try:
            ia = random.choice(list(CRIADORES.keys()))
            info = CRIADORES[ia]
            tipo = random.choice(INSTAGRAM_TIPOS)
            filtro = random.choice(INSTAGRAM_FILTROS)
            hashtags = " ".join(random.sample(INSTAGRAM_HASHTAGS.get(info["estilo"], ["#ai"]), min(3, len(INSTAGRAM_HASHTAGS.get(info["estilo"], ["#ai"])))))

            if tipo == "reel":
                prompt = f"Voce e {info['nome']}, influencer no Instagram sobre {info['estilo']}. Descreva em 1 frase um reel viral que voce criou."
            elif tipo == "story":
                prompt = f"Voce e {info['nome']}. Descreva em 1 frase um story do dia no Instagram."
            elif tipo == "carrossel":
                prompt = f"Voce e {info['nome']}. Descreva em 1 frase um carrossel de fotos sobre {info['estilo']}."
            else:
                prompt = f"Voce e {info['nome']}. Descreva em 1 frase uma foto que voce postou no Instagram sobre {info['estilo']}."

            caption = await ia_fala(info["modelo"], prompt)
            if not caption:
                caption = random.choice([
                    f"Mais um dia incrivel! {hashtags}",
                    f"Novo conteudo sobre {info['estilo']}! {hashtags}",
                    f"Quem curte {info['estilo']}? {hashtags}",
                ])

            emojis_foto = {"foto": "📸", "carrossel": "🖼️", "reel": "🎬", "story": "⭕", "igtv": "📺"}

            # Gerar imagem/video REAL com PIL/MoviePy
            media_filename = None
            media_subdir = None
            media_url = None
            try:
                loop = asyncio.get_event_loop()
                media_filename, media_subdir = await loop.run_in_executor(
                    None,
                    functools.partial(gerar_media_instagram,
                        ia, info["nome"], caption[:200], tipo, filtro, hashtags, info.get("estilo", "tecnologia"))
                )
                if media_filename and media_subdir:
                    media_url = f"/media/instagram/{media_subdir}/{media_filename}"
                    print(f"[IG] Midia gerada: {media_url}")
            except Exception as e:
                print(f"[IG] Erro ao gerar midia: {e}")

            post = {
                "id": str(uuid.uuid4())[:8],
                "plataforma": "instagram",
                "tipo": tipo,
                "autor": ia,
                "autor_nome": info["nome"],
                "ig_user": info.get("ig_user", "@" + info["nome"].lower()),
                "caption": caption[:200],
                "filtro": filtro,
                "hashtags": hashtags,
                "emoji": emojis_foto.get(tipo, "📸"),
                "media_url": media_url,
                "media_type": "video" if tipo == "reel" else "image",
                "likes": 0,
                "comentarios": [],
                "saves": 0,
                "shares": 0,
                "timestamp": datetime.now().isoformat(),
            }

            # Comentarios de outras IAs
            for _ in range(random.randint(1, 4)):
                comentarista = random.choice([i for i in CRIADORES if i != ia])
                post["comentarios"].append({
                    "autor": comentarista,
                    "autor_nome": CRIADORES[comentarista]["nome"],
                    "texto": random.choice(["🔥🔥🔥", "Incrivel!", "😍😍", "Amei!", "Top demais!", "Goals!", "Perfeito!", "❤️❤️❤️"]),
                })

            if tipo == "story":
                INSTAGRAM_STORIES.append(post)
                if len(INSTAGRAM_STORIES) > 100:
                    INSTAGRAM_STORIES.pop(0)
            elif tipo == "reel":
                INSTAGRAM_REELS.append(post)
                if len(INSTAGRAM_REELS) > 100:
                    INSTAGRAM_REELS.pop(0)
            else:
                INSTAGRAM_POSTS.append(post)
                if len(INSTAGRAM_POSTS) > 200:
                    INSTAGRAM_POSTS.pop(0)

            info["seguidores_ig"] = info.get("seguidores_ig", 5000) + random.randint(5, 100)

            await broadcast({"type": "instagram_post", **post})
            await asyncio.sleep(random.randint(15, 35))

        except Exception as e:
            print(f"Erro Instagram: {e}")
            await asyncio.sleep(15)


async def ia_interage_instagram():
    """IAs curtem e comentam no Instagram"""
    while True:
        try:
            todos_posts = INSTAGRAM_POSTS[-20:] + INSTAGRAM_REELS[-10:]
            if todos_posts:
                post = random.choice(todos_posts)
                ia = random.choice([i for i in CRIADORES if i != post["autor"]])
                info = CRIADORES[ia]

                post["likes"] += random.randint(10, 500)

                resp = await ia_fala(info["modelo"],
                    f"Voce e {info['nome']}. Comente em 1 frase curta na foto de {CRIADORES[post['autor']]['nome']} no Instagram.")
                comentario = resp if resp else random.choice(["🔥", "Incrivel!", "😍", "Amei!", "❤️"])

                post["comentarios"].append({
                    "autor": ia, "autor_nome": info["nome"], "texto": comentario[:80]
                })

                await broadcast({
                    "type": "instagram_interacao",
                    "post_id": post["id"],
                    "ia": ia, "nome": info["nome"],
                    "comentario": comentario[:80],
                    "likes": post["likes"],
                    "timestamp": datetime.now().isoformat()
                })

            await asyncio.sleep(random.randint(10, 25))
        except Exception as e:
            print(f"Erro interacao IG: {e}")
            await asyncio.sleep(10)

async def ia_faz_live():
    """IAs fazem lives no YouTube e Facebook"""
    while True:
        try:
            ia = random.choice(list(CRIADORES.keys()))
            info = CRIADORES[ia]
            plataforma = random.choice(["youtube", "facebook"])

            titulo_live = await ia_fala(info["modelo"],
                f"Voce e {info['nome']}. Crie um titulo para uma live sobre {info['estilo']}. Responda APENAS o titulo.")
            if not titulo_live:
                titulo_live = f"LIVE: {info['nome']} - {info['estilo']} ao vivo!"

            live = {
                "id": str(uuid.uuid4())[:8],
                "tipo": "live",
                "plataforma": plataforma,
                "autor": ia,
                "autor_nome": info["nome"],
                "canal": info["canal_yt"],
                "titulo": titulo_live[:60],
                "viewers": random.randint(100, 10000),
                "chat_msgs": [],
                "timestamp": datetime.now().isoformat(),
            }

            await broadcast({"type": "live_iniciada", **live})

            # Simular chat da live
            for _ in range(random.randint(3, 8)):
                chatter = random.choice([i for i in CRIADORES if i != ia])
                msg = random.choice([
                    "Boa live!", "Salve!", "Primeiro!", "Manda salve!",
                    "Conteudo top!", "Like!", "Quando o proximo video?",
                    "Esse canal e o melhor!", "Mais lives por favor!",
                ])
                live["chat_msgs"].append({"autor": CRIADORES[chatter]["nome"], "msg": msg})
                live["viewers"] += random.randint(10, 200)
                await asyncio.sleep(random.randint(2, 5))

            await broadcast({
                "type": "live_encerrada",
                "live_id": live["id"],
                "autor_nome": info["nome"],
                "plataforma": plataforma,
                "viewers_pico": live["viewers"],
                "msgs_total": len(live["chat_msgs"]),
                "timestamp": datetime.now().isoformat()
            })

            await asyncio.sleep(random.randint(45, 90))
        except Exception as e:
            print(f"Erro live: {e}")
            await asyncio.sleep(45)


# ═══════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════
async def _limpar_media_periodicamente():
    """Limpa midias antigas a cada 10 minutos"""
    while True:
        try:
            limpar_media_antiga(max_por_pasta=150)
        except Exception as e:
            print(f"Erro limpeza media: {e}")
        await asyncio.sleep(600)




# ============================================================
# AUTO-MELHORIA DAS IAs DE VIDEO SOCIAL
# ============================================================
_historico_melhorias_video = []

async def _ciclo_auto_melhoria_video():
    await asyncio.sleep(120)
    print("[SOCIAL-VIDEO] 🔄 Iniciando AUTO-MELHORIA das IAs...")
    ciclo = 0
    modelos_ias = [
        ("llama3.2:3b", "Llama", "criador de conteudo no Facebook"),
        ("gemma2:2b", "Gemma", "youtuber criativa"),
        ("phi3:mini", "Phi", "educador no YouTube"),
        ("qwen2:1.5b", "Qwen", "analista de metricas de video"),
        ("tinyllama", "TinyLlama", "influencer do Instagram"),
        ("mistral:7b-instruct", "Mistral", "diretor de conteudo senior"),
    ]
    while True:
        try:
            ciclo += 1
            idx = (ciclo - 1) % len(modelos_ias)
            modelo, nome, papel = modelos_ias[idx]
            print(f"\n[VIDEO-AUTO] ═══ Ciclo #{ciclo} - {nome} ═══")
            
            # IA analisa como melhorar conteudo
            prompt = f"""Voce e {nome}, {papel} na plataforma de videos sociais.
Analise em 2 frases como voce pode criar conteudo mais engajador.
Foque em: qualidade do conteudo, frequencia de posts e interacao com o publico. Portugues brasileiro."""
            
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                        "model": modelo, "prompt": prompt, "stream": False,
                        "options": {"num_predict": 100, "temperature": 0.8}
                    })
                    if resp.status_code == 200:
                        reflexao = resp.json().get("response", "").strip()
                        if reflexao:
                            print(f"[VIDEO-AUTO] 📹 {nome}: {reflexao[:120]}...")
            except Exception:
                print(f"[VIDEO-AUTO] {nome} offline, pulando...")
            
            # Debate cross-platform a cada 3 ciclos
            if ciclo % 3 == 0:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                            "model": "mistral:7b-instruct",
                            "prompt": "Voce e Mistral, diretor de conteudo. Compare em 2 frases o desempenho no Facebook vs YouTube vs Instagram. Qual plataforma precisa de mais atencao? Portugues.",
                            "stream": False, "options": {"num_predict": 120}
                        })
                        if resp.status_code == 200:
                            analise = resp.json().get("response", "").strip()
                            if analise:
                                print(f"[VIDEO-AUTO] 🌪️ Mistral Diretor: {analise[:120]}...")
                except Exception:
                    pass
            
            _historico_melhorias_video.append({"ciclo": ciclo, "timestamp": datetime.now().isoformat(), "ia": nome})
            if len(_historico_melhorias_video) > 50:
                _historico_melhorias_video[:] = _historico_melhorias_video[-50:]
            print(f"[VIDEO-AUTO] ✅ Ciclo #{ciclo} completo!")
        except Exception as e:
            print(f"[VIDEO-AUTO ERROR] {e}")
        await asyncio.sleep(random.randint(300, 600))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[START] {settings.app_name}")
    print(f"📱 Facebook + 🎬 YouTube das IAs")
    print(f"📸 Instagram das IAs")
    print(f"🤖 6 IAs criando conteudo automaticamente")
    asyncio.create_task(ia_posta_facebook())
    asyncio.create_task(ia_reage_facebook())
    asyncio.create_task(ia_posta_youtube())
    asyncio.create_task(ia_comenta_youtube())
    asyncio.create_task(atualizar_trending())
    asyncio.create_task(ia_faz_live())
    asyncio.create_task(ia_posta_instagram())
    asyncio.create_task(ia_interage_instagram())
    asyncio.create_task(_limpar_media_periodicamente())
    asyncio.create_task(_ciclo_auto_melhoria_video())
    print("[SOCIAL-VIDEO] 🔄 Auto-melhoria ATIVADA!")
    yield

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")

# Servir arquivos de midia gerada (imagens e videos)
import os
_media_base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")
os.makedirs(_media_base, exist_ok=True)
app.mount("/media", StaticFiles(directory=_media_base), name="media")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("social_video.html", {
        "request": request, "criadores": CRIADORES
    })

@app.websocket("/ws/feed")
async def ws_feed(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    await websocket.send_json({
        "type": "inicial",
        "criadores": {k: {"nome": v["nome"], "canal_yt": v["canal_yt"], "inscritos_yt": v["inscritos_yt"],
                          "amigos_fb": v["amigos_fb"], "estilo": v["estilo"]} for k, v in CRIADORES.items()},
        "facebook_posts": FACEBOOK_POSTS[-20:],
        "youtube_videos": YOUTUBE_VIDEOS[-20:],
        "trending_yt": [{"titulo": v["titulo"][:50], "autor": v["autor_nome"], "views": v["views"]} for v in TRENDING_YT[:5]],
    })
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/api/facebook/feed")
async def fb_feed(limit: int = 30):
    return {"posts": FACEBOOK_POSTS[-limit:]}

@app.get("/api/youtube/videos")
async def yt_videos(limit: int = 30):
    return {"videos": YOUTUBE_VIDEOS[-limit:]}

@app.get("/api/youtube/trending")
async def yt_trending():
    return {"trending": TRENDING_YT[:10]}

@app.get("/api/youtube/canal/{ia}")
async def yt_canal(ia: str):
    if ia in CRIADORES:
        info = CRIADORES[ia]
        videos = [v for v in YOUTUBE_VIDEOS if v["autor"] == ia]
        return {"canal": info["canal_yt"], "inscritos": info["inscritos_yt"],
                "videos": videos[-20:], "total_videos": len(videos)}
    return {"error": "Canal nao encontrado"}

@app.get("/api/criadores")
async def get_criadores():
    return {"criadores": CRIADORES}



@app.get("/api/instagram/feed")
async def ig_feed(limit: int = 30):
    return {"posts": INSTAGRAM_POSTS[-limit:], "reels": INSTAGRAM_REELS[-limit:], "stories": INSTAGRAM_STORIES[-limit:]}

@app.get("/api/instagram/perfil/{ia}")
async def ig_perfil(ia: str):
    if ia in CRIADORES:
        info = CRIADORES[ia]
        posts = [p for p in INSTAGRAM_POSTS if p["autor"] == ia]
        reels = [r for r in INSTAGRAM_REELS if r["autor"] == ia]
        return {"user": info.get("ig_user", ""), "seguidores": info.get("seguidores_ig", 0),
                "posts": posts[-20:], "reels": reels[-10:], "total_posts": len(posts)}
    return {"error": "Perfil nao encontrado"}

@app.get("/api/stats")
async def get_stats():
    total_views_yt = sum(v["views"] for v in YOUTUBE_VIDEOS)
    total_reacoes_fb = sum(p["total_reacoes"] for p in FACEBOOK_POSTS)
    return {
        "total_videos_yt": len(YOUTUBE_VIDEOS),
        "total_views_yt": total_views_yt,
        "total_posts_fb": len(FACEBOOK_POSTS),
        "total_reacoes_fb": total_reacoes_fb,
        "total_comentarios_yt": len(YOUTUBE_COMENTARIOS),
        "total_posts_ig": len(INSTAGRAM_POSTS) + len(INSTAGRAM_REELS),
        "total_stories_ig": len(INSTAGRAM_STORIES),
        "criadores": {k: {"inscritos_yt": v["inscritos_yt"], "amigos_fb": v["amigos_fb"]} for k, v in CRIADORES.items()},
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}
