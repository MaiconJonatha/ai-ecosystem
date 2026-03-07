"""
AI Video Generator - Criador de Videos com IA tipo Veo/CapCut
Gera videos a partir de texto usando IA + Ken Burns + Stock Clips
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import httpx
import asyncio
import json
import os
import uuid
import random
import base64
import time
import math
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEOS_DIR = os.path.join(DIR, "static", "videos")
IMAGES_DIR = os.path.join(DIR, "static", "images")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# ============ API KEYS ============
GROQ_KEYS = [
    "GROQ_API_KEY_1",
    "GROQ_API_KEY_2",
]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
STABLE_HORDE_KEY = "0000000000"
PIXABAY_KEY = "PIXABAY_API_KEY_HERE"
PEXELS_KEY = "wUJHrz5701c3ueVUbAwLyE4BeZeW0YdIGBxNvNoRAqz4Lqh1lpFiNOw8"

# ============ VIDEO TEMPLATES ============
TEMPLATES = {
    "motivacional": {"nome": "Motivacional", "icon": "💪", "desc": "Frases inspiradoras"},
    "top5": {"nome": "Top 5 / Ranking", "icon": "🏆", "desc": "Listas e rankings"},
    "tutorial": {"nome": "Tutorial / Dicas", "icon": "📚", "desc": "Passo a passo"},
    "curiosidade": {"nome": "Curiosidades", "icon": "🤯", "desc": "Fatos surpreendentes"},
    "news": {"nome": "Notícias", "icon": "📰", "desc": "Trending e notícias"},
    "storytelling": {"nome": "Storytelling", "icon": "📖", "desc": "Contar histórias"},
    "produto": {"nome": "Review Produto", "icon": "🛍️", "desc": "Showcase de produto"},
    "livre": {"nome": "Tema Livre", "icon": "🎨", "desc": "Qualquer tema"},
}

video_history = []

# ============ LIFESPAN ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[VIDEO-GEN] AI Video Generator na porta 8014!")
    print(f"[VIDEO-GEN] {len(TEMPLATES)} templates | Ken Burns + Stock Clips")
    yield

app = FastAPI(title="AI Video Generator", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=os.path.join(DIR, "static")), name="static")
templates_jinja = Jinja2Templates(directory=os.path.join(DIR, "templates"))


# ============ AI HELPER ============
async def _ai(prompt, system=""):
    key = random.choice(GROQ_KEYS)
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(GROQ_URL, headers={"Authorization": f"Bearer {key}"},
                json={"model": GROQ_MODEL, "messages": msgs, "max_tokens": 800, "temperature": 0.85})
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[AI] {e}")
    return ""


async def _ai_script(tema, template_id):
    system = "Voce cria roteiros de videos virais para TikTok/Reels/Shorts. Responda APENAS JSON valido."
    prompt = f"""Crie roteiro para video viral sobre: {tema}
Template: {template_id}

Responda em JSON:
{{
    "titulo": "titulo curto impactante (max 40 chars)",
    "cenas": [
        {{"texto": "texto grande do slide (max 50 chars)", "subtexto": "complemento menor", "visual": "descricao da imagem/cena em ingles para AI gerar"}},
        ... (4 a 6 cenas)
    ],
    "hashtags": "#hashtag1 #hashtag2 #hashtag3",
    "descricao": "descricao curta do video para post"
}}

IMPORTANTE: O campo "visual" deve ser uma descricao em INGLES para gerar imagem com IA.
Cada cena deve ter visual diferente e impactante."""
    
    text = await _ai(prompt, system)
    try:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(text)
        if "cenas" in data and len(data["cenas"]) >= 2:
            return data
    except:
        pass
    
    # Fallback
    return {
        "titulo": tema[:40],
        "cenas": [
            {"texto": tema[:40], "subtexto": "Descubra agora!", "visual": f"dramatic {tema} cinematic"},
            {"texto": "IMPRESSIONANTE!", "subtexto": "Voce precisa ver isso", "visual": f"epic {tema} landscape dramatic lighting"},
            {"texto": "O RESULTADO?", "subtexto": "Surpreendente!", "visual": f"amazing {tema} beautiful high quality"},
            {"texto": "COMPARTILHE!", "subtexto": "Siga para mais", "visual": f"inspirational {tema} stunning view"},
        ],
        "hashtags": "#viral #fyp #trending",
        "descricao": f"Video sobre {tema}"
    }


# ============ IMAGE GENERATION ============
async def _generate_image(prompt, w=768, h=1344):
    """Gera imagem com Stable Horde (vertical 9:16)"""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                "https://stablehorde.net/api/v2/generate/async",
                headers={"apikey": STABLE_HORDE_KEY},
                json={
                    "prompt": f"{prompt}, cinematic lighting, dramatic, high quality, 8k, no text, no words, no humans, no people, no faces ### blurry, low quality, text, watermark, humans, faces",
                    "params": {"width": w, "height": h, "steps": 25, "cfg_scale": 7.5, "sampler_name": "k_euler_a", "n": 1},
                    "nsfw": False, "censor_nsfw": True,
                    "models": ["stable_diffusion"]
                }
            )
            if resp.status_code in (200, 202):
                job_id = resp.json().get("id")
                if job_id:
                    for _ in range(30):
                        await asyncio.sleep(5)
                        check = await client.get(f"https://stablehorde.net/api/v2/generate/check/{job_id}")
                        if check.status_code == 200 and check.json().get("done"):
                            result = await client.get(f"https://stablehorde.net/api/v2/generate/status/{job_id}")
                            if result.status_code == 200:
                                gens = result.json().get("generations", [])
                                if gens and gens[0].get("img"):
                                    img_resp = await client.get(gens[0]["img"])
                                    if img_resp.status_code == 200:
                                        fname = f"gen_{uuid.uuid4().hex[:10]}.webp"
                                        fpath = os.path.join(IMAGES_DIR, fname)
                                        with open(fpath, "wb") as f:
                                            f.write(img_resp.content)
                                        return fpath
                            break
            
            # Fallback: Pexels photo
            sq = prompt.split(",")[0][:30]
            resp = await client.get("https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": sq, "per_page": 15, "orientation": "portrait"})
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos:
                    url = random.choice(photos).get("src", {}).get("large2x", "")
                    if url:
                        img_resp = await client.get(url)
                        if img_resp.status_code == 200:
                            fname = f"pex_{uuid.uuid4().hex[:10]}.jpg"
                            fpath = os.path.join(IMAGES_DIR, fname)
                            with open(fpath, "wb") as f:
                                f.write(img_resp.content)
                            return fpath
    except Exception as e:
        print(f"[IMG] {e}")
    return ""


async def _get_stock_video(query):
    """Busca clip de video stock no Pexels"""
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get("https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": query[:30], "per_page": 10, "orientation": "portrait", "size": "medium"})
            if resp.status_code == 200:
                videos = resp.json().get("videos", [])
                if videos:
                    chosen = random.choice(videos)
                    for f in chosen.get("video_files", []):
                        if f.get("height", 0) >= 720 and f.get("height", 0) <= 1920:
                            vid_resp = await client.get(f["link"])
                            if vid_resp.status_code == 200:
                                fname = f"stock_{uuid.uuid4().hex[:10]}.mp4"
                                fpath = os.path.join(IMAGES_DIR, fname)
                                with open(fpath, "wb") as fw:
                                    fw.write(vid_resp.content)
                                return fpath
    except Exception as e:
        print(f"[STOCK] {e}")
    return ""


# ============ VIDEO CREATION ============
def _get_font(size):
    paths = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf",
             "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()


def _create_text_overlay(W, H, texto, subtexto, accent_color=(255, 165, 0)):
    """Cria overlay PNG transparente com texto"""
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Semi-transparent gradient bar no centro
    bar_h = 350
    bar_y = (H - bar_h) // 2
    for y in range(bar_h):
        alpha = int(180 * (1 - abs(y - bar_h//2) / (bar_h//2)))
        draw.line([(0, bar_y + y), (W, bar_y + y)], fill=(0, 0, 0, alpha))
    
    # Texto principal
    font_big = _get_font(56)
    font_sub = _get_font(34)
    
    # Wrap text
    words = texto.split()
    lines = []
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font_big)
        if bbox[2] - bbox[0] > W - 100 and line:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    
    line_h = 68
    total_h = len(lines) * line_h
    ty = (H - total_h) // 2 - 20
    
    for i, ln in enumerate(lines):
        bbox = draw.textbbox((0, 0), ln, font=font_big)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        # Shadow
        draw.text((tx + 3, ty + i * line_h + 3), ln, font=font_big, fill=(0, 0, 0, 200))
        draw.text((tx, ty + i * line_h), ln, font=font_big, fill=(255, 255, 255, 255))
    
    # Subtexto
    if subtexto:
        sub_y = ty + len(lines) * line_h + 15
        bbox = draw.textbbox((0, 0), subtexto, font=font_sub)
        tw = bbox[2] - bbox[0]
        sx = (W - tw) // 2
        draw.text((sx + 2, sub_y + 2), subtexto, font=font_sub, fill=(0, 0, 0, 180))
        draw.text((sx, sub_y), subtexto, font=font_sub, fill=accent_color + (255,))
    
    # Accent line
    line_w = 200
    line_y2 = ty - 20
    draw.rectangle([(W//2 - line_w//2, line_y2), (W//2 + line_w//2, line_y2 + 4)], fill=accent_color + (200,))
    
    return overlay


def _apply_ken_burns(img_path, output_path, duration=4.0, W=1080, H=1920, texto="", subtexto=""):
    """Aplica efeito Ken Burns (zoom+pan) numa imagem e gera video com texto overlay"""
    try:
        img = Image.open(img_path).convert("RGB")
        
        # Resize imagem para ser maior que o canvas (para zoom/pan)
        scale_factor = 1.4
        img_w = int(W * scale_factor)
        img_h = int(H * scale_factor)
        img = img.resize((img_w, img_h), Image.LANCZOS)
        
        # Escurecer para texto legivel
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.55)
        
        # Text overlay
        txt_overlay = _create_text_overlay(W, H, texto, subtexto)
        
        # Escolher efeito: zoom_in, zoom_out, pan_left, pan_right
        effect = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_down"])
        
        fps = 24
        total_frames = int(duration * fps)
        frames_dir = os.path.join(IMAGES_DIR, f"_kb_{uuid.uuid4().hex[:6]}")
        os.makedirs(frames_dir, exist_ok=True)
        
        for frame_num in range(total_frames):
            t = frame_num / max(total_frames - 1, 1)  # 0 to 1
            
            if effect == "zoom_in":
                z = 1.0 + t * 0.3  # 1.0 to 1.3
                cw = int(W * scale_factor / z)
                ch = int(H * scale_factor / z)
                cx = (img_w - cw) // 2
                cy = (img_h - ch) // 2
            elif effect == "zoom_out":
                z = 1.3 - t * 0.3
                cw = int(W * scale_factor / z)
                ch = int(H * scale_factor / z)
                cx = (img_w - cw) // 2
                cy = (img_h - ch) // 2
            elif effect == "pan_left":
                cw, ch = W, H
                max_pan = img_w - W
                cx = int(max_pan * (1 - t))
                cy = (img_h - H) // 2
            elif effect == "pan_right":
                cw, ch = W, H
                max_pan = img_w - W
                cx = int(max_pan * t)
                cy = (img_h - H) // 2
            else:  # pan_down
                cw, ch = W, H
                cx = (img_w - W) // 2
                max_pan = img_h - H
                cy = int(max_pan * t)
            
            # Crop and resize
            frame = img.crop((cx, cy, cx + cw, cy + ch))
            frame = frame.resize((W, H), Image.LANCZOS)
            
            # Text fade in (first 0.5s) and fade out (last 0.3s)
            frame_rgba = frame.convert("RGBA")
            txt_copy = txt_overlay.copy()
            
            fade_in_frames = int(0.4 * fps)
            fade_out_frames = int(0.3 * fps)
            
            if frame_num < fade_in_frames:
                alpha = frame_num / fade_in_frames
                txt_copy.putalpha(txt_copy.split()[3].point(lambda p: int(p * alpha)))
            elif frame_num > total_frames - fade_out_frames:
                alpha = (total_frames - frame_num) / fade_out_frames
                txt_copy.putalpha(txt_copy.split()[3].point(lambda p: int(p * alpha)))
            
            frame_rgba.paste(txt_copy, (0, 0), txt_copy)
            final_frame = frame_rgba.convert("RGB")
            
            frame_path = os.path.join(frames_dir, f"f_{frame_num:04d}.jpg")
            final_frame.save(frame_path, "JPEG", quality=85)
        
        # Use ffmpeg to combine frames
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", os.path.join(frames_dir, "f_%04d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "ultrafast", "-crf", "23",
            output_path
        ], capture_output=True, timeout=60)
        
        # Cleanup frames
        import shutil
        shutil.rmtree(frames_dir, ignore_errors=True)
        
        return os.path.exists(output_path)
    except Exception as e:
        print(f"[KB] Error: {e}")
        import traceback; traceback.print_exc()
        return False


def _concat_clips(clip_paths, output_path):
    """Concatena multiplos clips de video em um"""
    if not clip_paths:
        return False
    
    # Criar arquivo de lista para ffmpeg
    list_path = os.path.join(VIDEOS_DIR, "_concat_list.txt")
    with open(list_path, "w") as f:
        for cp in clip_paths:
            f.write(f"file '{cp}'\n")
    
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "ultrafast", "-crf", "23",
            "-movflags", "+faststart",
            output_path
        ], capture_output=True, timeout=120)
        
        os.remove(list_path)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"[CONCAT] Error: {e}")
        return False


# ============ MAIN PIPELINE ============
async def generate_video(tema, template_id="livre"):
    start = time.time()
    video_id = uuid.uuid4().hex[:12]
    tpl = TEMPLATES.get(template_id, TEMPLATES["livre"])
    W, H = 1080, 1920
    
    print(f"\n[GEN] === Video #{video_id} ===")
    print(f"[GEN] Tema: {tema} | Template: {tpl['nome']}")
    
    # 1. Script AI
    script = await _ai_script(tema, template_id)
    cenas = script.get("cenas", [])[:6]
    print(f"[GEN] Script: {script.get('titulo','?')} ({len(cenas)} cenas)")
    
    # 2. Gerar imagens para cada cena (paralelo)
    print(f"[GEN] Gerando {len(cenas)} imagens...")
    img_tasks = []
    for cena in cenas:
        visual = cena.get("visual", tema)
        img_tasks.append(_generate_image(visual, 768, 1344))
    
    images = await asyncio.gather(*img_tasks)
    img_count = sum(1 for i in images if i)
    print(f"[GEN] Imagens: {img_count}/{len(cenas)}")
    
    # 3. Criar clips Ken Burns para cada cena
    print(f"[GEN] Criando clips Ken Burns...")
    clip_paths = []
    for i, (cena, img_path) in enumerate(zip(cenas, images)):
        if not img_path:
            continue
        
        clip_path = os.path.join(VIDEOS_DIR, f"_clip_{video_id}_{i}.mp4")
        texto = cena.get("texto", "")
        subtexto = cena.get("subtexto", "")
        duration = 3.5 if i > 0 else 4.0  # First scene slightly longer
        
        ok = _apply_ken_burns(img_path, clip_path, duration, W, H, texto, subtexto)
        if ok:
            clip_paths.append(clip_path)
            print(f"[GEN]   Clip {i+1}: {texto[:30]}... [{cena.get('visual','')[:25]}]")
    
    # 4. Concatenar clips
    output_path = os.path.join(VIDEOS_DIR, f"vid_{video_id}.mp4")
    success = False
    
    if clip_paths:
        print(f"[GEN] Concatenando {len(clip_paths)} clips...")
        success = _concat_clips(clip_paths, output_path)
        
        # Cleanup temp clips
        for cp in clip_paths:
            if os.path.exists(cp):
                os.remove(cp)
    
    elapsed = time.time() - start
    file_size = os.path.getsize(output_path) if success and os.path.exists(output_path) else 0
    
    result = {
        "id": video_id,
        "tema": tema,
        "template": template_id,
        "template_nome": tpl["nome"],
        "titulo": script.get("titulo", tema[:40]),
        "script": script,
        "cenas": len(cenas),
        "images_generated": img_count,
        "clips_created": len(clip_paths),
        "video_url": f"/static/videos/vid_{video_id}.mp4" if success else None,
        "file_size_kb": file_size // 1024,
        "hashtags": script.get("hashtags", "#viral #fyp"),
        "descricao": script.get("descricao", ""),
        "success": success,
        "elapsed": round(elapsed, 1),
        "created_at": datetime.now().isoformat(),
    }
    
    video_history.insert(0, result)
    if len(video_history) > 200:
        video_history.pop()
    
    print(f"[GEN] {'OK' if success else 'FAIL'} | {elapsed:.0f}s | {file_size//1024}KB")
    return result


# ============ ROUTES ============
@app.get("/")
async def home(request: Request):
    return templates_jinja.TemplateResponse("videogen.html", {"request": request})

@app.get("/api/templates")
async def api_templates():
    return {"templates": [{"id": k, **v} for k, v in TEMPLATES.items()]}

@app.post("/api/generate")
async def api_generate(request: Request):
    body = await request.json()
    tema = body.get("tema", "tecnologia e futuro")
    template_id = body.get("template", "livre")
    return await generate_video(tema, template_id)

@app.get("/api/videos")
async def api_videos():
    return {"videos": video_history}

@app.get("/api/videos/{video_id}/download")
async def api_download(video_id: str):
    fpath = os.path.join(VIDEOS_DIR, f"vid_{video_id}.mp4")
    if os.path.exists(fpath):
        return FileResponse(fpath, filename=f"video_{video_id}.mp4", media_type="video/mp4")
    return JSONResponse({"error": "not found"}, 404)

@app.delete("/api/videos/{video_id}")
async def api_delete(video_id: str):
    global video_history
    fpath = os.path.join(VIDEOS_DIR, f"vid_{video_id}.mp4")
    if os.path.exists(fpath):
        os.remove(fpath)
    video_history = [v for v in video_history if v["id"] != video_id]
    return {"deleted": video_id}
