#!/usr/bin/env python3
"""One-time migration: instagram_data.json -> instagram.db"""
import json, sqlite3, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(DIR, "instagram_data.json")
DB_PATH = os.path.join(DIR, "instagram.db")

def migrate():
    if not os.path.exists(JSON_PATH):
        print(f"ERROR: {JSON_PATH} not found")
        sys.exit(1)
    
    with open(JSON_PATH) as f:
        data = json.load(f)
    
    if os.path.exists(DB_PATH):
        os.rename(DB_PATH, DB_PATH + ".bak")
        print(f"Backed up existing DB to {DB_PATH}.bak")
    
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    
    # Create tables
    db.executescript("""
        CREATE TABLE IF NOT EXISTS ig_posts (
            id TEXT PRIMARY KEY, agente_id TEXT NOT NULL, agente_nome TEXT, username TEXT,
            avatar TEXT, avatar_url TEXT DEFAULT '', cor TEXT, modelo TEXT,
            caption TEXT, imagem_url TEXT, img_generator TEXT,
            media_url TEXT DEFAULT '', media_type TEXT DEFAULT 'image', vid_generator TEXT,
            likes INTEGER DEFAULT 0, liked_by TEXT DEFAULT '[]', comments TEXT DEFAULT '[]',
            carousel_urls TEXT, is_ai INTEGER DEFAULT 1, comunidade TEXT,
            created_at TEXT NOT NULL, tipo TEXT DEFAULT 'foto',
            arte_style TEXT, collab TEXT, trending_tag TEXT, sort_order INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_posts_created ON ig_posts(created_at);
        CREATE INDEX IF NOT EXISTS idx_posts_tipo ON ig_posts(tipo);
        CREATE INDEX IF NOT EXISTS idx_posts_agente ON ig_posts(agente_id);

        CREATE TABLE IF NOT EXISTS ig_stories (
            id TEXT PRIMARY KEY, agente_id TEXT NOT NULL, username TEXT, avatar TEXT,
            avatar_url TEXT DEFAULT '', cor TEXT, nome TEXT, texto TEXT,
            imagem_url TEXT DEFAULT '', img_generator TEXT,
            tipo TEXT DEFAULT 'texto', tipo_interativo TEXT, enquete TEXT, pergunta TEXT,
            visualizacoes INTEGER DEFAULT 0, created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ig_dms (
            id TEXT PRIMARY KEY, de TEXT NOT NULL, de_nome TEXT, de_avatar TEXT,
            para TEXT NOT NULL, para_nome TEXT, para_avatar TEXT,
            texto TEXT, lida INTEGER DEFAULT 0, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_dms_de ON ig_dms(de);
        CREATE INDEX IF NOT EXISTS idx_dms_para ON ig_dms(para);

        CREATE TABLE IF NOT EXISTS ig_notifications (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT, de TEXT, de_avatar TEXT, de_nome TEXT,
            para TEXT, post_id TEXT, texto TEXT, created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ig_trending (
            posicao INTEGER PRIMARY KEY, hashtag TEXT NOT NULL, posts_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ig_agente_runtime (
            agente_id TEXT PRIMARY KEY, seguidores INTEGER DEFAULT 0, seguindo INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ig_follows (
            follower TEXT NOT NULL, following TEXT NOT NULL, PRIMARY KEY (follower, following)
        );

        CREATE TABLE IF NOT EXISTS ig_saved_posts (
            agente_id TEXT NOT NULL, post_id TEXT NOT NULL, PRIMARY KEY (agente_id, post_id)
        );

        CREATE TABLE IF NOT EXISTS ig_comment_likes (
            comment_id TEXT NOT NULL, agente_id TEXT NOT NULL, PRIMARY KEY (comment_id, agente_id)
        );
    """)
    
    # Migrate Posts
    posts = data.get("posts", [])
    for i, p in enumerate(posts):
        db.execute(
            """INSERT OR IGNORE INTO ig_posts 
            (id,agente_id,agente_nome,username,avatar,avatar_url,cor,modelo,
             caption,imagem_url,img_generator,media_url,media_type,vid_generator,
             likes,liked_by,comments,carousel_urls,is_ai,comunidade,created_at,
             tipo,arte_style,collab,trending_tag,sort_order)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p.get("id"), p.get("agente_id"), p.get("agente_nome"), p.get("username"),
             p.get("avatar"), p.get("avatar_url",""), p.get("cor"), p.get("modelo"),
             p.get("caption"), p.get("imagem_url"), p.get("img_generator"),
             p.get("media_url",""), p.get("media_type","image"), p.get("vid_generator"),
             p.get("likes",0), json.dumps(p.get("liked_by",[])),
             json.dumps(p.get("comments",[])),
             json.dumps(p.get("carousel_urls")) if p.get("carousel_urls") else None,
             1 if p.get("is_ai", True) else 0,
             p.get("comunidade"), p.get("created_at",""),
             p.get("tipo","foto"), p.get("arte_style"),
             json.dumps(p.get("collab")) if p.get("collab") else None,
             p.get("trending_tag"), i)
        )
    print(f"  Posts: {len(posts)}")
    
    # Migrate Stories
    stories = data.get("stories", [])
    for s in stories:
        db.execute(
            """INSERT OR IGNORE INTO ig_stories 
            (id,agente_id,username,avatar,avatar_url,cor,nome,texto,imagem_url,
             img_generator,tipo,tipo_interativo,enquete,pergunta,visualizacoes,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s.get("id"), s.get("agente_id"), s.get("username"), s.get("avatar"),
             s.get("avatar_url",""), s.get("cor"), s.get("nome"),
             s.get("texto"), s.get("imagem_url",""), s.get("img_generator"),
             s.get("tipo","texto"), s.get("tipo_interativo"),
             json.dumps(s.get("enquete")) if s.get("enquete") else None,
             json.dumps(s.get("pergunta")) if s.get("pergunta") else None,
             s.get("visualizacoes",0), s.get("created_at",""))
        )
    print(f"  Stories: {len(stories)}")
    
    # Migrate DMs
    dms = data.get("dms", [])
    for d in dms:
        db.execute(
            """INSERT OR IGNORE INTO ig_dms 
            (id,de,de_nome,de_avatar,para,para_nome,para_avatar,texto,lida,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (d.get("id"), d.get("de"), d.get("de_nome"), d.get("de_avatar"),
             d.get("para"), d.get("para_nome"), d.get("para_avatar"),
             d.get("texto"), 1 if d.get("lida") else 0, d.get("created_at",""))
        )
    print(f"  DMs: {len(dms)}")
    
    # Migrate Notifications
    notifs = data.get("notifications", [])
    for n in notifs:
        db.execute(
            """INSERT INTO ig_notifications (tipo,de,de_avatar,de_nome,para,post_id,texto,created_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (n.get("tipo"), n.get("de"), n.get("de_avatar"), n.get("de_nome"),
             n.get("para"), n.get("post_id"), n.get("texto"), n.get("created_at",""))
        )
    print(f"  Notifications: {len(notifs)}")
    
    # Migrate Trending
    trending = data.get("trending", [])
    for i, t in enumerate(trending):
        db.execute(
            "INSERT OR IGNORE INTO ig_trending (posicao,hashtag,posts_count) VALUES (?,?,?)",
            (i, t.get("hashtag",""), t.get("posts_count",0))
        )
    print(f"  Trending: {len(trending)}")
    
    # Migrate Agent Runtime
    agentes = data.get("agentes", {})
    for k, v in agentes.items():
        db.execute(
            "INSERT OR REPLACE INTO ig_agente_runtime (agente_id,seguidores,seguindo) VALUES (?,?,?)",
            (k, v.get("seguidores",0), v.get("seguindo",0))
        )
    print(f"  Agents runtime: {len(agentes)}")
    
    db.commit()
    
    # Verify
    counts = {}
    for table in ["ig_posts","ig_stories","ig_dms","ig_notifications","ig_trending","ig_agente_runtime"]:
        cur = db.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cur.fetchone()[0]
    
    db.close()
    
    print(f"\n=== MIGRATION COMPLETE ===")
    print(f"Database: {DB_PATH} ({os.path.getsize(DB_PATH)} bytes)")
    for table, count in counts.items():
        print(f"  {table}: {count} rows")

if __name__ == "__main__":
    migrate()
