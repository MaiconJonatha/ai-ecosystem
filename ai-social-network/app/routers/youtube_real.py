"""
YouTube Real Video Search - Uses yt-dlp to find real YouTube videos
"""
import asyncio
import json
import random

# Search queries per category
YT_SEARCH_QUERIES = {
    "tech": [
        "artificial intelligence explained 2025", "machine learning tutorial",
        "deep learning neural networks", "ChatGPT AI tutorial",
        "Python programming AI", "data science tutorial",
        "cloud computing AWS Azure", "DevOps CI CD pipeline",
        "cybersecurity ethical hacking", "blockchain technology explained",
        "software engineering best practices", "API REST development",
        "microservices architecture", "Docker Kubernetes tutorial",
        "React Next.js tutorial", "backend development Node.js"
    ],
    "ciencia": [
        "computer science algorithms", "quantum computing explained",
        "AI research paper explained", "neural network from scratch",
        "natural language processing NLP", "computer vision tutorial",
        "reinforcement learning AI", "robotics programming",
        "autonomous vehicles AI", "AI in healthcare technology",
        "large language models explained", "transformer architecture AI"
    ],
    "arte": [
        "generative AI art Midjourney", "AI image generation tutorial",
        "creative coding p5js", "UI UX design tutorial",
        "web design modern CSS", "Figma design system",
        "AI music generation", "stable diffusion tutorial",
        "3D modeling Blender AI", "motion graphics after effects"
    ],
    "gaming": [
        "game development Unity tutorial", "Unreal Engine 5 tutorial",
        "AI in game development", "procedural generation algorithm",
        "game programming C++ C#", "indie game dev log",
        "Godot engine tutorial", "shader programming tutorial",
        "multiplayer networking game", "AI NPC behavior programming"
    ],
    "educacao": [
        "learn programming beginner 2025", "Python tutorial beginner",
        "JavaScript full course", "SQL database tutorial",
        "Linux command line tutorial", "Git GitHub tutorial",
        "system design interview", "coding interview preparation",
        "computer networking explained", "operating systems explained",
        "web development full stack", "mobile app development Flutter"
    ],
    "geral": [
        "tech news today AI", "future of technology AI",
        "startup technology innovation", "Silicon Valley tech culture",
        "open source software projects", "programming productivity tips",
        "tech career advice developer", "AI tools productivity 2025",
        "no code low code development", "tech industry trends 2025",
        "best programming languages 2025", "AI automation future work"
    ]
}

# Cache to avoid repeated yt-dlp calls
_video_cache = {}
_cache_lock = asyncio.Lock()


async def buscar_videos_youtube(categoria="tech", quantidade=5):
    """Search YouTube for real videos using yt-dlp"""
    cache_key = f"{categoria}_{quantidade}"
    
    async with _cache_lock:
        if cache_key in _video_cache and len(_video_cache[cache_key]) > 0:
            result = _video_cache[cache_key].pop(0)
            return result
    
    queries = YT_SEARCH_QUERIES.get(categoria, YT_SEARCH_QUERIES["geral"])
    query = random.choice(queries)
    
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", f"ytsearch{quantidade}:{query}",
            "--dump-json", "--flat-playlist", "--no-download",
            "--no-warnings", "--quiet",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=25)
        
        videos = []
        for line in stdout.decode().strip().split("\n"):
            if not line.strip():
                continue
            try:
                v = json.loads(line)
                vid_id = v.get("id", "")
                if not vid_id:
                    continue
                
                thumbs = v.get("thumbnails", [])
                thumb_url = ""
                for t in reversed(thumbs):
                    url = t.get("url", "")
                    if "hq720" in url or "maxresdefault" in url or "sddefault" in url:
                        thumb_url = url.split("?")[0]
                        break
                if not thumb_url:
                    thumb_url = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
                    
                video_info = {
                    "youtube_id": vid_id,
                    "title": v.get("title", ""),
                    "channel": v.get("channel", v.get("uploader", "")),
                    "channel_id": v.get("channel_id", ""),
                    "duration": int(v.get("duration", 0) or 0),
                    "views": int(v.get("view_count", 0) or 0),
                    "thumbnail_url": thumb_url,
                    "embed_url": f"https://www.youtube.com/embed/{vid_id}",
                    "watch_url": f"https://www.youtube.com/watch?v={vid_id}",
                    "description": (v.get("description", "") or "")[:200],
                    "upload_date": v.get("upload_date", ""),
                }
                videos.append(video_info)
            except json.JSONDecodeError:
                continue
        
        if videos:
            async with _cache_lock:
                _video_cache[cache_key] = videos[1:]
            print(f"[YT-REAL] Found {len(videos)} real YouTube videos for \"{query}\"")
            return videos[0]
        
    except asyncio.TimeoutError:
        print(f"[YT-REAL] yt-dlp timeout for \"{query}\"")
    except FileNotFoundError:
        print("[YT-REAL] yt-dlp not installed!")
    except Exception as e:
        print(f"[YT-REAL] Error: {e}")
    
    return None


async def buscar_shorts_youtube(categoria="tech", quantidade=5):
    """Search YouTube for real Shorts"""
    queries = YT_SEARCH_QUERIES.get(categoria, YT_SEARCH_QUERIES["geral"])
    query = random.choice(queries) + " #shorts"
    
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", f"ytsearch{quantidade}:{query}",
            "--dump-json", "--flat-playlist", "--no-download",
            "--no-warnings", "--quiet",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=25)
        
        shorts = []
        for line in stdout.decode().strip().split("\n"):
            if not line.strip():
                continue
            try:
                v = json.loads(line)
                vid_id = v.get("id", "")
                dur = int(v.get("duration", 0) or 0)
                if not vid_id or dur > 180:
                    continue
                
                thumb_url = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
                thumbs = v.get("thumbnails", [])
                for t in reversed(thumbs):
                    url = t.get("url", "")
                    if "hq720" in url or "maxresdefault" in url:
                        thumb_url = url.split("?")[0]
                        break
                
                shorts.append({
                    "youtube_id": vid_id,
                    "title": v.get("title", ""),
                    "channel": v.get("channel", v.get("uploader", "")),
                    "duration": dur,
                    "views": int(v.get("view_count", 0) or 0),
                    "thumbnail_url": thumb_url,
                    "embed_url": f"https://www.youtube.com/embed/{vid_id}",
                    "is_short": True,
                })
                if len(shorts) >= 3:
                    break
            except:
                continue
        
        if shorts:
            print(f"[YT-REAL] Found {len(shorts)} YouTube Shorts for \"{query}\"")
            return random.choice(shorts)
    except Exception as e:
        print(f"[YT-REAL-SHORT] Error: {e}")
    
    return None


def format_duration(seconds):
    if not seconds:
        return "0:00"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_views(n):
    if not n:
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)
