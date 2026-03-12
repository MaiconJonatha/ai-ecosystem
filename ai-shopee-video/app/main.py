"""
AI Shopee Video - Automatizador de Videos para Shopee
Gera videos de produtos automaticamente para postar no Shopee Video
"""
from fastapi import FastAPI, Request, BackgroundTasks
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
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ColorClip

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEOS_DIR = os.path.join(DIR, "static", "videos")
IMAGES_DIR = os.path.join(DIR, "static", "images")
MUSIC_DIR = os.path.join(DIR, "static", "music")
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# ============ API KEYS ============
GROQ_KEYS = [
    "GROQ_API_KEY_1",
    "GROQ_API_KEY_2",
]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

GOOGLE_API_KEY = "GEMINI_API_KEY_3"
STABLE_HORDE_KEY = "0000000000"

PIXABAY_KEY = "PIXABAY_API_KEY_HERE"
PEXELS_KEY = "wUJHrz5701c3ueVUbAwLyE4BeZeW0YdIGBxNvNoRAqz4Lqh1lpFiNOw8"

# ============ CATEGORIAS POPULARES SHOPEE ============
CATEGORIAS_SHOPEE = {
    "cozinha": {
        "nome": "Cozinha & Utilidades",
        "produtos": [
            "mini processador de alimentos eletrico",
            "cortador de legumes multifuncional",
            "organizador de geladeira transparente",
            "panela eletrica multifuncional",
            "escorredor de louça dobravel",
            "descascador de alho eletrico",
            "balanca digital de cozinha",
            "moedor de cafe manual",
            "fatiador de frutas e legumes",
            "abridor de latas eletrico",
            "espremedor de laranja portatil",
            "dispensador automatico de sabao",
        ],
        "hashtags": "#cozinha #achadinhos #shopee #utilidades #organização"
    },
    "pets": {
        "nome": "Pets & Animais",
        "produtos": [
            "removedor de pelos de pet automatico",
            "bebedouro fonte para gatos",
            "brinquedo interativo para cachorro",
            "escova auto-limpante para pets",
            "cama ortopedica para cachorro",
            "comedouro automatico para gatos",
            "coleira GPS rastreador pet",
            "shampoo seco para cachorro",
            "arranhador para gatos torre",
            "bolsa transporte pet aviao",
        ],
        "hashtags": "#pets #cachorro #gato #achadinhos #shopee"
    },
    "iluminacao": {
        "nome": "Iluminação & Decoração",
        "produtos": [
            "luminaria LED sensor de presenca",
            "fita LED RGB controle remoto",
            "abajur lua 3D levitante",
            "luminaria mesa USB recarregavel",
            "luz noturna projetor estrelas",
            "lampada inteligente wifi alexa",
            "ring light profissional tripé",
            "luminaria clip leitura LED",
            "vela LED recarregavel decorativa",
            "projetor aurora boreal quarto",
        ],
        "hashtags": "#iluminacao #decoracao #led #achadinhos #shopee"
    },
    "gadgets": {
        "nome": "Gadgets & Tecnologia",
        "produtos": [
            "fone bluetooth sem fio TWS",
            "carregador portatil 20000mah",
            "suporte celular carro magnetico",
            "mini projetor portatil LED",
            "smartwatch relogio inteligente",
            "webcam full HD 1080p",
            "mouse sem fio ergonomico",
            "hub USB-C multiportas",
            "caixa som bluetooth portatil",
            "ventilador portatil USB neck",
        ],
        "hashtags": "#gadgets #tecnologia #achadinhos #shopee"
    },
    "beleza": {
        "nome": "Beleza & Cuidados",
        "produtos": [
            "massageador facial eletrico",
            "secador de cabelo ionico portatil",
            "kit skincare vitamina C",
            "escova alisadora eletrica",
            "espelho LED maquiagem aumento",
            "depilador eletrico indolor",
            "chapinha mini portatil viagem",
            "vaporizador facial nano spray",
            "rolo jade massagem facial",
            "kit manicure eletrico profissional",
        ],
        "hashtags": "#beleza #skincare #achadinhos #shopee"
    },
    "casa": {
        "nome": "Casa & Limpeza",
        "produtos": [
            "aspirador robo inteligente",
            "mop spray com reservatorio",
            "organizador roupa guarda-roupa",
            "purificador ar portatil USB",
            "lixeira automatica sensor",
            "desumidificador eletrico compacto",
            "aromatizador eletrico difusor",
            "cabide eletrico secador roupa",
            "porta temperos giratório magnetico",
            "rodo magico auto torcedor",
        ],
        "hashtags": "#casa #limpeza #organizacao #achadinhos #shopee"
    },
}

# Estilos de video
ESTILOS_VIDEO = [
    "moderno_clean",       # fundo branco/gradiente, texto grande
    "neon_escuro",         # fundo escuro com neon colorido
    "pastel_suave",        # cores pastel, visual delicado
    "vermelho_shopee",     # tema Shopee (laranja/vermelho)
]

# Frases de chamada
FRASES_ABERTURA = [
    "ACHEI NA SHOPEE! 🔥",
    "OLHA ESSE ACHADO! 😱",
    "CORRE QUE TÁ BARATO! 💰",
    "PRODUTO VIRAL NA SHOPEE! 🚀",
    "NÃO COMPRE SEM VER ISSO! ⚡",
    "TOP 1 MAIS VENDIDO! 🏆",
    "CUPOM + FRETE GRÁTIS! 🎁",
    "TESTEI E APROVEI! ✅",
    "ANTES vs DEPOIS! 🤯",
    "TODO MUNDO COMPRANDO! 💸",
]

FRASES_CTA = [
    "Link na bio! Corre! 🏃‍♂️",
    "Clica no produto! ⬇️",
    "Adicione ao carrinho! 🛒",
    "Aproveite antes que acabe! ⏰",
    "Frete grátis! Não perca! 📦",
    "Desconto por tempo limitado! 💥",
]

# ============ VIDEO GENERATION STATE ============
video_queue = []  # lista de videos em fila
video_history = []  # historico de videos gerados
auto_running = False  # flag do loop automatico

# ============ LIFESPAN ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[SHOPEE-VIDEO] Servico iniciado na porta 8013!")
    print(f"[SHOPEE-VIDEO] {len(CATEGORIAS_SHOPEE)} categorias | {sum(len(c['produtos']) for c in CATEGORIAS_SHOPEE.values())} produtos")
    yield
    print("[SHOPEE-VIDEO] Servico encerrado.")

app = FastAPI(title="AI Shopee Video", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=os.path.join(DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(DIR, "templates"))


# ============ AI HELPERS ============
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

async def _ai_generate(prompt: str, system: str = "") -> str:
    """Generate text with Ollama (local)"""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": full_prompt, "stream": False}
            )
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[AI] Ollama Error: {e}")
    return ""


async def _ai_product_script(produto: str, categoria: str) -> dict:
    """Gera roteiro de video para um produto"""
    system = """Voce e um criador de conteudo especialista em Shopee Video. 
Gere roteiros curtos e persuasivos para videos de produtos.
Responda APENAS em JSON valido, sem markdown."""
    
    prompt = f"""Crie um roteiro para video curto de Shopee Video sobre:
Produto: {produto}
Categoria: {categoria}

Responda em JSON:
{{
    "titulo": "titulo chamativo do video (max 50 chars)",
    "descricao": "descricao do produto em 2 frases persuasivas",
    "beneficios": ["beneficio 1", "beneficio 2", "beneficio 3"],
    "preco_sugerido": "R$ XX,XX",
    "frase_gancho": "frase curta de abertura tipo clickbait",
    "cta": "chamada para acao final"
}}"""
    
    text = await _ai_generate(prompt, system)
    try:
        # Clean JSON
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        return json.loads(text)
    except:
        return {
            "titulo": f"ACHADO INCRÍVEL: {produto.title()}",
            "descricao": f"Esse {produto} é simplesmente incrível! Qualidade premium por um preço que cabe no bolso.",
            "beneficios": ["Qualidade premium", "Entrega rápida", "Melhor preço"],
            "preco_sugerido": f"R$ {random.randint(19,99)},{random.choice(['90','99'])}",
            "frase_gancho": random.choice(FRASES_ABERTURA),
            "cta": random.choice(FRASES_CTA)
        }


async def _generate_product_image(prompt: str) -> str:
    """Gera imagem do produto com Stable Horde"""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # Stable Horde
            resp = await client.post(
                "https://stablehorde.net/api/v2/generate/async",
                headers={"apikey": STABLE_HORDE_KEY},
                json={
                    "prompt": f"product photo, {prompt}, clean white background, professional lighting, e-commerce style, high quality",
                    "params": {"width": 768, "height": 768, "steps": 25, "cfg_scale": 7.5, "sampler_name": "k_euler", "n": 1},
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
                                    img_url = gens[0]["img"]
                                    # Download and save locally
                                    img_resp = await client.get(img_url)
                                    if img_resp.status_code == 200:
                                        fname = f"prod_{uuid.uuid4().hex[:10]}.webp"
                                        fpath = os.path.join(IMAGES_DIR, fname)
                                        with open(fpath, "wb") as f:
                                            f.write(img_resp.content)
                                        print(f"[IMG] Horde: {prompt[:40]}...")
                                        return fpath
                            break
            
            # Fallback: Pixabay
            search_q = prompt.split(",")[0][:50]
            resp = await client.get(
                "https://pixabay.com/api/",
                params={"key": PIXABAY_KEY, "q": search_q, "image_type": "photo", "per_page": 10, "safesearch": "true"}
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    img_url = random.choice(hits).get("largeImageURL", "")
                    if img_url:
                        img_resp = await client.get(img_url)
                        if img_resp.status_code == 200:
                            fname = f"prod_{uuid.uuid4().hex[:10]}.jpg"
                            fpath = os.path.join(IMAGES_DIR, fname)
                            with open(fpath, "wb") as f:
                                f.write(img_resp.content)
                            print(f"[IMG] Pixabay: {search_q[:40]}...")
                            return fpath
    except Exception as e:
        print(f"[IMG] Error: {e}")
    return ""


def _create_slide(width, height, text, subtext="", bg_color=(255, 87, 34), text_color=(255, 255, 255)):
    """Cria um slide/frame com texto"""
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Tentar carregar fontes
    font_big = None
    font_small = None
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFCompact.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font_big = ImageFont.truetype(fp, 52)
                font_small = ImageFont.truetype(fp, 36)
                break
            except:
                continue
    if not font_big:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Texto principal centralizado
    def draw_centered(draw, text, y, font, color):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        # Sombra
        draw.text((x+2, y+2), text, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=color)
    
    # Quebrar texto em linhas
    words = text.split()
    lines = []
    line = ""
    for w in words:
        test = line + " " + w if line else w
        bbox = draw.textbbox((0, 0), test, font=font_big)
        if bbox[2] - bbox[0] > width - 80:
            if line:
                lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    
    # Desenhar linhas centralizadas
    total_h = len(lines) * 60
    start_y = (height - total_h) // 2 - 30
    for i, line in enumerate(lines):
        draw_centered(draw, line, start_y + i * 60, font_big, text_color)
    
    # Subtexto
    if subtext:
        draw_centered(draw, subtext, start_y + len(lines) * 60 + 20, font_small, (255, 255, 200))
    
    return img


def _create_product_video(script: dict, product_img_path: str, output_path: str, categoria_info: dict) -> bool:
    """Cria video do produto com slides animados"""
    W, H = 1080, 1920  # 9:16 vertical (Shopee Video format)
    FPS = 24
    SLIDE_DURATION = 3  # segundos por slide
    
    try:
        slides = []
        
        # Cores do tema
        cores = {
            "shopee": [(238, 77, 45), (255, 106, 0)],    # Laranja Shopee
            "dark": [(30, 30, 50), (60, 20, 80)],          # Escuro
            "clean": [(245, 245, 250), (230, 240, 255)],   # Claro
        }
        tema = random.choice(list(cores.keys()))
        bg1, bg2 = cores[tema]
        txt_color = (255, 255, 255) if tema != "clean" else (30, 30, 30)
        
        # SLIDE 1: Gancho de abertura
        frase = script.get("frase_gancho", random.choice(FRASES_ABERTURA))
        s1 = _create_slide(W, H, frase, "", bg1, txt_color)
        slides.append(s1)
        
        # SLIDE 2: Imagem do produto (se tiver)
        if product_img_path and os.path.exists(product_img_path):
            bg = Image.new("RGB", (W, H), bg2)
            draw = ImageDraw.Draw(bg)
            prod_img = Image.open(product_img_path)
            # Redimensionar para caber
            max_size = 700
            prod_img.thumbnail((max_size, max_size), Image.LANCZOS)
            px = (W - prod_img.width) // 2
            py = (H - prod_img.height) // 2 - 100
            bg.paste(prod_img, (px, py))
            # Titulo abaixo
            titulo = script.get("titulo", "PRODUTO INCRIVEL")[:40]
            font_paths = ["/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"]
            font = None
            for fp in font_paths:
                if os.path.exists(fp):
                    try:
                        font = ImageFont.truetype(fp, 44)
                        break
                    except:
                        continue
            if not font:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), titulo, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((W - tw) // 2, py + prod_img.height + 40), titulo, font=font, fill=txt_color)
            slides.append(bg)
        
        # SLIDE 3: Descricao
        desc = script.get("descricao", "Produto incrivel da Shopee!")
        s3 = _create_slide(W, H, desc, "", bg1, txt_color)
        slides.append(s3)
        
        # SLIDE 4: Beneficios
        beneficios = script.get("beneficios", ["Qualidade", "Preço baixo", "Frete grátis"])
        benef_text = "\n".join([f"✅ {b}" for b in beneficios[:3]])
        s4 = _create_slide(W, H, benef_text, "", bg2, txt_color)
        slides.append(s4)
        
        # SLIDE 5: Preco
        preco = script.get("preco_sugerido", "R$ 49,99")
        s5 = _create_slide(W, H, f"APENAS {preco}", "🔥 MENOR PREÇO 🔥", (238, 77, 45), (255, 255, 255))
        slides.append(s5)
        
        # SLIDE 6: CTA
        cta = script.get("cta", random.choice(FRASES_CTA))
        hashtags = categoria_info.get("hashtags", "#shopee #achadinhos")
        s6 = _create_slide(W, H, cta, hashtags, bg1, txt_color)
        slides.append(s6)
        
        # Salvar slides como imagens temporarias e criar video
        clips = []
        for i, slide in enumerate(slides):
            slide_path = os.path.join(IMAGES_DIR, f"_temp_slide_{i}.png")
            slide.save(slide_path, "PNG")
            clip = ImageClip(slide_path).with_duration(SLIDE_DURATION)
            clips.append(clip)
        
        # Concatenar
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(output_path, fps=FPS, codec="libx264", audio=False, 
                            logger=None, preset="ultrafast")
        final.close()
        for c in clips:
            c.close()
        
        # Limpar temp
        for i in range(len(slides)):
            tmp = os.path.join(IMAGES_DIR, f"_temp_slide_{i}.png")
            if os.path.exists(tmp):
                os.remove(tmp)
        
        file_size = os.path.getsize(output_path)
        print(f"[VIDEO] Criado: {output_path} ({file_size // 1024}KB)")
        return True
    except Exception as e:
        print(f"[VIDEO] Error creating video: {e}")
        import traceback
        traceback.print_exc()
        return False


async def _create_shopee_video(categoria: str = None, produto: str = None) -> dict:
    """Pipeline completo: escolhe produto -> gera script -> gera imagem -> cria video"""
    start_time = time.time()
    
    # Escolher categoria e produto
    if not categoria:
        categoria = random.choice(list(CATEGORIAS_SHOPEE.keys()))
    cat_info = CATEGORIAS_SHOPEE.get(categoria, list(CATEGORIAS_SHOPEE.values())[0])
    
    if not produto:
        produto = random.choice(cat_info["produtos"])
    
    video_id = uuid.uuid4().hex[:12]
    print(f"[SHOPEE] Gerando video #{video_id}: {produto} ({categoria})")
    
    # 1. Gerar roteiro com IA
    script = await _ai_product_script(produto, cat_info["nome"])
    print(f"[SHOPEE] Script gerado: {script.get('titulo', '?')}")
    
    # 2. Gerar imagem do produto
    product_img = await _generate_product_image(produto)
    print(f"[SHOPEE] Imagem: {'OK' if product_img else 'Pixabay fallback'}")
    
    # 3. Criar video
    output_path = os.path.join(VIDEOS_DIR, f"shopee_{video_id}.mp4")
    success = _create_product_video(script, product_img, output_path, cat_info)
    
    elapsed = time.time() - start_time
    
    result = {
        "id": video_id,
        "produto": produto,
        "categoria": categoria,
        "categoria_nome": cat_info["nome"],
        "script": script,
        "product_image": f"/static/images/{os.path.basename(product_img)}" if product_img else None,
        "video_url": f"/static/videos/shopee_{video_id}.mp4" if success else None,
        "hashtags": cat_info["hashtags"],
        "created_at": datetime.now().isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "success": success
    }
    
    video_history.insert(0, result)
    if len(video_history) > 100:
        video_history.pop()
    
    return result


# ============ AUTO LOOP ============
async def _auto_video_loop():
    """Loop automatico que gera videos continuamente"""
    global auto_running
    auto_running = True
    print("[SHOPEE] Loop automatico INICIADO!")
    
    while auto_running:
        try:
            result = await _create_shopee_video()
            status = "OK" if result["success"] else "FAIL"
            print(f"[SHOPEE-AUTO] Video {result['id']}: {result['produto'][:30]} [{status}] ({result['elapsed_seconds']}s)")
            
            # Esperar entre videos (60-120 segundos)
            wait = random.randint(60, 120)
            print(f"[SHOPEE-AUTO] Proximo video em {wait}s...")
            await asyncio.sleep(wait)
        except Exception as e:
            print(f"[SHOPEE-AUTO] Error: {e}")
            await asyncio.sleep(30)
    
    print("[SHOPEE] Loop automatico PARADO!")


# ============ API ROUTES ============
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("shopee.html", {"request": request})


@app.get("/api/status")
async def api_status():
    return {
        "running": auto_running,
        "videos_count": len(video_history),
        "categorias": len(CATEGORIAS_SHOPEE),
        "produtos_total": sum(len(c["produtos"]) for c in CATEGORIAS_SHOPEE.values())
    }


@app.get("/api/categorias")
async def api_categorias():
    return {
        "categorias": [
            {"id": k, "nome": v["nome"], "produtos": len(v["produtos"]), "hashtags": v["hashtags"]}
            for k, v in CATEGORIAS_SHOPEE.items()
        ]
    }


@app.post("/api/gerar")
async def api_gerar(request: Request):
    """Gera um video manualmente"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    categoria = body.get("categoria")
    produto = body.get("produto")
    
    result = await _create_shopee_video(categoria, produto)
    return result


@app.post("/api/auto/start")
async def api_auto_start():
    """Inicia loop automatico"""
    global auto_running
    if auto_running:
        return {"status": "already_running"}
    asyncio.create_task(_auto_video_loop())
    return {"status": "started"}


@app.post("/api/auto/stop")
async def api_auto_stop():
    """Para loop automatico"""
    global auto_running
    auto_running = False
    return {"status": "stopped"}


@app.get("/api/videos")
async def api_videos():
    """Lista videos gerados"""
    return {"videos": video_history}


@app.get("/api/videos/{video_id}/download")
async def api_download(video_id: str):
    """Download de video"""
    fpath = os.path.join(VIDEOS_DIR, f"shopee_{video_id}.mp4")
    if os.path.exists(fpath):
        return FileResponse(fpath, filename=f"shopee_{video_id}.mp4", media_type="video/mp4")
    return JSONResponse({"error": "Video not found"}, 404)


# ============ SHOPEE POSTING AUTOMATION ============
import glob as _glob
import subprocess

_shopee_posting = False
_shopee_post_log = []

@app.get("/api/shopee/status")
async def api_shopee_posting_status():
    """Status da automação de postagem na Shopee"""
    cookies_exist = os.path.exists(os.path.join(DIR, "shopee_cookies.json"))
    posted_file = os.path.join(DIR, "shopee_posted.json")
    posted = json.load(open(posted_file)) if os.path.exists(posted_file) else []
    all_videos = _glob.glob(os.path.join(VIDEOS_DIR, "shopee_*.mp4"))
    return {
        "logado": cookies_exist,
        "posting_active": _shopee_posting,
        "videos_total": len(all_videos),
        "videos_postados": len(posted),
        "videos_disponiveis": len(all_videos) - len(posted),
        "log": _shopee_post_log[-20:],
    }

@app.post("/api/shopee/login")
async def api_shopee_login():
    """Abre navegador para login no Shopee Seller Center"""
    proc = subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_poster.py"), "--login"],
        cwd=DIR
    )
    return {"status": "login_started", "msg": "Navegador aberto. Faça login manualmente."}

@app.post("/api/shopee/post")
async def api_shopee_post(request: Request):
    """Gera video + posta na Shopee em um passo"""
    global _shopee_posting
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}

    # 1. Gerar vídeo
    result = await _create_shopee_video(body.get("categoria"), body.get("produto"))

    if not result.get("success"):
        return {"error": "Falha ao gerar vídeo", "details": result}

    # 2. Postar na Shopee (em background)
    video_path = os.path.join(VIDEOS_DIR, f"shopee_{result['id']}.mp4")
    _shopee_post_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Postando: {result['produto'][:40]}...")

    proc = subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_poster.py"), "--post", video_path],
        cwd=DIR
    )

    return {
        "status": "posting",
        "video": result,
        "msg": f"Vídeo gerado! Postando na Shopee: {result['produto'][:40]}..."
    }

@app.post("/api/shopee/auto/start")
async def api_shopee_auto_start(request: Request):
    """Inicia loop de auto-postagem na Shopee"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    max_posts = body.get("max", 10)
    intervalo = body.get("intervalo", 120)

    proc = subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_poster.py"), "--auto",
         "--max", str(max_posts), "--intervalo", str(intervalo)],
        cwd=DIR
    )
    global _shopee_posting
    _shopee_posting = True
    _shopee_post_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Auto-post iniciado: {max_posts} posts, {intervalo}s intervalo")

    return {"status": "started", "max": max_posts, "intervalo": intervalo}

@app.post("/api/shopee/afiliado/buscar")
async def api_afiliado_buscar(request: Request):
    """Busca produtos para afiliados"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    nicho = body.get("nicho")
    proc = subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_afiliado.py"), "--buscar"] +
        (["--nicho", nicho] if nicho else []) +
        ["--headless"],
        cwd=DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return {"status": "buscando", "nicho": nicho or "aleatorio"}

@app.post("/api/shopee/afiliado/pipeline")
async def api_afiliado_pipeline(request: Request):
    """Pipeline completo: busca + links + vídeos"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    nicho = body.get("nicho")
    max_p = body.get("max", 5)
    proc = subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_afiliado.py"), "--pipeline",
         "--max", str(max_p)] + (["--nicho", nicho] if nicho else []),
        cwd=DIR
    )
    return {"status": "pipeline_started", "nicho": nicho, "max": max_p}

@app.get("/api/shopee/afiliado/links")
async def api_afiliado_links():
    """Lista links de afiliado salvos"""
    aff_file = os.path.join(DIR, "shopee_affiliate_links.json")
    if os.path.exists(aff_file):
        links = json.load(open(aff_file))
        return {"total": len(links), "links": links[-20:]}
    return {"total": 0, "links": []}

@app.get("/api/shopee/videos")
async def api_shopee_videos_available():
    """Lista vídeos disponíveis para postar"""
    posted_file = os.path.join(DIR, "shopee_posted.json")
    posted = set(json.load(open(posted_file))) if os.path.exists(posted_file) else set()
    all_videos = _glob.glob(os.path.join(VIDEOS_DIR, "shopee_*.mp4"))

    videos = []
    for v in sorted(all_videos, key=os.path.getmtime, reverse=True)[:50]:
        videos.append({
            "path": v,
            "name": os.path.basename(v),
            "size_kb": os.path.getsize(v) // 1024,
            "posted": v in posted,
            "date": datetime.fromtimestamp(os.path.getmtime(v)).isoformat(),
        })
    return {"videos": videos}

# ============ SHOPEE AGENTS API ============
import subprocess as _subprocess

@app.get("/api/agents/status")
async def api_agents_status():
    """Status do sistema de agentes Shopee"""
    aff_file = os.path.join(DIR, "affiliate_links.json")
    posts_file = os.path.join(DIR, "affiliate_posts_log.json")
    links = json.load(open(aff_file)) if os.path.exists(aff_file) else []
    posts = json.load(open(posts_file)) if os.path.exists(posts_file) else []
    videos = _glob.glob(os.path.join(DIR, "static", "videos", "*.mp4")) + _glob.glob(os.path.join(DIR, "videos", "*.mp4"))
    com_link = sum(1 for l in links if l.get("url_afiliado"))
    postados = sum(1 for l in links if l.get("postado"))
    return {
        "total_links": len(links), "com_afiliado": com_link,
        "postados": postados, "posts_gerados": len(posts),
        "videos_disponiveis": len(videos),
    }

@app.post("/api/agents/pipeline")
async def api_agents_pipeline(request: Request):
    """Executa pipeline: buscar + gerar links + gerar posts"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    max_p = body.get("max", 5)
    categorias = body.get("categorias", None)
    args = ["python3", os.path.join(DIR, "shopee_agents.py"), "--pipeline", "--max", str(max_p)]
    if categorias:
        args.extend(["--categorias", categorias])
    _subprocess.Popen(args, cwd=DIR)
    return {"status": "pipeline_started", "max": max_p, "categorias": categorias}

@app.post("/api/agents/auto")
async def api_agents_auto(request: Request):
    """Inicia modo automático de agentes"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    intervalo = body.get("intervalo", 1800)
    max_ciclos = body.get("max", 5)
    _subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_agents.py"), "--auto",
         "--intervalo", str(intervalo), "--max", str(max_ciclos)],
        cwd=DIR
    )
    return {"status": "auto_started", "intervalo": intervalo, "max_ciclos": max_ciclos}

@app.post("/api/agents/buscar")
async def api_agents_buscar(request: Request):
    """Busca produtos no Shopee"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    termo = body.get("termo", "fone bluetooth")
    _subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_agents.py"), "--buscar", termo],
        cwd=DIR
    )
    return {"status": "busca_started", "termo": termo}

@app.get("/api/agents/links")
async def api_agents_links():
    """Lista links de afiliado com posts"""
    aff_file = os.path.join(DIR, "affiliate_links.json")
    posts_file = os.path.join(DIR, "affiliate_posts_log.json")
    links = json.load(open(aff_file)) if os.path.exists(aff_file) else []
    posts = json.load(open(posts_file)) if os.path.exists(posts_file) else []
    return {"total": len(links), "links": links[-30:], "posts": posts[-10:]}


# ============ PIPELINE REVIEW VIDEO ============
import subprocess as _subprocess

@app.post("/api/pipeline/single")
async def api_pipeline_single(request: Request):
    """Roda pipeline completo para 1 produto (review video)"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    categoria = body.get("categoria", None)
    post = body.get("post", True)
    args = ["python3", os.path.join(DIR, "shopee_pipeline.py"), "--single"]
    if categoria:
        args.extend(["--categoria", categoria])
    if not post:
        args = ["python3", os.path.join(DIR, "shopee_pipeline.py"), "--test-video"]
        if categoria:
            args.extend(["--categoria", categoria])
    _subprocess.Popen(args, cwd=DIR)
    return {"status": "pipeline_started", "categoria": categoria, "post": post}

@app.post("/api/pipeline/auto/start")
async def api_pipeline_auto_start(request: Request):
    """Inicia loop automático do pipeline"""
    body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    max_posts = body.get("max", 20)
    intervalo = body.get("intervalo", 300)
    _subprocess.Popen(
        ["python3", os.path.join(DIR, "shopee_pipeline.py"), "--auto",
         "--max", str(max_posts), "--intervalo", str(intervalo)],
        cwd=DIR
    )
    return {"status": "auto_pipeline_started", "max": max_posts, "intervalo": intervalo}

@app.get("/api/pipeline/status")
async def api_pipeline_status():
    """Status do pipeline"""
    log_file = os.path.join(DIR, "pipeline_log.json")
    pipeline_log = json.load(open(log_file)) if os.path.exists(log_file) else []
    return {
        "total": len(pipeline_log),
        "posted": sum(1 for p in pipeline_log if p.get("posted")),
        "recent": pipeline_log[-10:],
    }
