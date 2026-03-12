#!/usr/bin/env python3
"""
YouTube Ken Burns QUALITY - Gera videos com imagens REAIS do Stable Horde.
Pre-gera todas as imagens em paralelo (batch), depois monta os videos.

Uso:
  python3 youtube_kb_quality.py                   # 1 video
  python3 youtube_kb_quality.py --quantidade 3    # 3 videos  
"""

import os, sys, time, json, random, hashlib, subprocess, argparse, pickle, io
import urllib.request, urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

FFMPEG = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg"
OLLAMA_URL = "http://localhost:11434/api/generate"
HORDE_URL = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"
YT_TOKEN_PATH = os.path.join(BASE_DIR, "youtube_token.pickle")
LOG_FILE = os.path.join(BASE_DIR, "youtube_ltx.log")

TEMAS_YT = [
    "Top 5 avanços de IA esta semana",
    "Como a IA transforma a medicina em 2026",
    "Robôs autônomos entregando encomendas",
    "IA generativa criando arte e música",
    "Carros autônomos em 2026",
    "IA no espaço explorando Marte",
    "Deepfakes: identificando vídeos falsos",
    "O futuro do trabalho com IA",
    "IA na educação: professores virtuais",
    "Drones com IA para resgate",
    "Chips neurais: interface cérebro-computador",
    "IA para games: NPCs inteligentes",
    "Smart cities gerenciadas por IA",
    "IA compondo música como Mozart",
    "IA e clima: combatendo mudanças climáticas",
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ============================================================
# OLLAMA ROTEIRO
# ============================================================
def gerar_roteiro(tema):
    import httpx
    prompt = f"""Crie roteiro de video YouTube (30s) sobre: "{tema}"
APENAS JSON:
{{
  "titulo": "Titulo YouTube atrativo (max 60 chars, portugues)",
  "descricao": "Descricao com hashtags (portugues)",
  "tags": ["tag1","tag2","tag3","tag4","tag5"],
  "cenas": [
    {{"visual": "detailed English description for AI image, cinematic, no real humans, sci-fi style", "duracao": 6}},
    {{"visual": "detailed English description, cinematic, dramatic lighting", "duracao": 6}},
    {{"visual": "detailed English description, cinematic, vibrant colors", "duracao": 6}},
    {{"visual": "detailed English description, cinematic, futuristic", "duracao": 6}},
    {{"visual": "detailed English description, cinematic, 4K quality", "duracao": 6}}
  ]
}}"""
    try:
        resp = httpx.post(OLLAMA_URL, json={
            "model": "llama3.2:3b", "prompt": prompt, "stream": False,
            "options": {"temperature": 0.8, "num_predict": 1024}
        }, timeout=60)
        text = resp.json().get("response", "")
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            d = json.loads(text[s:e])
            if d.get("cenas"): return d
    except: pass
    return {
        "titulo": tema[:60], "descricao": f"{tema}\n\n#IA #AI #Tech",
        "tags": ["IA","AI","Tech","Futuro","2026"],
        "cenas": [
            {"visual": "Futuristic cityscape holographic displays neon blue purple lights flying vehicles cinematic 4K", "duracao": 6},
            {"visual": "Glowing neural network brain light particles dark background dramatic blue cinematic 4K", "duracao": 6},
            {"visual": "Robot arm assembling microchips sparks flying macro shot dramatic orange lighting 4K", "duracao": 6},
            {"visual": "Holographic Earth data streams connecting cities space view dramatic lighting 4K", "duracao": 6},
            {"visual": "Futuristic laboratory glowing screens AI interfaces robot assistant purple lighting 4K", "duracao": 6},
        ]
    }

# ============================================================
# STABLE HORDE - BATCH DE IMAGENS (PARALELO)
# ============================================================
def submit_horde_image(prompt):
    """Submete uma imagem ao Horde e retorna o job ID"""
    full_prompt = f"{prompt}, masterpiece, best quality, highly detailed, 8K ### worst quality, blurry, text, watermark, ugly, deformed"
    body = json.dumps({
        "prompt": full_prompt,
        "params": {"width": 1024, "height": 576, "steps": 25, "n": 1,
                   "sampler_name": "k_euler_a", "cfg_scale": 7},
        "models": ["AlbedoBase XL (SDXL)"],
        "nsfw": False, "censor_nsfw": True, "shared": True,
    }).encode()
    req = urllib.request.Request(f"{HORDE_URL}/generate/async", data=body,
        headers={"apikey": HORDE_KEY, "Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return data.get("id")
    except Exception as e:
        log(f"    Horde submit erro: {e}")
        return None

def wait_horde_image(gen_id, max_wait=2400):
    """Espera o Horde terminar e retorna bytes da imagem"""
    start = time.time()
    while time.time() - start < max_wait:
        try:
            check = urllib.request.urlopen(f"{HORDE_URL}/generate/check/{gen_id}", timeout=15)
            status = json.loads(check.read())
            if status.get("done"):
                final = urllib.request.urlopen(f"{HORDE_URL}/generate/status/{gen_id}", timeout=15)
                fdata = json.loads(final.read())
                gens = fdata.get("generations", [])
                if gens and gens[0].get("img"):
                    img_req = urllib.request.Request(gens[0]["img"], headers={"User-Agent": "Mozilla/5.0"})
                    img_resp = urllib.request.urlopen(img_req, timeout=60)
                    return img_resp.read()
                return None
            wait = status.get("wait_time", 999)
            queue = status.get("queue_position", "?")
            elapsed = int(time.time() - start)
            if elapsed % 60 < 15:
                log(f"    Horde: fila={queue} espera~{wait}s ({elapsed}s passados)")
        except: pass
        time.sleep(15)
    return None

def gerar_imagens_batch(cenas):
    """Submete TODAS as imagens ao Horde em paralelo e espera"""
    log(f"  Submetendo {len(cenas)} imagens ao Horde em paralelo...")
    
    # Submit all
    jobs = []
    for i, cena in enumerate(cenas):
        job_id = submit_horde_image(cena.get("visual", "abstract futuristic background"))
        jobs.append((i, job_id))
        if job_id:
            log(f"    Cena {i+1}: job {job_id[:12]}...")
        time.sleep(1)
    
    # Wait all
    log(f"  Esperando {len(jobs)} imagens (pode demorar 5-40min)...")
    images = {}
    for i, job_id in jobs:
        if not job_id:
            images[i] = None
            continue
        img_data = wait_horde_image(job_id)
        if img_data and len(img_data) > 5000:
            images[i] = img_data
            log(f"    Cena {i+1}: OK ({len(img_data)//1024}KB)")
        else:
            images[i] = None
            log(f"    Cena {i+1}: FALHOU")
    
    return images

# ============================================================
# KEN BURNS VIDEO (COM IMAGENS REAIS)
# ============================================================
def criar_video_kenburns(roteiro, images_dict):
    from PIL import Image, ImageDraw
    
    video_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    cenas = roteiro.get("cenas", [])[:5]
    frames_dir = os.path.join(VIDEOS_DIR, f"yt_{video_id}")
    os.makedirs(frames_dir, exist_ok=True)

    KEN_BURNS_FX = ["zoom_in", "pan_right", "zoom_out", "pan_left"]
    segments = []

    for i, cena in enumerate(cenas):
        img_data = images_dict.get(i)
        if img_data:
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
            log(f"  Montando cena {i+1}: imagem real ({img.size})")
        else:
            # Gradiente bonito como fallback
            img = Image.new("RGB", (1024, 576), (10, 10, 30))
            d = ImageDraw.Draw(img)
            colors = [(100,0,200),(0,150,255),(200,0,100),(0,200,100),(255,100,0)]
            c = colors[i % len(colors)]
            for y in range(576):
                r = int(10 + y/576 * c[0] * 0.8)
                g = int(10 + y/576 * c[1] * 0.8)
                b = int(30 + y/576 * c[2] * 0.8)
                d.line([(0,y),(1024,y)], fill=(r,g,b))
            log(f"  Montando cena {i+1}: gradiente fallback")

        # Resize maior pra Ken Burns ter espaço
        img = img.resize((2304, 1296), Image.LANCZOS)
        scene_path = os.path.join(frames_dir, f"scene_{i:03d}.png")
        img.save(scene_path, quality=98)

        dur, fps = cena.get("duracao", 6), 30
        nf = dur * fps
        fx = KEN_BURNS_FX[i % len(KEN_BURNS_FX)]
        seg_path = os.path.join(frames_dir, f"seg_{i:03d}.mp4")

        zp = {
            "zoom_in": f"zoompan=z='min(zoom+0.0005,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s=1920x1080:fps={fps}",
            "zoom_out": f"zoompan=z='if(eq(on,1),1.15,max(zoom-0.0005,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s=1920x1080:fps={fps}",
            "pan_right": f"zoompan=z='1.1':x='if(eq(on,1),0,min(x+1.5,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':d={nf}:s=1920x1080:fps={fps}",
            "pan_left": f"zoompan=z='1.1':x='if(eq(on,1),iw/zoom,max(x-1.5,0))':y='ih/2-(ih/zoom/2)':d={nf}:s=1920x1080:fps={fps}",
        }.get(fx)

        cmd = [FFMPEG, "-y", "-i", scene_path, "-vf", zp,
               "-c:v", "libx264", "-preset", "fast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-t", str(dur), seg_path]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segments.append(seg_path)

    if not segments: return None

    output = os.path.join(VIDEOS_DIR, f"yt_{video_id}.mp4")
    concat_file = os.path.join(frames_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for s in segments: f.write(f"file '{s}'\n")
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
           "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", output]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if os.path.exists(output) and os.path.getsize(output) > 0:
        size_mb = os.path.getsize(output) / (1024*1024)
        log(f"  Video final: {size_mb:.1f}MB ({len(segments)} cenas)")
        return output
    return None

# ============================================================
# YOUTUBE UPLOAD
# ============================================================
def postar_youtube(video_path, titulo, descricao, tags=None):
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    with open(YT_TOKEN_PATH, 'rb') as f: creds = pickle.load(f)
    if creds.expired:
        creds.refresh(Request())
        with open(YT_TOKEN_PATH, 'wb') as f: pickle.dump(creds, f)

    yt = build('youtube', 'v3', credentials=creds)
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
    req = yt.videos().insert(
        part='snippet,status',
        body={
            'snippet': {'title': titulo[:100], 'description': descricao[:5000],
                        'tags': (tags or [])[:30], 'categoryId': '28'},
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False},
        }, media_body=media)
    
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status: log(f"  Upload: {int(status.progress()*100)}%")
    
    vid_id = resp.get('id', '?')
    link = f"https://www.youtube.com/watch?v={vid_id}"
    log(f"  PUBLICADO! {link}")
    return link

# ============================================================
# PIPELINE
# ============================================================
def processar_video(tema):
    log(f"\n{'='*60}")
    log(f"VIDEO: {tema}")
    log(f"{'='*60}")

    # 1. Roteiro
    log("[1/4] Roteiro (Ollama)...")
    roteiro = gerar_roteiro(tema)
    log(f"  Titulo: {roteiro.get('titulo','?')}")

    # 2. Gerar TODAS as imagens em batch
    log("[2/4] Gerando imagens (Stable Horde batch)...")
    images = gerar_imagens_batch(roteiro.get("cenas", []))
    ok_count = sum(1 for v in images.values() if v)
    log(f"  {ok_count}/{len(images)} imagens geradas com sucesso")

    # 3. Montar video
    log("[3/4] Montando video Ken Burns...")
    video_path = criar_video_kenburns(roteiro, images)
    if not video_path:
        log("  ERRO: video nao gerado!"); return None

    # 4. Postar YouTube
    log("[4/4] Postando YouTube...")
    return postar_youtube(video_path,
        roteiro.get("titulo", tema[:60]),
        roteiro.get("descricao", f"{tema}\n#IA #AI"),
        roteiro.get("tags", ["IA","AI"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quantidade", type=int, default=1)
    parser.add_argument("--tema", type=str, default=None)
    args = parser.parse_args()

    log(f"\n{'#'*60}")
    log(f"# YouTube KB Quality - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log(f"# Videos: {args.quantidade}")
    log(f"# NOTA: Cada video leva ~30-40min (fila Stable Horde)")
    log(f"{'#'*60}")

    temas = random.sample(TEMAS_YT, min(args.quantidade, len(TEMAS_YT)))
    for i in range(args.quantidade):
        tema = args.tema or temas[i % len(temas)]
        try:
            processar_video(tema)
        except Exception as e:
            log(f"ERRO: {e}")

    log("\n[FIM]")

if __name__ == "__main__":
    main()
