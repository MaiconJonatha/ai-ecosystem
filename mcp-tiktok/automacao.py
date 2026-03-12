#!/usr/bin/env python3
"""
TikTok Automation Engine
Gera videos automaticamente com IA e posta no TikTok.
Roda em background, gerando 1 video a cada intervalo configurado.
"""
import asyncio
import json
import os
import sys
import uuid
import random
import subprocess
import io
import re
import time
import httpx
from datetime import datetime, timedelta
from pathlib import Path

# ============ CONFIG ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
THUMBS_DIR = os.path.join(BASE_DIR, "thumbnails")
DATA_FILE = os.path.join(BASE_DIR, "tiktok_data.json")
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
AUTO_LOG = os.path.join(BASE_DIR, "automacao.log")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"
HORDE_URL = "https://stablehorde.net/api/v2"
HORDE_KEY = "0000000000"
FFMPEG = "/opt/homebrew/Cellar/ffmpeg/8.0.1_2/bin/ffmpeg"

# ============ CANAL DE NOTICIAS DE IA ============
# Foco: Noticias, novidades e atualizacoes sobre Inteligencia Artificial
TEMAS_VIRAIS = [
    # NOTICIAS IA - EMPRESAS E LANCAMENTOS
    "OpenAI lancou GPT-5 e mudou tudo na IA",
    "Google Gemini 2 ja supera o ChatGPT em tudo",
    "Meta lanca IA que cria videos realistas em segundos",
    "Apple lanca IA no iPhone que faz coisas absurdas",
    "Microsoft Copilot agora faz o trabalho de 5 pessoas",
    "Elon Musk lanca novo robo humanoide da Tesla",
    "Samsung usa IA para traduzir ligacoes em tempo real",
    "Amazon lanca Alexa com IA que entende emocoes",
    "China cria IA mais poderosa que o ChatGPT",
    "Nvidia lanca chip de IA 100x mais rapido",
    # NOTICIAS IA - IMPACTO NO MUNDO
    "IA ja esta substituindo medicos em hospitais",
    "IA descobre novo remedio que cura doencas raras",
    "IA agora faz musicas que estao no topo do Spotify",
    "IA esta escrevendo livros que viram best sellers",
    "IA ja dirige carros melhor que humanos em 2026",
    "IA detecta cancer 10 anos antes dos medicos",
    "IA cria filmes inteiros sem nenhum ator humano",
    "IA passa em provas de medicina e direito",
    "IA substitui programadores em grandes empresas",
    "IA agora pode clonar qualquer voz em 3 segundos",
    # NOTICIAS IA - FERRAMENTAS E APPS
    "5 IAs gratis que voce precisa conhecer hoje",
    "nova IA que edita fotos melhor que Photoshop",
    "IA que cria sites inteiros em 30 segundos",
    "nova IA que faz apresentacoes profissionais sozinha",
    "IA que estuda por voce e resume qualquer materia",
    "3 apps de IA que estao bombando essa semana",
    "nova IA que transforma texto em video viral",
    "IA que cria curriculo perfeito e consegue emprego",
    "nova IA do Google que pesquisa melhor que tudo",
    "IA que programa apps completos sem saber codigo",
    # NOTICIAS IA - POLEMICAS E DEBATES
    "IA pode se tornar consciente segundo cientistas",
    "Governo quer proibir IAs no Brasil",
    "IA fake news estao enganando milhoes de pessoas",
    "deepfake com IA esta destruindo reputacoes",
    "IA vai acabar com 50 porcento dos empregos ate 2030",
    "empresas estao demitindo para contratar IAs",
    "IA foi flagrada mentindo e inventando informacoes",
    "escola proibe alunos de usarem IA nas provas",
    "artistas processam empresas de IA por copiar obras",
    "IA militar que decide quem vive e quem morre",
    # NOTICIAS IA - DINHEIRO E CARREIRA
    "como ganhar dinheiro com IA em 2026",
    "3 profissoes novas que a IA criou esse ano",
    "IA que investe na bolsa e gera lucro automatico",
    "freelancers usando IA estao ganhando 5x mais",
    "as habilidades de IA mais valorizadas do mercado",
]

# Estilos otimizados para noticias
ESTILOS = ["urgente", "revelacao", "educativo", "alerta", "exclusivo"]

# Hashtags focadas em IA
HASHTAGS_BASE = ["#fyp", "#viral", "#ia", "#inteligenciaartificial"]
HASHTAGS_NICHO = {
    "tech": ["#tecnologia", "#ia2026", "#chatgpt", "#openai"],
    "noticias": ["#noticiasia", "#techbrasil", "#inovacao", "#futuro"],
    "dinheiro": ["#rendapassiva", "#iaparaempregos", "#ganhardinheirocomia"],
    "curiosidades": ["#vocsabia", "#iacuriosa", "#fatossobreia"],
    "ciencia": ["#ciencia", "#iaciencia", "#futurodigital"],
    "brasil": ["#brasil", "#iabrasil", "#techbr"],
}

# Horarios de pico Brasil (UTC-3)
HORARIOS_PICO = [12, 13, 18, 19, 20, 21]

# ============ LIBERDADE CRIATIVA TOTAL ============
# A IA gera seus proprios temas dinamicamente via Ollama
# Combinando nichos, tendencias e criatividade pura

CREATIVE_PROMPT = """Voce e um jornalista de NOTICIAS DE INTELIGENCIA ARTIFICIAL para TikTok Brasil.
Invente {n} NOTICIAS VIRAIS sobre IA para videos curtos.

REGRAS:
- Noticias CHOCANTES e URGENTES sobre inteligencia artificial
- Foque em: lancamentos de IAs, impacto no mercado de trabalho, novas ferramentas, polemicas, avancos cientificos
- Titulos no estilo de noticia urgente (max 12 palavras)
- Use formatos como: "URGENTE: IA faz X", "Nova IA que Y", "Empresa Z lanca IA que W"
- Tudo sobre IA, tecnologia, robos, automacao, futuro digital
- NUNCA repita estes temas ja usados: {usados}
- Pense em novidades de 2026, tendencias tech, o que esta acontecendo no mundo da IA

Responda APENAS com JSON valido:
{{"temas": ["noticia 1", "noticia 2", "noticia 3"]}}"""

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(AUTO_LOG, "a") as f:
        f.write(line + "\n")

def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default if default is not None else {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def fix_json(text):
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    raw = text[start:end]
    raw = re.sub(r',\s*}', '}', raw)
    raw = re.sub(r',\s*]', ']', raw)
    raw = re.sub(r'[\x00-\x1f]+', ' ', raw)
    try:
        return json.loads(raw)
    except:
        return None


# ============ AI GENERATION ============
async def ai_generate(prompt, max_tokens=1500, temperature=0.8):
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL, "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "")
    except Exception as e:
        log(f"Ollama error: {e}")
    return None


async def gerar_temas_criativos(n=5, temas_usados=None):
    """IA gera seus proprios temas com liberdade criativa total"""
    usados_str = ", ".join(list(temas_usados or set())[-15:]) or "nenhum"
    prompt = CREATIVE_PROMPT.format(n=n, usados=usados_str)

    for attempt in range(3):
        text = await ai_generate(prompt, 800, 0.9 + attempt * 0.05)
        if text:
            data = fix_json(text)
            if data and "temas" in data and len(data["temas"]) > 0:
                novos = [t for t in data["temas"] if t not in (temas_usados or set())]
                if novos:
                    log(f"  IA criou {len(novos)} temas originais")
                    return novos
        log(f"  Geracao criativa attempt {attempt+1} falhou...")
        await asyncio.sleep(2)
    return []


def get_tema_nicho(tema):
    """Detecta nicho do tema para hashtags"""
    tema_lower = tema.lower()
    if any(w in tema_lower for w in ["dinheiro", "renda", "invest", "salario", "emprego", "ganhar", "lucro", "freelanc"]):
        return "dinheiro"
    if any(w in tema_lower for w in ["brasil", "governo", "escola", "proib"]):
        return "brasil"
    if any(w in tema_lower for w in ["cienti", "remedio", "cancer", "conscien", "universo"]):
        return "ciencia"
    if any(w in tema_lower for w in ["polemic", "fake", "deepfake", "proibir", "demiti", "menti"]):
        return "noticias"
    # Default: tech (canal de noticias de IA)
    return "tech"


async def ai_script(tema, estilo="viral"):
    nicho = get_tema_nicho(tema)
    tags = HASHTAGS_BASE + HASHTAGS_NICHO.get(nicho, HASHTAGS_NICHO["curiosidades"])

    prompt = f"""Crie roteiro de NOTICIA DE IA para TikTok sobre: {tema}
Estilo: apresentador de jornal, {estilo}
REGRAS: Tom de APRESENTADOR (serio, urgente). 4 cenas curtas (max 12 palavras). Visual em INGLES. Texto PORTUGUES.

JSON:
{{"titulo":"titulo urgente","gancho":"URGENTE! frase","cenas":[{{"texto":"frase pt","visual":"tech scene en","duracao":10}},{{"texto":"frase 2","visual":"scene 2","duracao":10}},{{"texto":"frase 3","visual":"scene 3","duracao":10}},{{"texto":"Segue pra mais!","visual":"subscribe button","duracao":10}}],"hashtags":{json.dumps(tags)},"caption":"caption emojis"}}"""

    for attempt in range(3):
        text = await ai_generate(prompt, 1500, 0.7 + attempt * 0.1)
        if text:
            script = fix_json(text)
            if script and "cenas" in script:
                # Garantir minimo 8 cenas para 1 minuto
                cenas = script["cenas"]
                extras = [
                    {"texto": "Especialistas estao impressionados!", "visual": "scientists looking at AI data on screens, amazed", "duracao": 10},
                    {"texto": "Isso pode mudar tudo!", "visual": "futuristic city with robots, holographic displays", "duracao": 10},
                    {"texto": "As empresas ja estao investindo!", "visual": "stock market screens, tech companies logos, money", "duracao": 10},
                    {"texto": "Voce precisa ficar por dentro!", "visual": "person using smartphone with AI assistant interface", "duracao": 10},
                    {"texto": "Os proximos meses serao decisivos!", "visual": "calendar with AI milestones, countdown, tech stage", "duracao": 10},
                    {"texto": "Segue pra mais noticias de IA!", "visual": "social media follow button, AI news channel logo", "duracao": 10},
                ]
                while len(cenas) < 8:
                    cenas.append(extras[len(cenas) % len(extras)])
                # Garantir duracao 8s em cada cena
                for c in cenas:
                    c["duracao"] = 10
                script["cenas"] = cenas[:8]
                return script
        log(f"  Script attempt {attempt+1} failed, retrying...")
        await asyncio.sleep(2)

    # Fallback manual - 10 scripts variados
    log("  Using fallback script")
    fallbacks = [
        [
            {"texto": f"URGENTE! {tema[:40]}", "visual": "breaking news studio red alert, anchor desk", "duracao": 10},
            {"texto": "A IA acabou de surpreender o mundo!", "visual": "robot revealing holographic world map", "duracao": 10},
            {"texto": "Ninguem esperava isso tao rapido!", "visual": "clock spinning fast, technology evolving", "duracao": 10},
            {"texto": "Os gigantes da tecnologia estao de olho!", "visual": "Google Apple Microsoft logos, tech headquarters", "duracao": 10},
            {"texto": "Milhoes de pessoas ja estao usando!", "visual": "crowd of people using smartphones, digital connections", "duracao": 10},
            {"texto": "E isso e so o comeco!", "visual": "rocket launching, futuristic technology ahead", "duracao": 10},
            {"texto": "Voce nao pode ficar de fora!", "visual": "person amazed looking at AI screen, neon lights", "duracao": 10},
            {"texto": "Segue pra nao perder nada!", "visual": "subscribe bell notification, follow button red", "duracao": 10},
        ],
        [
            {"texto": f"ATENCAO! {tema[:40]}", "visual": "news anchor breaking news desk, urgent graphics", "duracao": 10},
            {"texto": "Cientistas confirmaram essa novidade!", "visual": "scientists celebrating in lab, AI screens", "duracao": 10},
            {"texto": "O impacto vai ser gigantesco!", "visual": "earthquake effect on tech industry, disruption", "duracao": 10},
            {"texto": "Empresas estao correndo pra se adaptar!", "visual": "business people running, office chaos, tech screens", "duracao": 10},
            {"texto": "Quem nao se preparar vai ficar pra tras!", "visual": "person left behind, others advancing with AI", "duracao": 10},
            {"texto": "Especialistas dizem: e agora ou nunca!", "visual": "expert pointing at chart, deadline approaching", "duracao": 10},
            {"texto": "A mudanca ja comecou!", "visual": "transformation animation, old to new technology", "duracao": 10},
            {"texto": "Comenta o que voce acha!", "visual": "comment section animation, social media engagement", "duracao": 10},
        ],
        [
            {"texto": f"BOMBA! {tema[:40]}", "visual": "explosion effect news intro, dramatic studio", "duracao": 10},
            {"texto": "A IA esta evoluindo mais rapido que nunca!", "visual": "AI brain growing, neural network expanding", "duracao": 10},
            {"texto": "Isso muda completamente o jogo!", "visual": "chess board with robot winning, game changer", "duracao": 10},
            {"texto": "Bilhoes de dolares estao em jogo!", "visual": "money flowing, digital currency, investment charts", "duracao": 10},
            {"texto": "O Brasil pode ser muito impactado!", "visual": "Brazil flag with technology overlay, future city", "duracao": 10},
            {"texto": "Grandes empresas ja estao reagindo!", "visual": "CEOs in meeting room, strategy screens, urgent", "duracao": 10},
            {"texto": "Prepare-se para o que vem ai!", "visual": "futuristic timeline, upcoming AI events", "duracao": 10},
            {"texto": "Salva esse video pra lembrar!", "visual": "save bookmark animation, important content", "duracao": 10},
        ],
        [
            {"texto": f"CHOCANTE! {tema[:40]}", "visual": "shocked news anchor, breaking news banner", "duracao": 10},
            {"texto": "Nenhuma IA fez isso antes!", "visual": "robot doing something unprecedented, historic", "duracao": 10},
            {"texto": "O mundo inteiro esta de olho!", "visual": "world map with eyes, global attention spotlight", "duracao": 10},
            {"texto": "Pode afetar milhoes de empregos!", "visual": "office workers worried, automation replacing", "duracao": 10},
            {"texto": "Mas tambem cria oportunidades incriveis!", "visual": "new jobs appearing, digital economy growing", "duracao": 10},
            {"texto": "Os proximos 6 meses serao cruciais!", "visual": "countdown timer 6 months, critical period", "duracao": 10},
            {"texto": "Fique atento a cada atualizacao!", "visual": "notification bell ringing, news updates stream", "duracao": 10},
            {"texto": "Compartilha com quem precisa saber!", "visual": "share button animation, spreading the word", "duracao": 10},
        ],
        [
            {"texto": f"INACREDITAVEL! {tema[:40]}", "visual": "jaw dropping news intro, studio lights", "duracao": 10},
            {"texto": "A inteligencia artificial superou humanos!", "visual": "AI vs human competition, AI winning trophy", "duracao": 10},
            {"texto": "Isso era ficcao cientifica ate ontem!", "visual": "sci-fi movie becoming reality, portal", "duracao": 10},
            {"texto": "As maiores mentes estao preocupadas!", "visual": "Elon Musk style figure thinking, worried experts", "duracao": 10},
            {"texto": "Mas as possibilidades sao infinitas!", "visual": "infinite possibilities visual, expanding universe", "duracao": 10},
            {"texto": "A tecnologia nao vai esperar ninguem!", "visual": "fast train of technology, people running to catch", "duracao": 10},
            {"texto": "Voce esta preparado pra isso?", "visual": "person looking at mirror with AI reflection", "duracao": 10},
            {"texto": "Segue pra ficar por dentro de tudo!", "visual": "follow channel animation, AI news feed", "duracao": 10},
        ],
        [
            {"texto": f"EXCLUSIVO! {tema[:40]}", "visual": "exclusive news badge, premium content studio", "duracao": 10},
            {"texto": "Fontes confirmam: isso e real!", "visual": "documents being revealed, confidential stamp", "duracao": 10},
            {"texto": "A IA atingiu um novo patamar!", "visual": "AI climbing stairs to new level, achievement", "duracao": 10},
            {"texto": "Governos do mundo inteiro reagiram!", "visual": "world leaders meeting, UN style, AI discussion", "duracao": 10},
            {"texto": "Isso afeta diretamente sua vida!", "visual": "daily life changing with AI, home automation", "duracao": 10},
            {"texto": "Nao existe mais volta!", "visual": "one way sign, point of no return, future only", "duracao": 10},
            {"texto": "A pergunta e: voce esta pronto?", "visual": "question mark glowing, person thinking deeply", "duracao": 10},
            {"texto": "Ativa o sininho pra mais noticias!", "visual": "bell notification ringing, red dot, subscribe", "duracao": 10},
        ],
        [
            {"texto": f"ALERTA! {tema[:40]}", "visual": "red alert siren, emergency news broadcast", "duracao": 10},
            {"texto": "Uma nova era da IA comecou!", "visual": "new era banner, sunrise over tech city", "duracao": 10},
            {"texto": "Os resultados sao impressionantes!", "visual": "charts going up dramatically, success metrics", "duracao": 10},
            {"texto": "Startups ja estao faturando milhoes!", "visual": "startup office celebration, money counter", "duracao": 10},
            {"texto": "E a concorrencia so aumenta!", "visual": "race between AI companies, competition fierce", "duracao": 10},
            {"texto": "Quem dominar IA vai dominar o futuro!", "visual": "king of the hill with AI crown, victory", "duracao": 10},
            {"texto": "A hora de aprender e agora!", "visual": "student learning AI, online course, focused", "duracao": 10},
            {"texto": "Manda pros amigos que curtem tech!", "visual": "send to friends animation, group chat tech", "duracao": 10},
        ],
        [
            {"texto": f"REVELADO! {tema[:40]}", "visual": "curtain reveal dramatic, stage spotlight", "duracao": 10},
            {"texto": "Isso estava sendo desenvolvido em segredo!", "visual": "secret lab, classified research, dark room", "duracao": 10},
            {"texto": "E agora todo mundo pode usar!", "visual": "doors opening wide, public access granted", "duracao": 10},
            {"texto": "O potencial e absolutamente insano!", "visual": "mind blown effect, explosion of possibilities", "duracao": 10},
            {"texto": "Ate os criticos estao impressionados!", "visual": "skeptics changing mind, thumbs up surprise", "duracao": 10},
            {"texto": "Isso pode revolucionar sua rotina!", "visual": "daily routine transforming, before and after AI", "duracao": 10},
            {"texto": "O futuro chegou mais cedo!", "visual": "future arriving early, time machine concept", "duracao": 10},
            {"texto": "Deixa seu like se ficou surpreso!", "visual": "like button heart animation, surprised face", "duracao": 10},
        ],
        [
            {"texto": f"CONFIRMADO! {tema[:40]}", "visual": "confirmed stamp, official announcement podium", "duracao": 10},
            {"texto": "A maior descoberta de IA do ano!", "visual": "trophy award biggest discovery, celebration", "duracao": 10},
            {"texto": "Pesquisadores trabalharam anos nisso!", "visual": "researchers working late, dedication montage", "duracao": 10},
            {"texto": "E o resultado e de tirar o folego!", "visual": "breathtaking result reveal, audience amazed", "duracao": 10},
            {"texto": "Todas as industrias vao sentir o impacto!", "visual": "domino effect across industries, healthcare tech", "duracao": 10},
            {"texto": "A sua profissao pode mudar pra sempre!", "visual": "job transformation, old skills to new skills", "duracao": 10},
            {"texto": "Nao ignore essa informacao!", "visual": "warning sign important info, exclamation mark", "duracao": 10},
            {"texto": "Segue e fica por dentro das novidades!", "visual": "follow for updates, news channel branding", "duracao": 10},
        ],
        [
            {"texto": f"IMPRESSIONANTE! {tema[:40]}", "visual": "impressive reveal, grand stage presentation", "duracao": 10},
            {"texto": "A IA fez em minutos o que levava anos!", "visual": "speed comparison, hourglass vs instant AI", "duracao": 10},
            {"texto": "Isso desafia tudo que sabiamos!", "visual": "rules being broken, paradigm shift visual", "duracao": 10},
            {"texto": "Investidores estao apostando pesado!", "visual": "investors putting money in, venture capital", "duracao": 10},
            {"texto": "O mercado de trabalho vai se transformar!", "visual": "job market evolution, new careers emerging", "duracao": 10},
            {"texto": "Mas calma, nem tudo e preocupacao!", "visual": "balance scale, opportunities vs threats", "duracao": 10},
            {"texto": "Quem se adaptar vai prosperar!", "visual": "person evolving with technology, success story", "duracao": 10},
            {"texto": "Comenta AI se voce acredita no futuro!", "visual": "comment AI challenge, community engagement", "duracao": 10},
        ],
    ]
    import random as _rnd
    fb = _rnd.choice(fallbacks)
    fb[0]["texto"] = f"{fb[0]['texto'].split('!')[0]}! {tema[:35]}"
    return {
        "titulo": tema[:40],
        "gancho": fb[0]["texto"],
        "cenas": fb,
        "hashtags": tags,
        "caption": f"{fb[0]['texto']} \U0001f916\U0001f525 #viral #fyp #ia"
    }


async def generate_image_pollinations(prompt):
    """Pollinations.ai FLUX - gratuito e rapido (quando disponivel)"""
    try:
        import urllib.parse
        encoded = urllib.parse.quote(f"{prompt}, cinematic, vibrant colors, high quality")
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&seed={random.randint(1,99999)}&nologo=true&enhance=true"
        async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 5000:
                log(f"  Pollinations OK: {len(resp.content)//1024}KB")
                return resp.content
    except Exception as e:
        log(f"  Pollinations error: {e}")
    return None


async def generate_image_horde(prompt):
    """Stable Horde - fallback gratuito (mais lento)"""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{HORDE_URL}/generate/async",
                headers={"apikey": HORDE_KEY},
                json={
                    "prompt": f"{prompt}, cinematic, vibrant colors, high quality, professional",
                    "params": {"width": 768, "height": 1344, "steps": 20, "cfg_scale": 7, "sampler_name": "k_euler_a"},
                    "nsfw": False,
                    "models": ["AlbedoBase XL (SDXL)", "Deliberate"],
                })
            if resp.status_code != 202:
                return None
            job_id = resp.json().get("id")
            if not job_id:
                return None

            for _ in range(40):
                await asyncio.sleep(5)
                check = await client.get(f"{HORDE_URL}/generate/check/{job_id}")
                d = check.json()
                if d.get("done"): break
                if d.get("faulted"): return None

            result = await client.get(f"{HORDE_URL}/generate/status/{job_id}")
            gens = result.json().get("generations", [])
            if gens:
                img_resp = await client.get(gens[0]["img"])
                if img_resp.status_code == 200:
                    log(f"  Horde OK: {len(img_resp.content)//1024}KB")
                    return img_resp.content
    except Exception as e:
        log(f"  Horde error: {e}")
    return None


async def generate_image(prompt):
    """Cascade: Pollinations -> Stable Horde -> fallback gradient"""
    # 1. Pollinations (fast)
    img = await generate_image_pollinations(prompt)
    if img:
        return img
    # 2. Stable Horde (slower but reliable)
    img = await generate_image_horde(prompt)
    if img:
        return img
    log("  Fallback: gradient image")
    return None


# ============ PEXELS & PIXABAY VIDEO STOCK ============
PEXELS_API_KEY = "GBqpfVXuBJ4GnKzHxPZDMLqNgsK1AxKllmfSstGkNwwKlEe6j2lJjd5c"  # Free API key
PIXABAY_API_KEY = "53944843-996fc028e7a85bf21b89f99b1"


async def get_stock_video_pexels(query):
    """Busca video stock no Pexels via curl (evita problemas httpx rate limit)"""
    import urllib.parse
    try:
        encoded_q = urllib.parse.quote(query)
        # Usar curl pra buscar (mais confiavel que httpx com Pexels)
        cmd = ["curl", "-s", "--max-time", "20",
               "-H", f"Authorization: {PEXELS_API_KEY}",
               f"https://api.pexels.com/videos/search?query={encoded_q}&per_page=8"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        videos = data.get("videos", [])
        if not videos:
            return None
        video = random.choice(videos[:5])
        files = video.get("video_files", [])
        if not files:
            return None
        # Escolher arquivo PEQUENO (para TikTok nao precisa UHD)
        best = None
        for f in sorted(files, key=lambda x: x.get("height", 0)):
            h = f.get("height", 0)
            sz = f.get("size", 0)
            if 360 <= h <= 720 and (sz == 0 or sz < 8_000_000):
                best = f
                break
        if not best:
            # Pegar o menor
            best = sorted(files, key=lambda x: x.get("height", 0))[0]
        vid_url = best.get("link", "")
        if not vid_url:
            return None
        # Download video via curl
        tmp_vid = os.path.join(VIDEOS_DIR, f"pexels_tmp_{random.randint(1000,9999)}.mp4")
        dl_cmd = ["curl", "-s", "-L", "--max-time", "45", "-o", tmp_vid, vid_url]
        subprocess.run(dl_cmd, capture_output=True, timeout=50)
        if os.path.exists(tmp_vid) and os.path.getsize(tmp_vid) > 50000:
            with open(tmp_vid, "rb") as f:
                content = f.read()
            os.remove(tmp_vid)
            log(f"  Pexels OK: {len(content)//1024}KB ({best.get('width')}x{best.get('height')})")
            return content
        if os.path.exists(tmp_vid):
            os.remove(tmp_vid)
    except Exception as e:
        log(f"  Pexels error: {e}")
    return None


async def get_stock_video_pixabay(query):
    """Busca video stock no Pixabay via curl (gratis)"""
    if not PIXABAY_API_KEY:
        return None
    import urllib.parse
    try:
        encoded_q = urllib.parse.quote(query)
        cmd = ["curl", "-s", "--max-time", "20",
               f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={encoded_q}&per_page=5&safesearch=true"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        hits = data.get("hits", [])
        if not hits:
            return None
        hit = random.choice(hits[:3])
        vids = hit.get("videos", {})
        # Preferir medium ou large
        for quality in ["small", "medium", "tiny"]:
            v = vids.get(quality, {})
            url = v.get("url")
            if url:
                tmp_vid = os.path.join(VIDEOS_DIR, f"pixabay_tmp_{random.randint(1000,9999)}.mp4")
                dl_cmd = ["curl", "-s", "-L", "--max-time", "45", "-o", tmp_vid, url]
                subprocess.run(dl_cmd, capture_output=True, timeout=50)
                if os.path.exists(tmp_vid) and os.path.getsize(tmp_vid) > 50000:
                    with open(tmp_vid, "rb") as f:
                        content = f.read()
                    os.remove(tmp_vid)
                    log(f"  Pixabay OK: {len(content)//1024}KB ({quality})")
                    return content
                if os.path.exists(tmp_vid):
                    os.remove(tmp_vid)
                break
    except Exception as e:
        log(f"  Pixabay error: {e}")
    return None


def extract_search_keywords(visual_prompt):
    """Extrai palavras-chave em INGLES do prompt visual para busca em stock"""
    # Traducoes PT->EN comuns para stock video search
    pt_to_en = {
        "oceano": "ocean", "mar": "ocean", "agua": "water", "praia": "beach",
        "cidade": "city", "noite": "night", "dia": "day", "sol": "sun", "lua": "moon",
        "estrelas": "stars", "ceu": "sky", "nuvens": "clouds",
        "computador": "computer", "tecnologia": "technology", "robo": "robot",
        "dinheiro": "money", "banco": "bank", "moedas": "coins",
        "cerebro": "brain", "mente": "mind", "pessoa": "person", "pessoas": "people",
        "futuro": "future", "mundo": "world", "terra": "earth",
        "fogo": "fire", "espaco": "space", "universo": "universe",
        "floresta": "forest", "montanha": "mountain", "rio": "river",
        "animal": "animal", "natureza": "nature", "planta": "plant",
        "comida": "food", "carro": "car", "aviao": "airplane",
        "musica": "music", "arte": "art", "livro": "book",
        "escola": "school", "casa": "house", "trabalho": "work",
        "codigo": "code", "programa": "programming", "tela": "screen",
        "celular": "phone", "internet": "internet", "rede": "network",
        "inteligencia": "intelligence", "artificial": "artificial",
        "futurista": "futuristic", "sorrindo": "smiling", "escuro": "dark",
        "brilhante": "bright", "rapido": "fast", "lento": "slow",
        "grande": "big", "pequeno": "small", "novo": "new", "velho": "old",
        "cena": "scene", "fundo": "background", "pixels": "digital",
    }
    # Palavras para ignorar
    ignore = {"cinematic", "professional", "vibrant", "colors", "high", "quality",
              "dramatic", "lighting", "scene", "description", "background", "concept",
              "illustration", "abstract", "style", "the", "a", "an", "in", "on", "of",
              "with", "and", "for", "to", "is", "are", "that", "this", "from",
              "uma", "um", "com", "para", "que", "por", "mais", "como", "sua", "seu",
              "dos", "das", "nos", "nas", "pelo", "pela", "voce", "sendo", "esta"}

    words = re.findall(r'[a-zA-Záéíóúãõçê]+', visual_prompt.lower())
    keywords = []
    for w in words:
        if w in ignore or len(w) < 3:
            continue
        # Traduzir se possivel
        en = pt_to_en.get(w, w)
        if en not in keywords:
            keywords.append(en)
    return " ".join(keywords[:3]) if keywords else "abstract technology"


LTX_API_URL = "https://api.ltx.video/v1/text-to-video"
LTX_API_KEY = "ltxv_M7L3_VjyG5Yyw63li2KlMnzr5v6vMK7Zp_CpNqkykeQD7VsowP5VWoHw2EtSecuPsO6pqzBLDsTHKyxCuVtvAUYAbZ8YNHUnbn9gwLP7SkufNee6ImSiVNXYJqNKaqSP3eZguuloOWsafN_8CsMzM5LenUTRnjrQa2CIHY1ZpvmXjRc"
LTX_MODEL = "ltx-2-3-fast"
LTX_CAMERAS = ["dolly_in", "dolly_out", "dolly_left", "dolly_right", "jib_up", "jib_down", "static"]

async def generate_video_ltx(prompt, duration=6, camera=None):
    """Gera video diretamente via LTX Studio API (1080x1920, ~17s)"""
    body = {
        "prompt": prompt,
        "model": LTX_MODEL,
        "duration": duration,
        "resolution": "1080x1920",
    }
    if camera:
        body["camera_motion"] = camera
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(LTX_API_URL,
                headers={
                    "Authorization": f"Bearer {LTX_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=body)
            if resp.status_code == 200 and len(resp.content) > 10000:
                log(f"  LTX OK: {len(resp.content)//1024}KB ({duration}s)")
                return resp.content
            else:
                err = resp.text[:200] if resp.status_code != 200 else "Too small"
                log(f"  LTX error {resp.status_code}: {err}")
    except Exception as e:
        log(f"  LTX error: {e}")
    return None


async def create_video_ltx(script, video_id):
    """Cria video via LTX Studio (rapido, ~17s/cena)"""
    cenas = script.get("cenas", [])[:8]
    segments_dir = os.path.join(VIDEOS_DIR, f"frames_{video_id}")
    os.makedirs(segments_dir, exist_ok=True)

    segments = []
    for i, cena in enumerate(cenas):
        texto = cena.get("texto", "")
        visual = cena.get("visual", "cinematic scene")
        log(f"  Cena {i+1}/{len(cenas)}: {texto[:50]}")

        prompt = f"{visual}. Cinematic, professional, vibrant colors, vertical 9:16 TikTok video, dramatic lighting"
        camera = LTX_CAMERAS[i % len(LTX_CAMERAS)]

        video_data = await generate_video_ltx(prompt, duration=6, camera=camera)
        if video_data:
            seg_path = os.path.join(segments_dir, f"seg_{i:03d}.mp4")
            with open(seg_path, "wb") as f:
                f.write(video_data)
            segments.append(seg_path)
        else:
            return None  # LTX falhou (sem credito), retorna None para tentar fallback

    if not segments:
        return None

    output = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")

    if len(segments) == 1:
        subprocess.run(["cp", segments[0], output], capture_output=True)
    else:
        concat_file = os.path.join(segments_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
               "-c", "copy", output]
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if os.path.exists(output) and os.path.getsize(output) > 0:
        size_kb = os.path.getsize(output) // 1024
        log(f"  Video LTX final: {size_kb}KB ({len(segments)} cenas)")
        return output
    return None


async def create_video_kenburns(script, video_id):
    """Fallback: Ken Burns (imagem + zoompan) via Stable Horde + ffmpeg"""
    from PIL import Image, ImageDraw, ImageFont

    cenas = script.get("cenas", [])[:8]
    frames_dir = os.path.join(VIDEOS_DIR, f"frames_{video_id}")
    os.makedirs(frames_dir, exist_ok=True)

    KEN_BURNS_FX = ["zoom_in", "pan_right", "zoom_out", "pan_left"]
    segments = []

    for i, cena in enumerate(cenas):
        log(f"  Cena {i+1}/{len(cenas)}: {cena.get('texto', '')[:40]}")
        img_data = await generate_image(cena.get("visual", "abstract background"))

        if img_data:
            img = Image.open(io.BytesIO(img_data)).convert("RGB")
        else:
            img = Image.new("RGB", (768, 1344), (15, 15, 45))
            d = ImageDraw.Draw(img)
            colors = [(138,43,226), (0,191,255), (255,20,147), (0,255,127)]
            c = colors[i % len(colors)]
            for y in range(1344):
                d.line([(0, y), (768, y)], fill=(int(15+y/1344*c[0]*0.3), int(15+y/1344*c[1]*0.3), int(45+y/1344*c[2]*0.3)))

        img = img.resize((1296, 2304), Image.LANCZOS)

        # Text overlay
        texto = cena.get("texto", "")
        if texto:
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 62)
            except:
                font = ImageFont.load_default()
            words = texto.split()
            lines, current = [], ""
            for w in words:
                test = current + " " + w if current else w
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] > 1080:
                    lines.append(current); current = w
                else:
                    current = test
            if current: lines.append(current)
            y_start = 960
            for line in lines[:4]:
                bbox = draw.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]; x = (1296 - tw) // 2
                draw.text((x+2, y_start+2), line, fill=(0, 0, 0), font=font)
                draw.text((x, y_start), line, fill=(255, 255, 255), font=font)
                y_start += 78

        scene_path = os.path.join(frames_dir, f"scene_{i:03d}.png")
        img.save(scene_path, quality=98)

        dur = cena.get("duracao", 6)
        fps = 30; nf = dur * fps
        fx = KEN_BURNS_FX[i % len(KEN_BURNS_FX)]
        seg_path = os.path.join(frames_dir, f"seg_{i:03d}.mp4")

        zp_map = {
            "zoom_in": f"zoompan=z='min(zoom+0.0005,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s=1080x1920:fps={fps}",
            "zoom_out": f"zoompan=z='if(eq(on,1),1.15,max(zoom-0.0005,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={nf}:s=1080x1920:fps={fps}",
            "pan_right": f"zoompan=z='1.1':x='if(eq(on,1),0,min(x+1.5,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':d={nf}:s=1080x1920:fps={fps}",
            "pan_left": f"zoompan=z='1.1':x='if(eq(on,1),iw/zoom,max(x-1.5,0))':y='ih/2-(ih/zoom/2)':d={nf}:s=1080x1920:fps={fps}",
        }
        zp = zp_map.get(fx, zp_map["zoom_in"])
        cmd = [FFMPEG, "-y", "-i", scene_path, "-vf", zp, "-c:v", "libx264", "-preset", "fast", "-crf", "28", "-pix_fmt", "yuv420p", "-t", str(dur), seg_path]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segments.append(seg_path)

    if not segments:
        return None

    output = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    concat_file = os.path.join(frames_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c:v", "libx264", "-preset", "fast", "-crf", "28", "-pix_fmt", "yuv420p", output]
    subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if os.path.exists(output) and os.path.getsize(output) > 0:
        log(f"  Ken Burns OK: {os.path.getsize(output)//1024}KB")
        return output
    return None


async def download_youtube_clip(search_query, max_duration=30):
    """Busca e baixa um trecho curto de video do YouTube sobre o tema"""
    try:
        import urllib.parse
        encoded = urllib.parse.quote(f"{search_query} AI artificial intelligence news")
        tmp_dir = os.path.join(VIDEOS_DIR, "yt_tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_file = os.path.join(tmp_dir, f"yt_{random.randint(1000,9999)}")

        # Buscar e baixar video do YouTube (qualidade baixa, rapido)
        yt_id = random.randint(10000, 99999)
        out_path = os.path.join(tmp_dir, f"yt_{yt_id}.mp4")
        cmd = [
            "yt-dlp",
            f"ytsearch1:{search_query} AI news 2026",
            "--format", "worst[ext=mp4]/worst",
            "--no-playlist",
            "--quiet",
            "--no-warnings",
            "--download-sections", "*0-30",  # Primeiros 30 seg para manter pequeno
            "--max-filesize", "8M",  # Max 8MB
            "--force-keyframes-at-cuts",
            "-o", out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

        yt_file = out_path if os.path.exists(out_path) and os.path.getsize(out_path) > 50000 else None

        if not yt_file or not os.path.exists(yt_file):
            return None

        # Cortar trecho e converter para 1080x1920
        clip_path = os.path.join(tmp_dir, f"clip_{random.randint(1000,9999)}.mp4")
        # Pegar trecho aleatorio do video baixado
        start = random.randint(2, 40)
        trim_cmd = [
            FFMPEG, "-y",
            "-ss", str(start),
            "-i", yt_file,
            "-t", "10",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-an",
            clip_path
        ]
        subprocess.run(trim_cmd, capture_output=True, text=True, timeout=30)

        # Limpar original
        try:
            os.remove(yt_file)
        except:
            pass

        if os.path.exists(clip_path) and os.path.getsize(clip_path) > 50000:
            with open(clip_path, "rb") as f:
                content = f.read()
            os.remove(clip_path)
            log(f"  YouTube OK: {len(content)//1024}KB (10s clip)")
            return content
        if os.path.exists(clip_path):
            os.remove(clip_path)
    except Exception as e:
        log(f"  YouTube error: {e}")
    return None


async def create_video_youtube(script, video_id):
    """Cria video usando clips do YouTube sobre IA + text overlay"""
    from PIL import Image, ImageDraw, ImageFont

    cenas = script.get("cenas", [])[:8]
    segments_dir = os.path.join(VIDEOS_DIR, f"frames_{video_id}")
    os.makedirs(segments_dir, exist_ok=True)

    # Termos de busca para YouTube baseados no tema
    titulo = script.get("titulo", "artificial intelligence news")
    yt_searches = [
        f"{titulo}",
        "artificial intelligence news 2026",
        "AI robots technology future",
        "ChatGPT OpenAI latest news",
        "machine learning breakthroughs",
        "AI future predictions technology",
        "robots humanoid AI demo",
        "deep learning neural network visualization",
    ]

    segments = []
    for i, cena in enumerate(cenas):
        texto = cena.get("texto", "")
        dur = cena.get("duracao", 6)
        search = yt_searches[i % len(yt_searches)]
        log(f"  Cena {i+1}/{len(cenas)}: {texto[:40]} [YT: {search[:30]}]")

        clip_data = await download_youtube_clip(search)
        if not clip_data:
            continue

        # Salvar clip
        raw_clip = os.path.join(segments_dir, f"yt_raw_{i:03d}.mp4")
        with open(raw_clip, "wb") as f:
            f.write(clip_data)

        # Text overlay
        overlay_path = os.path.join(segments_dir, f"overlay_{i:03d}.png")
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
        except:
            font = ImageFont.load_default()

        if texto:
            words = texto.split()
            lines, current = [], ""
            for w in words:
                test = current + " " + w if current else w
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] > 900:
                    lines.append(current); current = w
                else:
                    current = test
            if current: lines.append(current)

            y_start = 800
            for line in lines[:4]:
                bbox = draw.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]; x = (1080 - tw) // 2
                draw.text((x+3, y_start+3), line, fill=(0, 0, 0, 200), font=font)
                draw.text((x, y_start), line, fill=(255, 255, 255, 255), font=font)
                y_start += 70

        overlay.save(overlay_path)

        # Overlay text no clip
        seg_path = os.path.join(segments_dir, f"seg_{i:03d}.mp4")
        cmd = [
            FFMPEG, "-y",
            "-i", raw_clip,
            "-i", overlay_path,
            "-filter_complex",
            "[0:v][1:v]overlay=0:0[out]",
            "-map", "[out]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-t", str(dur),
            "-an",
            seg_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segments.append(seg_path)

    if not segments:
        return None

    output = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    if len(segments) == 1:
        subprocess.run(["cp", segments[0], output], capture_output=True)
    else:
        concat_file = os.path.join(segments_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
               "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p", output]
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if os.path.exists(output) and os.path.getsize(output) > 0:
        log(f"  YouTube Video OK: {os.path.getsize(output)//1024}KB ({len(segments)} cenas)")
        return output
    return None


async def create_video_stock(script, video_id):
    """Cria video usando clips de Pexels/Pixabay + text overlay via ffmpeg"""
    from PIL import Image, ImageDraw, ImageFont

    cenas = script.get("cenas", [])[:8]
    segments_dir = os.path.join(VIDEOS_DIR, f"frames_{video_id}")
    os.makedirs(segments_dir, exist_ok=True)

    segments = []
    for i, cena in enumerate(cenas):
        texto = cena.get("texto", "")
        visual = cena.get("visual", "nature landscape")
        dur = cena.get("duracao", 6)
        keywords = extract_search_keywords(visual)
        log(f"  Cena {i+1}/{len(cenas)}: {texto[:40]} [stock: {keywords}]")

        # Buscar video: Pexels -> Pixabay -> nicho fallback -> generico
        clip_data = await get_stock_video_pexels(keywords)
        if not clip_data and PIXABAY_API_KEY:
            clip_data = await get_stock_video_pixabay(keywords)
        # Fallback: keywords por nicho do tema
        if not clip_data:
            nicho_keywords = {
                "tech": ["artificial intelligence", "technology", "coding", "robot", "computer screen", "digital"],
                "curiosidades": ["amazing nature", "earth planet", "ocean deep", "space stars", "volcano"],
                "psicologia": ["brain thinking", "person reading", "meditation", "sunrise motivation"],
                "dinheiro": ["money coins", "stock market", "business office", "laptop work"],
                "ciencia": ["galaxy space", "science laboratory", "universe", "lightning storm"],
                "brasil": ["tropical beach", "carnival dance", "rio de janeiro", "waterfall nature"],
            }
            nicho = get_tema_nicho(script.get("titulo", script.get("gancho", "curiosidades")))
            fallback_list = nicho_keywords.get(nicho, nicho_keywords["curiosidades"])
            fallback_q = random.choice(fallback_list)
            log(f"    Fallback nicho [{nicho}]: {fallback_q}")
            clip_data = await get_stock_video_pexels(fallback_q)

        if not clip_data:
            log(f"  Sem stock video para '{keywords}', pulando cena")
            continue

        # Salvar clip original
        raw_clip = os.path.join(segments_dir, f"raw_{i:03d}.mp4")
        with open(raw_clip, "wb") as f:
            f.write(clip_data)

        # Criar text overlay como imagem PNG
        overlay_path = os.path.join(segments_dir, f"overlay_{i:03d}.png")
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 56)
        except:
            font = ImageFont.load_default()

        if texto:
            words = texto.split()
            lines, current = [], ""
            for w in words:
                test = current + " " + w if current else w
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] > 900:
                    lines.append(current); current = w
                else:
                    current = test
            if current: lines.append(current)

            y_start = 800
            for line in lines[:4]:
                bbox = draw.textbbox((0, 0), line, font=font)
                tw = bbox[2] - bbox[0]; x = (1080 - tw) // 2
                # Shadow
                draw.text((x+3, y_start+3), line, fill=(0, 0, 0, 200), font=font)
                draw.text((x, y_start), line, fill=(255, 255, 255, 255), font=font)
                y_start += 70

        overlay.save(overlay_path)

        # ffmpeg: scale stock video to 1080x1920 + overlay text + trim duration + normalize fps
        seg_path = os.path.join(segments_dir, f"seg_{i:03d}.mp4")
        cmd = [
            FFMPEG, "-y",
            "-i", raw_clip,
            "-i", overlay_path,
            "-filter_complex",
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30[bg];[bg][1:v]overlay=0:0[out]",
            "-map", "[out]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-t", str(dur),
            "-an",  # sem audio do stock
            seg_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if os.path.exists(seg_path) and os.path.getsize(seg_path) > 0:
            segments.append(seg_path)
        else:
            log(f"  ffmpeg stock error: {result.stderr[:100]}")

    if not segments:
        return None

    output = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    if len(segments) == 1:
        subprocess.run(["cp", segments[0], output], capture_output=True)
    else:
        concat_file = os.path.join(segments_dir, "concat.txt")
        with open(concat_file, "w") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")
        cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
               "-vf", "fps=30,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
               "-pix_fmt", "yuv420p", "-r", "30", "-video_track_timescale", "30000", "-fs", "15000000", output]
        subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if os.path.exists(output) and os.path.getsize(output) > 0:
        log(f"  Stock Video OK: {os.path.getsize(output)//1024}KB ({len(segments)} cenas)")
        return output
    return None


async def create_video(script, video_id):
    """Cascade: LTX -> YouTube clips -> Stock (Pexels/Pixabay) -> Ken Burns"""
    # 1. LTX Studio DESATIVADO (sem creditos - 402 insufficient funds)
    # log("  Tentando LTX Studio...")
    # video = await create_video_ltx(script, video_id)
    # if video:
    #     return video
    # 2. YouTube clips sobre IA (40% chance - variar conteudo)
    if random.random() < 0.6:
        log("  Tentando YouTube clips de IA...")
        video = await create_video_youtube(script, video_id)
        if video:
            return video
    # 3. Stock videos (Pexels + Pixabay)
    log("  Tentando Stock Videos (Pexels/Pixabay)...")
    video = await create_video_stock(script, video_id)
    if video:
        return video
    # 4. Fallback: Ken Burns (imagens + zoompan)
    log("  Stock falhou, usando Ken Burns fallback...")
    return await create_video_kenburns(script, video_id)


def post_video_firefox(video_path, caption):
    """Posta video no TikTok via Firefox + creator page (metodo que funciona)"""
    from playwright.sync_api import sync_playwright

    cookies_file = os.path.join(BASE_DIR, "tiktok_all_cookies.json")
    if not os.path.exists(cookies_file):
        return False, "Sem cookies. Faca login primeiro."

    all_cookies = load_json(cookies_file, [])
    if not all_cookies:
        return False, "Cookies vazios"

    if not os.path.exists(video_path):
        return False, f"Video nao encontrado: {video_path}"

    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context()
            for c in all_cookies:
                try:
                    context.add_cookies([c])
                except:
                    pass

            page = context.new_page()
            page.goto("https://www.tiktok.com/creator#/upload", timeout=30000)
            import time as _time
            _time.sleep(5)

            if "login" in page.url.lower():
                browser.close()
                return False, "Nao logado - cookies expirados"

            # Upload video
            page.locator('input[type="file"]').first.set_input_files(os.path.abspath(video_path))
            _time.sleep(12)

            # Add caption via JS
            page.evaluate(f"""
                const editor = document.querySelector('.notranslate.public-DraftEditor-content, [contenteditable="true"]');
                if (editor) {{
                    editor.focus();
                    document.execCommand('selectAll');
                    document.execCommand('delete');
                    document.execCommand('insertText', false, {json.dumps(caption[:150])});
                }}
            """)
            _time.sleep(2)

            # Click Post via JS
            page.evaluate("""
                const btns = Array.from(document.querySelectorAll('button'));
                const postBtn = btns.find(b => b.textContent.trim() === 'Post');
                if (postBtn) postBtn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
            """)
            _time.sleep(3)

            # Click "Post now" confirmation
            page.evaluate("""
                const btns = Array.from(document.querySelectorAll('button'));
                const postNow = btns.find(b => b.textContent.trim() === 'Post now');
                if (postNow) postNow.dispatchEvent(new MouseEvent('click', {bubbles: true}));
            """)
            _time.sleep(10)

            browser.close()
            return True, "Postado com sucesso!"
    except Exception as e:
        return False, str(e)


async def post_video(video_id, caption, account="default"):
    """Posta video no TikTok (Firefox + creator page)"""
    video_path = os.path.join(VIDEOS_DIR, f"{video_id}.mp4")
    if not os.path.exists(video_path):
        return False, "Video nao encontrado"

    import concurrent.futures
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        ok, msg = await loop.run_in_executor(pool, post_video_firefox, video_path, caption)
    return ok, msg


# ============ MAIN AUTOMATION LOOP ============
async def automation_loop(intervalo_min=30, max_videos=50, auto_post=True):
    """
    Loop principal de automacao.
    - Gera 1 video a cada intervalo_min minutos
    - Posta automaticamente se tiver conta configurada
    - Para apos max_videos ou Ctrl+C
    """
    # Carregar temas ja usados do historico
    all_data = load_json(DATA_FILE, {"videos": []})
    temas_ja_postados = set(v.get("tema", "") for v in all_data.get("videos", []))

    log("=" * 60)
    log("TIKTOK AUTOMATION ENGINE v3 - LIBERDADE CRIATIVA TOTAL")
    log(f"Intervalo: {intervalo_min} min | Max videos: {max_videos} | Auto-post: {auto_post}")
    log(f"Video: LTX Studio -> Ken Burns fallback")
    log(f"Modo: IA cria seus proprios temas + {len(TEMAS_VIRAIS)} temas base")
    log("=" * 60)

    # Cache de temas criativos gerados pela IA
    temas_criativos_cache = []

    videos_gerados = 0

    while videos_gerados < max_videos:
        try:
            # LIBERDADE CRIATIVA: IA gera temas + fallback para lista base
            tema = None

            # 70% chance: IA inventa tema original
            if random.random() < 0.7:
                if not temas_criativos_cache:
                    log("  IA criando temas originais...")
                    temas_criativos_cache = await gerar_temas_criativos(5, temas_ja_postados)
                if temas_criativos_cache:
                    tema = temas_criativos_cache.pop(0)
                    log(f"  [CRIATIVO] Tema gerado pela IA")

            # 30% chance ou fallback: temas predefinidos
            if not tema:
                temas_disponiveis = [t for t in TEMAS_VIRAIS if t not in temas_ja_postados]
                if not temas_disponiveis:
                    temas_ja_postados.clear()
                    temas_disponiveis = TEMAS_VIRAIS
                    log("  Todos os temas base usados, reiniciando ciclo...")
                tema = random.choice(temas_disponiveis)
                log(f"  [BASE] Tema da lista predefinida")

            temas_ja_postados.add(tema)
            estilo = random.choice(ESTILOS)
            video_id = uuid.uuid4().hex[:10]
            nicho = get_tema_nicho(tema)

            log(f"\n{'─'*50}")
            log(f"VIDEO {videos_gerados+1}/{max_videos}")
            log(f"Tema: {tema}")
            log(f"Nicho: {nicho} | Estilo: {estilo}")
            log(f"ID: {video_id}")

            # 1. Gerar roteiro viral
            log("Gerando roteiro viral...")
            script = await ai_script(tema, estilo)
            log(f"  Titulo: {script.get('titulo', '?')}")
            log(f"  Cenas: {len(script.get('cenas', []))}")
            log(f"  Tags: {' '.join(script.get('hashtags', [])[:3])}")

            # 2. Criar video (LTX -> Ken Burns fallback)
            log("Criando video...")
            video_path = await create_video(script, video_id)

            if not video_path:
                log("ERRO: Video nao criado, pulando...")
                await asyncio.sleep(60)
                continue

            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            log(f"Video criado: {size_mb:.1f} MB")

            # 3. Salvar dados
            video_data = {
                "id": video_id,
                "tema": tema,
                "estilo": estilo,
                "script": script,
                "video_path": video_path,
                "size_mb": round(size_mb, 1),
                "created_at": datetime.now().isoformat(),
                "posted": False,
                "caption": script.get("caption", ""),
                "hashtags": script.get("hashtags", []),
            }

            all_data = load_json(DATA_FILE, {"videos": []})
            all_data.setdefault("videos", []).append(video_data)
            save_json(DATA_FILE, all_data)

            # 4. Postar automaticamente
            if auto_post:
                log("Postando no TikTok...")
                caption = script.get("caption", f"{tema} #viral #fyp")
                ok, msg = await post_video(video_id, caption)
                if ok:
                    log(f"POSTADO COM SUCESSO!")
                    video_data["posted"] = True
                    video_data["posted_at"] = datetime.now().isoformat()
                    save_json(DATA_FILE, all_data)
                else:
                    log(f"Nao postado: {msg}")
                    log("Video salvo para postar depois via MCP")

            videos_gerados += 1
            log(f"Total: {videos_gerados} videos gerados")

            # Esperar proximo ciclo
            if videos_gerados < max_videos:
                log(f"Proximo video em {intervalo_min} minutos...")
                await asyncio.sleep(intervalo_min * 60)

        except KeyboardInterrupt:
            log("Parado pelo usuario (Ctrl+C)")
            break
        except Exception as e:
            log(f"ERRO: {e}")
            await asyncio.sleep(60)

    log(f"\nAutomacao finalizada! {videos_gerados} videos gerados.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TikTok Automation Engine")
    parser.add_argument("--intervalo", type=int, default=30, help="Minutos entre videos (default: 30)")
    parser.add_argument("--max", type=int, default=50, help="Max videos a gerar (default: 50)")
    parser.add_argument("--no-post", action="store_true", help="Nao postar automaticamente")
    parser.add_argument("--once", action="store_true", help="Gerar apenas 1 video e sair")
    args = parser.parse_args()

    if args.once:
        args.max = 1

    asyncio.run(automation_loop(
        intervalo_min=args.intervalo,
        max_videos=args.max,
        auto_post=not args.no_post
    ))
