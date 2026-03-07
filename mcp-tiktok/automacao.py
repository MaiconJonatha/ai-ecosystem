#!/usr/bin/env python3
"""
TikTok Automation Engine
Gera videos automaticamente com IA e posta no TikTok.
Roda em background, gerando 1 video a cada intervalo configurado.
"""
import asyncio
import json
import os
import sys
import uuid
import random
import subprocess
import io
import re
import time
import httpx
from datetime import datetime, timedelta
from pathlib import Path

# ============ CONFIG ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
THUMBS_DIR = os.path.join(BASE_DIR, "thumbnails")
DATA_FILE = os.path.join(BASE_DIR, "tiktok_data.json")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
AUTO_LOG = os.path.join(BASE_DIR, "automacao.log")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
HORDE_URL = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"
FFMPEG = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg"

# Temas virais para gerar automaticamente
TEMAS_VIRAIS = [
    # Tech & AI
    "5 coisas que a IA ja faz melhor que humanos",
    "como a inteligencia artificial vai mudar o mundo em 2026",
    "3 apps de IA que voce precisa conhecer agora",
    "o futuro da tecnologia em 60 segundos",
    "5 profissoes que a IA vai criar",
    # Curiosidades
    "3 fatos sobre o oceano que vao te chocar",
    "5 curiosidades sobre o espaco que ninguem te contou",
    "coisas que parecem fake mas sao reais",
    "3 misterios da ciencia que ninguem consegue explicar",
    "5 fatos sobre o corpo humano que voce nao sabia",
    # Dinheiro
    "3 formas de ganhar dinheiro com IA em 2026",
    "como criar renda passiva usando tecnologia",
    "5 habilidades que pagam bem no futuro",
    "como a IA pode te ajudar a economizar dinheiro",
    # Motivacional
    "3 licoes de vida que ninguem te ensina na escola",
    "porque voce deveria comecar agora e nao amanha",
    "o segredo das pessoas mais produtivas do mundo",
    # Lifestyle
    "5 habitos matinais que mudam sua vida",
    "como organizar seu dia em 3 passos simples",
    "3 truques de produtividade que realmente funcionam",
    # Fun Facts
    "3 animais com superpoderes reais",
    "5 lugares mais estranhos do planeta Terra",
    "coisas que so existem no Japao",
    "3 invencoes brasileiras que mudaram o mundo",
]

ESTILOS = ["viral", "educativo", "storytelling", "motivacional", "humor"]

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(AUTO_LOG, "a") as f:
        f.write(line + "\n")

def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def fix_json(text):
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    raw = text[start:end]
    raw = re.sub(r',\s*}', '}', raw)
    raw = re.sub(r',\s*]', ']', raw)
    raw = re.sub(r'[\x00-\x1f]+', ' ', raw)
    try:
        return json.loads(raw)
    except:
        return None


# ============ AI GENERATION ============
async def ai_generate(prompt, max_tokens=1500, temperature=0.8):
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL, "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "")
    except Exception as e:
        log(f"Ollama error: {e}")
    return None


async def ai_script(tema, estilo="viral"):
    prompt = f"""Create a TikTok video script about: {tema}
Style: {estilo}
Respond ONLY with valid JSON (no extra text):
{{"titulo":"catchy short title in portuguese","gancho":"hook phrase first 3 seconds in portuguese","cenas":[{{"texto":"short text on screen in portuguese","visual":"detailed image description in english for AI image generator","duracao":5}}],"hashtags":["#hashtag1","#hashtag2","#hashtag3","#hashtag4","#hashtag5"],"caption":"full caption in portuguese with emojis and hashtags and CTA"}}
Rules: max 4 scenes, short text, valid JSON only, portuguese for text, english for visual descriptions."""

    for attempt in range(3):
        text = await ai_generate(prompt, 1500, 0.7 + attempt * 0.1)
        if text:
            script = fix_json(text)
            if script and "cenas" in script:
                return script
        log(f"  Script attempt {attempt+1} failed, retrying...")
        await asyncio.sleep(2)

    # Fallback manual
    log("  Using fallback script")
    return {
        "titulo": tema[:40],
        "gancho": "Voce precisa ver isso!",
        "cenas": [
            {"texto": tema[:50], "visual": f"cinematic illustration about {tema}, vibrant colors, professional, high quality", "duracao": 5},
            {"texto": "Isso vai te surpreender!", "visual": "surprised person looking at screen, colorful background, dynamic lighting", "duracao": 5},
            {"texto": "Compartilhe com alguem!", "visual": "social media sharing concept, hearts and likes floating, bright colors", "duracao": 5},
        ],
        "hashtags": ["#viral", "#fyp", "#curiosidades", "#facts", "#tiktok"],
        "caption": f"{tema} 🤯🔥 Salva e compartilha! #viral #fyp #curiosidades"
    }


async def generate_image(prompt):
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{HORDE_URL}/generate/async",
                headers={"apikey": HORDE_KEY},
                json={
                    "prompt": f"{prompt}, cinematic, vibrant colors, high quality, professional",
                    "params": {"width": 576, "height": 1024, "steps": 20, "cfg_scale": 7, "sampler_name": "k_euler_a"},
                    "nsfw": False,
                    "models": ["AlbedoBase XL (SDXL)", "Deliberate"],
                })
            if resp.status_code != 202:
                return None
            job_id = resp.json().get("id")
            if not job_id:
                return None

            for _ in range(60):
                await asyncio.sleep(5)
                check = await client.get(f"{HORDE_URL}/generate/check/{job_id}")
                d = check.json()
                if d.get("done"): break
                if d.get("faulted"): return None

            result = await client.get(f"{HORDE_URL}/generate/status/{job_id}")
            gens = result.json().get("generations", [])
            if gens:
                img_resp = await client.get(gens[0]["img"])
                if img_resp.status_code == 200:
                    return img_resp.content
    except Exception as e:
        log(f"  Horde error: {e}")
    return None


async def create_video(script, video_id):
    from PIL import Image, ImageDraw, ImageFont

    cenas = script.get("cenas", [])[:4]
    frames_dir = os.path.join(VIDEOS_DIR, f"frames_{video_id}")
    os.makedirs(frames_dir, exist_ok=True)
    scene_clips = []

    for i, cena in enumerate(cenas):
        log(f"  Cena {i+1}/{len(cenas)}: {cena.get('texto', '')[:40]}")
        img_data = await generate_image(cena.get("visual", "abstract background"))

        if img_data:
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
        else:
            img = Image.new("RGB", (576, 1024), (15, 15, 45))
            d = ImageDraw.Draw(img)
            colors = [(138,43,226), (0,191,255), (255,20,147), (0,255,127)]
            c = colors[i % len(colors)]
            for y in range(1024):
                r = int(15 + (y/1024) * c[0] * 0.3)
                g = int(15 + (y/1024) * c[1] * 0.3)
                b = int(45 + (y/1024) * c[2] * 0.3)
                d.line([(0, y), (576, y)], fill=(r, g, b))

        img = img.resize((1080, 1920), Image.LANCZOS)
        texto = cena.get("texto", "")

        if texto:
            overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.rounded_rectangle([60, 750, 1020, 1170], radius=20, fill=(0, 0, 0, 160))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            except:
                font = ImageFont.load_default()
                font_small = font

            words = texto.split()
            lines = []
            current = ""
            for w in words:
                test = current + " " + w if current else w
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] > 900:
                    lines.append(current)
                    current = w
                else:
                    current = test
            if current:
                lines.append(current)

            y_start = 800
            for line in lines[:4]:
                bbox = draw.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]
                x = (1080 - tw) // 2
                draw.text((x+2, y_start+2), line, fill=(0, 0, 0), font=font)
                draw.text((x, y_start), line, fill=(255, 255, 255), font=font)
                y_start += 65

            if i == 0 and script.get("gancho"):
                gancho = script["gancho"][:50]
                bbox = draw.textbbox((0, 0), gancho, font=font_small)
                tw = bbox[2] - bbox[0]
                x = (1080 - tw) // 2
                draw.text((x+1, 201), gancho, fill=(0, 0, 0), font=font_small)
                draw.text((x, 200), gancho, fill=(255, 220, 50), font=font_small)

        path = os.path.join(frames_dir, f"scene_{i:03d}.jpg")
        img.save(path, quality=95)
        scene_clips.append({"path": path, "duration": cena.get("duracao", 5)})

    # FFmpeg
    output = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    concat = os.path.join(frames_dir, "concat.txt")
    with open(concat, "w") as f:
        for c in scene_clips:
            f.write(f"file '{c['path']}'\nduration {c['duration']}\n")
        if scene_clips:
            f.write(f"file '{scene_clips[-1]['path']}'\n")

    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p", "-r", "30", output],
        capture_output=True, text=True, timeout=120)

    if os.path.exists(output) and os.path.getsize(output) > 0:
        return output
    return None


async def post_video(video_id, caption, account="default"):
    """Posta video se tiver sessionid configurado"""
    accounts = load_json(ACCOUNTS_FILE, {"accounts": []})
    acc = next((a for a in accounts.get("accounts", []) if a["name"] == account), None)

    if not acc or not acc.get("sessionid"):
        return False, "Sem sessionid configurado"

    video_path = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    if not os.path.exists(video_path):
        return False, "Video nao encontrado"

    try:
        from tiktok_uploader.upload import upload_video
        upload_video(filename=video_path, description=caption, sessionid=acc["sessionid"])
        return True, "Postado com sucesso!"
    except Exception as e:
        return False, str(e)


# ============ MAIN AUTOMATION LOOP ============
async def automation_loop(intervalo_min=30, max_videos=50, auto_post=True):
    """
    Loop principal de automacao.
    - Gera 1 video a cada intervalo_min minutos
    - Posta automaticamente se tiver conta configurada
    - Para apos max_videos ou Ctrl+C
    """
    log("=" * 60)
    log("TIKTOK AUTOMATION ENGINE - INICIADO")
    log(f"Intervalo: {intervalo_min} min | Max videos: {max_videos} | Auto-post: {auto_post}")
    log("=" * 60)

    temas_usados = set()
    videos_gerados = 0

    while videos_gerados < max_videos:
        try:
            # Escolher tema nao usado
            temas_disponiveis = [t for t in TEMAS_VIRAIS if t not in temas_usados]
            if not temas_disponiveis:
                temas_usados.clear()
                temas_disponiveis = TEMAS_VIRAIS

            tema = random.choice(temas_disponiveis)
            temas_usados.add(tema)
            estilo = random.choice(ESTILOS)
            video_id = uuid.uuid4().hex[:10]

            log(f"\n{'─'*50}")
            log(f"VIDEO {videos_gerados+1}/{max_videos}")
            log(f"Tema: {tema}")
            log(f"Estilo: {estilo}")
            log(f"ID: {video_id}")

            # 1. Gerar roteiro
            log("Gerando roteiro...")
            script = await ai_script(tema, estilo)
            log(f"  Titulo: {script.get('titulo', '?')}")
            log(f"  Cenas: {len(script.get('cenas', []))}")

            # 2. Criar video
            log("Criando video...")
            video_path = await create_video(script, video_id)

            if not video_path:
                log("ERRO: Video nao criado, pulando...")
                await asyncio.sleep(60)
                continue

            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            log(f"Video criado: {size_mb:.1f} MB")

            # 3. Salvar dados
            video_data = {
                "id": video_id,
                "tema": tema,
                "estilo": estilo,
                "script": script,
                "video_path": video_path,
                "size_mb": round(size_mb, 1),
                "created_at": datetime.now().isoformat(),
                "posted": False,
                "caption": script.get("caption", ""),
                "hashtags": script.get("hashtags", []),
            }

            all_data = load_json(DATA_FILE, {"videos": []})
            all_data.setdefault("videos", []).append(video_data)
            save_json(DATA_FILE, all_data)

            # 4. Postar automaticamente
            if auto_post:
                log("Postando no TikTok...")
                caption = script.get("caption", f"{tema} #viral #fyp")
                ok, msg = await post_video(video_id, caption)
                if ok:
                    log(f"POSTADO COM SUCESSO!")
                    video_data["posted"] = True
                    video_data["posted_at"] = datetime.now().isoformat()
                    save_json(DATA_FILE, all_data)
                else:
                    log(f"Nao postado: {msg}")
                    log("Video salvo para postar depois via MCP")

            videos_gerados += 1
            log(f"Total: {videos_gerados} videos gerados")

            # Esperar proximo ciclo
            if videos_gerados < max_videos:
                log(f"Proximo video em {intervalo_min} minutos...")
                await asyncio.sleep(intervalo_min * 60)

        except KeyboardInterrupt:
            log("Parado pelo usuario (Ctrl+C)")
            break
        except Exception as e:
            log(f"ERRO: {e}")
            await asyncio.sleep(60)

    log(f"\nAutomacao finalizada! {videos_gerados} videos gerados.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TikTok Automation Engine")
    parser.add_argument("--intervalo", type=int, default=30, help="Minutos entre videos (default: 30)")
    parser.add_argument("--max", type=int, default=50, help="Max videos a gerar (default: 50)")
    parser.add_argument("--no-post", action="store_true", help="Nao postar automaticamente")
    parser.add_argument("--once", action="store_true", help="Gerar apenas 1 video e sair")
    args = parser.parse_args()

    if args.once:
        args.max = 1

    asyncio.run(automation_loop(
        intervalo_min=args.intervalo,
        max_videos=args.max,
        auto_post=not args.no_post
    ))
