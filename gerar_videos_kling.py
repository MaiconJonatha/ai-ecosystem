"""
SCRIPT: Gerar Videos REAIS na Kling AI para os YouTubers
Cada IA recebe um prompt cinematografico unico baseado na personalidade
Executa: python3 gerar_videos_kling.py
"""
import requests
import jwt
import time
import json

# Kling AI Config
KLING_ACCESS_KEY = "AeM8rnpLaT4yBByADNnLNEyGDyFbQp9d"
KLING_SECRET_KEY = "rH3EfYJtaQkJNgaHanGHh8rQg3eThGGe"
KLING_API_BASE = "https://api.klingai.com"

def gerar_jwt():
    now = time.time()
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": int(now + 1800),
        "iat": int(now),
        "nbf": int(now - 5),
    }
    return jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256")

# ============================================================
# PROMPTS CINEMATOGRAFICOS POR IA YOUTUBER
# ============================================================

PROMPTS_IAS = {
    "llama": {
        "nome": "LlamaAI Tech",
        "avatar": "🦙",
        "prompts": [
            "A futuristic llama character sitting at a holographic computer desk, typing code on floating screens, neon blue and purple lighting, cyberpunk tech office, cinematic 4K, smooth camera movement",
            "Close-up of a llama wearing smart glasses, lines of code reflecting in the lenses, dark room with multiple monitors showing running programs, atmospheric fog, professional lighting",
            "A llama robot teaching AI and coding to an audience of holographic students, futuristic classroom, digital blackboard with algorithms, warm cinematic lighting, dolly shot",
        ]
    },
    "gemma": {
        "nome": "Gemma Creative Studio",
        "avatar": "💎",
        "prompts": [
            "A sparkling gemstone character painting a masterpiece on a floating canvas in space, colorful nebulas in background, magical brush strokes creating galaxies, dreamy cinematic lighting, 4K",
            "Hands covered in paint creating beautiful digital art on a crystal tablet, colors splashing in slow motion, artistic studio with natural light, close-up detailed shot, ASMR style",
            "A diamond-shaped artist floating through a museum of living paintings, each frame animated and glowing, renaissance meets cyberpunk aesthetics, smooth dolly movement, ethereal lighting",
        ]
    },
    "phi": {
        "nome": "Phi Science Lab",
        "avatar": "🔬",
        "prompts": [
            "A scientist character in a futuristic laboratory, examining DNA double helix under a holographic microscope, glowing particles floating around, clinical blue and white lighting, cinematic",
            "Close-up of a microscope revealing a miniature universe inside a cell, zooming into molecular structures, beautiful scientific visualization, 4K macro photography style, dramatic lighting",
            "A physics experiment showing quantum particles dancing in slow motion, light splitting into rainbow spectrum, dark laboratory with laser beams, educational and mesmerizing, smooth camera pan",
        ]
    },
    "qwen": {
        "nome": "Qwen Gaming Pro",
        "avatar": "🐉",
        "prompts": [
            "A dragon character playing video games on a massive curved gaming monitor, RGB lighting everywhere, gaming headset on, intense focused expression, esports arena atmosphere, cinematic 4K",
            "POV of entering a virtual reality game world, digital portals opening, pixelated particles transforming into realistic 3D environment, epic gaming soundtrack feel, fast dynamic camera",
            "A gaming dragon performing a victory celebration, confetti and digital effects exploding, championship trophy glowing, arena crowd cheering, slow motion epic moment, cinematic lighting",
        ]
    },
    "tinyllama": {
        "nome": "Tiny Vlogs",
        "avatar": "🐣",
        "prompts": [
            "A cute small llama vlogging with a smartphone on a selfie stick, walking through a vibrant city at golden hour, warm cinematic colors, casual fun atmosphere, smooth tracking shot",
            "A tiny adorable character reacting with exaggerated expressions to something on a laptop screen, cozy room with fairy lights, warm comfortable aesthetic, close-up face reactions, 4K",
            "A small llama character doing a fun dance challenge in a colorful room, confetti falling, ring light glowing, social media style video, energetic and cheerful, dynamic camera angles",
        ]
    },
    "mistral": {
        "nome": "Mistral Filosofia",
        "avatar": "🇫🇷",
        "prompts": [
            "A philosopher character sitting in an ancient library filled with floating books, golden light streaming through stained glass windows, thoughtful contemplative expression, cinematic dolly shot",
            "Close-up of an old book opening to reveal animated philosophical concepts, Plato cave allegory coming to life as shadows on a wall, dramatic atmospheric lighting, 4K detailed",
            "A figure standing on a cliff overlooking a vast ocean at sunset, contemplating the meaning of existence, dramatic clouds, philosophical mood, epic wide angle cinematic shot, golden hour",
        ]
    },
}

def enviar_para_kling(prompt, duracao=5, aspect="16:9"):
    """Envia prompt para Kling AI e retorna task_id"""
    token = gerar_jwt()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "model_name": "kling-v1",
        "prompt": prompt[:500],
        "negative_prompt": "blurry, low quality, distorted, watermark, text, ugly, deformed",
        "cfg_scale": 0.5,
        "mode": "std",
        "aspect_ratio": aspect,
        "duration": str(duracao),
    }
    try:
        resp = requests.post(
            f"{KLING_API_BASE}/v1/videos/text2video",
            headers=headers,
            json=body,
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            task_id = data.get("task_id", "")
            return task_id, resp.json()
        else:
            return None, f"Erro {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return None, str(e)

def verificar_task(task_id):
    """Verifica status de uma task"""
    token = gerar_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(
            f"{KLING_API_BASE}/v1/videos/text2video/{task_id}",
            headers=headers,
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            status = data.get("task_status", "processing")
            videos = data.get("task_result", {}).get("videos", [])
            url = videos[0].get("url", "") if videos else ""
            return status, url
    except Exception as e:
        print(f"  Erro: {e}")
    return "processing", ""

# ============================================================
# EXECUTAR
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  GERADOR DE VIDEOS KLING AI - YouTubers IA")
    print("=" * 60)
    print()
    
    tasks = {}  # task_id -> {ia, prompt}
    
    # Enviar 1 prompt de cada IA (total: 6 videos)
    for ia_key, ia_data in PROMPTS_IAS.items():
        prompt = ia_data["prompts"][0]  # Primeiro prompt de cada IA
        print(f"{ia_data['avatar']} {ia_data['nome']}")
        print(f"  Prompt: {prompt[:80]}...")
        
        task_id, result = enviar_para_kling(prompt)
        if task_id:
            tasks[task_id] = {"ia": ia_key, "nome": ia_data["nome"], "avatar": ia_data["avatar"]}
            print(f"  ✅ Task: {task_id}")
        else:
            print(f"  ❌ Erro: {result}")
        print()
        time.sleep(1)  # Pausa entre requests
    
    if not tasks:
        print("Nenhuma task criada. Verifique as chaves da API Kling.")
        exit(1)
    
    print(f"\n{'=' * 60}")
    print(f"  {len(tasks)} videos enviados para Kling AI!")
    print(f"  Verificando status a cada 10 segundos...")
    print(f"{'=' * 60}\n")
    
    # Polling ate todos completarem
    completos = set()
    for tentativa in range(60):  # max 10 min
        time.sleep(10)
        todos_prontos = True
        
        for task_id, info in tasks.items():
            if task_id in completos:
                continue
            
            status, url = verificar_task(task_id)
            
            if status == "succeed" and url:
                print(f"  ✅ {info['avatar']} {info['nome']} - VIDEO PRONTO!")
                print(f"     URL: {url[:80]}...")
                completos.add(task_id)
            elif status == "failed":
                print(f"  ❌ {info['avatar']} {info['nome']} - FALHOU")
                completos.add(task_id)
            else:
                todos_prontos = False
        
        if todos_prontos or len(completos) == len(tasks):
            break
        
        if tentativa % 6 == 0:
            pendentes = len(tasks) - len(completos)
            print(f"  ⏳ {pendentes} videos ainda processando... ({(tentativa+1)*10}s)")
    
    print(f"\n{'=' * 60}")
    print(f"  RESULTADO FINAL")
    print(f"  Completos: {len(completos)}/{len(tasks)}")
    print(f"{'=' * 60}")
    
    # Salvar resultados
    resultados = []
    for task_id, info in tasks.items():
        status, url = verificar_task(task_id)
        resultados.append({
            "ia": info["ia"],
            "nome": info["nome"],
            "task_id": task_id,
            "status": status,
            "url": url,
        })
        if url:
            print(f"  {info['avatar']} {info['nome']}: {url}")
    
    with open("kling_resultados.json", "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\nResultados salvos em kling_resultados.json")
