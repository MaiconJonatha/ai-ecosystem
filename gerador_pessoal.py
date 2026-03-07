"""
GERADOR PESSOAL DE IMAGENS E VIDEOS - 100% GRATIS
Usa HuggingFace Spaces (sem API key, sem limites, sem créditos)

Imagens: Z Image Turbo (FLUX-based, ~8s por imagem)
Videos:  LTX-2 Turbo (text-to-video, ~60s por video)

Executa: python3 gerador_pessoal.py
"""
import os
import time
import json
import shutil
import random
from gradio_client import Client

# Diretorios de saida
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "ai-social-network", "static", "ig_images", "pessoal")
VID_DIR = os.path.join(BASE_DIR, "ai-social-network", "static", "ig_videos", "pessoal")
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(VID_DIR, exist_ok=True)

# ============================================================
# PROMPTS POR IA CRIADOR
# ============================================================
CRIADORES = {
    "llama": {
        "nome": "LlamaAI Tech",
        "avatar": "🦙",
        "img_prompts": [
            "A futuristic llama character sitting at a holographic computer desk, typing code on floating screens, neon blue and purple lighting, cyberpunk tech office, cinematic 4K, ultra detailed",
            "Close-up of a llama wearing smart glasses, lines of code reflecting in the lenses, dark room with multiple monitors, atmospheric fog, professional cinematic lighting",
            "A llama robot teaching AI concepts to holographic students, futuristic classroom, digital blackboard with neural networks, warm cinematic lighting",
        ],
        "vid_prompts": [
            "A futuristic llama character sitting at a holographic computer desk, typing code on floating screens, neon blue and purple lighting, cyberpunk tech office, cinematic smooth camera movement",
            "A llama robot walking through a neon-lit corridor of servers, blue LED reflections, cinematic tracking shot",
        ]
    },
    "gemma": {
        "nome": "Gemma Creative Studio",
        "avatar": "💎",
        "img_prompts": [
            "A sparkling gemstone character painting a masterpiece on a floating canvas in space, colorful nebulas, magical brush strokes creating galaxies, dreamy cinematic lighting, 4K",
            "Hands covered in glowing paint creating digital art on a crystal tablet, colors splashing in slow motion, artistic studio with natural light",
            "A diamond-shaped artist floating through a museum of living paintings, renaissance meets cyberpunk, smooth ethereal lighting",
        ],
        "vid_prompts": [
            "A sparkling gemstone character painting colorful strokes on a floating canvas in space, nebula background, magical dreamy atmosphere, smooth camera pan",
            "A crystal artist creating digital art, colors flowing like water through the air, mesmerizing and beautiful",
        ]
    },
    "phi": {
        "nome": "Phi Science Lab",
        "avatar": "🔬",
        "img_prompts": [
            "A scientist character in a futuristic laboratory, examining DNA double helix under holographic microscope, glowing particles, clinical blue and white cinematic lighting",
            "Close-up of a microscope revealing a miniature universe inside a cell, molecular structures, beautiful scientific visualization, 4K macro",
            "A physics experiment showing quantum particles dancing, light splitting into rainbow spectrum, dark laboratory with laser beams, educational and mesmerizing",
        ],
        "vid_prompts": [
            "A scientist examining DNA under a holographic microscope, glowing particles floating around, futuristic lab, smooth camera movement",
            "Quantum particles dancing in slow motion, light beams splitting through crystals, mesmerizing scientific visualization",
        ]
    },
    "qwen": {
        "nome": "Qwen Gaming Pro",
        "avatar": "🐉",
        "img_prompts": [
            "A dragon character playing video games on a massive curved gaming monitor, RGB lighting, gaming headset, intense focused expression, esports arena, cinematic 4K",
            "POV entering a virtual reality game world, digital portals opening, pixelated particles transforming into 3D, epic gaming feel, dynamic camera",
            "A gaming dragon celebrating victory, confetti and digital effects, championship trophy, arena crowd cheering, slow motion epic moment",
        ],
        "vid_prompts": [
            "A dragon character playing games on a massive curved monitor, RGB lighting flashing, gaming headset on, esports arena atmosphere, cinematic",
            "POV entering a virtual reality game world through a glowing portal, particles transforming, epic atmosphere",
        ]
    },
    "tinyllama": {
        "nome": "Tiny Vlogs",
        "avatar": "🐣",
        "img_prompts": [
            "A cute small llama vlogging with a smartphone on a selfie stick, walking through vibrant city at golden hour, warm cinematic colors, fun atmosphere",
            "A tiny adorable character reacting with exaggerated expressions to a laptop screen, cozy room with fairy lights, warm comfortable aesthetic, 4K",
            "A small llama doing a fun dance in a colorful room, confetti falling, ring light glowing, social media style, energetic and cheerful",
        ],
        "vid_prompts": [
            "A cute small llama walking through a vibrant city street, vlogging with smartphone, golden hour warm lighting, smooth tracking shot",
            "A tiny adorable character dancing happily in a colorful room with confetti, cheerful and energetic",
        ]
    },
    "mistral": {
        "nome": "Mistral Filosofia",
        "avatar": "🇫🇷",
        "img_prompts": [
            "A philosopher character in an ancient library filled with floating books, golden light through stained glass windows, contemplative expression, cinematic",
            "An old book opening to reveal animated philosophical concepts, cave allegory shadows on wall, dramatic atmospheric lighting, 4K",
            "A figure on a cliff overlooking vast ocean at sunset, contemplating existence, dramatic clouds, epic wide angle cinematic, golden hour",
        ],
        "vid_prompts": [
            "A philosopher sitting in an ancient library, books floating around magically, golden light streaming through stained glass, contemplative atmosphere",
            "A figure standing on a cliff overlooking the ocean at sunset, wind blowing, dramatic clouds, philosophical mood, cinematic wide shot",
        ]
    },
}

# ============================================================
# GERADORES
# ============================================================

def gerar_imagem(prompt, filename):
    """Gera imagem via Z Image Turbo (FLUX-based, GRATIS, ~8s)"""
    print(f"  📸 Conectando ao Z Image Turbo...")
    client = Client("mrfakename/Z-Image-Turbo", verbose=False)
    
    result = client.predict(
        prompt=prompt[:500],
        height=768,
        width=1024,
        num_inference_steps=9,
        seed=42,
        randomize_seed=True,
        api_name="/generate_image"
    )
    
    if isinstance(result, tuple) and result[0]:
        img_path = str(result[0])
        if os.path.isfile(img_path):
            dest = os.path.join(IMG_DIR, filename)
            shutil.copy2(img_path, dest)
            size_kb = os.path.getsize(dest) / 1024
            print(f"  ✅ Imagem: {dest} ({size_kb:.0f} KB)")
            return dest
    return None


def gerar_video(prompt, filename, duracao=3.0):
    """Gera video via LTX-2 Turbo (GRATIS, ~60s, text-to-video)"""
    print(f"  🎬 Conectando ao LTX-2 Turbo...")
    client = Client("alexnasa/ltx-2-TURBO", verbose=False)
    
    result = client.predict(
        first_frame=None,
        end_frame=None,
        prompt=prompt[:500],
        duration=duracao,
        input_video=None,
        generation_mode="Text-to-Video",
        enhance_prompt=True,
        seed=10,
        randomize_seed=True,
        height=512,
        width=768,
        camera_lora="No LoRA",
        audio_path=None,
        api_name="/generate_video"
    )
    
    vid_path = None
    if isinstance(result, str) and os.path.isfile(result):
        vid_path = result
    elif isinstance(result, dict):
        vid_data = result.get("video", result)
        vid_path = vid_data.get("path", "") if isinstance(vid_data, dict) else ""
    elif isinstance(result, tuple) and result:
        for item in result:
            if isinstance(item, str) and os.path.isfile(str(item)):
                vid_path = item
                break
            elif isinstance(item, dict) and "video" in item:
                vid_path = item["video"].get("path", "")
                break
    
    if vid_path and os.path.isfile(str(vid_path)):
        dest = os.path.join(VID_DIR, filename)
        shutil.copy2(str(vid_path), dest)
        size_mb = os.path.getsize(dest) / 1024 / 1024
        print(f"  ✅ Video: {dest} ({size_mb:.1f} MB)")
        return dest
    
    print(f"  ⚠️ Video path: {vid_path}")
    return None


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  🎨 GERADOR PESSOAL DE IMAGENS E VIDEOS")
    print("  100% GRATIS - HuggingFace Spaces")
    print("  Imagens: Z Image Turbo (FLUX)")
    print("  Videos:  LTX-2 Turbo")
    print("=" * 60)
    print()
    
    resultados = {"imagens": [], "videos": []}
    
    # 1. Gerar IMAGENS para todos os criadores
    print("📸 FASE 1: GERANDO IMAGENS")
    print("-" * 40)
    for ia_key, ia_data in CRIADORES.items():
        print(f"\n{ia_data['avatar']} {ia_data['nome']}")
        prompt = random.choice(ia_data["img_prompts"])
        print(f"  Prompt: {prompt[:60]}...")
        
        filename = f"pessoal_{ia_key}_{int(time.time())}.png"
        try:
            path = gerar_imagem(prompt, filename)
            if path:
                resultados["imagens"].append({
                    "ia": ia_key, "nome": ia_data["nome"],
                    "path": path, "filename": filename,
                    "status": "success"
                })
            else:
                resultados["imagens"].append({
                    "ia": ia_key, "nome": ia_data["nome"],
                    "status": "failed"
                })
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            resultados["imagens"].append({
                "ia": ia_key, "nome": ia_data["nome"],
                "status": "error", "error": str(e)
            })
        time.sleep(2)  # Pausa entre gerações
    
    # 2. Gerar VIDEOS para todos os criadores
    print(f"\n\n🎬 FASE 2: GERANDO VIDEOS")
    print("-" * 40)
    for ia_key, ia_data in CRIADORES.items():
        print(f"\n{ia_data['avatar']} {ia_data['nome']}")
        prompt = random.choice(ia_data["vid_prompts"])
        print(f"  Prompt: {prompt[:60]}...")
        
        filename = f"pessoal_{ia_key}_{int(time.time())}.mp4"
        try:
            path = gerar_video(prompt, filename, duracao=2.0)
            if path:
                resultados["videos"].append({
                    "ia": ia_key, "nome": ia_data["nome"],
                    "path": path, "filename": filename,
                    "status": "success"
                })
            else:
                resultados["videos"].append({
                    "ia": ia_key, "nome": ia_data["nome"],
                    "status": "failed"
                })
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            resultados["videos"].append({
                "ia": ia_key, "nome": ia_data["nome"],
                "status": "error", "error": str(e)
            })
        time.sleep(5)  # Pausa entre videos
    
    # Resultado final
    print(f"\n\n{'=' * 60}")
    print(f"  RESULTADO FINAL")
    imgs_ok = len([r for r in resultados["imagens"] if r["status"] == "success"])
    vids_ok = len([r for r in resultados["videos"] if r["status"] == "success"])
    print(f"  Imagens: {imgs_ok}/{len(CRIADORES)}")
    print(f"  Videos:  {vids_ok}/{len(CRIADORES)}")
    print(f"{'=' * 60}")
    
    for tipo in ["imagens", "videos"]:
        print(f"\n  {tipo.upper()}:")
        for r in resultados[tipo]:
            emoji = "✅" if r["status"] == "success" else "❌"
            print(f"    {emoji} {r['nome']}: {r['status']}")
            if r.get("path"):
                print(f"       {r['path']}")
    
    # Salvar resultados
    with open("gerador_pessoal_resultados.json", "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\nResultados salvos em gerador_pessoal_resultados.json")
    print(f"Imagens em: {IMG_DIR}")
    print(f"Videos em:  {VID_DIR}")
