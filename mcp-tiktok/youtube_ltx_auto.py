#!/usr/bin/env python3
"""
YouTube Auto - Gera videos com IA (multiplas APIs) e posta no YouTube.

APIs de video (em ordem de prioridade):
  1. LTX API (pago, melhor qualidade)
  2. SiliconFlow / Wan2.2 ($1 gratis)
  3. Zhipu AI / CogVideoX (20M tokens gratis)
  4. Ken Burns fallback (100% gratis, imagens + zoompan)

Uso:
  python3 youtube_ltx_auto.py                   # 1 video
  python3 youtube_ltx_auto.py --quantidade 5    # 5 videos
  python3 youtube_ltx_auto.py --loop            # Loop infinito
  python3 youtube_ltx_auto.py --apenas-gerar    # Sem postar
  python3 youtube_ltx_auto.py --tema "IA na saude"
"""

import os, sys, time, json, random, hashlib, asyncio, subprocess, argparse, pickle, io
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(VIDEOS_DIR, exist_ok=True)

FFMPEG = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg"
OLLAMA_URL = "http://localhost:11434/api/generate"

# --- API KEYS ---
LTX_API_KEY = "ltxv_-D2RkRa6Qy9RHwsr15FGtEzjmEz9KRXMrcMiWvLTauUZSDMO5CDF3Ag_VF9IzF0LcMalPiMJkCJK3mnDPve3Y-gynD4XLVdLAGpwapltL7M0TQZdv_6t8qmA_5WrNJzzjG-zl-eQt8jrV5J8HHKJPRir-NYXFB1pDmJRabVQwQ"
SILICONFLOW_KEY = os.environ.get("SILICONFLOW_KEY", "sk-qfwhuxuvyjinlbqwhyygylaznzynkzbhyexojwpvyygjnemh")  # Cole sua key aqui ou export SILICONFLOW_KEY=sk-xxx
ZHIPU_KEY = os.environ.get("ZHIPU_KEY", "")              # Cole sua key aqui ou export ZHIPU_KEY=xxx

# --- LTX ---
LTX_API_URL = "https://api.ltx.video/v1/text-to-video"
LTX_MODEL = "ltx-2-3-fast"
LTX_CAMERAS = ["dolly_in", "dolly_out", "dolly_left", "dolly_right", "jib_up", "jib_down", "static"]

# --- SiliconFlow ---
SF_SUBMIT_URL = "https://api.siliconflow.com/v1/video/submit"
SF_STATUS_URL = "https://api.siliconflow.com/v1/video/status"
SF_MODEL = "Wan-AI/Wan2.2-T2V-A14B"  # mais barato: $0.21/video

# --- Zhipu AI ---
ZHIPU_MODEL = "cogvideox-2"  # cogvideox-2 ou cogvideox-3

# --- Stable Horde (Ken Burns) ---
HORDE_URL = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"

# --- YouTube ---
YT_TOKEN_PATH = os.path.join(BASE_DIR, "youtube_token.pickle")

LOG_FILE = os.path.join(BASE_DIR, "youtube_ltx.log")

# ============================================================
# TEMAS
# ============================================================
TEMAS_YT = [
    "Top 5 avanços de Inteligência Artificial esta semana",
    "Como a IA está transformando a medicina em 2026",
    "Robôs autônomos: o futuro da entrega de encomendas",
    "IA generativa: criando arte, música e vídeos do zero",
    "Os perigos da IA: o que precisamos saber",
    "Carros autônomos em 2026: onde estamos?",
    "IA no espaço: como robôs exploram Marte",
    "Deepfakes: como identificar vídeos falsos",
    "O futuro do trabalho com inteligência artificial",
    "IA na educação: professores virtuais já são realidade",
    "Drones com IA: vigilância, entregas e resgate",
    "Chips neurais: a interface cérebro-computador",
    "IA para games: NPCs que realmente pensam",
    "Como IA prevê terremotos e desastres naturais",
    "Hologramas e IA: a comunicação do futuro",
    "Fazendas inteligentes: IA na agricultura",
    "IA detectando câncer antes dos médicos",
    "Metaverso com IA: mundos virtuais inteligentes",
    "Tradução em tempo real com IA: fim das barreiras de idioma",
    "IA compondo música: o novo Mozart é uma máquina?",
    "Quantum computing + IA: a próxima revolução",
    "IA em cibersegurança: hackers vs defensores",
    "Smart cities: cidades gerenciadas por IA",
    "IA na moda: design e tendências geradas por máquina",
    "IA e clima: combatendo mudanças climáticas com dados",
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ============================================================
# OLLAMA - ROTEIRO
# ============================================================
def gerar_roteiro_ollama(tema):
    import httpx
    prompt = f"""Crie um roteiro para video curto YouTube (30s) sobre: "{tema}"
Responda APENAS JSON:
{{
  "titulo": "Titulo atrativo (max 60 chars, portugues)",
  "descricao": "Descricao YouTube com hashtags (portugues)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "cenas": [
    {{"visual": "detailed visual in English, cinematic, no real humans", "duracao": 6}},
    {{"visual": "detailed visual in English, cinematic, no real humans", "duracao": 6}},
    {{"visual": "detailed visual in English, cinematic, no real humans", "duracao": 6}},
    {{"visual": "detailed visual in English, cinematic, no real humans", "duracao": 6}},
    {{"visual": "detailed visual in English, cinematic, no real humans", "duracao": 6}}
  ]
}}
5 cenas de 6s. Visual em INGLES, sci-fi/tech. Titulo em PT. Apenas JSON."""

    try:
        resp = httpx.post(OLLAMA_URL, json={
            "model": "llama3.2:3b", "prompt": prompt, "stream": False,
            "options": {"temperature": 0.8, "num_predict": 1024}
        }, timeout=60)
        text = resp.json().get("response", "")
        start, end = text.find("{"), text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
            if data.get("cenas"): return data
    except Exception as e:
        log(f"  Ollama erro: {e}")
    return {
        "titulo": tema[:60],
        "descricao": f"{tema}\n\n#IA #AI #Tecnologia #Futuro #2026",
        "tags": ["IA", "AI", "Tecnologia", "Futuro", "2026"],
        "cenas": [
            {"visual": "Futuristic cityscape holographic displays neon lights flying vehicles cinematic 4K dramatic lighting", "duracao": 6},
            {"visual": "Glowing neural network brain made of light particles dark background dramatic blue lighting 4K", "duracao": 6},
            {"visual": "Robot arm assembling microchips sparks flying cinematic macro shot dramatic orange lighting 4K", "duracao": 6},
            {"visual": "Holographic Earth data streams connecting cities cinematic space view dramatic lighting 4K", "duracao": 6},
            {"visual": "Futuristic laboratory glowing screens AI interfaces robot assistant cinematic purple lighting 4K", "duracao": 6},
        ]
    }

# ============================================================
# 1. LTX API
# ============================================================
async def gerar_video_ltx(roteiro):
    import httpx
    if not LTX_API_KEY: return None
    video_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    cenas = roteiro.get("cenas", [])[:5]
    seg_dir = os.path.join(VIDEOS_DIR, f"yt_{video_id}")
    os.makedirs(seg_dir, exist_ok=True)
    segments = []

    for i, cena in enumerate(cenas):
        prompt = f"{cena.get('visual', '')}. Cinematic, professional, horizontal 16:9, 4K"
        camera = LTX_CAMERAS[i % len(LTX_CAMERAS)]
        log(f"  LTX cena {i+1}/{len(cenas)}: {cena.get('visual','')[:50]}...")
        try:
            async with httpx.AsyncClient(timeout=180) as client:
                resp = await client.post(LTX_API_URL,
                    headers={"Authorization": f"Bearer {LTX_API_KEY}", "Content-Type": "application/json"},
                    json={"prompt": prompt, "model": LTX_MODEL, "duration": 6,
                          "resolution": "1920x1080", "camera_motion": camera})
                if resp.status_code == 200 and len(resp.content) > 10000:
                    seg = os.path.join(seg_dir, f"seg_{i:03d}.mp4")
                    with open(seg, "wb") as f: f.write(resp.content)
                    segments.append(seg)
                    log(f"    OK: {len(resp.content)//1024}KB")
                elif resp.status_code == 402:
                    log("    LTX sem credito!"); return None
                else:
                    log(f"    Erro {resp.status_code}")
        except Exception as e:
            log(f"    Erro: {e}")

    return _concat_segments(segments, video_id) if segments else None

# ============================================================
# 2. SILICONFLOW / Wan2.2
# ============================================================
async def gerar_video_siliconflow(roteiro):
    import httpx
    if not SILICONFLOW_KEY: return None
    log("  [SiliconFlow] Gerando video...")

    cenas = roteiro.get("cenas", [])[:5]
    video_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    seg_dir = os.path.join(VIDEOS_DIR, f"yt_{video_id}")
    os.makedirs(seg_dir, exist_ok=True)
    segments = []
    headers = {"Authorization": f"Bearer {SILICONFLOW_KEY}", "Content-Type": "application/json"}

    for i, cena in enumerate(cenas):
        prompt = f"{cena.get('visual', '')}. Cinematic, professional, 4K quality"
        log(f"  SF cena {i+1}/{len(cenas)}: {cena.get('visual','')[:50]}...")
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                # Submit
                resp = await client.post(SF_SUBMIT_URL, headers=headers, json={
                    "model": SF_MODEL,
                    "prompt": prompt,
                    "negative_prompt": "blurry, low quality, distorted, text",
                    "image_size": "1280x720",
                })
                data = resp.json()
                req_id = data.get("requestId")
                if not req_id:
                    log(f"    SF erro submit: {data}")
                    continue

                # Poll status
                for _ in range(60):
                    await asyncio.sleep(10)
                    status = await client.post(SF_STATUS_URL, headers=headers,
                                               json={"requestId": req_id})
                    sdata = status.json()
                    st = sdata.get("status", "")
                    if st == "Succeed":
                        vids = sdata.get("results", {}).get("videos", [])
                        if vids and vids[0].get("url"):
                            vid_resp = await client.get(vids[0]["url"])
                            if vid_resp.status_code == 200 and len(vid_resp.content) > 10000:
                                seg = os.path.join(seg_dir, f"seg_{i:03d}.mp4")
                                with open(seg, "wb") as f: f.write(vid_resp.content)
                                segments.append(seg)
                                log(f"    OK: {len(vid_resp.content)//1024}KB")
                        break
                    elif st == "Failed":
                        log(f"    SF falhou: {sdata.get('reason','?')}"); break
                    elif st == "InsufficientBalance":
                        log("    SF sem saldo!"); return None
        except Exception as e:
            log(f"    SF erro: {e}")

    return _concat_segments(segments, video_id) if segments else None

# ============================================================
# 3. ZHIPU AI / CogVideoX
# ============================================================
async def gerar_video_zhipu(roteiro):
    if not ZHIPU_KEY: return None
    log("  [Zhipu/CogVideoX] Gerando video...")

    cenas = roteiro.get("cenas", [])[:5]
    video_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    seg_dir = os.path.join(VIDEOS_DIR, f"yt_{video_id}")
    os.makedirs(seg_dir, exist_ok=True)
    segments = []

    try:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=ZHIPU_KEY)
    except Exception as e:
        log(f"    Zhipu import erro: {e}"); return None

    for i, cena in enumerate(cenas):
        prompt = f"{cena.get('visual', '')}. Cinematic, professional, 4K quality"
        log(f"  Zhipu cena {i+1}/{len(cenas)}: {cena.get('visual','')[:50]}...")
        try:
            response = client.videos.generations(
                model=ZHIPU_MODEL,
                prompt=prompt,
                quality="speed",
                size="1920x1080",
                fps=30,
            )
            # Poll result
            import httpx
            for _ in range(60):
                await asyncio.sleep(10)
                result = client.videos.retrieve_videos_result(id=response.id)
                if hasattr(result, 'video_result') and result.video_result:
                    for vr in result.video_result:
                        if hasattr(vr, 'url') and vr.url:
                            async with httpx.AsyncClient(timeout=120) as hc:
                                vid_resp = await hc.get(vr.url)
                                if vid_resp.status_code == 200 and len(vid_resp.content) > 10000:
                                    seg = os.path.join(seg_dir, f"seg_{i:03d}.mp4")
                                    with open(seg, "wb") as f: f.write(vid_resp.content)
                                    segments.append(seg)
                                    log(f"    OK: {len(vid_resp.content)//1024}KB")
                            break
                    break
                elif hasattr(result, 'task_status') and result.task_status == 'FAIL':
                    log(f"    Zhipu falhou"); break
        except Exception as e:
            log(f"    Zhipu erro: {e}")

    return _concat_segments(segments, video_id) if segments else None

# ============================================================
# 4. KEN BURNS FALLBACK (100% GRATIS)
# ============================================================
async def gerar_video_kenburns(roteiro):
    from PIL import Image, ImageDraw, ImageFont
    import httpx

    video_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:10]
    cenas = roteiro.get("cenas", [])[:5]
    frames_dir = os.path.join(VIDEOS_DIR, f"yt_{video_id}")
    os.makedirs(frames_dir, exist_ok=True)

    KEN_BURNS_FX = ["zoom_in", "pan_right", "zoom_out", "pan_left"]
    segments = []

    for i, cena in enumerate(cenas):
        visual = cena.get("visual", "abstract background")
        log(f"  KB cena {i+1}/{len(cenas)}: {visual[:50]}...")

        # Gerar imagem via Stable Horde
        img_data = None
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{HORDE_URL}/generate/async",
                    headers={"apikey": HORDE_KEY, "Content-Type": "application/json"},
                    json={"prompt": visual + " ### worst quality, blurry, text",
                          "params": {"width": 1920, "height": 1088, "steps": 25, "n": 1,
                                     "sampler_name": "k_euler_a", "cfg_scale": 7},
                          "models": ["AlbedoBase XL (SDXL)"],
                          "nsfw": False, "censor_nsfw": True, "shared": True})
                if resp.status_code == 202:
                    gen_id = resp.json().get("id")
                    for _ in range(60):
                        await asyncio.sleep(10)
                        st = await client.get(f"{HORDE_URL}/generate/check/{gen_id}")
                        if st.json().get("done"):
                            res = await client.get(f"{HORDE_URL}/generate/status/{gen_id}")
                            gens = res.json().get("generations", [])
                            if gens and gens[0].get("img"):
                                ir = await client.get(gens[0]["img"])
                                if ir.status_code == 200: img_data = ir.content
                            break
        except Exception as e:
            log(f"    Horde erro: {e}")

        if img_data:
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
        else:
            img = Image.new("RGB", (1920, 1088), (15, 15, 45))
            d = ImageDraw.Draw(img)
            c = [(138,43,226),(0,191,255),(255,20,147),(0,255,127)][i%4]
            for y in range(1088):
                d.line([(0,y),(1920,y)], fill=(int(15+y/1088*c[0]*0.3), int(15+y/1088*c[1]*0.3), int(45+y/1088*c[2]*0.3)))

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
        cmd = [FFMPEG, "-y", "-i", scene_path, "-vf", zp, "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p", "-t", str(dur), seg_path]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segments.append(seg_path)

    return _concat_segments(segments, video_id) if segments else None

# ============================================================
# CONCAT HELPER
# ============================================================
def _concat_segments(segments, video_id):
    if not segments: return None
    output = os.path.join(VIDEOS_DIR, f"yt_{video_id}.mp4")
    if len(segments) == 1:
        subprocess.run(["cp", segments[0], output], capture_output=True)
    else:
        seg_dir = os.path.dirname(segments[0])
        concat_file = os.path.join(seg_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for s in segments: f.write(f"file '{s}'\n")
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            cmd2 = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p", output]
            subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
    if os.path.exists(output) and os.path.getsize(output) > 0:
        log(f"  Video: {os.path.getsize(output)//(1024*1024)}MB ({len(segments)} cenas)")
        return output
    return None

# ============================================================
# YOUTUBE UPLOAD
# ============================================================
def postar_youtube_api(video_path, titulo, descricao, tags=None):
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    if not os.path.exists(YT_TOKEN_PATH):
        log("[YT] Token nao encontrado!"); return None
    with open(YT_TOKEN_PATH, 'rb') as f: creds = pickle.load(f)
    if creds.expired:
        creds.refresh(Request())
        with open(YT_TOKEN_PATH, 'wb') as f: pickle.dump(creds, f)

    youtube = build('youtube', 'v3', credentials=creds)
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
    log(f"[YT] Upload: {os.path.getsize(video_path)//(1024*1024)}MB...")

    request = youtube.videos().insert(
        part='snippet,status',
        body={
            'snippet': {'title': titulo[:100], 'description': descricao[:5000],
                        'tags': (tags or ["IA","AI","Tech"])[:30], 'categoryId': '28'},
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False},
        },
        media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status: log(f"  Upload: {int(status.progress()*100)}%")

    vid_id = response.get('id', '?')
    link = f"https://www.youtube.com/watch?v={vid_id}"
    log(f"[YT] PUBLICADO! {link}")
    return link

# ============================================================
# PIPELINE PRINCIPAL
# ============================================================
async def processar_um_video(tema, apenas_gerar=False):
    log(f"\n{'='*60}")
    log(f"VIDEO: {tema}")
    log(f"{'='*60}")

    # 1. Roteiro
    log("[1/3] Roteiro (Ollama)...")
    roteiro = gerar_roteiro_ollama(tema)
    titulo = roteiro.get("titulo", tema[:60])
    descricao = roteiro.get("descricao", f"{tema}\n\n#IA #AI #Tech")
    tags = roteiro.get("tags", ["IA", "AI", "Tech"])
    log(f"  Titulo: {titulo}")

    # 2. Video - cascade de APIs
    log("[2/3] Gerando video...")
    video_path = None
    metodo = ""

    # Tentar LTX
    if LTX_API_KEY and not video_path:
        log("  Tentando LTX...")
        video_path = await gerar_video_ltx(roteiro)
        if video_path: metodo = "LTX"

    # Tentar SiliconFlow
    if SILICONFLOW_KEY and not video_path:
        log("  Tentando SiliconFlow/Wan2.2...")
        video_path = await gerar_video_siliconflow(roteiro)
        if video_path: metodo = "SiliconFlow"

    # Tentar Zhipu
    if ZHIPU_KEY and not video_path:
        log("  Tentando Zhipu/CogVideoX...")
        video_path = await gerar_video_zhipu(roteiro)
        if video_path: metodo = "Zhipu"

    # Ken Burns fallback
    if not video_path:
        log("  Fallback: Ken Burns...")
        video_path = await gerar_video_kenburns(roteiro)
        metodo = "Ken Burns"

    if not video_path:
        log("  ERRO: Nenhum video gerado!"); return None

    log(f"  OK ({metodo}): {video_path}")

    if apenas_gerar:
        log("  [apenas gerar]"); return video_path

    # 3. YouTube
    log("[3/3] Postando YouTube...")
    return postar_youtube_api(video_path, titulo, descricao, tags)


async def main():
    parser = argparse.ArgumentParser(description="YouTube Auto (LTX + Chinese APIs)")
    parser.add_argument("--quantidade", type=int, default=1)
    parser.add_argument("--apenas-gerar", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--tema", type=str, default=None)
    parser.add_argument("--intervalo", type=int, default=30)
    args = parser.parse_args()

    apis = []
    if LTX_API_KEY: apis.append("LTX")
    if SILICONFLOW_KEY: apis.append("SiliconFlow")
    if ZHIPU_KEY: apis.append("Zhipu")
    apis.append("KenBurns")

    log(f"\n{'#'*60}")
    log(f"# YouTube Auto - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log(f"# APIs: {' > '.join(apis)}")
    log(f"# Quantidade: {'loop' if args.loop else args.quantidade}")
    log(f"{'#'*60}")

    if args.loop:
        ciclo = 0
        while True:
            ciclo += 1
            tema = args.tema or random.choice(TEMAS_YT)
            log(f"\n>>> Ciclo {ciclo}")
            try: await processar_um_video(tema, args.apenas_gerar)
            except Exception as e: log(f"ERRO: {e}")
            log(f"Proximo em {args.intervalo}min...")
            await asyncio.sleep(args.intervalo * 60)
    else:
        temas = random.sample(TEMAS_YT, min(args.quantidade, len(TEMAS_YT)))
        for i in range(args.quantidade):
            tema = args.tema or temas[i % len(temas)]
            try: await processar_um_video(tema, args.apenas_gerar)
            except Exception as e: log(f"ERRO video {i+1}: {e}")
            if i < args.quantidade - 1:
                log("Proximo em 60s..."); await asyncio.sleep(60)

    log("\n[FIM]")

if __name__ == "__main__":
    asyncio.run(main())
