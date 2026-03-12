#!/usr/bin/env python3
"""
Set thumbnail on recent YouTube videos using YouTube Data API v3.
Uses OAuth2 with client_secret for authentication.
"""

import os
import sys
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CLIENT_SECRET = "/Users/maiconjonathamartinsdasilva/Downloads/client_secret_633536180211-i7lah4bvp9t3m3hpe8k4ub8vo56afeop.apps.googleusercontent.com.json"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "youtube_token.pickle")
THUMBNAIL_PATH = sys.argv[1] if len(sys.argv) > 1 else "/Users/maiconjonathamartinsdasilva/Downloads/Jesus_christ_standing_on_a_mountain_top_surrounded_delpmaspu.png"
MAX_VIDEOS = int(sys.argv[2]) if len(sys.argv) > 2 else 10

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[*] Refreshing token...")
            creds.refresh(Request())
        else:
            print("[*] Abrindo navegador para autenticacao OAuth2...")
            print("[*] Selecione sua conta Google e autorize o acesso ao YouTube.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=8888, open_browser=True)
        
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
        print("[+] Token salvo!")
    
    return build("youtube", "v3", credentials=creds)

def main():
    print(f"[*] Thumbnail: {THUMBNAIL_PATH}")
    
    if not os.path.exists(THUMBNAIL_PATH):
        print(f"[!] Arquivo nao encontrado: {THUMBNAIL_PATH}")
        return
    
    youtube = get_authenticated_service()
    
    # Listar vídeos do canal
    print(f"[*] Buscando ultimos {MAX_VIDEOS} videos do canal...")
    
    # Primeiro, pegar o canal do usuário
    channels = youtube.channels().list(part="contentDetails", mine=True).execute()
    
    if not channels.get("items"):
        print("[!] Nenhum canal encontrado!")
        return
    
    uploads_playlist = channels["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    print(f"[*] Playlist de uploads: {uploads_playlist}")
    
    # Listar vídeos da playlist de uploads
    videos = []
    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=uploads_playlist,
        maxResults=MAX_VIDEOS
    )
    response = request.execute()
    
    for item in response.get("items", []):
        vid_id = item["contentDetails"]["videoId"]
        title = item["snippet"]["title"]
        videos.append({"id": vid_id, "title": title})
        print(f"  - {title} ({vid_id})")
    
    if not videos:
        print("[!] Nenhum video encontrado!")
        return
    
    print(f"\n[*] Setando thumbnail em {len(videos)} videos...")
    
    success = 0
    for v in videos:
        try:
            print(f"\n[*] Video: {v['title'][:50]}... ({v['id']})")
            
            media = MediaFileUpload(THUMBNAIL_PATH, mimetype="image/png", resumable=True)
            
            result = youtube.thumbnails().set(
                videoId=v["id"],
                media_body=media
            ).execute()
            
            print(f"[+] Thumbnail setada! URL: {result['items'][0]['default']['url']}")
            success += 1
            
        except Exception as e:
            err_str = str(e)
            print(f"[!] Erro: {err_str[:200]}")
            if "forbidden" in err_str.lower() or "403" in err_str:
                print("[!] Sem permissao. Verifique se a API YouTube Data v3 esta habilitada no Google Cloud Console.")
                break
    
    print(f"\n{'='*60}")
    print(f"[+] Thumbnail atualizada em {success}/{len(videos)} videos!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
