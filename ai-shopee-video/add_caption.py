#!/usr/bin/env python3
"""
Adiciona legendas/captions nos vídeos do Telegram antes de postar no Shopee Video.
Usa moviepy + PIL para overlay de texto (ffmpeg sem drawtext neste sistema).
"""
import json, os, sys, hashlib, random, re
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

try:
    sys.stdout.reconfigure(line_buffering=True)
except:
    pass

DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIR)
PENDING_FILE = os.path.join(DIR, "telegram_pending.json")
FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
PROCESSED_DIR = os.path.join(DIR, "static", "videos", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Emojis e textos para variar as legendas
SHOPEE_CTAS = [
    "CORRE PRA SHOPEE!", "LINK NA BIO!", "COMPRE AGORA!",
    "OFERTA IMPERDÍVEL!", "PREÇO INCRÍVEL!", "ACHADO DA SHOPEE!",
    "APROVEITE!", "NÃO PERCA!", "TÁ BARATO DEMAIS!",
]

HASHTAGS_SHOPEE = "#shopee #achadosshopee #shopeehaul #shopeefinds #promoção #oferta"


def create_caption_overlay(width, height, product_name, shopee_link="", position="bottom"):
    """Cria imagem PNG transparente com legenda para overlay no vídeo"""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font_big = ImageFont.truetype(FONT_PATH, 42)
        font_med = ImageFont.truetype(FONT_PATH, 32)
        font_small = ImageFont.truetype(FONT_PATH, 24)
    except:
        font_big = font_med = font_small = ImageFont.load_default()

    # Barra no topo (CTA)
    cta = random.choice(SHOPEE_CTAS)
    bar_h_top = 70
    draw.rectangle([(0, 0), (width, bar_h_top)], fill=(238, 77, 45, 220))
    bbox = draw.textbbox((0, 0), cta, font=font_big)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, 12), cta, fill=(255, 255, 255), font=font_big)

    # Barra no fundo (nome do produto + link)
    bar_h = 140
    bar_y = height - bar_h
    draw.rectangle([(0, bar_y), (width, height)], fill=(0, 0, 0, 200))

    # Nome do produto
    name = product_name[:60]
    words = name.split()
    lines, current = [], ""
    for w in words:
        test = f"{current} {w}".strip() if current else w
        bbox = draw.textbbox((0, 0), test, font=font_med)
        if bbox[2] - bbox[0] > width - 40 and current:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    y = bar_y + 10
    for line in lines[:2]:
        bbox = draw.textbbox((0, 0), line, font=font_med)
        tw = bbox[2] - bbox[0]
        x = (width - tw) // 2
        draw.text((x, y), line, fill=(255, 255, 255), font=font_med)
        y += 38

    # Shopee icon + link
    if shopee_link:
        link_text = f"🛒 Shopee • Link na bio"
        bbox = draw.textbbox((0, 0), link_text, font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, y + 5), link_text, fill=(255, 193, 7), font=font_small)

    return overlay


def add_caption_to_video(video_path, product_name, shopee_link="", output_path=None):
    """Adiciona legenda no vídeo usando moviepy"""
    if not output_path:
        base = os.path.basename(video_path).replace(".mp4", "")
        output_path = os.path.join(PROCESSED_DIR, f"{base}_caption.mp4")

    if os.path.exists(output_path):
        print(f"  ⏭️ Já processado: {os.path.basename(output_path)}")
        return output_path

    try:
        clip = VideoFileClip(video_path)
        w, h = clip.size
        duration = clip.duration

        # Limitar duração a 60s para Shopee Video
        if duration > 60:
            clip = clip.subclip(0, 60)
            duration = 60

        # Criar overlay PNG
        overlay_img = create_caption_overlay(w, h, product_name, shopee_link)
        overlay_path = output_path.replace(".mp4", "_overlay.png")
        overlay_img.save(overlay_path)

        # Criar clip do overlay (moviepy 1.x API)
        overlay_clip = (ImageClip(overlay_path, duration=duration)
                       .set_position((0, 0)))

        # Compor vídeo + overlay
        final = CompositeVideoClip([clip, overlay_clip])

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=clip.fps or 30,
            preset="fast",
            logger=None,
        )

        # Cleanup
        clip.close()
        final.close()
        if os.path.exists(overlay_path):
            os.remove(overlay_path)

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✅ {os.path.basename(output_path)} ({size_mb:.1f}MB)")
        return output_path

    except Exception as e:
        print(f"  ❌ Erro: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None


def process_all_pending():
    """Processa todos os vídeos pendentes: adiciona legenda"""
    pending = json.load(open(PENDING_FILE))
    not_posted = [p for p in pending if not p.get("posted_to_shopee")]

    print(f"\n🎬 Processando {len(not_posted)} vídeos com legendas...\n")

    processed = 0
    seen_links = set()

    for i, entry in enumerate(not_posted):
        video_path = entry.get("video_path", "")
        if not os.path.exists(video_path):
            continue

        # Deduplicar por link
        link = entry.get("shopee_link", "")
        if link and link in seen_links:
            print(f"  ⏭️ Duplicata: {link[:40]}")
            continue
        if link:
            seen_links.add(link)

        # Extrair nome do produto do texto
        text = entry.get("text", "")
        # Limpar: pegar primeira linha antes do link
        name = text.split("https")[0].split("http")[0].strip()
        name = re.sub(r'Vídeo \d+:', '', name).strip()
        name = name.split("\n")[0][:60].strip()
        if not name or len(name) < 3:
            name = "Achado Incrível da Shopee"

        print(f"[{i+1}/{len(not_posted)}] {name[:40]}")
        result = add_caption_to_video(video_path, name, link)

        if result:
            # Atualizar path no pending para o vídeo com legenda
            entry["video_path_original"] = video_path
            entry["video_path"] = result
            processed += 1

    # Salvar pendentes atualizados
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)

    print(f"\n🏁 {processed} vídeos processados com legendas!")
    return processed


if __name__ == "__main__":
    process_all_pending()
