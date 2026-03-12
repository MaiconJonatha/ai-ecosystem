#!/usr/bin/env python3
"""
Gera thumbnails únicas com IA (Stable Horde) para cada vídeo do YouTube
e seta via YouTube Data API v3.
"""

import os
import sys
import time
import json
import pickle
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_SECRET = "/Users/maiconjonathamartinsdasilva/Downloads/client_secret_633536180211-i7lah4bvp9t3m3hpe8k4ub8vo56afeop.apps.googleusercontent.com.json"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "youtube_token.pickle")
THUMB_DIR = os.path.join(os.path.dirname(__file__), "thumbnails_yt")
os.makedirs(THUMB_DIR, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]

HORDE_API = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"

# Prompts específicos para cada vídeo baseado no título
VIDEO_PROMPTS = {
    "NY87gptbJVE": None,  # Já tem thumbnail do Jesus - SKIP
    "CmpnUanc5V0": "futuristic AI neural network visualization, 6 glowing AI robots sitting around a table chatting on social media, holographic screens, cyberpunk neon blue purple, digital art, 4k, ultra detailed",
    "YJKupUePTjs": "beautiful golden sunrise over mountains, divine light rays from heaven, cross silhouette, inspirational christian message, warm golden tones, oil painting style, 4k",
    "rQ6BbIgUY84": "beautiful woman praying with hands together, divine golden light from above, peaceful garden, white dress, spiritual atmosphere, renaissance painting style, warm colors, 4k",
    "yIqiwMBYdq8": "peaceful night sky full of stars, moonlight over calm lake, reflection, good night blessing, serene atmosphere, deep blue and purple tones, digital painting, 4k",
    "q2TKEyoUp1E": "woman kneeling in prayer in a beautiful cathedral, stained glass windows with colorful light, divine atmosphere, spiritual peace, renaissance art style, 4k",
    "MxxOnxzvl08": "open glowing bible with golden light emanating from pages, divine rays, cross in background, spiritual message from God, warm golden atmosphere, digital art, 4k",
    "yED9Qz1G3mU": "person standing on cliff edge looking at dramatic sky with golden light breaking through dark clouds, spiritual revelation, divine message, cinematic, 4k",
    "wYg8VWkWxJg": "peaceful person resting under a beautiful tree in green meadow, golden hour sunlight, butterflies, God says rest, serene paradise, oil painting style, 4k",
    "zM4EgCmhvIs": "hands holding a glowing heart with divine light, spiritual transformation, golden rays from heaven, emotional powerful moment, renaissance style, warm colors, 4k",
}

def get_youtube():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=8888)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)

def generate_image(prompt, output_path):
    """Gera imagem via Stable Horde"""
    print(f"  [*] Gerando imagem...")
    
    # Request generation
    payload = {
        "prompt": prompt + ", masterpiece, best quality, highly detailed",
        "params": {
            "width": 1280,
            "height": 768,
            "steps": 30,
            "cfg_scale": 7.5,
            "sampler_name": "k_euler_a",
        },
        "nsfw": False,
        "models": ["AlbedoBase XL (SDXL)"],
        "r2": True,
    }
    
    time.sleep(2)  # Rate limit
    resp = requests.post(f"{HORDE_API}/generate/async",
                        json=payload,
                        headers={"apikey": HORDE_KEY})
    
    if resp.status_code != 202:
        print(f"  [!] Erro ao iniciar geração: {resp.status_code} {resp.text[:200]}")
        return False
    
    gen_id = resp.json().get("id")
    print(f"  [*] Job ID: {gen_id}")
    
    # Poll for completion
    for i in range(120):
        time.sleep(5)
        check = requests.get(f"{HORDE_API}/generate/check/{gen_id}")
        data = check.json()
        
        if data.get("done"):
            break
        
        if i % 4 == 0:
            wait = data.get("wait_time", "?")
            pos = data.get("queue_position", "?")
            print(f"  [*] Aguardando... pos={pos} wait={wait}s")
    
    # Get result
    result = requests.get(f"{HORDE_API}/generate/status/{gen_id}")
    gens = result.json().get("generations", [])
    
    if not gens:
        print("  [!] Nenhuma imagem gerada!")
        return False
    
    img_url = gens[0].get("img")
    if not img_url:
        print("  [!] URL da imagem vazia!")
        return False
    
    # Download
    img_data = requests.get(img_url)
    img = Image.open(BytesIO(img_data.content))
    
    # Garantir 1280x720
    if img.size != (1280, 720):
        img = img.resize((1280, 720), Image.LANCZOS)
    
    img.save(output_path, "JPEG", quality=92)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  [+] Imagem salva: {output_path} ({size_kb:.0f} KB)")
    return True

def main():
    youtube = get_youtube()
    
    # Listar vídeos
    print("[*] Buscando videos do canal...")
    channels = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads_playlist = channels["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    response = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist,
        maxResults=10
    ).execute()
    
    videos = []
    for item in response.get("items", []):
        vid_id = item["contentDetails"]["videoId"]
        title = item["snippet"]["title"]
        videos.append({"id": vid_id, "title": title})
    
    print(f"[*] {len(videos)} videos encontrados\n")
    
    success = 0
    for v in videos:
        vid_id = v["id"]
        title = v["title"]
        
        print(f"\n{'='*60}")
        print(f"[*] {title[:60]}")
        print(f"[*] ID: {vid_id}")
        
        prompt = VIDEO_PROMPTS.get(vid_id)
        if prompt is None:
            print(f"[*] SKIP - já tem thumbnail custom")
            continue
        
        thumb_path = os.path.join(THUMB_DIR, f"{vid_id}.jpg")
        
        # Gerar imagem
        if os.path.exists(thumb_path):
            print(f"  [*] Usando imagem existente: {thumb_path}")
        else:
            ok = generate_image(prompt, thumb_path)
            if not ok:
                print(f"  [!] Falha na geração, pulando...")
                continue
        
        # Setar thumbnail
        try:
            media = MediaFileUpload(thumb_path, mimetype="image/jpeg", resumable=True)
            result = youtube.thumbnails().set(videoId=vid_id, media_body=media).execute()
            print(f"  [+] THUMBNAIL SETADA!")
            success += 1
        except Exception as e:
            print(f"  [!] Erro ao setar: {str(e)[:200]}")
    
    print(f"\n{'='*60}")
    print(f"[+] Thumbnails atualizadas: {success} videos!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
