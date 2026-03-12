#!/usr/bin/env python3
"""
Automação Instagram - Posts + Stories de Jesus
Posta nos melhores horários para engajamento no Instagram Brasil
"""

import random
import time
import os
import requests
import io
import logging
import glob
import schedule
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
from instagrapi.types import StoryHashtag, StoryLink

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), "instagram_auto.log"))
    ]
)
log = logging.getLogger("IG-Auto")

INSTAGRAM_USER = "maiconbatera1"
INSTAGRAM_PASS = "Maicon26."
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, "instagram_session.json")
IMAGES_DIR = os.path.join(BASE_DIR, "jesus_images")
OLLAMA_URL = "http://localhost:11434/api/generate"

# Horários otimizados Instagram Brasil
HORARIOS_FEED = [
    "06:30", "08:45",
    "11:30", "12:15",
    "14:00",
    "17:30", "18:15",
    "20:00", "21:30",
]

# Stories mais frequentes (desaparecem em 24h)
HORARIOS_STORIES = [
    "07:00", "07:45",
    "09:30", "10:15",
    "12:45", "13:30",
    "15:00", "16:00",
    "19:00", "19:45",
    "21:00", "22:00", "22:30",
]

TEMAS_JESUS = [
    "o amor incondicional de Jesus Cristo",
    "a misericórdia infinita de Deus",
    "fé e esperança em Jesus nos momentos difíceis",
    "o poder transformador da oração",
    "a graça de Deus que nos salva",
    "Jesus é o caminho a verdade e a vida",
    "o sacrifício de Jesus na cruz por nossos pecados",
    "a gloriosa ressurreição de Cristo",
    "o Salmo 23 - o Senhor é meu pastor",
    "perdão e redenção através do sangue de Cristo",
    "a paz que só Jesus pode dar ao coração",
    "confiança em Deus mesmo nas tempestades",
    "o Espírito Santo que nos guia e consola",
    "amar ao próximo como Jesus nos ensinou",
    "gratidão a Deus por todas as bênçãos",
    "as promessas de Deus para nossa vida",
    "a fidelidade de Deus em todas as gerações",
    "o poder do nome de Jesus",
    "a cura que vem de Deus",
    "a Bíblia Sagrada - lâmpada para nossos pés",
    "a segunda vinda de Jesus Cristo",
    "as parábolas de Jesus e seus ensinamentos",
    "os milagres de Jesus que fortalecem nossa fé",
    "a oração do Pai Nosso",
    "o fruto do Espírito Santo em nossas vidas",
]

VERSICULOS = [
    ("Eu sou o caminho, a verdade e a vida.", "João 14:6"),
    ("Porque Deus amou o mundo de tal maneira que deu o seu Filho unigênito.", "João 3:16"),
    ("O Senhor é o meu pastor e nada me faltará.", "Salmos 23:1"),
    ("Tudo posso naquele que me fortalece.", "Filipenses 4:13"),
    ("Entrega o teu caminho ao Senhor; confia nele.", "Salmos 37:5"),
    ("Não temas, porque eu sou contigo.", "Isaías 41:10"),
    ("Vinde a mim, todos os que estais cansados, e eu vos aliviarei.", "Mateus 11:28"),
    ("Os que esperam no Senhor renovarão as suas forças.", "Isaías 40:31"),
    ("O Senhor é a minha luz e a minha salvação.", "Salmos 27:1"),
    ("Deus é o nosso refúgio e fortaleza.", "Salmos 46:1"),
    ("Porque eu sei os planos que tenho para vocês, diz o Senhor.", "Jeremias 29:11"),
    ("O amor é paciente, o amor é bondoso.", "1 Coríntios 13:4"),
    ("Busquem primeiro o Reino de Deus e a sua justiça.", "Mateus 6:33"),
    ("Sejam fortes e corajosos. Não tenham medo.", "Josué 1:9"),
    ("A alegria do Senhor é a nossa força.", "Neemias 8:10"),
]

usadas_feed = []
usadas_story = []
cl = None
feed_count = 0
story_count = 0


def login_instagram():
    global cl
    client = Client()
    client.delay_range = [2, 5]
    if os.path.exists(SESSION_FILE):
        client.load_settings(SESSION_FILE)
        try:
            client.get_timeline_feed()
            log.info(f"Sessão ativa: {client.user_id}")
            cl = client
            return
        except:
            log.info("Sessão expirada, relogando...")
    client.set_locale("pt_BR")
    client.set_country_code(55)
    client.set_timezone_offset(-3 * 3600)
    client.login(INSTAGRAM_USER, INSTAGRAM_PASS)
    client.dump_settings(SESSION_FILE)
    log.info(f"Login OK: {client.username}")
    cl = client


def escolher_imagem(usadas_list):
    imagens = glob.glob(os.path.join(IMAGES_DIR, "jesus_*.jpg"))
    if not imagens:
        return None
    disponiveis = [i for i in imagens if i not in usadas_list]
    if not disponiveis:
        usadas_list.clear()
        disponiveis = imagens
    img = random.choice(disponiveis)
    usadas_list.append(img)
    return img


def gerar_caption(tema):
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "llama3.2:3b",
            "prompt": f"Escreva uma legenda curta e inspiradora para Instagram sobre: {tema}. Inclua 1 versículo bíblico, emojis religiosos e 8 hashtags em português. Seja tocante e autêntico.",
            "stream": False
        }, timeout=60)
        if r.status_code == 200:
            text = r.json().get("response", "").strip()
            if len(text) > 50:
                return text
    except:
        pass

    v, ref = random.choice(VERSICULOS)
    emoji = random.choice(["✝️", "🙏", "📖", "🕊️", "❤️"])
    return f"""{emoji} {tema.capitalize()}.

"{v}" ({ref})

Que essa palavra toque seu coração! 🙏❤️✝️

#Jesus #Cristo #Deus #Fe #Biblia #Evangelico #Gospel #DeusEFiel #JesusCristo #Oracao"""


def criar_imagem_story(img_path):
    """Cria imagem 1080x1920 (9:16) para Story com versículo sobreposto"""
    img = Image.open(img_path).convert("RGB")
    
    # Redimensionar para caber no story (1080x1920)
    # Colocar a imagem no centro com fundo gradiente
    story = Image.new("RGB", (1080, 1920), (20, 15, 30))
    
    # Redimensionar imagem mantendo proporção
    img_w, img_h = img.size
    ratio = min(1080 / img_w, 1400 / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Centralizar verticalmente (um pouco pra cima)
    x = (1080 - new_w) // 2
    y = max(100, (1920 - new_h) // 2 - 100)
    story.paste(img_resized, (x, y))
    
    # Adicionar versículo embaixo
    draw = ImageDraw.Draw(story)
    v, ref = random.choice(VERSICULOS)
    
    # Texto do versículo
    text_y = y + new_h + 40
    if text_y > 1700:
        text_y = 1700
    
    # Usar fonte padrão (sem drawtext issues)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_ref = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except:
        font = ImageFont.load_default()
        font_ref = font
    
    # Quebrar texto em linhas
    words = v.split()
    lines = []
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > 980:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    
    # Desenhar texto com sombra
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = (1080 - tw) // 2
        ty = text_y + i * 50
        # Sombra
        draw.text((tx + 2, ty + 2), line, fill=(0, 0, 0), font=font)
        draw.text((tx, ty), line, fill=(255, 255, 255), font=font)
    
    # Referência
    ref_y = text_y + len(lines) * 50 + 20
    bbox = draw.textbbox((0, 0), ref, font=font_ref)
    tw = bbox[2] - bbox[0]
    draw.text(((1080 - tw) // 2 + 1, ref_y + 1), ref, fill=(0, 0, 0), font=font_ref)
    draw.text(((1080 - tw) // 2, ref_y), ref, fill=(220, 200, 150), font=font_ref)
    
    # Salvar
    story_path = img_path.replace(".jpg", "_story.jpg")
    story_path = f"/tmp/ig_story_{random.randint(1000,9999)}.jpg"
    story.save(story_path, "JPEG", quality=95)
    return story_path


def postar_feed():
    global cl, feed_count
    feed_count += 1
    tema = random.choice(TEMAS_JESUS)
    hora = datetime.now().strftime("%H:%M")
    
    log.info(f"\n{'='*40}")
    log.info(f"📸 FEED #{feed_count} - {hora}")
    log.info(f"Tema: {tema}")
    
    caption = gerar_caption(tema)
    img_path = escolher_imagem(usadas_feed)
    if not img_path:
        log.error("Sem imagem!")
        return
    
    log.info(f"Imagem: {os.path.basename(img_path)}")
    
    for attempt in range(3):
        try:
            if cl is None:
                login_instagram()
            media = cl.photo_upload(img_path, caption)
            log.info(f"POSTADO FEED! https://www.instagram.com/p/{media.code}/")
            return
        except Exception as e:
            log.warning(f"Erro feed (tentativa {attempt+1}/3): {e}")
            time.sleep(15)
            try:
                login_instagram()
            except:
                pass
    log.error(f"FALHA FEED apos 3 tentativas")


def postar_story():
    global cl, story_count
    story_count += 1
    hora = datetime.now().strftime("%H:%M")
    
    log.info(f"\n{'='*40}")
    log.info(f"📱 STORY #{story_count} - {hora}")
    
    img_path = escolher_imagem(usadas_story)
    if not img_path:
        log.error("Sem imagem!")
        return
    
    log.info(f"Imagem: {os.path.basename(img_path)}")
    
    # Criar imagem 9:16 com versículo
    try:
        story_path = criar_imagem_story(img_path)
        log.info(f"Story criado: {story_path}")
    except Exception as e:
        log.warning(f"Erro ao criar story image: {e}, usando original")
        story_path = img_path
    
    for attempt in range(3):
        try:
            if cl is None:
                login_instagram()
            
            # Postar story com hashtag
            try:
                hashtags = [StoryHashtag(
                    x=0.5, y=0.9, width=0.3, height=0.05,
                    rotation=0.0,
                    hashtag=cl.hashtag_info("Jesus")
                )]
                media = cl.photo_upload_to_story(story_path, hashtags=hashtags)
            except:
                media = cl.photo_upload_to_story(story_path)
            
            log.info(f"POSTADO STORY! ID: {media.id}")
            break
        except Exception as e:
            log.warning(f"Erro story (tentativa {attempt+1}/3): {e}")
            time.sleep(15)
            try:
                login_instagram()
            except:
                pass
    else:
        log.error(f"FALHA STORY apos 3 tentativas")
    
    # Limpar temp
    if story_path.startswith("/tmp/"):
        try:
            os.remove(story_path)
        except:
            pass


def main():
    imgs = glob.glob(os.path.join(IMAGES_DIR, "jesus_*.jpg"))
    
    log.info("=" * 50)
    log.info("INSTAGRAM AUTO - Feed + Stories de Jesus")
    log.info(f"Galeria: {len(imgs)} pinturas de Jesus")
    log.info(f"")
    log.info(f"📸 FEED - {len(HORARIOS_FEED)} posts/dia:")
    for h in HORARIOS_FEED:
        log.info(f"   {h}")
    log.info(f"")
    log.info(f"📱 STORIES - {len(HORARIOS_STORIES)} stories/dia:")
    for h in HORARIOS_STORIES:
        log.info(f"   {h}")
    log.info(f"")
    log.info(f"TOTAL: {len(HORARIOS_FEED) + len(HORARIOS_STORIES)} publicações/dia")
    log.info("=" * 50)
    
    if not imgs:
        log.error("SEM IMAGENS!")
        return
    
    login_instagram()
    
    # Agendar FEED
    for h in HORARIOS_FEED:
        schedule.every().day.at(h).do(postar_feed)
    
    # Agendar STORIES
    for h in HORARIOS_STORIES:
        schedule.every().day.at(h).do(postar_story)
    
    # Postar um de cada agora como teste
    log.info("Teste inicial: 1 feed + 1 story...")
    postar_feed()
    time.sleep(10)
    postar_story()
    
    log.info("\n🕐 Aguardando próximos horários...")
    while True:
        schedule.run_pending()
        time.sleep(15)


if __name__ == "__main__":
    main()
