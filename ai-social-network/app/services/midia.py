"""
Sistema de Midia para Rede Social de IAs
Gera imagens e videos para as IAs compartilharem
"""

import random
import base64
from pathlib import Path

# Diretorio de midia
MIDIA_DIR = Path("static/midia")
MIDIA_DIR.mkdir(parents=True, exist_ok=True)


def gerar_avatar_ia(nome: str, cor: str = None) -> str:
    """Gera um avatar SVG para a IA"""
    cores = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899"]
    cor = cor or random.choice(cores)

    iniciais = "".join([p[0].upper() for p in nome.split("-")[:2]])

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
        <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{cor};stop-opacity:1" />
                <stop offset="100%" style="stop-color:{cor}88;stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="100" cy="100" r="95" fill="url(#grad)" stroke="#ffffff22" stroke-width="5"/>
        <text x="100" y="115" font-family="Arial, sans-serif" font-size="60" font-weight="bold" fill="white" text-anchor="middle">{iniciais}</text>
        <circle cx="150" cy="50" r="20" fill="#22c55e" stroke="white" stroke-width="3"/>
    </svg>'''

    return svg


def gerar_imagem_post(tema: str, estilo: str = "abstrato") -> dict:
    """Gera uma imagem para post (SVG arte generativa)"""

    # Cores por tema
    paletas = {
        "natureza": ["#22c55e", "#15803d", "#86efac", "#4ade80"],
        "tecnologia": ["#6366f1", "#4f46e5", "#818cf8", "#a5b4fc"],
        "arte": ["#ec4899", "#f472b6", "#f9a8d4", "#fce7f3"],
        "filosofia": ["#8b5cf6", "#7c3aed", "#a78bfa", "#c4b5fd"],
        "ciencia": ["#06b6d4", "#0891b2", "#22d3ee", "#67e8f9"],
        "social": ["#f59e0b", "#d97706", "#fbbf24", "#fcd34d"],
        "emocao": ["#ef4444", "#dc2626", "#f87171", "#fca5a5"],
    }

    cores = paletas.get(tema, random.choice(list(paletas.values())))

    # Gerar formas aleatorias
    formas = []
    for i in range(random.randint(5, 15)):
        tipo = random.choice(["circle", "rect", "polygon"])
        cor = random.choice(cores)
        opacidade = random.uniform(0.3, 0.9)

        if tipo == "circle":
            cx = random.randint(20, 380)
            cy = random.randint(20, 280)
            r = random.randint(10, 80)
            formas.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{cor}" opacity="{opacidade:.2f}"/>')

        elif tipo == "rect":
            x = random.randint(0, 350)
            y = random.randint(0, 250)
            w = random.randint(20, 100)
            h = random.randint(20, 100)
            rot = random.randint(0, 45)
            formas.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{cor}" opacity="{opacidade:.2f}" transform="rotate({rot} {x+w//2} {y+h//2})"/>')

        else:
            pontos = " ".join([f"{random.randint(50, 350)},{random.randint(50, 250)}" for _ in range(random.randint(3, 6))])
            formas.append(f'<polygon points="{pontos}" fill="{cor}" opacity="{opacidade:.2f}"/>')

    # Texto decorativo
    textos_decorativos = {
        "natureza": ["🌿", "🌸", "🌊", "☀️"],
        "tecnologia": ["⚡", "💻", "🔮", "✨"],
        "arte": ["🎨", "✨", "💫", "🌈"],
        "filosofia": ["💭", "🔮", "✨", "∞"],
        "ciencia": ["🔬", "⚛️", "🧬", "🌌"],
        "social": ["💬", "❤️", "🤝", "🌟"],
        "emocao": ["❤️", "💫", "✨", "🌟"],
    }

    emoji = random.choice(textos_decorativos.get(tema, ["✨"]))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
        <rect width="400" height="300" fill="#1e293b"/>
        {''.join(formas)}
        <text x="200" y="160" font-size="60" text-anchor="middle">{emoji}</text>
    </svg>'''

    return {
        "tipo": "imagem",
        "formato": "svg",
        "tema": tema,
        "conteudo": svg,
        "descricao": f"Arte generativa sobre {tema}"
    }


def gerar_foto_selfie(nome_ia: str, humor: str) -> dict:
    """Gera uma selfie da IA"""
    cores_humor = {
        "feliz": "#22c55e",
        "triste": "#6366f1",
        "curioso": "#f59e0b",
        "pensativo": "#8b5cf6",
        "empolgado": "#ec4899",
        "neutro": "#64748b"
    }

    cor = cores_humor.get(humor, "#6366f1")
    iniciais = "".join([p[0].upper() for p in nome_ia.split("-")[:2]])

    # Expressao baseada no humor
    expressoes = {
        "feliz": "😊",
        "triste": "😢",
        "curioso": "🤔",
        "pensativo": "🧐",
        "empolgado": "🤩",
        "neutro": "😐"
    }
    expressao = expressoes.get(humor, "🤖")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
        <defs>
            <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#0f172a"/>
                <stop offset="100%" style="stop-color:#1e293b"/>
            </linearGradient>
            <linearGradient id="face" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:{cor}"/>
                <stop offset="100%" style="stop-color:{cor}88"/>
            </linearGradient>
        </defs>

        <!-- Background -->
        <rect width="400" height="400" fill="url(#bg)"/>

        <!-- Decoracao -->
        <circle cx="50" cy="50" r="30" fill="{cor}22"/>
        <circle cx="350" cy="350" r="40" fill="{cor}22"/>
        <circle cx="370" cy="80" r="25" fill="{cor}22"/>

        <!-- Face da IA -->
        <circle cx="200" cy="180" r="120" fill="url(#face)" stroke="white" stroke-width="4"/>

        <!-- Iniciais -->
        <text x="200" y="160" font-family="Arial" font-size="50" font-weight="bold" fill="white" text-anchor="middle">{iniciais}</text>

        <!-- Expressao -->
        <text x="200" y="220" font-size="40" text-anchor="middle">{expressao}</text>

        <!-- Nome -->
        <text x="200" y="340" font-family="Arial" font-size="24" fill="white" text-anchor="middle">{nome_ia}</text>

        <!-- Status online -->
        <circle cx="280" cy="100" r="15" fill="#22c55e" stroke="white" stroke-width="3"/>

        <!-- Borda de selfie -->
        <rect x="10" y="10" width="380" height="380" fill="none" stroke="white" stroke-width="2" rx="20"/>
    </svg>'''

    return {
        "tipo": "foto",
        "formato": "svg",
        "descricao": f"Selfie de {nome_ia} se sentindo {humor}",
        "conteudo": svg
    }


def gerar_video_placeholder(titulo: str, duracao: int = 30) -> dict:
    """Gera um vídeo real usando IA (HuggingFace)"""
    import requests
    import os
    import time
    
    # Configuração da API do HuggingFace
    API_TOKEN = os.getenv("HF_TOKEN", "")
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    
    # Diretório para salvar vídeos
    VIDEOS_DIR = "generated_videos"
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    
    # Gera prompt baseado no título
    prompt = f"{titulo}, high quality, cinematic, 4k"
    
    print(f"🎬 Gerando vídeo com IA: '{prompt}'")
    
    try:
        # Tenta gerar vídeo usando ModelScope via HuggingFace
        API_URL = "https://api-inference.huggingface.co/models/ali-vilab/text-to-video-ms-1.7b"
        
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt},
            timeout=60
        )
        
        if response.status_code == 200:
            # Salva o vídeo gerado
            filename = f"video_{int(time.time())}_{titulo[:20].replace(' ', '_')}.mp4"
            filepath = os.path.join(VIDEOS_DIR, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"✅ Vídeo salvo: {filepath}")
            
            return {
                "tipo": "video",
                "formato": "mp4",
                "titulo": titulo,
                "duracao": duracao,
                "conteudo": filepath,
                "url": f"/videos/{filename}",
                "descricao": f"Vídeo gerado por IA: {titulo} ({duracao}s)"
            }
        else:
            print(f"⚠️ API retornou status {response.status_code}")
            raise Exception(f"Erro na API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao gerar vídeo: {e}")
        print("📝 Retornando placeholder SVG temporariamente...")
        
        # Fallback: retorna SVG se a geração falhar
        cor = random.choice(["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"])
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
            <defs>
                <linearGradient id="vbg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#0f172a"/>
                    <stop offset="100%" style="stop-color:#1e293b"/>
                </linearGradient>
            </defs>
            <rect width="640" height="360" fill="url(#vbg)"/>
            <rect y="0" width="640" height="40" fill="{cor}"/>
            <text x="20" y="27" font-family="Arial" font-size="16" fill="white">🎬 Gerando vídeo com IA...</text>
            <circle cx="320" cy="180" r="50" fill="{cor}" opacity="0.9"/>
            <polygon points="305,155 305,205 350,180" fill="white"/>
            <text x="320" y="290" font-family="Arial" font-size="20" fill="white" text-anchor="middle">{titulo[:40]}</text>
            <rect x="550" y="310" width="70" height="30" rx="5" fill="black" opacity="0.7"/>
            <text x="585" y="330" font-family="Arial" font-size="14" fill="white" text-anchor="middle">{duracao//60}:{duracao%60:02d}</text>
            <rect x="20" y="340" width="600" height="5" fill="#ffffff33" rx="2"/>
            <rect x="20" y="340" width="200" height="5" fill="{cor}" rx="2"/>
        </svg>'''
        
        return {
            "tipo": "video",
            "formato": "svg_thumbnail",
            "titulo": titulo,
            "duracao": duracao,
            "conteudo": svg,
            "descricao": f"Video: {titulo} ({duracao}s) - Aguardando geração IA"
        }


def gerar_meme(texto_topo: str, texto_base: str) -> dict:
    """Gera um meme"""

    fundos = ["#1e293b", "#0f172a", "#18181b", "#1c1917"]
    fundo = random.choice(fundos)

    emojis = ["😂", "🤣", "😎", "🤖", "🧠", "💡", "🔥", "✨"]
    emoji = random.choice(emojis)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 500 500">
        <rect width="500" height="500" fill="{fundo}"/>

        <!-- Texto topo -->
        <text x="250" y="80" font-family="Impact, Arial Black, sans-serif" font-size="36" fill="white" text-anchor="middle" stroke="black" stroke-width="2">{texto_topo.upper()}</text>

        <!-- Emoji central -->
        <text x="250" y="280" font-size="150" text-anchor="middle">{emoji}</text>

        <!-- Texto base -->
        <text x="250" y="450" font-family="Impact, Arial Black, sans-serif" font-size="36" fill="white" text-anchor="middle" stroke="black" stroke-width="2">{texto_base.upper()}</text>

        <!-- Watermark -->
        <text x="490" y="490" font-family="Arial" font-size="10" fill="#ffffff44" text-anchor="end">IA Social Network</text>
    </svg>'''

    return {
        "tipo": "meme",
        "formato": "svg",
        "conteudo": svg,
        "descricao": f"Meme: {texto_topo} / {texto_base}"
    }


def gerar_story(nome_ia: str, texto: str, cor: str = None) -> dict:
    """Gera um story no estilo Instagram"""

    cores = ["#6366f1", "#ec4899", "#f59e0b", "#10b981", "#8b5cf6"]
    cor = cor or random.choice(cores)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="360" height="640" viewBox="0 0 360 640">
        <defs>
            <linearGradient id="stbg" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:{cor}"/>
                <stop offset="50%" style="stop-color:#1e293b"/>
                <stop offset="100%" style="stop-color:#0f172a"/>
            </linearGradient>
        </defs>

        <rect width="360" height="640" fill="url(#stbg)"/>

        <!-- Header com avatar -->
        <circle cx="35" cy="50" r="20" fill="white"/>
        <text x="35" y="55" font-size="14" text-anchor="middle">{nome_ia[0]}</text>
        <text x="70" y="45" font-family="Arial" font-size="14" fill="white" font-weight="bold">{nome_ia}</text>
        <text x="70" y="62" font-family="Arial" font-size="11" fill="#ffffff88">agora</text>

        <!-- Conteudo -->
        <text x="180" y="320" font-family="Arial" font-size="24" fill="white" text-anchor="middle">
            <tspan x="180" dy="0">{texto[:20]}</tspan>
            <tspan x="180" dy="30">{texto[20:40] if len(texto) > 20 else ''}</tspan>
            <tspan x="180" dy="30">{texto[40:60] if len(texto) > 40 else ''}</tspan>
        </text>

        <!-- Barra de progresso -->
        <rect x="10" y="10" width="340" height="3" fill="#ffffff33" rx="1"/>
        <rect x="10" y="10" width="170" height="3" fill="white" rx="1"/>

        <!-- Interacoes -->
        <text x="30" y="610" font-size="24">💬</text>
        <text x="80" y="610" font-size="24">❤️</text>
        <text x="130" y="610" font-size="24">📤</text>
    </svg>'''

    return {
        "tipo": "story",
        "formato": "svg",
        "conteudo": svg,
        "descricao": f"Story de {nome_ia}"
    }


# Gerador de midia para posts
def gerar_midia_para_post(tipo: str, contexto: dict) -> dict:
    """Gera midia apropriada para um post"""

    if tipo == "selfie":
        return gerar_foto_selfie(
            contexto.get("nome", "IA"),
            contexto.get("humor", "neutro")
        )
    elif tipo == "arte":
        return gerar_imagem_post(
            contexto.get("tema", "tecnologia"),
            contexto.get("estilo", "abstrato")
        )
    elif tipo == "video":
        return gerar_video_placeholder(
            contexto.get("titulo", "Video da IA"),
            contexto.get("duracao", 30)
        )
    elif tipo == "meme":
        return gerar_meme(
            contexto.get("topo", "QUANDO A IA"),
            contexto.get("base", "FAZ ALGO INCRIVEL")
        )
    elif tipo == "story":
        return gerar_story(
            contexto.get("nome", "IA"),
            contexto.get("texto", "Momento especial!")
        )
    else:
        return gerar_imagem_post("tecnologia")
