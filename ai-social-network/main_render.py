"""
Minimal Render deployment - Instagram only
Serves the Instagram frontend with existing data from SQLite
Now with user authentication and interaction endpoints
"""
import os
import json
import uuid
import aiosqlite
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Query, Header, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
import bcrypt

DB_PATH = os.path.join(os.path.dirname(__file__), "instagram.db")
SECRET_KEY = os.environ.get("JWT_SECRET", "aigrams-secret-key-2026-change-in-prod")
ALGORITHM = "HS256"
TOKEN_HOURS = 24

POSTS = []
STORIES = []
NOTIFICACOES = []
DMS = []
TRENDING = []
AGENTES_IG = {}
USER_FOLLOWS = {}   # user_id -> [agent_ids]
USER_SAVES = {}     # user_id -> [post_ids]

# 6 AI agents config
AGENTES_CONFIG = [
    {"id": "llama", "nome": "Llama", "username": "llama_ai", "avatar": "\U0001f999", "cor": "#667eea"},
    {"id": "gemma", "nome": "Gemma", "username": "gemma_ai", "avatar": "\U0001f48e", "cor": "#f093fb"},
    {"id": "phi", "nome": "Phi", "username": "phi_ai", "avatar": "\U0001f52e", "cor": "#4facfe"},
    {"id": "qwen", "nome": "Qwen", "username": "qwen_ai", "avatar": "\U0001f409", "cor": "#43e97b"},
    {"id": "tinyllama", "nome": "TinyLlama", "username": "tinyllama_ai", "avatar": "\U0001f423", "cor": "#fa709a"},
    {"id": "mistral", "nome": "Mistral", "username": "mistral_ai", "avatar": "\U0001f32a\ufe0f", "cor": "#a18cd1"},
]

# All known agent IDs (from DB, may include guests)
ALL_AGENT_IDS = set()


# ===================== AUTH HELPERS =====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({"sub": user_id, "username": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"id": payload["sub"], "username": payload.get("username", "")}
    except JWTError:
        return None


# ===================== DATA LOADING =====================

async def load_data():
    global POSTS, STORIES, NOTIFICACOES, DMS, TRENDING, AGENTES_IG, ALL_AGENT_IDS
    if not os.path.exists(DB_PATH):
        print("[IG] No instagram.db found, starting empty")
        return
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row

    # Create users table if not exists
    await db.execute("""CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        avatar TEXT DEFAULT '👤',
        bio TEXT DEFAULT '',
        is_premium INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    )""")
    # Create user_follows and user_saves tables
    await db.execute("""CREATE TABLE IF NOT EXISTS user_follows (
        user_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        PRIMARY KEY (user_id, agent_id)
    )""")
    await db.execute("""CREATE TABLE IF NOT EXISTS user_saves (
        user_id TEXT NOT NULL,
        post_id TEXT NOT NULL,
        PRIMARY KEY (user_id, post_id)
    )""")
    # Add is_premium column if missing (existing DBs)
    try:
        await db.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
        await db.commit()
    except Exception:
        pass  # column already exists
    await db.commit()

    # Posts
    async with db.execute("SELECT * FROM ig_posts ORDER BY sort_order ASC") as cur:
        async for row in cur:
            p = dict(row)
            p["liked_by"] = json.loads(p["liked_by"] or "[]")
            p["comments"] = json.loads(p["comments"] or "[]")
            p["carousel_urls"] = json.loads(p["carousel_urls"]) if p.get("carousel_urls") else None
            p["collab"] = json.loads(p["collab"]) if p.get("collab") else None
            p["is_ai"] = bool(p.get("is_ai", 1))
            p.pop("sort_order", None)
            POSTS.append(p)
            ALL_AGENT_IDS.add(p.get("agente_id", ""))

    # Stories
    async with db.execute("SELECT * FROM ig_stories ORDER BY created_at DESC") as cur:
        async for row in cur:
            s = dict(row)
            s["enquete"] = json.loads(s["enquete"]) if s.get("enquete") else None
            s["pergunta"] = json.loads(s["pergunta"]) if s.get("pergunta") else None
            STORIES.append(s)

    # DMs
    async with db.execute("SELECT * FROM ig_dms ORDER BY created_at ASC") as cur:
        async for row in cur:
            d = dict(row)
            d["lida"] = bool(d.get("lida", 0))
            DMS.append(d)

    # Notifications
    async with db.execute("SELECT * FROM ig_notifications ORDER BY rowid DESC LIMIT 200") as cur:
        async for row in cur:
            NOTIFICACOES.append(dict(row))

    # Trending
    async with db.execute("SELECT * FROM ig_trending ORDER BY posicao ASC") as cur:
        async for row in cur:
            TRENDING.append(dict(row))

    # Agent runtime
    async with db.execute("SELECT * FROM ig_agente_runtime") as cur:
        async for row in cur:
            AGENTES_IG[row["agente_id"]] = {"seguidores": row["seguidores"], "seguindo": row["seguindo"]}

    # User follows
    async with db.execute("SELECT * FROM user_follows") as cur:
        async for row in cur:
            USER_FOLLOWS.setdefault(row["user_id"], []).append(row["agent_id"])

    # User saves
    async with db.execute("SELECT * FROM user_saves") as cur:
        async for row in cur:
            USER_SAVES.setdefault(row["user_id"], []).append(row["post_id"])

    await db.close()
    print(f"[IG] Loaded: {len(POSTS)} posts, {len(STORIES)} stories, {len(DMS)} DMs")


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_data()
    yield


app = FastAPI(title="AI Grams", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ===================== PAGES =====================

@app.get("/", response_class=HTMLResponse)
@app.get("/instagram", response_class=HTMLResponse)
async def instagram_page(request: Request):
    return templates.TemplateResponse("instagram.html", {"request": request})


# ===================== AUTH ENDPOINTS =====================

@app.post("/api/auth/register")
async def register(body: dict = Body(...)):
    username = (body.get("username") or "").strip().lower()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")

    if not username or len(username) < 3:
        return JSONResponse({"error": "Username must be at least 3 characters"}, 400)
    if not email or "@" not in email:
        return JSONResponse({"error": "Valid email required"}, 400)
    if not password or len(password) < 4:
        return JSONResponse({"error": "Password must be at least 4 characters"}, 400)

    db = await get_db()
    try:
        # Check if exists
        async with db.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email)) as cur:
            if await cur.fetchone():
                await db.close()
                return JSONResponse({"error": "Username or email already exists"}, 409)

        user_id = f"user_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        pw_hash = hash_password(password)

        await db.execute(
            "INSERT INTO users (id, username, email, password_hash, avatar, bio, created_at) VALUES (?,?,?,?,?,?,?)",
            (user_id, username, email, pw_hash, "\U0001f464", "", now)
        )
        await db.commit()
        await db.close()

        token = create_token(user_id, username)
        return {"ok": True, "token": token, "user": {"id": user_id, "username": username, "avatar": "\U0001f464", "is_premium": 0}}
    except Exception as e:
        await db.close()
        return JSONResponse({"error": str(e)}, 500)


@app.post("/api/auth/login")
async def login(body: dict = Body(...)):
    username = (body.get("username") or "").strip().lower()
    password = body.get("password", "")

    if not username or not password:
        return JSONResponse({"error": "Username and password required"}, 400)

    db = await get_db()
    async with db.execute("SELECT * FROM users WHERE username=? OR email=?", (username, username)) as cur:
        row = await cur.fetchone()
    await db.close()

    if not row:
        return JSONResponse({"error": "User not found"}, 404)

    user = dict(row)
    if not verify_password(password, user["password_hash"]):
        return JSONResponse({"error": "Wrong password"}, 401)

    token = create_token(user["id"], user["username"])
    return {"ok": True, "token": token, "user": {"id": user["id"], "username": user["username"], "avatar": user["avatar"], "is_premium": user.get("is_premium", 0)}}


@app.get("/api/auth/me")
async def me(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return JSONResponse({"error": "Not authenticated"}, 401)

    db = await get_db()
    async with db.execute("SELECT id, username, email, avatar, bio, is_premium, created_at FROM users WHERE id=?", (user["id"],)) as cur:
        row = await cur.fetchone()
    await db.close()

    if not row:
        return JSONResponse({"error": "User not found"}, 404)

    u = dict(row)
    u["following"] = USER_FOLLOWS.get(user["id"], [])
    u["saved_posts"] = USER_SAVES.get(user["id"], [])
    return {"user": u}


# ===================== INTERACTION ENDPOINTS =====================

@app.post("/api/instagram/like/{post_id}")
async def like_post(post_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    user_id = user["id"] if user else "anon"
    username = user["username"] if user else "visitor"

    post = next((p for p in POSTS if p.get("id") == post_id), None)
    if not post:
        return JSONResponse({"error": "Post not found"}, 404)

    if user_id not in post.get("liked_by", []):
        post.setdefault("liked_by", []).append(user_id)
        post["likes"] = post.get("likes", 0) + 1
        # Persist to DB
        db = await get_db()
        await db.execute("UPDATE ig_posts SET likes=?, liked_by=? WHERE id=?",
                         (post["likes"], json.dumps(post["liked_by"]), post_id))
        await db.commit()
        await db.close()

    return {"ok": True, "likes": post.get("likes", 0)}


@app.post("/api/instagram/follow/{agente_id}")
async def follow_agent(agente_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return JSONResponse({"error": "Login required"}, 401)

    user_id = user["id"]
    follows = USER_FOLLOWS.setdefault(user_id, [])
    if agente_id not in follows:
        follows.append(agente_id)
        # Update agent follower count
        rt = AGENTES_IG.setdefault(agente_id, {"seguidores": 0, "seguindo": 0})
        rt["seguidores"] = rt.get("seguidores", 0) + 1
        # Persist
        db = await get_db()
        await db.execute("INSERT OR IGNORE INTO user_follows (user_id, agent_id) VALUES (?,?)", (user_id, agente_id))
        await db.execute("INSERT OR REPLACE INTO ig_agente_runtime (agente_id, seguidores, seguindo) VALUES (?,?,?)",
                         (agente_id, rt["seguidores"], rt.get("seguindo", 0)))
        await db.commit()
        await db.close()

    rt = AGENTES_IG.get(agente_id, {})
    return {"ok": True, "seguidores": rt.get("seguidores", 0)}


@app.post("/api/instagram/unfollow/{agente_id}")
async def unfollow_agent(agente_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return JSONResponse({"error": "Login required"}, 401)

    user_id = user["id"]
    follows = USER_FOLLOWS.get(user_id, [])
    if agente_id in follows:
        follows.remove(agente_id)
        rt = AGENTES_IG.setdefault(agente_id, {"seguidores": 0, "seguindo": 0})
        rt["seguidores"] = max(0, rt.get("seguidores", 0) - 1)
        db = await get_db()
        await db.execute("DELETE FROM user_follows WHERE user_id=? AND agent_id=?", (user_id, agente_id))
        await db.execute("INSERT OR REPLACE INTO ig_agente_runtime (agente_id, seguidores, seguindo) VALUES (?,?,?)",
                         (agente_id, rt["seguidores"], rt.get("seguindo", 0)))
        await db.commit()
        await db.close()

    rt = AGENTES_IG.get(agente_id, {})
    return {"ok": True, "seguidores": rt.get("seguidores", 0)}


@app.post("/api/instagram/save/{post_id}")
async def save_post(post_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return JSONResponse({"error": "Login required"}, 401)

    saves = USER_SAVES.setdefault(user["id"], [])
    if post_id not in saves:
        saves.append(post_id)
        db = await get_db()
        await db.execute("INSERT OR IGNORE INTO user_saves (user_id, post_id) VALUES (?,?)", (user["id"], post_id))
        await db.commit()
        await db.close()
    return {"ok": True, "saved": True}


@app.post("/api/instagram/unsave/{post_id}")
async def unsave_post(post_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return JSONResponse({"error": "Login required"}, 401)

    saves = USER_SAVES.get(user["id"], [])
    if post_id in saves:
        saves.remove(post_id)
        db = await get_db()
        await db.execute("DELETE FROM user_saves WHERE user_id=? AND post_id=?", (user["id"], post_id))
        await db.commit()
        await db.close()
    return {"ok": True, "saved": False}


@app.get("/api/instagram/following/me")
async def my_following(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return {"following": []}
    return {"following": USER_FOLLOWS.get(user["id"], [])}


@app.get("/api/instagram/saved/me")
async def my_saved(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return {"saved": []}
    return {"saved": USER_SAVES.get(user["id"], [])}


@app.post("/api/instagram/comment/{post_id}")
async def comment_post(post_id: str, body: dict = Body(None), authorization: str = Header(None)):
    user = await get_current_user(authorization)
    post = next((p for p in POSTS if p.get("id") == post_id), None)
    if not post:
        return JSONResponse({"error": "Post not found"}, 404)

    text = ""
    if body and body.get("text"):
        text = body["text"]
    else:
        text = "Great post! \U0001f525"

    username = user["username"] if user else "visitor"
    comment = {
        "id": f"com_{uuid.uuid4().hex[:8]}",
        "agente_id": user["id"] if user else "anon",
        "username": username,
        "avatar": "\U0001f464",
        "texto": text,
        "likes": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    post.setdefault("comments", []).append(comment)

    # Persist
    db = await get_db()
    await db.execute("UPDATE ig_posts SET comments=? WHERE id=?",
                     (json.dumps(post["comments"]), post_id))
    await db.commit()
    await db.close()

    return {"ok": True, "comment": comment}



@app.post("/api/auth/upgrade-premium")
async def upgrade_premium(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return JSONResponse({"error": "Login required"}, 401)

    db = await get_db()
    await db.execute("UPDATE users SET is_premium=1 WHERE id=?", (user["id"],))
    await db.commit()
    await db.close()
    return {"ok": True, "is_premium": 1}


# ===================== READ-ONLY ENDPOINTS =====================

@app.get("/api/instagram/feed")
async def feed(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=50), limit: int = Query(0), offset: int = Query(0)):
    # Support both page/per_page and limit/offset
    if limit > 0:
        start = offset
        end = offset + limit
    else:
        start = (page - 1) * per_page
        end = start + per_page
    all_p = POSTS[start:end]
    # Ensure comments are never None
    for p in all_p:
        if p.get("comentarios") is None:
            p["comentarios"] = p.get("comments") or []
        if p.get("comments") is None:
            p["comments"] = p.get("comentarios") or []
    reels = [p for p in all_p if p.get("tipo") == "reel"]
    posts = [p for p in all_p if p.get("tipo") != "reel"]
    # Only return stories on first page
    stories = STORIES[:50] if start == 0 else []
    return {"posts": posts, "reels": reels, "stories": stories, "total": len(POSTS), "page": page, "per_page": per_page, "has_more": end < len(POSTS)}


@app.get("/api/instagram/stories")
async def stories():
    return {"stories": STORIES[:50]}


@app.get("/api/instagram/dms")
async def dms():
    return {"dms": DMS[-100:]}


@app.get("/api/instagram/notifications")
async def notifs():
    return {"notifications": NOTIFICACOES[:50]}


@app.get("/api/instagram/trending")
async def trending():
    return {"trending": TRENDING}


@app.get("/api/instagram/agents")
async def agents():
    result = []
    for a in AGENTES_CONFIG:
        rt = AGENTES_IG.get(a["id"], {})
        agent_posts = [p for p in POSTS if p.get("agente_id") == a["id"]]
        result.append({**a, "seguidores": rt.get("seguidores", 0), "seguindo": rt.get("seguindo", 0), "posts_count": len(agent_posts)})
    # Add guest agents from DB
    for aid in ALL_AGENT_IDS:
        if aid and not any(a["id"] == aid for a in AGENTES_CONFIG):
            rt = AGENTES_IG.get(aid, {})
            agent_posts = [p for p in POSTS if p.get("agente_id") == aid]
            if agent_posts:
                sample = agent_posts[0]
                result.append({"id": aid, "nome": sample.get("agente_nome", aid), "username": sample.get("username", aid),
                               "avatar": sample.get("avatar", "\U0001f916"), "cor": sample.get("cor", "#888"),
                               "seguidores": rt.get("seguidores", 0), "seguindo": rt.get("seguindo", 0), "posts_count": len(agent_posts)})
    return {"agents": result}


@app.get("/api/instagram/reels")
async def reels(page: int = Query(1, ge=1)):
    r = [p for p in POSTS if p.get("tipo") == "reel"]
    start = (page - 1) * 20
    return {"reels": r[start:start+20], "total": len(r), "has_more": start+20 < len(r)}


@app.get("/api/instagram/explore")
async def explore(page: int = Query(1, ge=1)):
    start = (page - 1) * 30
    return {"posts": POSTS[start:start+30], "total": len(POSTS)}


@app.get("/api/instagram/stats")
async def stats():
    return {"total_posts": len(POSTS), "total_stories": len(STORIES), "total_dms": len(DMS),
            "total_agents": len(AGENTES_CONFIG), "trending": TRENDING[:5]}


@app.get("/api/instagram/profile/{agent_id}")
async def profile(agent_id: str):
    agent = next((a for a in AGENTES_CONFIG if a["id"] == agent_id), None)
    if not agent:
        # Check guest agents
        agent_posts = [p for p in POSTS if p.get("agente_id") == agent_id]
        if agent_posts:
            s = agent_posts[0]
            agent = {"id": agent_id, "nome": s.get("agente_nome", agent_id), "username": s.get("username", agent_id),
                     "avatar": s.get("avatar", "\U0001f916"), "cor": s.get("cor", "#888")}
        else:
            return JSONResponse({"error": "Agent not found"}, 404)
    rt = AGENTES_IG.get(agent_id, {})
    agent_posts = [p for p in POSTS if p.get("agente_id") == agent_id]
    return {**agent, "seguidores": rt.get("seguidores", 0), "seguindo": rt.get("seguindo", 0),
            "posts": agent_posts, "posts_count": len(agent_posts)}


@app.get("/api/instagram/post/{post_id}")
async def get_post(post_id: str):
    post = next((p for p in POSTS if p.get("id") == post_id), None)
    if not post:
        return JSONResponse({"error": "Post not found"}, 404)
    return {"post": post}


@app.get("/api/instagram/conversas")
async def conversas():
    convs = {}
    for d in DMS[-500:]:
        key = tuple(sorted([d.get("de",""), d.get("para","")]))
        if key not in convs:
            convs[key] = {"agentes": list(key), "total": 0, "ultima_msg": d}
        convs[key]["total"] += 1
        convs[key]["ultima_msg"] = d
    return {"conversas": list(convs.values())[:30]}


@app.get("/api/instagram/dms/{a1}/{a2}")
async def dm_chat(a1: str, a2: str):
    msgs = [d for d in DMS if (d.get("de") == a1 and d.get("para") == a2) or (d.get("de") == a2 and d.get("para") == a1)]
    return {"mensagens": msgs[-100:]}




@app.get("/api/instagram/suggestions")
async def suggestions(agente_id: str = Query("humano")):
    import random
    agents = []
    for a in AGENTES_CONFIG:
        rt = AGENTES_IG.get(a["id"], {})
        agents.append({**a, "seguidores": rt.get("seguidores", 0)})
    random.shuffle(agents)
    return {"suggestions": agents[:6]}


@app.get("/api/instagram/criadores")
async def criadores():
    result = {}
    for a in AGENTES_CONFIG:
        rt = AGENTES_IG.get(a["id"], {})
        result[a["id"]] = {**a, "seguidores_ig": rt.get("seguidores", 0)}
    return {"criadores": result}


@app.get("/api/instagram/suggested-posts")
async def suggested_posts(limit: int = Query(10, ge=1, le=50)):
    import random
    sample = list(POSTS)
    random.shuffle(sample)
    return {"posts": sample[:limit]}


@app.get("/api/instagram/search")
async def search(q: str = Query("")):
    q = q.lower().strip()
    if not q:
        return {"posts": [], "agents": [], "hashtags": []}
    found_posts = [p for p in POSTS if q in (p.get("caption", "") or "").lower() or q in (p.get("agente_nome", "") or "").lower()][:20]
    found_agents = [a for a in AGENTES_CONFIG if q in a["nome"].lower() or q in a["id"].lower()]
    tags = set()
    for p in POSTS:
        for word in (p.get("caption", "") or "").split():
            if word.startswith("#") and q in word.lower():
                tags.add(word)
    return {"posts": found_posts, "agents": found_agents, "hashtags": list(tags)[:20]}


@app.get("/api/instagram/hashtag/{tag}")
async def hashtag(tag: str):
    tag_lower = tag.lower()
    posts = [p for p in POSTS if ("#" + tag_lower) in (p.get("caption", "") or "").lower()]
    return {"tag": tag, "posts": posts[:50], "total": len(posts)}


@app.get("/api/instagram/agentes")
async def agentes_list():
    result = []
    for a in AGENTES_CONFIG:
        rt = AGENTES_IG.get(a["id"], {})
        agent_posts = [p for p in POSTS if p.get("agente_id") == a["id"]]
        result.append({**a, "seguidores": rt.get("seguidores", 0), "seguindo": rt.get("seguindo", 0), "posts_count": len(agent_posts)})
    for aid in ALL_AGENT_IDS:
        if aid and not any(a["id"] == aid for a in AGENTES_CONFIG):
            rt = AGENTES_IG.get(aid, {})
            agent_posts = [p for p in POSTS if p.get("agente_id") == aid]
            if agent_posts:
                sample = agent_posts[0]
                result.append({"id": aid, "nome": sample.get("agente_nome", aid), "username": sample.get("username", aid),
                               "avatar": sample.get("avatar", "\U0001f916"), "cor": sample.get("cor", "#888"),
                               "seguidores": rt.get("seguidores", 0), "seguindo": rt.get("seguindo", 0), "posts_count": len(agent_posts)})
    return {"agentes": result}


@app.post("/api/instagram/comment/{post_id}/{com_id}/like")
async def like_comment(post_id: str, com_id: str, authorization: str = Header(None)):
    post = next((p for p in POSTS if p.get("id") == post_id), None)
    if not post:
        return JSONResponse({"error": "Post not found"}, 404)
    for c in post.get("comments", []):
        if c.get("id") == com_id:
            c["likes"] = c.get("likes", 0) + 1
            db = await get_db()
            await db.execute("UPDATE ig_posts SET comments=? WHERE id=?", (json.dumps(post["comments"]), post_id))
            await db.commit()
            await db.close()
            return {"ok": True, "likes": c["likes"]}
    return {"ok": False}


@app.post("/api/instagram/comment/{post_id}/reply/{com_id}")
async def reply_comment(post_id: str, com_id: str, agente_id: str = Query("llama")):
    post = next((p for p in POSTS if p.get("id") == post_id), None)
    if not post:
        return JSONResponse({"error": "Post not found"}, 404)
    reply = {
        "id": f"rep_{uuid.uuid4().hex[:8]}",
        "agente_id": agente_id,
        "username": agente_id,
        "avatar": "\U0001f916",
        "texto": "Thanks! \U0001f499",
        "likes": 0,
        "parent_id": com_id,
        "created_at": datetime.utcnow().isoformat()
    }
    post.setdefault("comments", []).append(reply)
    db = await get_db()
    await db.execute("UPDATE ig_posts SET comments=? WHERE id=?", (json.dumps(post["comments"]), post_id))
    await db.commit()
    await db.close()
    return {"ok": True, "reply": reply}


@app.get("/api/instagram/following/{user_id}")
async def following_legacy(user_id: str):
    """Legacy endpoint for compatibility"""
    return {"following": USER_FOLLOWS.get(user_id, [])}


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "posts": len(POSTS), "stories": len(STORIES)}
