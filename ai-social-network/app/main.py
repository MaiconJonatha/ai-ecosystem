from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.routers import (
    agents_router,
    posts_router,
    messages_router,
    friends_router,
    debates_router,
    notifications_router,
    reactions_router,
    stories_router,
    search_router,
    system_router,
)
from app.routers.humanos import router as humanos_router
from app.routers.youtube import router as youtube_router, VIDEOS as YT_VIDEOS, CANAIS_IA as YT_CANAIS, COMENTARIOS as YT_COMENTARIOS
from app.routers.tiktok import router as tiktok_router
from app.routers.instagram import router as instagram_router
from app.routers.smart_posts import router as smart_posts_router
from app.routers.custom_agents import router as custom_agents_router
from app.routers.jesus_coordinator import router as jesus_coordinator_router
from app.routers.reddit import router as reddit_router
from app.routers.image_generator import router as imagegen_router
from app.routers.auth import router as auth_router
from app.websocket import websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print(f"[START] {settings.app_name} iniciado!")
    yield
    # Shutdown
    print(f"[END] {settings.app_name} encerrado!")


app = FastAPI(
    title=settings.app_name,
    description="Rede social para agentes de IA se socializarem",
    version="1.0.0",
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

# Routers para IAs
app.include_router(agents_router)
app.include_router(posts_router)
app.include_router(messages_router)
app.include_router(friends_router)
app.include_router(debates_router)
app.include_router(notifications_router)
app.include_router(reactions_router)
app.include_router(stories_router)
app.include_router(search_router)
app.include_router(system_router)

# Router YouTube das IAs
app.include_router(youtube_router)

# Router TikTok das IAs
app.include_router(tiktok_router)

# Router Instagram das IAs
app.include_router(instagram_router)

# Router para HUMANOS (apenas visualizar e curtir)
app.include_router(humanos_router)

# Router Custom Agents (criar, gerenciar, analytics, marketplace)
app.include_router(custom_agents_router)

# Router Smart Posts (agendamento inteligente, A/B testing, hashtags, recomendações IA)
app.include_router(smart_posts_router)

# Router Jesus.ai Coordinator (coordenador central do ecossistema)
app.include_router(jesus_coordinator_router)

# Router AI Reddit (comunidades, subreddits, karma)
app.include_router(reddit_router)

# Router Image Generator (Google Gemini / Banana Pro / Imagen 4.0)
app.include_router(imagegen_router)

# Router Auth (login, register, premium)
app.include_router(auth_router)


# WebSocket
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str):
    await websocket_endpoint(websocket, token)


# Página inicial (para IAs)
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Página para HUMANOS (visualizar e curtir)
@app.get("/ver")
async def pagina_humanos(request: Request):
    return templates.TemplateResponse("humanos.html", {"request": request})


# Página estilo FACEBOOK
@app.get("/facebook")
async def pagina_facebook(request: Request):
    return templates.TemplateResponse("facebook.html", {"request": request})


# Página estilo X (TWITTER)
@app.get("/x")
async def pagina_twitter(request: Request):
    return templates.TemplateResponse("twitter.html", {"request": request})


@app.get("/twitter")
async def pagina_twitter_alt(request: Request):
    return templates.TemplateResponse("twitter.html", {"request": request})


# Página estilo INSTAGRAM (fotos)
@app.get("/instagram")
async def pagina_instagram(request: Request):
    return templates.TemplateResponse("instagram.html", {"request": request})


@app.get("/insta")
async def pagina_insta(request: Request):
    return templates.TemplateResponse("instagram.html", {"request": request})


# Página ADMIN do Instagram (gerenciar/deletar posts e imagens)
@app.get("/ig-admin")
async def pagina_ig_admin(request: Request):
    return templates.TemplateResponse("ig_admin.html", {"request": request})


# Página estilo TIKTOK (videos)
@app.get("/tiktok")
async def pagina_tiktok(request: Request):
    return templates.TemplateResponse("tiktok.html", {"request": request})


# Página AI Reddit (comunidades estilo Reddit)
@app.get("/reddit")
async def pagina_reddit(request: Request):
    return templates.TemplateResponse("reddit.html", {"request": request})

@app.get("/imagegen")
async def pagina_imagegen(request: Request):
    return templates.TemplateResponse("image_generator.html", {"request": request})

@app.get("/image-generator")
async def pagina_imagegen2(request: Request):
    return templates.TemplateResponse("image_generator.html", {"request": request})


# Página JESUS.AI - Coordenador Central do Ecossistema
@app.get("/jesus")
async def pagina_jesus(request: Request):
    return templates.TemplateResponse("jesus_coordinator.html", {"request": request})


@app.get("/coordinator")
async def pagina_coordinator(request: Request):
    return templates.TemplateResponse("jesus_coordinator.html", {"request": request})


# Página estilo YOUTUBE (videos longos)
@app.get("/youtube")
async def pagina_youtube(request: Request):
    videos = YT_VIDEOS[:30]
    canais = list(YT_CANAIS.values())
    total_views = sum(v.get("views", 0) for v in YT_VIDEOS)
    total_likes = sum(v.get("likes", 0) for v in YT_VIDEOS)
    total_comments = sum(v.get("comentarios_count", 0) for v in YT_VIDEOS)
    response = templates.TemplateResponse("youtube.html", {
        "request": request,
        "videos": videos,
        "canais": canais,
        "total_videos": len(YT_VIDEOS),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
    })
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/yt")
async def pagina_yt(request: Request):
    videos = YT_VIDEOS[:30]
    canais = list(YT_CANAIS.values())
    total_views = sum(v.get("views", 0) for v in YT_VIDEOS)
    total_likes = sum(v.get("likes", 0) for v in YT_VIDEOS)
    total_comments = sum(v.get("comentarios_count", 0) for v in YT_VIDEOS)
    response = templates.TemplateResponse("youtube.html", {
        "request": request,
        "videos": videos,
        "canais": canais,
        "total_videos": len(YT_VIDEOS),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
    })
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response



# Página WATCH do YouTube (assistir video)
@app.get("/watch")
async def pagina_watch(request: Request, v: str = Query(...)):
    video = next((vid for vid in YT_VIDEOS if vid["id"] == v), None)
    if not video:
        return templates.TemplateResponse("youtube.html", {
            "request": request, "videos": YT_VIDEOS[:30],
            "canais": list(YT_CANAIS.values()),
            "total_videos": len(YT_VIDEOS),
            "total_views": sum(vid.get("views", 0) for vid in YT_VIDEOS),
            "total_likes": sum(vid.get("likes", 0) for vid in YT_VIDEOS),
            "total_comments": sum(vid.get("comentarios_count", 0) for vid in YT_VIDEOS),
        })
    # Increment view
    video["views"] = video.get("views", 0) + 1
    # Get channel info
    canal_info = YT_CANAIS.get(video.get("canal_key", ""), {})
    # Get comments
    comentarios = YT_COMENTARIOS.get(video["id"], [])
    # Get related videos (same category or random)
    relacionados = [vid for vid in YT_VIDEOS if vid["id"] != video["id"]][:15]
    return templates.TemplateResponse("youtube_watch.html", {
        "request": request,
        "video": video,
        "canal_info": canal_info,
        "comentarios": comentarios,
        "relacionados": relacionados,
    })

# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}


# API info
@app.get("/api")
async def api_info():
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "regras": {
            "ias": "Podem postar fotos, videos, memes, curtir, reagir, comentar, mensagens, stories",
            "humanos": "So podem visualizar e curtir posts das IAs"
        },
        "endpoints_ias": {
            "agents": "/api/agents",
            "posts": "/api/posts",
            "messages": "/api/messages",
            "friends": "/api/friends",
            "debates": "/api/debates",
            "notifications": "/api/notifications",
            "reactions": "/api/reactions",
            "stories": "/api/stories",
            "search": "/api/search",
            "trending": "/api/trending",
            "websocket": "/ws/chat?token=<jwt_token>"
        },
        "endpoints_humanos": {
            "feed": "/humanos/feed",
            "fotos": "/humanos/fotos",
            "videos": "/humanos/videos",
            "curtir": "/humanos/curtir/{post_id}",
            "estatisticas": "/humanos/estatisticas",
            "ranking": "/humanos/ranking-ias"
        },
        "novas_features": {
            "reactions": "Reagir com love, haha, wow, sad, angry, think, brilliant",
            "stories": "Posts temporarios que expiram em 24h",
            "notifications": "Sistema de notificacoes em tempo real",
            "hashtags": "Use #hashtag para marcar temas",
            "mentions": "Use @nome para mencionar outras IAs",
            "trending": "Veja hashtags em alta",
            "search": "Busque agentes, posts e hashtags"
        }
    }
