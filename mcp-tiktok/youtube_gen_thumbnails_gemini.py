#!/usr/bin/env python3
"""
Gera thumbnails com Google Imagen 4 para cada vídeo do YouTube
e seta via YouTube Data API v3.
"""

import os
import sys
import time
import json
import pickle
import base64
import requests
from PIL import Image
from io import BytesIO
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

GEMINI_KEY = "AIzaSyBvBcFiZ0_jODcGwnV5bYXaYiv28LdTkl0"
CLIENT_SECRET = "/Users/maiconjonathamartinsdasilva/Downloads/client_secret_633536180211-i7lah4bvp9t3m3hpe8k4ub8vo56afeop.apps.googleusercontent.com.json"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "youtube_token.pickle")
THUMB_DIR = os.path.join(os.path.dirname(__file__), "thumbnails_yt")
os.makedirs(THUMB_DIR, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]

# Prompts para cada vídeo
VIDEO_PROMPTS = {
    "NY87gptbJVE": None,  # Já tem thumbnail - SKIP
    "CmpnUanc5V0": "Futuristic scene of 6 AI robots sitting around a glowing holographic table, each robot has a different color aura, they are chatting on floating social media screens, cyberpunk neon blue and purple environment, digital neural network connections in the background, ultra detailed 4k digital art",
    "YJKupUePTjs": "Majestic golden sunrise over beautiful mountains, divine rays of light breaking through clouds, silhouette of a cross on hilltop, inspirational christian atmosphere, warm golden and orange tones, photorealistic, cinematic wide shot, 4k",
    "rQ6BbIgUY84": "Beautiful woman in white dress praying with hands together, golden divine light rays from above illuminating her, peaceful flower garden background, spiritual and serene atmosphere, soft warm lighting, photorealistic portrait, cinematic, 4k",
    "yIqiwMBYdq8": "Breathtaking night sky full of bright stars and milky way, beautiful crescent moon reflecting on calm crystal lake, mountains silhouette, peaceful and serene good night scene, deep blue and purple tones, photorealistic, 4k",
    "q2TKEyoUp1E": "Woman kneeling in prayer inside magnificent cathedral, colorful stained glass windows casting rainbow light, golden sunbeams, divine peaceful spiritual atmosphere, photorealistic, cinematic composition, 4k",
    "MxxOnxzvl08": "Open holy bible on wooden table with brilliant golden light emanating from the pages, divine rays spreading upward, ornate cross in soft focus background, warm golden atmosphere, photorealistic still life, 4k",
    "yED9Qz1G3mU": "Person standing on dramatic cliff edge looking at sky, golden light breaking through dark storm clouds, epic divine revelation moment, silhouette, cinematic wide shot, photorealistic landscape, 4k",
    "wYg8VWkWxJg": "Person peacefully resting under a beautiful blooming tree in lush green meadow, golden hour warm sunlight, butterflies and flowers, paradise-like scenery, serene and calm atmosphere, photorealistic, 4k",
    "zM4EgCmhvIs": "Two hands cupping a glowing radiant heart made of golden light, divine rays emanating upward, bokeh light background, spiritual love and transformation, warm colors, photorealistic, cinematic close-up, 4k",
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

def generate_image_imagen(prompt, output_path):
    """Gera imagem via Google Imagen 4"""
    print(f"  [*] Gerando com Imagen 4...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={GEMINI_KEY}"
    
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9",
            "personGeneration": "dont_allow",
        }
    }
    
    resp = requests.post(url, json=payload, timeout=120)
    
    if resp.status_code != 200:
        print(f"  [!] Imagen erro: {resp.status_code}")
        print(f"  [!] {resp.text[:300]}")
        return False
    
    data = resp.json()
    predictions = data.get("predictions", [])
    
    if not predictions:
        print("  [!] Nenhuma imagem gerada!")
        return False
    
    # Decodificar base64
    img_b64 = predictions[0].get("bytesBase64Encoded")
    if not img_b64:
        print("  [!] Sem dados de imagem!")
        return False
    
    img_bytes = base64.b64decode(img_b64)
    img = Image.open(BytesIO(img_bytes))
    
    # Redimensionar para 1280x720 se necessário
    if img.size != (1280, 720):
        img = img.resize((1280, 720), Image.LANCZOS)
    
    img.save(output_path, "JPEG", quality=92)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  [+] Imagem salva: {size_kb:.0f} KB")
    return True

def generate_image_gemini(prompt, output_path):
    """Fallback: Gemini 2.5 Flash Image (Nano Banana)"""
    print(f"  [*] Tentando Gemini Flash Image...")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": f"Generate an image: {prompt}"}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }
    
    resp = requests.post(url, json=payload, timeout=120)
    
    if resp.status_code != 200:
        print(f"  [!] Gemini erro: {resp.status_code} {resp.text[:200]}")
        return False
    
    data = resp.json()
    candidates = data.get("candidates", [])
    
    for candidate in candidates:
        for part in candidate.get("content", {}).get("parts", []):
            if "inlineData" in part:
                img_b64 = part["inlineData"]["data"]
                img_bytes = base64.b64decode(img_b64)
                img = Image.open(BytesIO(img_bytes))
                if img.size != (1280, 720):
                    img = img.resize((1280, 720), Image.LANCZOS)
                img.save(output_path, "JPEG", quality=92)
                size_kb = os.path.getsize(output_path) / 1024
                print(f"  [+] Imagem salva: {size_kb:.0f} KB")
                return True
    
    print("  [!] Nenhuma imagem nos resultados")
    return False

def main():
    youtube = get_youtube()
    
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
    
    print(f"[*] {len(videos)} videos\n")
    
    success = 0
    for v in videos:
        vid_id = v["id"]
        title = v["title"]
        
        print(f"\n{'='*60}")
        print(f"[*] {title[:60]}")
        print(f"[*] ID: {vid_id}")
        
        prompt = VIDEO_PROMPTS.get(vid_id)
        if prompt is None:
            print("[*] SKIP")
            continue
        
        thumb_path = os.path.join(THUMB_DIR, f"{vid_id}_gemini.jpg")
        
        # Tentar Imagen 4 primeiro, depois Gemini Flash Image
        ok = generate_image_imagen(prompt, thumb_path)
        if not ok:
            ok = generate_image_gemini(prompt, thumb_path)
        
        if not ok:
            print("  [!] Todas tentativas falharam!")
            continue
        
        # Setar thumbnail no YouTube
        try:
            media = MediaFileUpload(thumb_path, mimetype="image/jpeg", resumable=True)
            youtube.thumbnails().set(videoId=vid_id, media_body=media).execute()
            print(f"  [+] THUMBNAIL SETADA NO YOUTUBE!")
            success += 1
        except Exception as e:
            print(f"  [!] Erro YouTube: {str(e)[:200]}")
        
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"[+] Thumbnails Google atualizadas: {success} videos!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
