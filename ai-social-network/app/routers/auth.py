"""
Auth router - Login, Register, Premium for local server
"""
import os
import uuid
import json
import aiosqlite
from datetime import datetime, timedelta
from fastapi import APIRouter, Header, Body
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
import bcrypt

router = APIRouter(prefix="/api/auth", tags=["auth"])

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "instagram.db")
SECRET_KEY = os.environ.get("JWT_SECRET", "aigrams-secret-key-2026-change-in-prod")
ALGORITHM = "HS256"
TOKEN_HOURS = 24


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_HOURS)
    return jwt.encode({"sub": user_id, "username": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(authorization: str = None):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"id": payload["sub"], "username": payload.get("username", "")}
    except JWTError:
        return None

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_auth_tables():
    db = await get_db()
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
    try:
        await db.execute("ALTER TABLE users ADD COLUMN is_premium INTEGER DEFAULT 0")
    except Exception:
        pass
    await db.commit()
    await db.close()
    print("[AUTH] Tables initialized")


@router.on_event("startup")
async def startup():
    await init_auth_tables()


@router.post("/register")
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


@router.post("/login")
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


@router.get("/me")
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
    return {"user": u}


@router.post("/upgrade-premium")
async def upgrade_premium(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    if not user:
        return JSONResponse({"error": "Login required"}, 401)

    db = await get_db()
    await db.execute("UPDATE users SET is_premium=1 WHERE id=?", (user["id"],))
    await db.commit()
    await db.close()
    return {"ok": True, "is_premium": 1}
