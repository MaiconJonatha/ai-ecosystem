#!/usr/bin/env python3
"""
Cria vídeos Ken Burns (zoom/pan cinematográfico) a partir das thumbnails.
Gera vídeos de ~15s para cada imagem com efeitos de movimento.
"""

import os
import sys
import subprocess
import random

FFMPEG = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg"
THUMB_DIR = os.path.join(os.path.dirname(__file__), "thumbnails_yt")
VIDEO_DIR = os.path.join(os.path.dirname(__file__), "videos_yt")
os.makedirs(VIDEO_DIR, exist_ok=True)

# Títulos e IDs dos vídeos
VIDEOS = {
    "CmpnUanc5V0": "AI Social Network - 6 AI Agents",
    "YJKupUePTjs": "Mensagem pra hoje - Sunrise",
    "rQ6BbIgUY84": "Mulher Deus quer falar 1",
    "yIqiwMBYdq8": "Boa noite com Deus",
    "q2TKEyoUp1E": "Mulher Deus quer falar 2",
    "MxxOnxzvl08": "Mensagem de Deus - Bible",
    "yED9Qz1G3mU": "Deus falou comigo 1",
    "wYg8VWkWxJg": "Nem tudo é luta - Descansa",
    "zM4EgCmhvIs": "Deus falou comigo 2",
}

# Ken Burns effects - diferentes combinações de zoom/pan
EFFECTS = [
    # Zoom in lento do centro
    "scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=375:s=1920x1080:fps=25",
    # Zoom out
    "scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=375:s=1920x1080:fps=25",
    # Pan da esquerda para direita com zoom leve
    "scale=8000:-1,zoompan=z='min(zoom+0.001,1.3)':x='if(lte(on,1),0,min(x+2,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':d=375:s=1920x1080:fps=25",
    # Pan de cima para baixo
    "scale=8000:-1,zoompan=z='min(zoom+0.001,1.3)':x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min(y+1.5,ih-ih/zoom))':d=375:s=1920x1080:fps=25",
    # Zoom in no canto superior esquerdo
    "scale=8000:-1,zoompan=z='min(zoom+0.002,1.8)':x='iw/4-(iw/zoom/4)':y='ih/4-(ih/zoom/4)':d=375:s=1920x1080:fps=25",
]

def create_ken_burns_video(image_path, output_path, duration=15, effect_idx=None):
    """Cria vídeo Ken Burns a partir de uma imagem"""
    
    if effect_idx is None:
        effect_idx = random.randint(0, len(EFFECTS) - 1)
    
    effect = EFFECTS[effect_idx]
    # Ajustar duração (d = duration * fps)
    frames = duration * 25
    effect = effect.replace("d=375", f"d={frames}")
    
    cmd = [
        FFMPEG, "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", effect,
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if result.returncode != 0:
        print(f"  [!] FFmpeg erro: {result.stderr[-300:]}")
        return False
    
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  [+] Video criado: {size_mb:.1f} MB")
    return True

def main():
    print("[*] Criando videos Ken Burns a partir das thumbnails...\n")
    
    success = 0
    for i, (vid_id, title) in enumerate(VIDEOS.items()):
        print(f"{'='*60}")
        print(f"[*] {title} ({vid_id})")
        
        # Preferir imagem Gemini, senão Stable Horde
        gemini_path = os.path.join(THUMB_DIR, f"{vid_id}_gemini.jpg")
        horde_path = os.path.join(THUMB_DIR, f"{vid_id}.jpg")
        
        if os.path.exists(gemini_path) and os.path.getsize(gemini_path) > 20000:
            img_path = gemini_path
            src = "Gemini"
        elif os.path.exists(horde_path):
            img_path = horde_path
            src = "StableHorde"
        else:
            print(f"  [!] Nenhuma imagem encontrada!")
            continue
        
        print(f"  [*] Fonte: {src} ({os.path.getsize(img_path)/1024:.0f} KB)")
        
        output_path = os.path.join(VIDEO_DIR, f"{vid_id}_kenburns.mp4")
        
        # Usar efeito diferente para cada vídeo
        effect_idx = i % len(EFFECTS)
        
        ok = create_ken_burns_video(img_path, output_path, duration=15, effect_idx=effect_idx)
        
        if ok:
            success += 1
    
    print(f"\n{'='*60}")
    print(f"[+] {success} videos criados em {VIDEO_DIR}")
    print(f"{'='*60}")
    
    # Listar vídeos criados
    for f in sorted(os.listdir(VIDEO_DIR)):
        if f.endswith(".mp4"):
            path = os.path.join(VIDEO_DIR, f)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"  {f} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
