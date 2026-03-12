#!/usr/bin/env python3
"""
Automatiza geração de imagens via Gemini no Chrome + screenshot crop.
Depois seta thumbnails via YouTube Data API.
"""

import os
import sys
import time
import subprocess
import pickle
from PIL import Image
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_SECRET = "/Users/maiconjonathamartinsdasilva/Downloads/client_secret_633536180211-i7lah4bvp9t3m3hpe8k4ub8vo56afeop.apps.googleusercontent.com.json"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "youtube_token.pickle")
THUMB_DIR = os.path.join(os.path.dirname(__file__), "thumbnails_yt")
os.makedirs(THUMB_DIR, exist_ok=True)

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"]

VIDEO_PROMPTS = {
    "CmpnUanc5V0": "6 colorful AI robots sitting around a glowing holographic table chatting on floating social media screens, cyberpunk neon blue and purple city, neural network connections, ultra detailed 4k",
    "YJKupUePTjs": "Majestic golden sunrise over mountains, divine rays of light from heaven, cross silhouette on hilltop, warm golden tones, photorealistic cinematic, 4k",
    "rQ6BbIgUY84": "Beautiful woman in white dress praying with hands together, golden divine light from above, flower garden, spiritual atmosphere, photorealistic, 4k",
    "yIqiwMBYdq8": "Breathtaking night sky with milky way and stars, crescent moon reflecting on calm crystal lake, peaceful serene scene, deep blue purple tones, 4k",
    "q2TKEyoUp1E": "Woman kneeling in prayer inside magnificent cathedral, colorful stained glass windows, golden divine sunbeams, peaceful atmosphere, 4k",
    "MxxOnxzvl08": "Open holy bible on wooden table with brilliant golden light from pages, divine rays upward, cross in background, warm atmosphere, 4k",
    "yED9Qz1G3mU": "Person standing on cliff edge, golden light breaking through dark storm clouds, divine revelation, dramatic cinematic silhouette, 4k",
    "wYg8VWkWxJg": "Person peacefully resting under beautiful blooming tree, lush green meadow, golden hour sunlight, butterflies, paradise scenery, 4k",
    "zM4EgCmhvIs": "Two hands cupping a glowing radiant heart of golden light, divine rays, bokeh background, spiritual love, warm colors, 4k",
}

def run_as(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

def chrome_js(js):
    js_esc = js.replace('\\', '\\\\').replace('"', '\\"')
    return run_as(f'tell application "Google Chrome"\ntell active tab of first window\nexecute javascript "{js_esc}"\nend tell\nend tell')

def chrome_nav(url):
    run_as(f'tell application "Google Chrome"\nset URL of active tab of first window to "{url}"\nend tell')

def get_chrome_window_bounds():
    b = run_as('tell application "Google Chrome"\ntell first window\nset b to bounds\nreturn (item 1 of b as string) & "," & (item 2 of b as string) & "," & (item 3 of b as string) & "," & (item 4 of b as string)\nend tell\nend tell')
    parts = b.split(",")
    return int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])

def send_enter():
    run_as('tell application "Chrome" to activate')
    time.sleep(0.3)
    run_as('tell application "System Events"\ntell process "Google Chrome"\nkey code 36\nend tell\nend tell')

def generate_and_capture(prompt, vid_id):
    """Gera imagem no Gemini e captura via screenshot"""
    print(f"  [*] Navegando para Gemini...")
    chrome_nav("https://gemini.google.com/app")
    time.sleep(6)
    
    # Preencher prompt
    full_prompt = f"Generate a stunning YouTube thumbnail image (landscape 16:9 ratio): {prompt}. NO text, NO letters, NO watermarks, photorealistic quality."
    
    print(f"  [*] Preenchendo prompt...")
    result = chrome_js(f'''
    (function() {{
        let editor = document.querySelector(".ql-editor");
        if (!editor) return "NO_EDITOR";
        editor.focus();
        editor.click();
        document.execCommand("selectAll", false, null);
        document.execCommand("insertText", false, `{full_prompt}`);
        return "OK:" + editor.innerText.length;
    }})()
    ''')
    print(f"  [*] Input: {result}")
    
    if "NO_EDITOR" in str(result):
        return None
    
    time.sleep(1)
    
    # Enviar com Enter
    print(f"  [*] Enviando...")
    run_as('tell application "Google Chrome" to activate')
    time.sleep(0.5)
    run_as('tell application "System Events"\ntell process "Google Chrome"\nkey code 36\nend tell\nend tell')
    
    # Aguardar imagem ser gerada
    print(f"  [*] Aguardando geração...")
    for i in range(60):
        time.sleep(5)
        
        try:
            result = chrome_js('''
            (function() {
                let imgs = document.querySelectorAll("img");
                for (let img of imgs) {
                    if (img.naturalWidth > 500 && img.src.includes("googleusercontent")) {
                        img.scrollIntoView({block: "center"});
                        let rect = img.getBoundingClientRect();
                        return "FOUND:" + rect.x + "," + rect.y + "," + rect.width + "," + rect.height + ":" + img.naturalWidth + "x" + img.naturalHeight;
                    }
                }
                return "WAITING";
            })()
            ''')
        except:
            result = "TIMEOUT"
        
        if i % 4 == 0:
            print(f"  [*] ({i*5}s) {str(result)[:60]}")
        
        if "FOUND:" in str(result):
            print(f"  [+] Imagem gerada!")
            time.sleep(2)
            
            # Parse position
            parts = str(result).split(":")[1].split(",")
            img_x = float(parts[0])
            img_y = float(parts[1])
            img_w = float(parts[2])
            img_h = float(parts[3])
            
            # Screenshot
            run_as('tell application "Google Chrome" to activate')
            time.sleep(1)
            subprocess.run(["screencapture", "-x", "/tmp/chrome_screen.png"], timeout=10)
            
            # Get window bounds
            wx, wy, wx2, wy2 = get_chrome_window_bounds()
            
            # Chrome toolbar height (~88px)
            toolbar_h = 88
            scale = 2  # Retina
            
            # Calculate absolute crop position
            abs_x = int((wx + img_x) * scale)
            abs_y = int((wy + toolbar_h + img_y) * scale)
            abs_w = int(img_w * scale)
            abs_h = int(img_h * scale)
            
            # Add small margin to exclude any UI overlay
            margin = int(10 * scale)
            abs_x += margin
            abs_y += margin
            abs_w -= margin * 2
            abs_h -= margin * 2
            
            screen = Image.open("/tmp/chrome_screen.png")
            cropped = screen.crop((abs_x, abs_y, abs_x + abs_w, abs_y + abs_h))
            thumb = cropped.resize((1280, 720), Image.LANCZOS).convert("RGB")
            
            thumb_path = os.path.join(THUMB_DIR, f"{vid_id}_gemini.jpg")
            thumb.save(thumb_path, "JPEG", quality=92)
            
            size_kb = os.path.getsize(thumb_path) / 1024
            print(f"  [+] Salva: {size_kb:.0f} KB")
            return thumb_path
    
    print(f"  [!] Timeout - imagem nao gerada")
    return None

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

def main():
    youtube = get_youtube()
    
    print("[*] Buscando videos...")
    channels = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads = channels["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    response = youtube.playlistItems().list(
        part="snippet,contentDetails", playlistId=uploads, maxResults=10
    ).execute()
    
    videos = []
    for item in response.get("items", []):
        vid_id = item["contentDetails"]["videoId"]
        title = item["snippet"]["title"]
        if vid_id in VIDEO_PROMPTS:
            videos.append({"id": vid_id, "title": title})
    
    print(f"[*] {len(videos)} videos para processar\n")
    
    success = 0
    for v in videos:
        vid_id = v["id"]
        prompt = VIDEO_PROMPTS[vid_id]
        
        print(f"\n{'='*60}")
        print(f"[*] {v['title'][:55]}")
        
        thumb_path = generate_and_capture(prompt, vid_id)
        
        if thumb_path:
            try:
                media = MediaFileUpload(thumb_path, mimetype="image/jpeg", resumable=True)
                youtube.thumbnails().set(videoId=vid_id, media_body=media).execute()
                print(f"  [+] THUMBNAIL ATUALIZADA NO YOUTUBE!")
                success += 1
            except Exception as e:
                print(f"  [!] Erro: {str(e)[:150]}")
        
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"[+] {success}/{len(videos)} thumbnails Gemini atualizadas!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
