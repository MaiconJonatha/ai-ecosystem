"""
AI Image Generator - Google Gemini / Nano Banana Pro / Imagen 4.0
Gerador de imagens visuais com múltiplos modelos do Google
"""

import os
import json
import uuid
import base64
import asyncio
import httpx
import time
from datetime import datetime
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/imagegen", tags=["image-generator"])

# ============================================================
# CONFIG
# ============================================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Carregar do .env se não estiver no environ
if not GOOGLE_API_KEY:
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("GOOGLE_API_KEY="):
                    GOOGLE_API_KEY = line.strip().split("=", 1)[1]

PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
if not PIXABAY_API_KEY or not PEXELS_API_KEY:
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("PIXABAY_API_KEY=") and not PIXABAY_API_KEY:
                    PIXABAY_API_KEY = line.strip().split("=", 1)[1]
                elif line.startswith("PEXELS_API_KEY=") and not PEXELS_API_KEY:
                    PEXELS_API_KEY = line.strip().split("=", 1)[1]

# Diretório para salvar imagens geradas
IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "generated_images")
os.makedirs(IMG_DIR, exist_ok=True)

# Histórico de gerações
HISTORICO = []
STATS = {"total_geradas": 0, "por_modelo": {}, "erros": 0}

# ============================================================
# MODELOS GOOGLE - Cascade de qualidade
# ============================================================
GOOGLE_MODELS = [
    {
        "id": "nano-banana-pro-preview",
        "nome": "Nano Banana Pro",
        "emoji": "🍌",
        "descricao": "Modelo experimental de ponta do Google - Máxima qualidade",
        "tipo": "generateContent",
        "suporta_imagem": True,
        "cor": "#FFD700"
    },
    {
        "id": "gemini-3-pro-image-preview",
        "nome": "Gemini 3 Pro Image",
        "emoji": "💎",
        "descricao": "Gemini 3 Pro - Geração de imagens de altíssima qualidade",
        "tipo": "generateContent",
        "suporta_imagem": True,
        "cor": "#4285f4"
    },
    {
        "id": "gemini-2.5-flash-image",
        "nome": "Gemini 2.5 Flash Image",
        "emoji": "⚡",
        "descricao": "Gemini Flash - Rápido e eficiente para imagens",
        "tipo": "generateContent",
        "suporta_imagem": True,
        "cor": "#34a853"
    },
    {
        "id": "gemini-3-flash-preview",
        "nome": "Gemini 3 Flash",
        "emoji": "🚀",
        "descricao": "Gemini 3 Flash - Nova geração ultrarrápida",
        "tipo": "generateContent",
        "suporta_imagem": True,
        "cor": "#ea4335"
    },
    {
        "id": "gemini-3.1-pro-preview",
        "nome": "Gemini 3.1 Pro",
        "emoji": "🧠",
        "descricao": "Gemini 3.1 Pro - O mais avançado",
        "tipo": "generateContent",
        "suporta_imagem": True,
        "cor": "#9333ea"
    },
    {
        "id": "imagen-4.0-fast-generate-001",
        "nome": "Imagen 4.0 Fast",
        "emoji": "🖼️",
        "descricao": "Google Imagen 4.0 - Geração ultrarrápida",
        "tipo": "predict",
        "suporta_imagem": True,
        "cor": "#f59e0b"
    },
    {
        "id": "imagen-4.0-generate-001",
        "nome": "Imagen 4.0",
        "emoji": "🎨",
        "descricao": "Google Imagen 4.0 - Qualidade padrão",
        "tipo": "predict",
        "suporta_imagem": True,
        "cor": "#06b6d4"
    },
    {
        "id": "imagen-4.0-ultra-generate-001",
        "nome": "Imagen 4.0 Ultra",
        "emoji": "👑",
        "descricao": "Google Imagen 4.0 Ultra - Máxima resolução",
        "tipo": "predict",
        "suporta_imagem": True,
        "cor": "#dc2626"
    },
]

# Estilos artísticos disponíveis
ESTILOS = {
    "realista": "photorealistic, ultra high detail, 8k resolution, professional photography, sharp focus",
    "anime": "anime style, vibrant colors, detailed illustration, manga aesthetic, cel shading",
    "pintura": "oil painting style, brush strokes visible, artistic, masterpiece, fine art",
    "cyberpunk": "cyberpunk aesthetic, neon lights, futuristic city, rain, dark atmosphere, blade runner style",
    "fantasia": "fantasy art, magical, ethereal, mystical atmosphere, epic composition, dramatic lighting",
    "cartoon": "cartoon style, colorful, fun, animated, bold outlines, playful",
    "3d": "3D render, octane render, unreal engine 5, ray tracing, volumetric lighting, photorealistic CGI",
    "pixel": "pixel art, retro game style, 16-bit, nostalgic, colorful sprites",
    "aquarela": "watercolor painting, soft colors, flowing, artistic, delicate brushwork",
    "minimalista": "minimalist design, clean lines, simple shapes, modern, elegant, white space",
    "surreal": "surrealist art, dreamlike, Salvador Dali style, impossible geometry, mind-bending",
    "steampunk": "steampunk aesthetic, Victorian era, brass gears, steam engines, mechanical, industrial",
    "vaporwave": "vaporwave aesthetic, pastel colors, retro 80s, glitch art, synthwave, neon grid",
    "nenhum": ""
}


# ============================================================
# FUNÇÕES DE GERAÇÃO
# ============================================================

async def _gerar_com_gemini(prompt: str, modelo_id: str, estilo: str = "realista") -> dict:
    """Gera imagem com modelos Gemini (generateContent)"""
    if not GOOGLE_API_KEY:
        return {"ok": False, "erro": "GOOGLE_API_KEY não configurada"}
    
    estilo_texto = ESTILOS.get(estilo, "")
    full_prompt = f"Generate a stunning, high-quality image: {prompt}"
    if estilo_texto:
        full_prompt += f", {estilo_texto}"
    full_prompt = full_prompt[:1500]
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_id}:generateContent",
                headers={
                    "x-goog-api-key": GOOGLE_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    texto_resp = ""
                    imagem_url = None
                    
                    for p in parts:
                        if "inlineData" in p:
                            img_b64 = p["inlineData"].get("data", "")
                            mime = p["inlineData"].get("mimeType", "image/png")
                            ext = "png" if "png" in mime else "jpg" if "jpeg" in mime or "jpg" in mime else "webp"
                            
                            # Salvar imagem
                            fname = f"{modelo_id.split('-')[0]}_{uuid.uuid4().hex[:8]}.{ext}"
                            fpath = os.path.join(IMG_DIR, fname)
                            with open(fpath, "wb") as f:
                                f.write(base64.b64decode(img_b64))
                            
                            imagem_url = f"/static/generated_images/{fname}"
                            size_kb = os.path.getsize(fpath) // 1024
                            
                        elif "text" in p:
                            texto_resp = p["text"]
                    
                    if imagem_url:
                        return {
                            "ok": True,
                            "imagem_url": imagem_url,
                            "modelo": modelo_id,
                            "texto": texto_resp,
                            "tamanho_kb": size_kb
                        }
                    else:
                        return {"ok": False, "erro": f"Modelo respondeu sem imagem", "texto": texto_resp}
                        
                return {"ok": False, "erro": "Sem candidatos na resposta"}
            
            elif resp.status_code == 429:
                error_data = resp.json().get("error", {})
                msg = error_data.get("message", "")
                retry_match = ""
                if "retry in" in msg.lower():
                    retry_match = msg.split("retry in")[-1].strip().split("s")[0] + "s"
                return {"ok": False, "erro": f"Rate limit - aguarde {retry_match}", "retry": True}
            
            elif resp.status_code == 400:
                error_msg = resp.json().get("error", {}).get("message", "")
                return {"ok": False, "erro": error_msg}
            
            else:
                return {"ok": False, "erro": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                
    except Exception as e:
        return {"ok": False, "erro": str(e)}


async def _gerar_com_imagen(prompt: str, modelo_id: str, estilo: str = "realista") -> dict:
    """Gera imagem com Imagen 4.0 (predict)"""
    if not GOOGLE_API_KEY:
        return {"ok": False, "erro": "GOOGLE_API_KEY não configurada"}
    
    estilo_texto = ESTILOS.get(estilo, "")
    full_prompt = f"{prompt}"
    if estilo_texto:
        full_prompt += f", {estilo_texto}"
    full_prompt = full_prompt[:1500]
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_id}:predict",
                headers={
                    "x-goog-api-key": GOOGLE_API_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "instances": [{"prompt": full_prompt}],
                    "parameters": {"sampleCount": 1, "aspectRatio": "1:1"}
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                predictions = data.get("predictions", [])
                if predictions:
                    img_b64 = predictions[0].get("bytesBase64Encoded", "")
                    mime = predictions[0].get("mimeType", "image/png")
                    
                    if img_b64:
                        ext = "png" if "png" in mime else "jpg"
                        fname = f"imagen4_{uuid.uuid4().hex[:8]}.{ext}"
                        fpath = os.path.join(IMG_DIR, fname)
                        with open(fpath, "wb") as f:
                            f.write(base64.b64decode(img_b64))
                        
                        size_kb = os.path.getsize(fpath) // 1024
                        return {
                            "ok": True,
                            "imagem_url": f"/static/generated_images/{fname}",
                            "modelo": modelo_id,
                            "tamanho_kb": size_kb
                        }
                
                return {"ok": False, "erro": "Sem predições na resposta"}
            
            elif resp.status_code == 400:
                error_msg = resp.json().get("error", {}).get("message", "")
                return {"ok": False, "erro": error_msg}
            
            else:
                return {"ok": False, "erro": f"HTTP {resp.status_code}: {resp.text[:200]}"}
                
    except Exception as e:
        return {"ok": False, "erro": str(e)}


async def _fallback_pixabay(prompt: str) -> dict:
    """Busca imagem no Pixabay como fallback"""
    if not PIXABAY_API_KEY:
        return {"ok": False, "erro": "Pixabay API key não configurada"}
    try:
        # Extrair palavras-chave do prompt
        keywords = " ".join(prompt.split()[:5])
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://pixabay.com/api/", params={
                "key": PIXABAY_API_KEY,
                "q": keywords,
                "per_page": 5,
                "image_type": "photo",
                "safesearch": "true"
            })
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    import random
                    img = random.choice(hits[:3])
                    return {
                        "ok": True,
                        "imagem_url": img.get("largeImageURL", img.get("webformatURL")),
                        "modelo": "pixabay-fallback",
                        "texto": f"Imagem de stock: {img.get('tags', '')}",
                        "fonte": "Pixabay"
                    }
        return {"ok": False, "erro": "Nenhuma imagem encontrada"}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


async def _fallback_pexels(prompt: str) -> dict:
    """Busca imagem no Pexels como fallback"""
    if not PEXELS_API_KEY:
        return {"ok": False, "erro": "Pexels API key não configurada"}
    try:
        keywords = " ".join(prompt.split()[:5])
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get("https://api.pexels.com/v1/search", 
                params={"query": keywords, "per_page": 5},
                headers={"Authorization": PEXELS_API_KEY}
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos:
                    import random
                    img = random.choice(photos[:3])
                    return {
                        "ok": True,
                        "imagem_url": img.get("src", {}).get("large2x", img.get("src", {}).get("large")),
                        "modelo": "pexels-fallback",
                        "texto": f"Foto: {img.get('alt', '')}",
                        "fonte": "Pexels"
                    }
        return {"ok": False, "erro": "Nenhuma imagem encontrada"}
    except Exception as e:
        return {"ok": False, "erro": str(e)}


# ============================================================
# ENDPOINTS
# ============================================================

@router.get("/modelos")
async def listar_modelos():
    """Lista todos os modelos disponíveis"""
    return {"modelos": GOOGLE_MODELS, "estilos": list(ESTILOS.keys())}


@router.post("/gerar")
async def gerar_imagem(
    prompt: str = Query(..., min_length=3, max_length=2000),
    modelo: str = Query(default="nano-banana-pro-preview"),
    estilo: str = Query(default="realista"),
    cascade: bool = Query(default=True)
):
    """Gera uma imagem com o modelo escolhido. Se cascade=True, tenta outros modelos em caso de falha."""
    
    resultados = []
    
    # Encontrar modelo solicitado
    modelo_info = None
    for m in GOOGLE_MODELS:
        if m["id"] == modelo:
            modelo_info = m
            break
    
    if not modelo_info:
        modelo_info = GOOGLE_MODELS[0]
        modelo = modelo_info["id"]
    
    # Tentar modelo principal
    print(f"[ImageGen] Gerando com {modelo_info['nome']} ({modelo})...")
    
    if modelo_info["tipo"] == "predict":
        resultado = await _gerar_com_imagen(prompt, modelo, estilo)
    else:
        resultado = await _gerar_com_gemini(prompt, modelo, estilo)
    
    if resultado["ok"]:
        resultado["modelo_nome"] = modelo_info["nome"]
        resultado["modelo_emoji"] = modelo_info["emoji"]
        _registrar(prompt, resultado, estilo)
        return resultado
    
    resultados.append({"modelo": modelo_info["nome"], "erro": resultado.get("erro", "Falha")})
    
    # Cascade: tentar outros modelos
    if cascade:
        for m in GOOGLE_MODELS:
            if m["id"] == modelo:
                continue
            
            print(f"[ImageGen] Tentando fallback: {m['nome']}...")
            
            if m["tipo"] == "predict":
                resultado = await _gerar_com_imagen(prompt, m["id"], estilo)
            else:
                resultado = await _gerar_com_gemini(prompt, m["id"], estilo)
            
            if resultado["ok"]:
                resultado["modelo_nome"] = m["nome"]
                resultado["modelo_emoji"] = m["emoji"]
                resultado["fallback"] = True
                _registrar(prompt, resultado, estilo)
                return resultado
            
            resultados.append({"modelo": m["nome"], "erro": resultado.get("erro", "Falha")})
        
        # Fallback final: Pixabay/Pexels
        print("[ImageGen] Tentando fallback Pixabay...")
        resultado = await _fallback_pixabay(prompt)
        if resultado["ok"]:
            resultado["fallback"] = True
            resultado["modelo_nome"] = "Pixabay Stock"
            resultado["modelo_emoji"] = "📷"
            _registrar(prompt, resultado, estilo)
            return resultado
        
        print("[ImageGen] Tentando fallback Pexels...")
        resultado = await _fallback_pexels(prompt)
        if resultado["ok"]:
            resultado["fallback"] = True
            resultado["modelo_nome"] = "Pexels Stock"
            resultado["modelo_emoji"] = "📸"
            _registrar(prompt, resultado, estilo)
            return resultado
    
    STATS["erros"] += 1
    return {
        "ok": False,
        "erro": "Nenhum modelo conseguiu gerar a imagem",
        "tentativas": resultados
    }


@router.get("/historico")
async def ver_historico(limite: int = Query(default=50, le=200)):
    """Retorna histórico de imagens geradas"""
    return {"historico": HISTORICO[-limite:], "total": len(HISTORICO)}


@router.get("/stats")
async def ver_stats():
    """Estatísticas de geração"""
    return STATS


@router.get("/galeria")
async def ver_galeria():
    """Lista todas as imagens salvas localmente"""
    imagens = []
    if os.path.exists(IMG_DIR):
        for fname in sorted(os.listdir(IMG_DIR), reverse=True):
            if fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
                fpath = os.path.join(IMG_DIR, fname)
                imagens.append({
                    "url": f"/static/generated_images/{fname}",
                    "nome": fname,
                    "tamanho_kb": os.path.getsize(fpath) // 1024,
                    "criado_em": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat()
                })
    return {"imagens": imagens, "total": len(imagens)}


def _registrar(prompt, resultado, estilo):
    """Registra geração no histórico"""
    STATS["total_geradas"] += 1
    modelo_nome = resultado.get("modelo_nome", resultado.get("modelo", "?"))
    STATS["por_modelo"][modelo_nome] = STATS["por_modelo"].get(modelo_nome, 0) + 1
    
    HISTORICO.append({
        "id": uuid.uuid4().hex[:8],
        "prompt": prompt,
        "estilo": estilo,
        "modelo": modelo_nome,
        "emoji": resultado.get("modelo_emoji", "🖼️"),
        "imagem_url": resultado.get("imagem_url", ""),
        "fallback": resultado.get("fallback", False),
        "fonte": resultado.get("fonte", "Google AI"),
        "criado_em": datetime.now().isoformat()
    })
    
    if len(HISTORICO) > 500:
        HISTORICO[:] = HISTORICO[-300:]


print("[ImageGen] 🎨 AI Image Generator carregado - Google Gemini / Banana Pro / Imagen 4.0")
