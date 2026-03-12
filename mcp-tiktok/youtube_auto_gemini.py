#!/usr/bin/env python3
"""
Automatiza geração de imagens via Google Gemini no Chrome (já logado)
usando AppleScript + JS injection, depois seta thumbnails via YouTube API.
"""

import os
import sys
import time
import json
import pickle
import subprocess
import base64
import glob
from PIL import Image
from io import BytesIO
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_SECRET = "/Users/maiconjonathamartinsdasilva/Downloads/client_secret_633536180211-i7lah4bvp9t3m3hpe8k4ub8vo56afeop.apps.googleusercontent.com.json"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "youtube_token.pickle")
THUMB_DIR = os.path.join(os.path.dirname(__file__), "thumbnails_yt")
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
os.makedirs(THUMB_DIR, exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]

VIDEO_PROMPTS = {
    "CmpnUanc5V0": "6 AI robots sitting around holographic table chatting on social media screens, cyberpunk neon blue purple, digital art, 4k",
    "YJKupUePTjs": "golden sunrise over mountains, divine light rays, cross silhouette on hilltop, cinematic, 4k",
    "rQ6BbIgUY84": "woman in white dress praying, golden divine light from above, flower garden, spiritual atmosphere, 4k",
    "yIqiwMBYdq8": "night sky stars milky way, crescent moon reflecting calm lake, peaceful good night scene, 4k",
    "q2TKEyoUp1E": "woman praying inside cathedral, stained glass windows, golden sunbeams, divine atmosphere, 4k",
    "MxxOnxzvl08": "open holy bible with golden light from pages, divine rays, cross background, warm golden, 4k",
    "yED9Qz1G3mU": "person on cliff edge, golden light through dark clouds, divine revelation, cinematic, 4k",
    "wYg8VWkWxJg": "person resting under blooming tree, green meadow, golden hour, butterflies, paradise, 4k",
    "zM4EgCmhvIs": "hands cupping glowing golden heart, divine rays, spiritual love, warm colors, 4k",
}

def run_applescript(script):
    """Executa AppleScript e retorna resultado"""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def chrome_js(js_code):
    """Executa JavaScript no Chrome via AppleScript"""
    # Escapar aspas para AppleScript
    js_escaped = js_code.replace('\\', '\\\\').replace('"', '\\"')
    script = f'''
    tell application "Google Chrome"
        tell active tab of first window
            execute javascript "{js_escaped}"
        end tell
    end tell
    '''
    return run_applescript(script)

def chrome_navigate(url):
    """Navega para URL no Chrome"""
    script = f'''
    tell application "Google Chrome"
        set URL of active tab of first window to "{url}"
    end tell
    '''
    run_applescript(script)

def generate_image_gemini_browser(prompt, vid_id):
    """Gera imagem via Gemini no navegador Chrome"""
    print(f"  [*] Abrindo Gemini...")
    
    chrome_navigate("https://gemini.google.com/app")
    time.sleep(5)
    
    # Digitar prompt no campo de texto
    full_prompt = f"Generate a YouTube thumbnail image (1280x720, landscape): {prompt}. NO text, NO watermarks, photorealistic quality."
    
    print(f"  [*] Digitando prompt...")
    
    # Encontrar e preencher o campo de input
    js = f'''
    (function() {{
        // Tentar encontrar o campo de input do Gemini
        let input = document.querySelector('.ql-editor, [contenteditable="true"], textarea[aria-label], .input-area textarea, rich-textarea .ql-editor');
        if (!input) {{
            // Tentar outros seletores
            let all = document.querySelectorAll('[contenteditable="true"]');
            for (let el of all) {{
                if (el.offsetHeight > 0) {{ input = el; break; }}
            }}
        }}
        if (input) {{
            input.focus();
            input.innerHTML = '';
            document.execCommand('insertText', false, `{full_prompt}`);
            return 'OK';
        }}
        return 'INPUT_NOT_FOUND: ' + document.querySelectorAll('[contenteditable]').length;
    }})()
    '''
    
    result = chrome_js(js)
    print(f"  [*] Input: {result}")
    
    if 'NOT_FOUND' in str(result):
        # Tentar com p tag dentro do editor
        time.sleep(3)
        js2 = f'''
        (function() {{
            let editors = document.querySelectorAll('.ql-editor, [contenteditable="true"]');
            for (let e of editors) {{
                if (e.offsetHeight > 20 && e.offsetWidth > 100) {{
                    e.focus();
                    e.innerText = `{full_prompt}`;
                    e.dispatchEvent(new Event('input', {{bubbles: true}}));
                    return 'OK2: ' + e.className;
                }}
            }}
            return 'STILL_NOT_FOUND';
        }})()
        '''
        result = chrome_js(js2)
        print(f"  [*] Input2: {result}")
    
    time.sleep(1)
    
    # Clicar no botão de enviar
    print(f"  [*] Enviando prompt...")
    js_send = '''
    (function() {
        // Botão de enviar no Gemini
        let btn = document.querySelector('.send-button, button[aria-label*="Send"], button[aria-label*="Enviar"], .send-button-container button, [data-mat-icon-name="send"]');
        if (!btn) {
            let buttons = document.querySelectorAll('button');
            for (let b of buttons) {
                let aria = b.getAttribute('aria-label') || '';
                let svg = b.querySelector('svg, mat-icon');
                if (aria.toLowerCase().includes('send') || aria.toLowerCase().includes('enviar') || (svg && b.offsetHeight < 60)) {
                    btn = b;
                    break;
                }
            }
        }
        if (btn) {
            btn.click();
            return 'SENT';
        }
        // Tentar Enter
        let input = document.querySelector('.ql-editor, [contenteditable="true"]');
        if (input) {
            input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', bubbles: true}));
            return 'ENTER_SENT';
        }
        return 'BTN_NOT_FOUND';
    })()
    '''
    result = chrome_js(js_send)
    print(f"  [*] Send: {result}")
    
    # Aguardar geração (Gemini pode demorar 30-60s para gerar imagem)
    print(f"  [*] Aguardando geração da imagem...")
    
    for i in range(60):
        time.sleep(5)
        
        # Verificar se há imagem gerada
        js_check = '''
        (function() {
            let imgs = document.querySelectorAll('img[src*="blob:"], img[src*="data:image"], img[src*="googleusercontent"], .generated-image img, .response-container img');
            let results = [];
            for (let img of imgs) {
                if (img.naturalWidth > 200 && img.naturalHeight > 200) {
                    results.push(img.src.substring(0, 100));
                }
            }
            return results.length > 0 ? 'FOUND:' + results.length + ':' + results[results.length-1] : 'WAITING:' + imgs.length;
        })()
        '''
        
        result = chrome_js(js_check)
        
        if i % 4 == 0:
            print(f"  [*] Check ({i*5}s): {str(result)[:80]}")
        
        if 'FOUND' in str(result):
            print(f"  [+] Imagem encontrada!")
            
            # Tentar baixar a imagem via fetch e salvar como base64
            js_download = '''
            (function() {
                let imgs = document.querySelectorAll('img');
                let target = null;
                for (let img of imgs) {
                    if (img.naturalWidth > 200 && img.naturalHeight > 200 && !img.src.includes('avatar') && !img.src.includes('icon')) {
                        target = img;
                    }
                }
                if (!target) return 'NO_IMG';
                
                // Criar canvas e converter para base64
                let canvas = document.createElement('canvas');
                canvas.width = target.naturalWidth;
                canvas.height = target.naturalHeight;
                let ctx = canvas.getContext('2d');
                ctx.drawImage(target, 0, 0);
                try {
                    return canvas.toDataURL('image/jpeg', 0.92);
                } catch(e) {
                    // CORS - tentar download link
                    let a = document.createElement('a');
                    a.href = target.src;
                    a.download = 'thumbnail_''' + vid_id + '''.jpg';
                    a.click();
                    return 'DOWNLOADED_VIA_CLICK';
                }
            })()
            '''
            
            result = chrome_js(js_download)
            
            if str(result).startswith('data:image'):
                # Salvar base64 como arquivo
                b64_data = str(result).split(',', 1)[1]
                img_bytes = base64.b64decode(b64_data)
                thumb_path = os.path.join(THUMB_DIR, f"{vid_id}_gemini.jpg")
                
                img = Image.open(BytesIO(img_bytes))
                if img.size != (1280, 720):
                    img = img.resize((1280, 720), Image.LANCZOS)
                img.save(thumb_path, "JPEG", quality=92)
                
                size_kb = os.path.getsize(thumb_path) / 1024
                print(f"  [+] Salva: {thumb_path} ({size_kb:.0f} KB)")
                return thumb_path
            
            elif 'DOWNLOADED_VIA_CLICK' in str(result):
                # Esperar download
                time.sleep(3)
                # Procurar arquivo recente no Downloads
                files = sorted(glob.glob(f"{DOWNLOAD_DIR}/thumbnail_{vid_id}*"), key=os.path.getmtime, reverse=True)
                if files:
                    thumb_path = os.path.join(THUMB_DIR, f"{vid_id}_gemini.jpg")
                    img = Image.open(files[0])
                    img = img.resize((1280, 720), Image.LANCZOS)
                    img.save(thumb_path, "JPEG", quality=92)
                    print(f"  [+] Salva do download: {thumb_path}")
                    return thumb_path
            
            break
    
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
        if vid_id in VIDEO_PROMPTS:
            videos.append({"id": vid_id, "title": title})
    
    print(f"[*] {len(videos)} videos para processar\n")
    
    success = 0
    for v in videos:
        vid_id = v["id"]
        title = v["title"]
        prompt = VIDEO_PROMPTS[vid_id]
        
        print(f"\n{'='*60}")
        print(f"[*] {title[:55]}")
        
        thumb_path = generate_image_gemini_browser(prompt, vid_id)
        
        if thumb_path:
            try:
                media = MediaFileUpload(thumb_path, mimetype="image/jpeg", resumable=True)
                youtube.thumbnails().set(videoId=vid_id, media_body=media).execute()
                print(f"  [+] THUMBNAIL YOUTUBE ATUALIZADA!")
                success += 1
            except Exception as e:
                print(f"  [!] Erro YouTube: {str(e)[:200]}")
        
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"[+] {success}/{len(videos)} thumbnails atualizadas via Gemini!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
