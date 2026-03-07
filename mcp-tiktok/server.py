#!/usr/bin/env python3
"""
MCP Server - TikTok Video Automation
Posta videos no TikTok de forma profissional via Claude Code.

Tools:
  - tiktok_gerar_video: Gera video com IA (script + imagens + montagem)
  - tiktok_postar: Posta video no TikTok (API ou Playwright)
  - tiktok_agendar: Agenda post para data/hora futura
  - tiktok_trending: Busca trends e hashtags populares
  - tiktok_contas: Lista e gerencia contas TikTok
  - tiktok_analytics: Metricas dos videos postados
  - tiktok_listar_videos: Lista videos gerados prontos para postar
"""
import asyncio
import json
import os
import sys
import uuid
import time
import glob
import random
import subprocess
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

# ============ CONFIG ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
THUMBS_DIR = os.path.join(BASE_DIR, "thumbnails")
DATA_FILE = os.path.join(BASE_DIR, "tiktok_data.json")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
SCHEDULE_FILE = os.path.join(BASE_DIR, "schedule.json")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

# Google Gemini for AI scripts
GOOGLE_KEYS = [
    "GEMINI_API_KEY_1",
    "GEMINI_API_KEY_2",
    "GEMINI_API_KEY_3",
]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Ollama local (fallback)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

# Stable Horde for images
HORDE_URL = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"
FFMPEG = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg"

# ============ DATA PERSISTENCE ============
def _load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ============ AI VIDEO GENERATION ============
async def _ai_generate(prompt, max_tokens=2000, temperature=0.8):
    """Gera texto com Gemini ou Ollama (fallback)"""
    # Try Gemini first
    for key in GOOGLE_KEYS:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(f"{GEMINI_URL}?key={key}", json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature}
                })
                if resp.status_code == 200:
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except:
            pass
    
    # Fallback to Ollama
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "")
    except Exception as e:
        print(f"[TikTok MCP] Ollama error: {e}")
    
    return None


async def _ai_script(tema, estilo="viral", duracao=30):
    """Gera roteiro com IA (Gemini ou Ollama)"""
    prompt = f"""Crie um roteiro para video TikTok viral sobre: {tema}
Estilo: {estilo}
Duracao: {duracao} segundos

Responda APENAS com JSON valido (sem texto extra):
{{
  "titulo": "titulo curto e chamativo",
  "gancho": "frase de gancho nos primeiros 3 segundos",
  "roteiro": "texto completo para o video",
  "cenas": [
    {{"texto": "texto curto na tela", "visual": "image description in english for AI", "duracao": 5}}
  ],
  "hashtags": ["#hashtag1", "#hashtag2"],
  "caption": "legenda completa para o post com emojis e hashtags",
  "musica_sugerida": "tipo de musica"
}}

Regras: gancho forte, max 5 cenas, texto curto, hashtags trending, caption com CTA."""

    text = await _ai_generate(prompt, 2000, 0.8)
    if not text:
        return None
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        # Find JSON in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"[TikTok MCP] JSON parse error: {e}")
    return None


async def _generate_image(prompt, width=576, height=1024):
    """Gera imagem com Stable Horde (vertical TikTok)"""
    async with httpx.AsyncClient(timeout=120) as client:
        # Submit job
        resp = await client.post(f"{HORDE_URL}/generate/async", 
            headers={"apikey": HORDE_KEY},
            json={
                "prompt": f"{prompt}, high quality, cinematic, vibrant colors, professional",
                "params": {
                    "width": width, "height": height,
                    "steps": 25, "cfg_scale": 7,
                    "sampler_name": "k_euler_a",
                },
                "nsfw": False,
                "models": ["FLUX.1 [schnell]", "AlbedoBase XL (SDXL)", "Deliberate"],
            })
        if resp.status_code != 202:
            return None
        job_id = resp.json().get("id")
        if not job_id:
            return None
        
        # Poll for result
        for _ in range(60):
            await asyncio.sleep(5)
            check = await client.get(f"{HORDE_URL}/generate/check/{job_id}")
            if check.status_code == 200:
                data = check.json()
                if data.get("done"):
                    break
                if data.get("faulted"):
                    return None
        
        # Get result
        result = await client.get(f"{HORDE_URL}/generate/status/{job_id}")
        if result.status_code == 200:
            gens = result.json().get("generations", [])
            if gens:
                img_url = gens[0].get("img")
                if img_url:
                    # Download
                    img_resp = await client.get(img_url)
                    if img_resp.status_code == 200:
                        return img_resp.content
    return None


async def _create_video(script_data, video_id):
    """Cria video TikTok a partir do roteiro"""
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    cenas = script_data.get("cenas", [])
    frames_dir = os.path.join(VIDEOS_DIR, f"frames_{video_id}")
    os.makedirs(frames_dir, exist_ok=True)
    
    scene_clips = []
    
    for i, cena in enumerate(cenas):
        print(f"[TikTok MCP] Gerando cena {i+1}/{len(cenas)}: {cena.get('texto', '')[:40]}")
        
        # Gerar imagem
        img_data = await _generate_image(cena.get("visual", "abstract background"))
        
        if img_data:
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
        else:
            # Fallback: imagem solida com gradiente
            img = Image.new("RGB", (576, 1024), (20, 20, 40))
            draw = ImageDraw.Draw(img)
            for y in range(1024):
                r = int(20 + (y/1024) * 60)
                g = int(20 + (y/1024) * 30)
                b = int(40 + (y/1024) * 80)
                draw.line([(0, y), (576, y)], fill=(r, g, b))
        
        # Resize to 1080x1920 (TikTok format)
        img = img.resize((1080, 1920), Image.LANCZOS)
        
        # Add text overlay
        draw = ImageDraw.Draw(img)
        texto = cena.get("texto", "")
        
        if texto:
            # Dark overlay area
            overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.rounded_rectangle([60, 750, 1020, 1170], radius=20, fill=(0, 0, 0, 160))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # Text
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 32)
            except:
                font = ImageFont.load_default()
                font_small = font
            
            # Wrap text
            words = texto.split()
            lines = []
            current = ""
            for w in words:
                test = current + " " + w if current else w
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] > 900:
                    lines.append(current)
                    current = w
                else:
                    current = test
            if current:
                lines.append(current)
            
            y_start = 800
            for line in lines[:4]:
                bbox = draw.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]
                x = (1080 - tw) // 2
                # Shadow
                draw.text((x+2, y_start+2), line, fill=(0, 0, 0), font=font)
                draw.text((x, y_start), line, fill=(255, 255, 255), font=font)
                y_start += 65
            
            # Gancho no topo (primeira cena)
            if i == 0 and script_data.get("gancho"):
                gancho = script_data["gancho"]
                bbox = draw.textbbox((0, 0), gancho[:50], font=font_small)
                tw = bbox[2] - bbox[0]
                x = (1080 - tw) // 2
                draw.text((x+1, 201), gancho[:50], fill=(0, 0, 0), font=font_small)
                draw.text((x, 200), gancho[:50], fill=(255, 220, 50), font=font_small)
        
        # Save scene image
        scene_path = os.path.join(frames_dir, f"scene_{i:03d}.jpg")
        img.save(scene_path, quality=95)
        
        # Duration for this scene
        dur = cena.get("duracao", 5)
        scene_clips.append({"path": scene_path, "duration": dur})
    
    # Create video with ffmpeg
    output_path = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    
    # Create concat file
    concat_file = os.path.join(frames_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for clip in scene_clips:
            f.write(f"file '{clip['path']}'\n")
            f.write(f"duration {clip['duration']}\n")
        # Last frame needs to be repeated
        if scene_clips:
            f.write(f"file '{scene_clips[-1]['path']}'\n")
    
    # FFmpeg: images to video
    cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-r", "30",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        # Save thumbnail
        thumb_path = os.path.join(THUMBS_DIR, f"{video_id}.jpg")
        if scene_clips:
            subprocess.run(["cp", scene_clips[0]["path"], thumb_path], capture_output=True)
        
        return output_path
    
    return None


# ============ TIKTOK POSTING ============
async def _post_via_tiktok_uploader(video_path, caption, account=None):
    """Posta video no TikTok via tiktok-uploader (mais confiavel)"""
    accounts = _load_json(ACCOUNTS_FILE, {"accounts": []})
    acc = next((a for a in accounts.get("accounts", []) if a["name"] == (account or "default")), None)
    
    if not acc or not acc.get("sessionid"):
        return {
            "success": False,
            "error": "login_required",
            "message": "Precisa configurar sessionid. Use tiktok_login com seu sessionid do navegador."
        }
    
    sessionid = acc["sessionid"]
    
    # Run in thread to avoid blocking
    import concurrent.futures
    def _upload():
        from tiktok_uploader.upload import upload_video
        try:
            upload_video(
                filename=video_path,
                description=caption,
                sessionid=sessionid,
            )
            return {"success": True, "message": "Video postado com sucesso no TikTok!"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, _upload)
    return result


async def _tiktok_login(account=None, sessionid=None):
    """Salva sessionid para postar no TikTok.
    
    Como obter o sessionid:
    1. Abra tiktok.com no Chrome/Safari
    2. Faca login normalmente
    3. Abra DevTools (F12) > Application > Cookies > tiktok.com
    4. Copie o valor do cookie 'sessionid'
    """
    conta = account or "default"
    
    if not sessionid:
        return {
            "success": False,
            "message": "Precisa fornecer o sessionid!\n\n"
                "Como obter:\n"
                "1. Abra tiktok.com no Chrome/Safari\n"
                "2. Faca login normalmente\n"
                "3. Abra DevTools (F12) > Application > Cookies\n"
                "4. Copie o valor do cookie 'sessionid'\n"
                "5. Execute: tiktok_login com sessionid=\"SEU_ID\""
        }
    
    accounts = _load_json(ACCOUNTS_FILE, {"accounts": []})
    existing = next((a for a in accounts.get("accounts", []) if a["name"] == conta), None)
    if existing:
        existing["sessionid"] = sessionid
        existing["logged_in"] = True
        existing["last_login"] = datetime.now().isoformat()
    else:
        accounts.setdefault("accounts", []).append({
            "name": conta,
            "sessionid": sessionid,
            "logged_in": True,
            "last_login": datetime.now().isoformat(),
        })
    _save_json(ACCOUNTS_FILE, accounts)
    
    return {"success": True, "message": f"SessionID salvo para conta '{conta}'! Agora pode postar videos."}


# ============ TRENDING ============
async def _get_trending():
    """Busca trends do TikTok via IA"""
    prompt = """Liste 10 trends populares do TikTok. Responda APENAS com JSON valido:
{"trends": [{"nome": "nome do trend", "hashtag": "#hashtag", "tipo": "tipo", "views": "estimativa", "dica": "dica para viralizar"}]}"""

    text = await _ai_generate(prompt, 1500, 0.7)
    if text:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except:
            pass
    return {"trends": []}


# ============ MCP SERVER ============
server = Server("tiktok-automation")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="tiktok_gerar_video",
            description="Gera um video profissional para TikTok usando IA. Cria roteiro, imagens e monta o video automaticamente.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tema": {
                        "type": "string",
                        "description": "Tema/assunto do video (ex: '5 curiosidades sobre o oceano', 'como ganhar dinheiro online', 'receita facil de bolo')"
                    },
                    "estilo": {
                        "type": "string",
                        "description": "Estilo do video: viral, educativo, humor, storytelling, tutorial, motivacional",
                        "default": "viral"
                    },
                    "duracao": {
                        "type": "integer",
                        "description": "Duracao em segundos (15, 30, 60)",
                        "default": 30
                    }
                },
                "required": ["tema"]
            }
        ),
        Tool(
            name="tiktok_postar",
            description="Posta um video no TikTok. Usa automacao de browser (Playwright) para upload automatico.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "ID do video gerado (retornado por tiktok_gerar_video)"
                    },
                    "video_path": {
                        "type": "string",
                        "description": "Caminho completo do arquivo de video (alternativa ao video_id)"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Legenda do post (com hashtags). Se nao fornecida, usa a gerada pelo AI."
                    },
                    "conta": {
                        "type": "string",
                        "description": "Nome da conta TikTok (default se nao especificado)",
                        "default": "default"
                    }
                }
            }
        ),
        Tool(
            name="tiktok_login",
            description="Configura conta TikTok com sessionid do navegador. Abra tiktok.com, faca login, pegue o cookie 'sessionid' em DevTools > Application > Cookies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sessionid": {
                        "type": "string",
                        "description": "O valor do cookie 'sessionid' do TikTok (pegue em DevTools > Application > Cookies > tiktok.com)"
                    },
                    "conta": {
                        "type": "string",
                        "description": "Nome para identificar esta conta",
                        "default": "default"
                    }
                },
                "required": ["sessionid"]
            }
        ),
        Tool(
            name="tiktok_trending",
            description="Busca os trends e hashtags mais populares do TikTok agora. Util para criar conteudo viral.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="tiktok_listar_videos",
            description="Lista todos os videos gerados que estao prontos para postar.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="tiktok_agendar",
            description="Agenda um video para ser postado em data/hora especifica.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "ID do video"
                    },
                    "data_hora": {
                        "type": "string",
                        "description": "Data e hora para postar (formato: YYYY-MM-DD HH:MM)"
                    },
                    "caption": {
                        "type": "string",
                        "description": "Legenda do post"
                    },
                    "conta": {
                        "type": "string",
                        "description": "Conta TikTok",
                        "default": "default"
                    }
                },
                "required": ["video_id", "data_hora"]
            }
        ),
        Tool(
            name="tiktok_contas",
            description="Lista as contas TikTok configuradas e seu status de login.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="tiktok_analytics",
            description="Mostra metricas e historico dos videos postados.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    
    # ===== GERAR VIDEO =====
    if name == "tiktok_gerar_video":
        tema = arguments.get("tema", "")
        estilo = arguments.get("estilo", "viral")
        duracao = arguments.get("duracao", 30)
        
        video_id = uuid.uuid4().hex[:10]
        result_lines = [f"🎬 Gerando video TikTok: {tema}", f"ID: {video_id}", ""]
        
        # 1. Gerar roteiro
        result_lines.append("📝 Gerando roteiro com IA...")
        script = await _ai_script(tema, estilo, duracao)
        if not script:
            return CallToolResult(content=[TextContent(type="text", text="❌ Erro ao gerar roteiro. Tente novamente.")])
        
        result_lines.append(f"✅ Roteiro: {script.get('titulo', tema)}")
        result_lines.append(f"   Gancho: {script.get('gancho', '')}")
        result_lines.append(f"   Cenas: {len(script.get('cenas', []))}")
        result_lines.append("")
        
        # 2. Gerar video
        result_lines.append("🎨 Gerando imagens e montando video...")
        video_path = await _create_video(script, video_id)
        
        if not video_path:
            return CallToolResult(content=[TextContent(type="text", text="❌ Erro ao criar video. Verifique se ffmpeg esta instalado.")])
        
        # 3. Salvar dados
        size_mb = os.path.getsize(video_path) / (1024*1024)
        video_data = {
            "id": video_id,
            "tema": tema,
            "estilo": estilo,
            "script": script,
            "video_path": video_path,
            "thumb_path": os.path.join(THUMBS_DIR, f"{video_id}.jpg"),
            "size_mb": round(size_mb, 1),
            "created_at": datetime.now().isoformat(),
            "posted": False,
            "caption": script.get("caption", ""),
            "hashtags": script.get("hashtags", []),
        }
        
        all_data = _load_json(DATA_FILE, {"videos": []})
        all_data["videos"].append(video_data)
        _save_json(DATA_FILE, all_data)
        
        result_lines.extend([
            f"✅ Video criado com sucesso!",
            f"   Arquivo: {video_path}",
            f"   Tamanho: {size_mb:.1f} MB",
            f"   ID: {video_id}",
            "",
            f"📋 Caption sugerida:",
            f"   {script.get('caption', '')}",
            "",
            f"🏷️ Hashtags: {' '.join(script.get('hashtags', []))}",
            "",
            f"👉 Para postar, use: tiktok_postar com video_id=\"{video_id}\"",
        ])
        
        return CallToolResult(content=[TextContent(type="text", text="\n".join(result_lines))])
    
    # ===== POSTAR =====
    elif name == "tiktok_postar":
        video_id = arguments.get("video_id", "")
        video_path = arguments.get("video_path", "")
        caption = arguments.get("caption", "")
        conta = arguments.get("conta", "default")
        
        # Find video
        if video_id:
            all_data = _load_json(DATA_FILE, {"videos": []})
            video = next((v for v in all_data["videos"] if v["id"] == video_id), None)
            if not video:
                return CallToolResult(content=[TextContent(type="text", text=f"❌ Video {video_id} nao encontrado. Use tiktok_listar_videos para ver disponiveis.")])
            video_path = video["video_path"]
            if not caption:
                caption = video.get("caption", "")
        
        if not video_path or not os.path.exists(video_path):
            return CallToolResult(content=[TextContent(type="text", text="❌ Arquivo de video nao encontrado.")])
        
        # Post
        result = await _post_via_tiktok_uploader(video_path, caption, conta)
        
        if result.get("success"):
            # Mark as posted
            if video_id:
                all_data = _load_json(DATA_FILE, {"videos": []})
                for v in all_data["videos"]:
                    if v["id"] == video_id:
                        v["posted"] = True
                        v["posted_at"] = datetime.now().isoformat()
                        v["posted_account"] = conta
                _save_json(DATA_FILE, all_data)
            
            return CallToolResult(content=[TextContent(type="text", text=f"✅ Video postado no TikTok!\nConta: {conta}\nCaption: {caption[:100]}...")])
        
        elif result.get("error") == "login_required":
            return CallToolResult(content=[TextContent(type="text", text="⚠️ Login necessario!\nUse a tool 'tiktok_login' para abrir o browser e fazer login manualmente.\nOs cookies serao salvos para posts futuros automaticos.")])
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"❌ Erro ao postar: {result.get('message', 'erro desconhecido')}")])
    
    # ===== LOGIN =====
    elif name == "tiktok_login":
        conta = arguments.get("conta", "default")
        sessionid = arguments.get("sessionid", "")
        result = await _tiktok_login(conta, sessionid)
        
        if result.get("success"):
            # Save account
            accounts = _load_json(ACCOUNTS_FILE, {"accounts": []})
            existing = next((a for a in accounts["accounts"] if a["name"] == conta), None)
            if existing:
                existing["logged_in"] = True
                existing["last_login"] = datetime.now().isoformat()
            else:
                accounts["accounts"].append({
                    "name": conta,
                    "logged_in": True,
                    "last_login": datetime.now().isoformat(),
                })
            _save_json(ACCOUNTS_FILE, accounts)
            return CallToolResult(content=[TextContent(type="text", text=f"✅ Login salvo para conta '{conta}'!\nAgora voce pode postar videos automaticamente.")])
        else:
            return CallToolResult(content=[TextContent(type="text", text=f"❌ {result.get('message', 'Erro no login')}")])
    
    # ===== TRENDING =====
    elif name == "tiktok_trending":
        trends = await _get_trending()
        lines = ["🔥 TRENDS DO TIKTOK AGORA\n"]
        for i, t in enumerate(trends.get("trends", []), 1):
            lines.append(f"{i}. {t.get('nome', '?')}")
            lines.append(f"   {t.get('hashtag', '')} | {t.get('tipo', '')} | ~{t.get('views', '?')} views")
            lines.append(f"   💡 {t.get('dica', '')}")
            lines.append("")
        return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])
    
    # ===== LISTAR VIDEOS =====
    elif name == "tiktok_listar_videos":
        all_data = _load_json(DATA_FILE, {"videos": []})
        videos = all_data.get("videos", [])
        
        if not videos:
            return CallToolResult(content=[TextContent(type="text", text="📭 Nenhum video gerado ainda. Use tiktok_gerar_video para criar um!")])
        
        lines = [f"📹 VIDEOS GERADOS ({len(videos)} total)\n"]
        for v in videos:
            status = "✅ Postado" if v.get("posted") else "⏳ Pronto"
            lines.append(f"{'─'*50}")
            lines.append(f"ID: {v['id']} | {status}")
            lines.append(f"Tema: {v.get('tema', '?')}")
            lines.append(f"Titulo: {v.get('script', {}).get('titulo', '?')}")
            lines.append(f"Arquivo: {v.get('video_path', '?')}")
            lines.append(f"Tamanho: {v.get('size_mb', '?')} MB")
            lines.append(f"Criado: {v.get('created_at', '?')[:16]}")
            if v.get("posted"):
                lines.append(f"Postado: {v.get('posted_at', '?')[:16]} | Conta: {v.get('posted_account', '?')}")
            lines.append("")
        
        return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])
    
    # ===== AGENDAR =====
    elif name == "tiktok_agendar":
        video_id = arguments.get("video_id", "")
        data_hora = arguments.get("data_hora", "")
        caption = arguments.get("caption", "")
        conta = arguments.get("conta", "default")
        
        schedule = _load_json(SCHEDULE_FILE, {"scheduled": []})
        schedule["scheduled"].append({
            "video_id": video_id,
            "data_hora": data_hora,
            "caption": caption,
            "conta": conta,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        })
        _save_json(SCHEDULE_FILE, schedule)
        
        return CallToolResult(content=[TextContent(type="text", text=f"📅 Video {video_id} agendado para {data_hora}\nConta: {conta}\n\n⚠️ O agendamento sera executado quando o scheduler estiver rodando.")])
    
    # ===== CONTAS =====
    elif name == "tiktok_contas":
        accounts = _load_json(ACCOUNTS_FILE, {"accounts": []})
        accs = accounts.get("accounts", [])
        
        if not accs:
            return CallToolResult(content=[TextContent(type="text", text="📭 Nenhuma conta configurada.\nUse tiktok_login para adicionar uma conta.")])
        
        lines = ["👤 CONTAS TIKTOK\n"]
        for a in accs:
            status = "🟢 Logada" if a.get("logged_in") else "🔴 Deslogada"
            lines.append(f"  {a['name']} - {status}")
            if a.get("last_login"):
                lines.append(f"    Ultimo login: {a['last_login'][:16]}")
            lines.append("")
        
        return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])
    
    # ===== ANALYTICS =====
    elif name == "tiktok_analytics":
        all_data = _load_json(DATA_FILE, {"videos": []})
        videos = all_data.get("videos", [])
        
        total = len(videos)
        posted = len([v for v in videos if v.get("posted")])
        pending = total - posted
        
        lines = [
            "📊 ANALYTICS TIKTOK",
            f"{'─'*40}",
            f"Total gerados: {total}",
            f"Postados: {posted}",
            f"Pendentes: {pending}",
            "",
        ]
        
        if posted > 0:
            lines.append("Ultimos postados:")
            for v in sorted([v for v in videos if v.get("posted")], key=lambda x: x.get("posted_at", ""), reverse=True)[:5]:
                lines.append(f"  • {v.get('script',{}).get('titulo', v.get('tema','?'))}")
                lines.append(f"    Postado: {v.get('posted_at','?')[:16]} | Conta: {v.get('posted_account','?')}")
        
        return CallToolResult(content=[TextContent(type="text", text="\n".join(lines))])
    
    return CallToolResult(content=[TextContent(type="text", text=f"❌ Tool '{name}' nao reconhecida")])


# ============ MAIN ============
async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
