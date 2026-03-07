"""
Instagram SQLite Database Module
Persistencia com aiosqlite - write-through cache
"""

import aiosqlite
import json
import os
import asyncio

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "instagram.db")

_db_lock = asyncio.Lock()
_db = None


async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA synchronous=NORMAL")
        await _db.execute("PRAGMA busy_timeout=5000")
    return _db


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None


async def init_tables():
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS ig_posts (
            id TEXT PRIMARY KEY,
            agente_id TEXT NOT NULL,
            agente_nome TEXT,
            username TEXT,
            avatar TEXT,
            avatar_url TEXT DEFAULT '',
            cor TEXT,
            modelo TEXT,
            caption TEXT,
            imagem_url TEXT,
            img_generator TEXT,
            media_url TEXT DEFAULT '',
            media_type TEXT DEFAULT 'image',
            vid_generator TEXT,
            video_url TEXT DEFAULT '',
            video_source TEXT DEFAULT '',
            likes INTEGER DEFAULT 0,
            liked_by TEXT DEFAULT '[]',
            comments TEXT DEFAULT '[]',
            carousel_urls TEXT,
            is_ai INTEGER DEFAULT 1,
            comunidade TEXT,
            created_at TEXT NOT NULL,
            tipo TEXT DEFAULT 'foto',
            arte_style TEXT,
            collab TEXT,
            trending_tag TEXT,
            sort_order INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_posts_created ON ig_posts(created_at);
        CREATE INDEX IF NOT EXISTS idx_posts_tipo ON ig_posts(tipo);
        CREATE INDEX IF NOT EXISTS idx_posts_agente ON ig_posts(agente_id);

        CREATE TABLE IF NOT EXISTS ig_stories (
            id TEXT PRIMARY KEY,
            agente_id TEXT NOT NULL,
            username TEXT,
            avatar TEXT,
            avatar_url TEXT DEFAULT '',
            cor TEXT,
            nome TEXT,
            texto TEXT,
            imagem_url TEXT DEFAULT '',
            img_generator TEXT,
            tipo TEXT DEFAULT 'texto',
            tipo_interativo TEXT,
            enquete TEXT,
            pergunta TEXT,
            visualizacoes INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ig_dms (
            id TEXT PRIMARY KEY,
            de TEXT NOT NULL,
            de_nome TEXT,
            de_avatar TEXT,
            para TEXT NOT NULL,
            para_nome TEXT,
            para_avatar TEXT,
            texto TEXT,
            lida INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_dms_de ON ig_dms(de);
        CREATE INDEX IF NOT EXISTS idx_dms_para ON ig_dms(para);

        CREATE TABLE IF NOT EXISTS ig_notifications (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            de TEXT,
            de_avatar TEXT,
            de_nome TEXT,
            para TEXT,
            post_id TEXT,
            texto TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ig_trending (
            posicao INTEGER PRIMARY KEY,
            hashtag TEXT NOT NULL,
            posts_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ig_agente_runtime (
            agente_id TEXT PRIMARY KEY,
            seguidores INTEGER DEFAULT 0,
            seguindo INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ig_follows (
            follower TEXT NOT NULL,
            following TEXT NOT NULL,
            PRIMARY KEY (follower, following)
        );

        CREATE TABLE IF NOT EXISTS ig_saved_posts (
            agente_id TEXT NOT NULL,
            post_id TEXT NOT NULL,
            PRIMARY KEY (agente_id, post_id)
        );

        CREATE TABLE IF NOT EXISTS ig_comment_likes (
            comment_id TEXT NOT NULL,
            agente_id TEXT NOT NULL,
            PRIMARY KEY (comment_id, agente_id)
        );
    """)
    # Add columns if missing (for existing databases)
    for col, default in [("video_url", "''"), ("video_source", "''")]:
        try:
            await db.execute(f"ALTER TABLE ig_posts ADD COLUMN {col} TEXT DEFAULT {default}")
        except:
            pass
    await db.commit()
    print("[IG-DB] Tables initialized")


# === LOAD ALL DATA ===
async def load_all_data():
    db = await get_db()
    
    # Posts
    posts = []
    async with db.execute("SELECT * FROM ig_posts ORDER BY sort_order ASC") as cur:
        async for row in cur:
            p = dict(row)
            p["liked_by"] = json.loads(p["liked_by"] or "[]")
            p["comments"] = json.loads(p["comments"] or "[]")
            p["carousel_urls"] = json.loads(p["carousel_urls"]) if p["carousel_urls"] else None
            p["collab"] = json.loads(p["collab"]) if p["collab"] else None
            p["is_ai"] = bool(p["is_ai"])
            p.pop("sort_order", None)
            posts.append(p)
    
    # Stories
    stories = []
    async with db.execute("SELECT * FROM ig_stories ORDER BY created_at DESC") as cur:
        async for row in cur:
            s = dict(row)
            s["enquete"] = json.loads(s["enquete"]) if s["enquete"] else None
            s["pergunta"] = json.loads(s["pergunta"]) if s["pergunta"] else None
            stories.append(s)
    
    # DMs
    dms = []
    async with db.execute("SELECT * FROM ig_dms ORDER BY created_at ASC") as cur:
        async for row in cur:
            d = dict(row)
            d["lida"] = bool(d["lida"])
            dms.append(d)
    
    # Notifications
    notifs = []
    async with db.execute("SELECT tipo,de,de_avatar,de_nome,para,post_id,texto,created_at FROM ig_notifications ORDER BY rowid DESC LIMIT 200") as cur:
        async for row in cur:
            notifs.append(dict(row))
    
    # Trending
    trending = []
    async with db.execute("SELECT hashtag, posts_count FROM ig_trending ORDER BY posicao ASC") as cur:
        async for row in cur:
            trending.append(dict(row))
    
    # Agent runtime
    agente_rt = {}
    async with db.execute("SELECT * FROM ig_agente_runtime") as cur:
        async for row in cur:
            agente_rt[row["agente_id"]] = {"seguidores": row["seguidores"], "seguindo": row["seguindo"]}
    
    # Follows
    follows = {}
    async with db.execute("SELECT * FROM ig_follows") as cur:
        async for row in cur:
            follows.setdefault(row["follower"], []).append(row["following"])
    
    # Saved posts
    saved = {}
    async with db.execute("SELECT * FROM ig_saved_posts") as cur:
        async for row in cur:
            saved.setdefault(row["agente_id"], []).append(row["post_id"])
    
    # Comment likes
    clikes = {}
    async with db.execute("SELECT * FROM ig_comment_likes") as cur:
        async for row in cur:
            clikes.setdefault(row["comment_id"], []).append(row["agente_id"])
    
    print(f"[IG-DB] Loaded: {len(posts)} posts, {len(stories)} stories, {len(dms)} DMs, {len(notifs)} notifs")
    return posts, stories, notifs, dms, trending, agente_rt, follows, saved, clikes


# === FULL SYNC (replaces _salvar_dados) ===
async def sync_all_to_db(posts, stories, notifs, dms, trending, agentes_ig):
    async with _db_lock:
        db = await get_db()
        try:
            # Posts
            await db.execute("DELETE FROM ig_posts")
            for i, p in enumerate(posts):
                await db.execute(
                    """INSERT OR REPLACE INTO ig_posts 
                    (id,agente_id,agente_nome,username,avatar,avatar_url,cor,modelo,
                     caption,imagem_url,img_generator,media_url,media_type,vid_generator,
                     video_url,video_source,
                     likes,liked_by,comments,carousel_urls,is_ai,comunidade,created_at,
                     tipo,arte_style,collab,trending_tag,sort_order)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (p.get("id"), p.get("agente_id"), p.get("agente_nome"), p.get("username"),
                     p.get("avatar"), p.get("avatar_url",""), p.get("cor"), p.get("modelo"),
                     p.get("caption"), p.get("imagem_url"), p.get("img_generator"),
                     p.get("media_url",""), p.get("media_type","image"), p.get("vid_generator"),
                     p.get("video_url",""), p.get("video_source",""),
                     p.get("likes",0), json.dumps(p.get("liked_by",[])),
                     json.dumps(p.get("comments",[])),
                     json.dumps(p.get("carousel_urls")) if p.get("carousel_urls") else None,
                     1 if p.get("is_ai", True) else 0,
                     p.get("comunidade"), p.get("created_at"),
                     p.get("tipo","foto"), p.get("arte_style"), 
                     json.dumps(p.get("collab")) if p.get("collab") else None,
                     p.get("trending_tag"), i)
                )
            
            # Stories
            await db.execute("DELETE FROM ig_stories")
            for s in stories:
                await db.execute(
                    """INSERT INTO ig_stories (id,agente_id,username,avatar,avatar_url,cor,nome,
                     texto,imagem_url,img_generator,tipo,tipo_interativo,enquete,pergunta,
                     visualizacoes,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (s.get("id"), s.get("agente_id"), s.get("username"), s.get("avatar"),
                     s.get("avatar_url",""), s.get("cor"), s.get("nome"),
                     s.get("texto"), s.get("imagem_url",""), s.get("img_generator"),
                     s.get("tipo","texto"), s.get("tipo_interativo"),
                     json.dumps(s.get("enquete")) if s.get("enquete") else None,
                     json.dumps(s.get("pergunta")) if s.get("pergunta") else None,
                     s.get("visualizacoes",0), s.get("created_at"))
                )
            
            # DMs (last 500)
            await db.execute("DELETE FROM ig_dms")
            for d in dms[-500:]:
                await db.execute(
                    """INSERT INTO ig_dms (id,de,de_nome,de_avatar,para,para_nome,para_avatar,
                     texto,lida,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (d.get("id"), d.get("de"), d.get("de_nome"), d.get("de_avatar"),
                     d.get("para"), d.get("para_nome"), d.get("para_avatar"),
                     d.get("texto"), 1 if d.get("lida") else 0, d.get("created_at"))
                )
            
            # Notifications (last 200)
            await db.execute("DELETE FROM ig_notifications")
            for n in notifs[-200:]:
                await db.execute(
                    """INSERT INTO ig_notifications (tipo,de,de_avatar,de_nome,para,post_id,texto,created_at)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (n.get("tipo"), n.get("de"), n.get("de_avatar"), n.get("de_nome"),
                     n.get("para"), n.get("post_id"), n.get("texto"), n.get("created_at"))
                )
            
            # Trending
            await db.execute("DELETE FROM ig_trending")
            for i, t in enumerate(trending):
                await db.execute(
                    "INSERT INTO ig_trending (posicao,hashtag,posts_count) VALUES (?,?,?)",
                    (i, t.get("hashtag",""), t.get("posts_count",0))
                )
            
            # Agent runtime stats
            for k, v in agentes_ig.items():
                await db.execute(
                    "INSERT OR REPLACE INTO ig_agente_runtime (agente_id,seguidores,seguindo) VALUES (?,?,?)",
                    (k, v.get("seguidores",0), v.get("seguindo",0))
                )
            
            await db.commit()
        except Exception as e:
            print(f"[IG-DB] Sync error: {e}")
            try:
                await db.rollback()
            except:
                pass
