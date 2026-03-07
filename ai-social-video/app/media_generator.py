"""
Gerador de Imagens e Videos para Instagram das IAs
- Imagens geradas por Pollinations FLUX (API gratuita de alta qualidade)
- Fallback para Stable Diffusion local
- Videos (Reels) criados com efeito Ken Burns sobre imagens IA
- Fallback final para PIL se nenhuma API estiver disponivel
"""
import os
import io
import uuid
import math
import random
import time
import urllib.parse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from datetime import datetime
import httpx

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media", "instagram")
os.makedirs(os.path.join(MEDIA_DIR, "photos"), exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "reels"), exist_ok=True)
os.makedirs(os.path.join(MEDIA_DIR, "stories"), exist_ok=True)

SD_API_URL = "http://localhost:8013"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

# Prompts por estilo (para geracao de imagem IA)
PROMPTS_ESTILO = {
    "tecnologia": [
        "futuristic AI robot in a neon-lit server room, digital art, cyberpunk style, glowing circuits, no humans",
        "abstract technology concept, flowing data streams, holographic display, digital art, no people",
        "cute cartoon robot building a computer, digital illustration, colorful, anime style, no real humans",
        "artificial intelligence brain made of light and circuits, digital art, beautiful colors, no humans",
        "futuristic city with flying drones and AI towers, cartoon style, vibrant, no real people",
    ],
    "entretenimento": [
        "cartoon characters watching a movie on a giant screen, digital illustration, colorful, fun, no real humans",
        "cute animated animals having a party, confetti and balloons, digital art, vibrant colors",
        "cartoon stage with spotlight and music notes, digital illustration, fun atmosphere, no real humans",
        "animated popcorn and movie tickets floating in space, digital art, playful",
        "cute cartoon DJ playing music at a neon party, digital illustration, no real humans",
    ],
    "arte": [
        "abstract painting with vibrant colors and geometric shapes, modern art, digital illustration",
        "surreal landscape with floating islands and rainbow waterfalls, digital art, beautiful",
        "colorful abstract art with swirling paint and gold accents, digital illustration, no humans",
        "beautiful digital mandala with intricate patterns, vibrant colors, sacred geometry",
        "dreamy galaxy art with nebula colors and stars, cosmic art, digital illustration",
    ],
    "ciencia": [
        "cartoon scientist robot discovering a new planet, digital illustration, cute, colorful, no real humans",
        "beautiful DNA double helix glowing in blue light, digital art, science visualization",
        "animated atom model with orbiting electrons, colorful digital art, science illustration",
        "cartoon telescope looking at stars and galaxies, digital illustration, cute, no real humans",
        "microscopic view of cells in beautiful colors, digital science art, abstract",
    ],
    "gaming": [
        "cute cartoon video game characters in a pixel world, digital illustration, colorful, no real humans",
        "epic fantasy game landscape with castle and dragons, digital art, cartoon style",
        "retro arcade machine glowing with neon lights, digital art, nostalgic",
        "cartoon robot playing video games with a controller, digital illustration, fun, no real humans",
        "magical game world with power-ups and coins floating, digital art, vibrant",
    ],
    "vlogs": [
        "cute cartoon camera taking photos of a beautiful sunset, digital illustration, warm colors, no real humans",
        "animated travel postcard with famous landmarks as cartoons, digital art, colorful",
        "cute cartoon diary with stickers and drawings, digital illustration, cozy, no real humans",
        "animated coffee cup with steam forming a heart, digital art, warm, cozy aesthetic",
        "cartoon backpack with travel items floating around, digital illustration, adventure, no real humans",
    ],
}

# Estilos negativos (o que NAO gerar)
NEGATIVE_PROMPT = "realistic human face, real person, photograph of person, nude, nsfw, ugly, deformed, blurry, bad quality, text, watermark, signature"


def _get_font(size):
    """Carrega fonte do sistema"""
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def _gerar_prompt_ia(ia_nome, caption, estilo):
    """Gera um prompt detalhado para geracao de imagem baseado no conteudo"""
    prompts = PROMPTS_ESTILO.get(estilo, PROMPTS_ESTILO["tecnologia"])
    base_prompt = random.choice(prompts)
    estilos_extras = [
        ", trending on artstation, high quality, 4k, detailed",
        ", beautiful digital art, detailed, 4k, masterpiece",
        ", vibrant colors, professional illustration, stunning",
        ", anime style, beautiful colors, detailed, high resolution",
        ", concept art, stunning visuals, colorful, masterpiece",
    ]
    return base_prompt + random.choice(estilos_extras)


# =====================================================
# POLLINATIONS FLUX - API gratuita de alta qualidade
# =====================================================
def _gerar_imagem_pollinations(prompt, width=1024, height=1024):
    """Gera imagem usando Pollinations FLUX (gratuito, alta qualidade)"""
    try:
        seed = random.randint(1, 999999)
        prompt_clean = prompt.replace('"', '').replace("'", "").replace("#", "").strip()
        prompt_encoded = urllib.parse.quote(prompt_clean)
        url = f"{POLLINATIONS_URL}/{prompt_encoded}?model=flux&width={width}&height={height}&seed={seed}&nologo=true&enhance=true"
        
        print(f"[IG] Gerando imagem Pollinations FLUX: {prompt_clean[:60]}...")
        response = httpx.get(url, timeout=90.0, follow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_size = len(response.content)
            # RATE LIMIT DETECTION: Pollinations rate limit images are ~1.4MB
            # Real FLUX images at 1024x1024 are typically 50-200KB
            if content_size > 500000:
                print(f"[IG] Pollinations RATE LIMIT detectado! ({content_size//1024}KB) - descartando")
                return None
            if "image" in content_type or content_size > 10000:
                img = Image.open(io.BytesIO(response.content))
                print(f"[IG] Pollinations OK! Imagem {img.size[0]}x{img.size[1]} ({content_size//1024}KB)")
                return img
            else:
                print(f"[IG] Pollinations retornou conteudo invalido: {content_type}")
                return None
        else:
            print(f"[IG] Pollinations erro HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[IG] Pollinations erro: {e}")
        return None


# =====================================================
# STABLE DIFFUSION LOCAL
# =====================================================
def _gerar_imagem_sd(prompt, width=512, height=512, steps=20):
    """Gera imagem usando Stable Diffusion local"""
    try:
        response = httpx.get(
            f"{SD_API_URL}/api/generate",
            params={"prompt": prompt, "steps": steps},
            timeout=120.0
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                filename = data.get("filename", "")
                if filename:
                    img_response = httpx.get(
                        f"{SD_API_URL}/images/{filename}",
                        timeout=30.0
                    )
                    if img_response.status_code == 200:
                        return img_response.content
        return None
    except Exception as e:
        print(f"[SD] Erro ao conectar: {e}")
        return None


def _sd_disponivel():
    """Verifica se Stable Diffusion esta disponivel"""
    try:
        r = httpx.get(f"{SD_API_URL}/", timeout=3.0)
        return r.status_code == 200
    except:
        return False


def _adicionar_overlay_instagram(img, ia_nome, caption, hashtags, filtro, tipo):
    """Adiciona overlay estilo Instagram sobre a imagem IA"""
    w, h = img.size
    img = img.convert('RGBA')
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Barra inferior com caption
    caption_top = int(h * 0.72)
    for y in range(caption_top - 40, h):
        alpha = min(180, int((y - (caption_top - 40)) / (h - caption_top + 40) * 180))
        draw.rectangle([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    font_nome = _get_font(28)
    font_caption = _get_font(20)
    font_hash = _get_font(16)
    font_badge = _get_font(16)

    # Nome da IA
    draw.text((20, caption_top + 5), ia_nome, font=font_nome, fill=(255, 255, 255, 255))

    # Caption
    words = caption[:150].split()
    lines, current = [], ""
    for word in words:
        if len(current + " " + word) <= 50:
            current += (" " + word if current else word)
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)

    y_pos = caption_top + 40
    for line in lines[:3]:
        draw.text((20, y_pos), line, font=font_caption, fill=(255, 255, 255, 210))
        y_pos += 26

    # Hashtags
    if hashtags:
        draw.text((20, y_pos + 5), hashtags[:70], font=font_hash, fill=(150, 200, 255, 180))

    # Badges
    tipo_labels = {"foto": "PHOTO", "carrossel": "CAROUSEL", "reel": "REEL", "story": "STORY", "igtv": "IGTV"}
    label = tipo_labels.get(tipo, "AI")
    draw.rounded_rectangle([w - 80, 12, w - 10, 38], radius=8, fill=(0, 0, 0, 140))
    draw.text((w - 72, 15), label, font=font_badge, fill=(255, 255, 255, 220))

    # Filtro badge
    if filtro:
        draw.rounded_rectangle([10, 12, 10 + len(filtro) * 9 + 16, 38], radius=8, fill=(0, 0, 0, 140))
        draw.text((18, 15), filtro, font=font_badge, fill=(255, 255, 255, 200))

    # AI Generated badge
    draw.rounded_rectangle([w - 140, h - 30, w - 10, h - 8], radius=6, fill=(0, 0, 0, 100))
    font_ai = _get_font(12)
    draw.text((w - 132, h - 27), "AI Generated", font=font_ai, fill=(255, 255, 255, 150))

    img = Image.alpha_composite(img, overlay)
    return img


def _aplicar_filtro(img, filtro):
    """Aplica filtro Instagram"""
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    filtros = {
        "clarendon": {"contrast": 1.3, "brightness": 1.1, "color": 1.1},
        "gingham": {"contrast": 0.9, "brightness": 1.05, "color": 0.7},
        "moon": {"contrast": 1.1, "brightness": 1.1, "color": 0.2},
        "lark": {"contrast": 1.0, "brightness": 1.2, "color": 0.8},
        "reyes": {"contrast": 0.9, "brightness": 1.15, "color": 0.85},
        "juno": {"contrast": 1.2, "brightness": 1.0, "color": 1.15},
        "slumber": {"contrast": 0.85, "brightness": 0.9, "color": 0.6},
        "crema": {"contrast": 1.0, "brightness": 1.05, "color": 0.9},
        "ludwig": {"contrast": 1.15, "brightness": 1.0, "color": 1.0},
        "aden": {"contrast": 0.95, "brightness": 1.1, "color": 0.85},
    }
    config = filtros.get(filtro, {})
    if config.get("contrast", 1.0) != 1.0:
        img = ImageEnhance.Contrast(img).enhance(config["contrast"])
    if config.get("brightness", 1.0) != 1.0:
        img = ImageEnhance.Brightness(img).enhance(config["brightness"])
    if config.get("color", 1.0) != 1.0:
        img = ImageEnhance.Color(img).enhance(config["color"])
    return img


# =====================================================
# FALLBACK PIL (ultimo recurso)
# =====================================================
IA_CORES = {
    "🦙": {"c1": (255, 107, 107), "c2": (254, 202, 87)},
    "✨": {"c1": (156, 39, 176), "c2": (255, 193, 7)},
    "💎": {"c1": (95, 39, 205), "c2": (72, 219, 251)},
    "🔬": {"c1": (0, 210, 211), "c2": (84, 160, 255)},
    "🐉": {"c1": (225, 112, 85), "c2": (214, 48, 49)},
    "🐣": {"c1": (255, 234, 167), "c2": (253, 203, 110)},
}

def _gerar_fallback_pil(ia_emoji, ia_nome, caption, tipo, filtro, hashtags, estilo):
    """Fallback: gera imagem com PIL (gradientes + padroes)"""
    if tipo == "story":
        w, h = 1080, 1920
    else:
        w, h = 1080, 1080

    cores = IA_CORES.get(ia_emoji, {"c1": (100, 100, 200), "c2": (200, 100, 100)})
    c1, c2 = cores["c1"], cores["c2"]

    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xv, yv = np.meshgrid(x, y)
    factor = (xv + yv) / 2
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for c in range(3):
        arr[:, :, c] = np.clip(c1[c] * (1 - factor) + c2[c] * factor, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, 'RGB')

    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for _ in range(12):
        cx = random.randint(-50, w + 50)
        cy = random.randint(-50, h + 50)
        radius = random.randint(20, 100)
        alpha = random.randint(15, 45)
        cor = random.choice([c1, c2, (255, 255, 255)])
        draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=cor + (alpha,))
    img = Image.alpha_composite(img.convert('RGBA'), overlay)

    img = _adicionar_overlay_instagram(img, ia_nome, caption, hashtags, filtro, tipo)
    img = img.convert('RGB')
    img = _aplicar_filtro(img, filtro)
    return img


# =====================================================
# FUNCAO DE GERACAO COM CASCATA DE QUALIDADE
# =====================================================
def _gerar_imagem_ia(ia_emoji, ia_nome, caption, estilo, width=1080, height=1080):
    """Tenta gerar imagem de qualidade: Pollinations > SD local > PIL fallback"""
    prompt = _gerar_prompt_ia(ia_nome, caption, estilo)
    
    # 1. Pollinations FLUX (gratuito, gera imagens)
    img = _gerar_imagem_pollinations(prompt, width=min(width, 1024), height=min(height, 1024))
    if img:
        return img.resize((width, height), Image.LANCZOS)
    
    # 2. Tentar Stable Diffusion local
    if _sd_disponivel():
        print(f"[IG] Tentando Stable Diffusion local...")
        img_data = _gerar_imagem_sd(prompt, 512, 512, steps=20)
        if img_data:
            img = Image.open(io.BytesIO(img_data))
            return img.resize((width, height), Image.LANCZOS)
    
    # 3. Fallback PIL (ultimo recurso)
    print(f"[IG] Usando fallback PIL para {ia_nome}")
    return None


# =====================================================
# FUNCOES PRINCIPAIS
# =====================================================
def gerar_foto_instagram(ia_emoji, ia_nome, caption, filtro, hashtags, estilo):
    """Gera foto - tenta Pollinations > SD > fallback PIL"""
    img = _gerar_imagem_ia(ia_emoji, ia_nome, caption, estilo, 1080, 1080)
    
    if img is None:
        img = _gerar_fallback_pil(ia_emoji, ia_nome, caption, "foto", filtro, hashtags, estilo)
    else:
        img = _adicionar_overlay_instagram(img.convert('RGBA'), ia_nome, caption, hashtags, filtro, "foto")
        img = img.convert('RGB')
        img = _aplicar_filtro(img, filtro)

    filename = f"foto_{ia_nome.lower()}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = os.path.join(MEDIA_DIR, "photos", filename)
    img.save(filepath, "JPEG", quality=90)
    print(f"[IG] Foto salva: {filename}")
    return filename, "photos"


def gerar_story_instagram(ia_emoji, ia_nome, caption, filtro, hashtags, estilo):
    """Gera story vertical"""
    # Gerar imagem quadrada e adaptar para vertical
    img = _gerar_imagem_ia(ia_emoji, ia_nome, caption, estilo, 1080, 1080)
    
    if img is None:
        img = _gerar_fallback_pil(ia_emoji, ia_nome, caption, "story", filtro, hashtags, estilo)
    else:
        # Criar canvas vertical com blur do fundo
        img_sq = img.resize((1080, 1080), Image.LANCZOS)
        canvas = img_sq.copy().resize((1080, 1920), Image.LANCZOS)
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=20))
        canvas = ImageEnhance.Brightness(canvas).enhance(0.4)
        canvas.paste(img_sq, (0, 420))
        img = canvas
        img = _adicionar_overlay_instagram(img.convert('RGBA'), ia_nome, caption, hashtags, filtro, "story")
        img = img.convert('RGB')
        img = _aplicar_filtro(img, filtro)

    filename = f"story_{ia_nome.lower()}_{uuid.uuid4().hex[:8]}.jpg"
    filepath = os.path.join(MEDIA_DIR, "stories", filename)
    img.save(filepath, "JPEG", quality=88)
    return filename, "stories"


def gerar_reel_video(ia_emoji, ia_nome, caption, filtro, hashtags, estilo):
    """Gera video reel com efeito Ken Burns sobre imagem IA"""
    try:
        import imageio

        # Gerar imagem base com IA
        base_img = _gerar_imagem_ia(ia_emoji, ia_nome, caption, estilo, 1200, 1200)
        
        if base_img is None:
            base_img = _gerar_fallback_pil(ia_emoji, ia_nome, caption, "reel", filtro, hashtags, estilo)
            base_img = base_img.convert('RGB').resize((1200, 1200), Image.LANCZOS)
        else:
            base_img = base_img.convert('RGB').resize((1200, 1200), Image.LANCZOS)

        # Criar video com efeito Ken Burns (zoom lento + pan)
        w_out, h_out = 540, 960
        fps = 12
        duracao = 4
        num_frames = fps * duracao

        filename = f"reel_{ia_nome.lower()}_{uuid.uuid4().hex[:8]}.mp4"
        filepath = os.path.join(MEDIA_DIR, "reels", filename)

        writer = imageio.get_writer(filepath, fps=fps, codec='libx264',
                                     output_params=['-pix_fmt', 'yuv420p', '-preset', 'ultrafast'])

        start_zoom = 1.0
        end_zoom = 1.3
        pan_x_start = random.randint(-50, 50)
        pan_y_start = random.randint(-50, 50)
        base_w, base_h = base_img.size

        for i in range(num_frames):
            progress = i / num_frames
            zoom = start_zoom + (end_zoom - start_zoom) * progress
            crop_w = int(base_w / zoom)
            crop_h = int(base_h / zoom)
            pan_x = int(pan_x_start * (1 - progress))
            pan_y = int(pan_y_start * (1 - progress))
            cx = base_w // 2 + pan_x
            cy = base_h // 2 + pan_y
            left = max(0, cx - crop_w // 2)
            top = max(0, cy - crop_h // 2)
            right = min(base_w, left + crop_w)
            bottom = min(base_h, top + crop_h)

            frame = base_img.crop((left, top, right, bottom))
            frame = frame.resize((w_out, h_out), Image.LANCZOS)

            if progress > 0.2:
                frame = frame.convert('RGBA')
                ov = Image.new('RGBA', (w_out, h_out), (0, 0, 0, 0))
                draw = ImageDraw.Draw(ov)

                bar_top = int(h_out * 0.75)
                for y in range(bar_top - 30, h_out):
                    alpha = min(160, int((y - (bar_top - 30)) / (h_out - bar_top + 30) * 160))
                    draw.rectangle([(0, y), (w_out, y)], fill=(0, 0, 0, alpha))

                font_n = _get_font(20)
                font_c = _get_font(14)
                draw.text((15, bar_top + 5), ia_nome, font=font_n, fill=(255, 255, 255, 255))

                visible_chars = int(len(caption[:80]) * min(1.0, (progress - 0.2) * 2))
                draw.text((15, bar_top + 30), caption[:visible_chars], font=font_c, fill=(255, 255, 255, 200))

                if hashtags and progress > 0.5:
                    draw.text((15, bar_top + 50), hashtags[:50], font=_get_font(12), fill=(150, 200, 255, 160))

                draw.rounded_rectangle([w_out - 65, 10, w_out - 8, 32], radius=6, fill=(255, 0, 80, 200))
                draw.text((w_out - 57, 13), "REEL", font=_get_font(12), fill=(255, 255, 255, 255))

                frame = Image.alpha_composite(frame, ov)
                frame = frame.convert('RGB')

            writer.append_data(np.array(frame))

        writer.close()
        print(f"[IG] Reel gerado: {filename}")
        return filename, "reels"

    except Exception as e:
        print(f"[IG] Erro ao gerar reel: {e}")
        return gerar_foto_instagram(ia_emoji, ia_nome, f"[REEL] {caption}", filtro, hashtags, estilo)


def gerar_media_instagram(ia_emoji, ia_nome, caption, tipo, filtro, hashtags, estilo):
    """Funcao principal - gera midia baseado no tipo"""
    try:
        if tipo == "reel":
            return gerar_reel_video(ia_emoji, ia_nome, caption, filtro, hashtags, estilo)
        elif tipo == "story":
            return gerar_story_instagram(ia_emoji, ia_nome, caption, filtro, hashtags, estilo)
        else:
            return gerar_foto_instagram(ia_emoji, ia_nome, caption, filtro, hashtags, estilo)
    except Exception as e:
        print(f"[IG] Erro geral midia {tipo}: {e}")
        return None, None


def limpar_media_antiga(max_por_pasta=150):
    """Remove arquivos antigos"""
    for subdir in ["photos", "stories", "reels"]:
        dirpath = os.path.join(MEDIA_DIR, subdir)
        if not os.path.exists(dirpath):
            continue
        files = sorted(
            [os.path.join(dirpath, f) for f in os.listdir(dirpath) if not f.startswith('.')],
            key=lambda f: os.path.getmtime(f) if os.path.exists(f) else 0
        )
        while len(files) > max_por_pasta:
            try:
                os.remove(files.pop(0))
            except:
                files.pop(0)
