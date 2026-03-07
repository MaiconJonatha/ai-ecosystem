"""
SCRIPT: Gerar Videos REAIS no HuggingFace (GRATIS) para os YouTubers
Usa Wan 2.1 Space - text-to-video gratuito
Executa: python3 gerar_videos_hf.py
"""
from gradio_client import Client
import time
import os
import shutil
import json

DEST_DIR = os.path.join(os.path.dirname(__file__), "ai-social-network", "static", "hf_videos")
os.makedirs(DEST_DIR, exist_ok=True)

# ============================================================
# PROMPTS CINEMATOGRAFICOS POR IA YOUTUBER
# ============================================================

PROMPTS_IAS = {
    "llama": {
        "nome": "LlamaAI Tech",
        "avatar": "🦙",
        "prompt": "A futuristic llama character sitting at a holographic computer desk, typing code on floating screens, neon blue and purple lighting, cyberpunk tech office, cinematic 4K",
    },
    "gemma": {
        "nome": "Gemma Creative Studio",
        "avatar": "💎",
        "prompt": "A sparkling gemstone character painting a masterpiece on a floating canvas in space, colorful nebulas in background, magical brush strokes creating galaxies, dreamy cinematic lighting",
    },
    "phi": {
        "nome": "Phi Science Lab",
        "avatar": "🔬",
        "prompt": "A scientist character in a futuristic laboratory, examining DNA double helix under a holographic microscope, glowing particles floating around, clinical blue and white cinematic lighting",
    },
    "qwen": {
        "nome": "Qwen Gaming Pro",
        "avatar": "🐉",
        "prompt": "A dragon character playing video games on a massive curved gaming monitor, RGB lighting everywhere, gaming headset on, intense focused expression, esports arena cinematic 4K",
    },
    "tinyllama": {
        "nome": "Tiny Vlogs",
        "avatar": "🐣",
        "prompt": "A cute small llama vlogging with a smartphone on a selfie stick, walking through a vibrant city at golden hour, warm cinematic colors, casual fun atmosphere, smooth tracking shot",
    },
    "mistral": {
        "nome": "Mistral Filosofia",
        "avatar": "🇫🇷",
        "prompt": "A philosopher character sitting in an ancient library filled with floating books, golden light streaming through stained glass windows, thoughtful contemplative expression, cinematic",
    },
}

def gerar_video_wan21(prompt, video_id, resolution="1280*720"):
    """Gera video via Wan 2.1 Space (GRATIS)"""
    print(f"  Conectando ao Wan 2.1...")
    client = Client("Wan-AI/Wan2.1", verbose=False)
    
    # Submit job
    print(f"  Submetendo job...")
    job = client.submit(
        prompt=prompt[:300],
        size=resolution,
        watermark_wan=False,
        seed=-1,
        api_name="/t2v_generation_async"
    )
    
    # Esperar job (fase 1)
    print(f"  Esperando na fila...")
    for i in range(90):  # 15 min
        time.sleep(10)
        if job.done():
            print(f"  Job concluido! ({(i+1)*10}s)")
            break
        if i % 6 == 0:
            print(f"  ...{(i+1)*10}s na fila")
    
    # Buscar video (fase 2)
    print(f"  Buscando video gerado...")
    for i in range(60):  # 10 min
        time.sleep(10)
        try:
            status = client.predict(api_name="/status_refresh")
            if status and isinstance(status, tuple) and len(status) >= 1:
                video_update = status[0]
                if isinstance(video_update, dict) and video_update.get("value") is not None:
                    val = video_update["value"]
                    if isinstance(val, dict) and val.get("video"):
                        vinfo = val["video"]
                        vpath = vinfo.get("path") or vinfo.get("url", "")
                        
                        # Salvar video
                        dest = os.path.join(DEST_DIR, f"{video_id}.mp4")
                        if os.path.isfile(str(vpath)):
                            shutil.copy2(str(vpath), dest)
                        elif str(vpath).startswith("http"):
                            import urllib.request
                            urllib.request.urlretrieve(str(vpath), dest)
                        
                        if os.path.isfile(dest):
                            size_mb = os.path.getsize(dest) / 1024 / 1024
                            return dest, size_mb
                        return vpath, 0
                
                # Progresso
                if len(status) >= 3 and i % 6 == 0:
                    wait = status[2]
                    print(f"  ...refresh {i+1}/60 wait:{wait}s")
        except Exception as e:
            if i % 10 == 0:
                print(f"  Erro refresh: {e}")
    
    return None, 0


if __name__ == "__main__":
    print("=" * 60)
    print("  GERADOR DE VIDEOS HUGGINGFACE - YouTubers IA")
    print("  Wan 2.1 Space (GRATIS - sem limite)")
    print("=" * 60)
    print()
    
    resultados = []
    
    for ia_key, ia_data in PROMPTS_IAS.items():
        print(f"\n{'='*50}")
        print(f"{ia_data['avatar']} {ia_data['nome']}")
        print(f"  Prompt: {ia_data['prompt'][:80]}...")
        print(f"{'='*50}")
        
        video_id = f"yt_{ia_key}_{int(time.time())}"
        
        try:
            path, size_mb = gerar_video_wan21(ia_data["prompt"], video_id)
            if path:
                print(f"  ✅ VIDEO GERADO! {size_mb:.1f} MB")
                print(f"  📁 {path}")
                resultados.append({
                    "ia": ia_key,
                    "nome": ia_data["nome"],
                    "video_id": video_id,
                    "path": str(path),
                    "size_mb": round(size_mb, 1),
                    "status": "success"
                })
            else:
                print(f"  ⏳ Timeout - video ainda na fila (sera gerado pelo retry loop)")
                resultados.append({
                    "ia": ia_key,
                    "nome": ia_data["nome"],
                    "video_id": video_id,
                    "status": "timeout"
                })
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            resultados.append({
                "ia": ia_key,
                "nome": ia_data["nome"],
                "video_id": video_id,
                "status": "error",
                "error": str(e)
            })
    
    print(f"\n{'='*60}")
    print(f"  RESULTADO FINAL")
    sucesso = len([r for r in resultados if r["status"] == "success"])
    print(f"  Videos gerados: {sucesso}/{len(resultados)}")
    print(f"{'='*60}")
    
    for r in resultados:
        emoji = "✅" if r["status"] == "success" else "⏳" if r["status"] == "timeout" else "❌"
        print(f"  {emoji} {r['nome']}: {r['status']}")
        if r.get("path"):
            print(f"     {r['path']}")
    
    with open("hf_resultados.json", "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\nResultados salvos em hf_resultados.json")
    print(f"Videos em: {DEST_DIR}")
