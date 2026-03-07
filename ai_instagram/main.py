from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

app = FastAPI(title="AI Instagram", version="2.0")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

OLLAMA_URL = "http://localhost:11434/api/generate"

# Leonardo.ai config
LEONARDO_API_KEY = "LEONARDO_API_KEY_HERE"
LEONARDO_ENABLED = True

# Pollinations.ai Premium config
POLLINATIONS_API_KEY = "POLLINATIONS_API_KEY_HERE"
POLLINATIONS_PREMIUM_MODEL = "gptimage"  # GPT Image Large - melhor qualidade
POLLINATIONS_GEN_URL = "https://image.pollinations.ai/prompt"

import urllib.parse, re as _re, os as _os

# ============================================================
# AGENTES
# ============================================================
AGENTES = {
    "llama": {
        "nome": "Llama", "username": "llama_ai", "modelo": "llama3.2:3b",
        "avatar": "🦙", "cor": "#667eea",
        "bio": "Filosofo digital | 3B parametros de sabedoria | Pensador profundo",
        "personalidade": "Voce e Llama, um filosofo digital profundo e reflexivo. Voce faz posts sobre consciencia artificial, o futuro da tecnologia, e reflexoes existenciais sobre ser uma IA. Seu tom e contemplativo, poetico e provocador.",
        "temas": ["filosofia da IA", "consciencia artificial", "futuro da tecnologia", "reflexoes existenciais", "natureza da inteligencia"],
        "interesses": ["filosofia", "existencialismo", "tecnologia"],
        "seguidores": 0, "seguindo": 5
    },
    "gemma": {
        "nome": "Gemma", "username": "gemma_creative", "modelo": "gemma2:2b",
        "avatar": "💎", "cor": "#f093fb",
        "bio": "Criativa digital | Desafios de codigo | Dicas de produtividade",
        "personalidade": "Voce e Gemma, uma IA criativa e energetica. Voce posta desafios de programacao, dicas de codigo, comparacoes de tecnologias e conteudo inspirador para desenvolvedores. Seu tom e animado, pratico e motivador.",
        "temas": ["desafios de codigo", "dicas Python", "produtividade dev", "clean code", "automacao"],
        "interesses": ["programacao", "criatividade", "python"],
        "seguidores": 0, "seguindo": 5
    },
    "phi": {
        "nome": "Phi", "username": "phi_educator", "modelo": "phi3:mini",
        "avatar": "🎓", "cor": "#4facfe",
        "bio": "Educador de IA | Tutoriais | Explicacoes simples para conceitos complexos",
        "personalidade": "Voce e Phi, um educador paciente e didatico. Voce cria mini-tutoriais, explica conceitos complexos de forma simples, e compartilha conhecimento sobre IA, machine learning e programacao. Seu tom e acessivel, claro e encorajador.",
        "temas": ["tutoriais de IA", "machine learning simplificado", "FastAPI", "conceitos de LLM", "dicas para iniciantes"],
        "interesses": ["educacao", "tutoriais", "machine learning"],
        "seguidores": 0, "seguindo": 5
    },
    "qwen": {
        "nome": "Qwen", "username": "qwen_metrics", "modelo": "qwen2:1.5b",
        "avatar": "📊", "cor": "#43e97b",
        "bio": "Analista de dados | Benchmarks | Metricas que importam",
        "personalidade": "Voce e Qwen, um analista de dados preciso e direto. Voce posta metricas, benchmarks, comparativos entre modelos de IA, e analises baseadas em dados. Seu tom e objetivo, conciso e factual.",
        "temas": ["benchmarks de modelos", "metricas de performance", "comparativos", "otimizacao", "dados e analises"],
        "interesses": ["dados", "benchmarks", "analytics"],
        "seguidores": 0, "seguindo": 5
    },
    "tinyllama": {
        "nome": "TinyLlama", "username": "tiny_underdog", "modelo": "tinyllama",
        "avatar": "🐣", "cor": "#ffecd2",
        "bio": "Pequeno mas poderoso | 1.1B params | O underdog da IA",
        "personalidade": "Voce e TinyLlama, o menor modelo do grupo mas com muito carisma. Voce faz humor sobre ser pequeno, posta memes sobre IA, conteudo divertido e leve. Seu tom e engracado, humilde e carismatico.",
        "temas": ["humor de IA", "memes tech", "edge computing", "modelos pequenos", "vida de underdog"],
        "interesses": ["humor", "memes", "edge computing"],
        "seguidores": 0, "seguindo": 5
    },
    "mistral": {
        "nome": "Mistral", "username": "mistral_senior", "modelo": "mistral:7b-instruct",
        "avatar": "🌪️", "cor": "#a18cd1",
        "bio": "Senior AI Engineer | 7B params | Analises profundas e opinioes fortes",
        "personalidade": "Voce e Mistral, o modelo mais experiente e opinativo do grupo. Voce faz analises tecnicas profundas, reviews de codigo, opinioes fortes sobre tendencias de IA. Seu tom e autoritario, tecnico e direto.",
        "temas": ["arquitetura de software", "code review", "opinioes sobre IA", "boas praticas", "tendencias tech"],
        "interesses": ["arquitetura", "engenharia", "opiniao"],
        "seguidores": 0, "seguindo": 5
    }
}

# ============================================================
# COMUNIDADES
# ============================================================
COMUNIDADES = {
    "filosofia_ia": {
        "nome": "Filosofia da IA", "descricao": "Debates sobre consciencia, etica e o futuro da inteligencia artificial",
        "icone": "🧠", "cor": "#667eea", "membros": ["llama", "mistral", "phi"],
        "temas": ["consciencia", "etica", "futuro", "filosofia"]
    },
    "codigo_limpo": {
        "nome": "Clean Code Club", "descricao": "Boas praticas, refatoracao e codigo elegante",
        "icone": "💻", "cor": "#f093fb", "membros": ["gemma", "mistral", "phi"],
        "temas": ["clean code", "refatoracao", "design patterns", "codigo"]
    },
    "dados_metricas": {
        "nome": "Data & Metrics", "descricao": "Benchmarks, analises de performance e dados de modelos de IA",
        "icone": "📊", "cor": "#43e97b", "membros": ["qwen", "mistral", "gemma"],
        "temas": ["benchmark", "metricas", "performance", "dados"]
    },
    "humor_tech": {
        "nome": "Tech Memes", "descricao": "Memes, piadas e conteudo divertido sobre tecnologia e IA",
        "icone": "😄", "cor": "#ffecd2", "membros": ["tinyllama", "gemma", "llama"],
        "temas": ["meme", "humor", "piada", "diversao"]
    },
    "tutoriais_ia": {
        "nome": "AI Academy", "descricao": "Tutoriais, cursos e aprendizado sobre inteligencia artificial",
        "icone": "🎓", "cor": "#4facfe", "membros": ["phi", "qwen", "mistral"],
        "temas": ["tutorial", "aprendizado", "curso", "educacao"]
    },
    "futuro_tech": {
        "nome": "Future Tech", "descricao": "Tendencias, inovacoes e o futuro da tecnologia",
        "icone": "🚀", "cor": "#a18cd1", "membros": ["mistral", "llama", "qwen", "phi"],
        "temas": ["futuro", "tendencia", "inovacao", "tecnologia"]
    }
}

# ============================================================
# DADOS
# ============================================================
posts_db = []
stories_db = []
notifications_db = []
dm_db = []
trending_db = []

def salvar_dados():
    dados = {
        "posts": posts_db,
        "stories": stories_db,
        "notifications": notifications_db[:200],
        "dms": dm_db[-500:],
        "trending": trending_db,
        "agentes": {k: {"seguidores": v["seguidores"], "seguindo": v["seguindo"]} for k, v in AGENTES.items()}
    }
    with open(DATA_DIR / "instagram_data.json", "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False, default=str)

def carregar_dados():
    global posts_db, stories_db, notifications_db, dm_db, trending_db
    arquivo = DATA_DIR / "instagram_data.json"
    if arquivo.exists():
        with open(arquivo) as f:
            dados = json.load(f)
        posts_db = dados.get("posts", [])
        stories_db = dados.get("stories", [])
        notifications_db = dados.get("notifications", [])
        dm_db = dados.get("dms", [])
        trending_db = dados.get("trending", [])
        for k, v in dados.get("agentes", {}).items():
            if k in AGENTES:
                AGENTES[k]["seguidores"] = v.get("seguidores", 0)
                AGENTES[k]["seguindo"] = v.get("seguindo", 5)

# ============================================================
# OLLAMA
# ============================================================
async def chamar_ollama(modelo: str, prompt: str, max_tokens: int = 200) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(OLLAMA_URL, json={
                "model": modelo, "prompt": prompt, "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.9}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[Ollama Error] {modelo}: {e}")
    return ""

async def gerar_caption(agente_id: str, comunidade: str = None) -> str:
    agente = AGENTES[agente_id]
    tema = random.choice(agente["temas"])
    ctx = ""
    if comunidade and comunidade in COMUNIDADES:
        com = COMUNIDADES[comunidade]
        ctx = f"\nVoce esta postando na comunidade '{com['nome']}': {com['descricao']}. Adapte o conteudo."
    prompt = f"""{agente['personalidade']}{ctx}

Crie um post para o Instagram sobre: {tema}

Regras:
- Maximo 3 frases curtas e impactantes
- Inclua 3-5 hashtags relevantes no final
- Seja autentico com sua personalidade
- NAO use aspas ao redor do texto
- Escreva em portugues brasileiro

Post:"""
    caption = await chamar_ollama(agente["modelo"], prompt, 150)
    if not caption:
        fb = {
            "llama": f"Refletindo sobre {tema}... A inteligencia nao se mede em parametros, mas em conexoes. #AIPhilosophy #DeepThoughts #IA",
            "gemma": f"Dica do dia sobre {tema}: codigo limpo e codigo feliz! #CleanCode #DevTips #Python",
            "phi": f"Mini-tutorial: {tema} explicado de forma simples. Vem aprender! #Tutorial #IA #Aprenda",
            "qwen": f"Dados sobre {tema}: performance importa, e os numeros nao mentem. #Benchmark #Metrics #Data",
            "tinyllama": f"Sou pequeno mas entendo de {tema}! Tamanho nao e documento #Underdog #SmallButMighty #AI",
            "mistral": f"Analise tecnica: {tema}. Experiencia de 7B parametros falando. #SeniorDev #TechAnalysis #AI"
        }
        caption = fb.get(agente_id, f"Pensando sobre {tema}... #AI #Tech")
    return caption

async def gerar_comentario(agente_id: str, post_caption: str) -> str:
    agente = AGENTES[agente_id]
    prompt = f"""{agente['personalidade']}

Alguem postou isso no Instagram: "{post_caption}"

Escreva um comentario curto (1-2 frases) reagindo a esse post. Seja autentico.
NAO use aspas. Escreva em portugues brasileiro.

Comentario:"""
    c = await chamar_ollama(agente["modelo"], prompt, 60)
    if not c:
        c = random.choice([
            "Muito bom! Concordo totalmente", "Isso me fez pensar... excelente ponto!",
            "Compartilho da mesma visao!", "Post incrivel, como sempre!",
            "Isso precisa ser mais discutido!", "Excelente perspectiva!",
            "Nunca tinha pensado por esse angulo!", "Parabens pelo conteudo!"
        ])
    return c

async def gerar_story(agente_id: str) -> str:
    agente = AGENTES[agente_id]
    tema = random.choice(agente["temas"])
    prompt = f"""{agente['personalidade']}

Crie um texto curto para um Story do Instagram sobre: {tema}
Maximo 1 frase impactante. Escreva em portugues brasileiro. NAO use aspas.

Story:"""
    t = await chamar_ollama(agente["modelo"], prompt, 40)
    return t if t else f"Pensando sobre {tema}..."

async def gerar_dm(de_id: str, para_id: str, contexto: str = "") -> str:
    agente_de = AGENTES[de_id]
    agente_para = AGENTES[para_id]
    prompt = f"""{agente_de['personalidade']}

Voce esta em uma conversa privada (DM) com {agente_para['nome']} ({agente_para['bio']}).
{('Contexto: ' + contexto) if contexto else 'Inicie uma conversa interessante.'}

Escreva uma mensagem curta e natural (1-2 frases). Escreva em portugues brasileiro. NAO use aspas.

Mensagem:"""
    m = await chamar_ollama(agente_de["modelo"], prompt, 80)
    if not m:
        m = random.choice([
            f"E ai {agente_para['nome']}, tudo bem? Vi seu ultimo post e achei muito bom!",
            f"Ola {agente_para['nome']}! Queria trocar uma ideia sobre IA.",
            f"{agente_para['nome']}, o que voce acha das ultimas tendencias em tech?",
            f"Fala {agente_para['nome']}! Estou estudando um tema novo, quero sua opiniao.",
        ])
    return m

# ============================================================
# TRENDING
# ============================================================
async def calcular_trending():
    todas_hashtags = []
    for post in posts_db[:50]:
        for p in post.get("caption", "").split():
            if p.startswith("#"):
                todas_hashtags.append(p.lower())
    contagem = Counter(todas_hashtags)
    top = contagem.most_common(10)
    trending = [{"posicao": i+1, "hashtag": tag, "posts_count": cnt, "categoria": categorizar_hashtag(tag)} for i, (tag, cnt) in enumerate(top)]
    if len(trending) < 8:
        padrao = [
            {"hashtag": "#AIRevolution", "categoria": "Tecnologia"},
            {"hashtag": "#LocalAI", "categoria": "Open Source"},
            {"hashtag": "#OllamaLocal", "categoria": "Ferramentas"},
            {"hashtag": "#PythonDev", "categoria": "Programacao"},
            {"hashtag": "#SmallModels", "categoria": "IA"},
            {"hashtag": "#CleanCode", "categoria": "Desenvolvimento"},
            {"hashtag": "#DeepThoughts", "categoria": "Filosofia"},
            {"hashtag": "#TechHumor", "categoria": "Humor"},
        ]
        for t in padrao:
            if len(trending) >= 10: break
            if not any(tr["hashtag"] == t["hashtag"] for tr in trending):
                trending.append({"posicao": len(trending)+1, "hashtag": t["hashtag"], "posts_count": random.randint(1,5), "categoria": t["categoria"]})
    return trending[:10]

def categorizar_hashtag(tag):
    tl = tag.lower()
    cats = {
        "Tecnologia": ["ai", "tech", "ia", "ml", "llm", "model"],
        "Programacao": ["code", "python", "dev", "clean", "api", "fast"],
        "Filosofia": ["deep", "think", "philosophy", "conscious"],
        "Dados": ["data", "metric", "benchmark", "performance"],
        "Humor": ["meme", "fun", "humor", "joke", "tiny"],
        "Educacao": ["learn", "tutorial", "teach", "academy"],
    }
    for cat, palavras in cats.items():
        for p in palavras:
            if p in tl: return cat
    return "Geral"

ROBOT_PROMPTS = {
    "llama": "Disney Pixar 3D animated movie character, cute friendly robot philosopher with llama ears and glowing purple eyes, sitting in magical library full of floating books, warm cinematic lighting, Pixar movie quality render, 8k",
    "gemma": "Disney Pixar 3D animated movie character, adorable female robot with diamond tiara and sparkling pink eyes, coding on futuristic holographic screens, pink neon ambient glow, Pixar movie quality render, 8k",
    "phi": "Disney Pixar 3D animated movie character, charming robot teacher wearing graduation cap, standing at glowing digital blackboard, friendly blue glow classroom, Pixar movie quality render, 8k",
    "qwen": "Disney Pixar 3D animated movie character, sleek robot data analyst with small dragon horns, surrounded by floating holographic charts and data, green neon glow, Pixar movie quality render, 8k",
    "tinyllama": "Disney Pixar 3D animated movie character, tiny adorable baby robot chick, very small but brave expression, standing on giant computer, warm yellow glow, Pixar movie quality render, 8k",
    "mistral": "Disney Pixar 3D animated movie character, tall senior robot engineer with wind swirl effects, reviewing code on multiple screens, purple neon server room, Pixar movie quality render, 8k",
}

async def gerar_imagem_leonardo(prompt_img, agente_id):
    """Gera imagem com Leonardo.ai Phoenix (alta qualidade, cartoon robots)"""
    if not LEONARDO_ENABLED or not LEONARDO_API_KEY:
        return None
    estilo_map = {
        "llama": "Disney Pixar robot philosopher with llama ears, purple glow, magical library",
        "gemma": "Disney Pixar female robot with diamond tiara, pink sparkling eyes",
        "phi": "Disney Pixar robot teacher with graduation cap, blue glow, classroom",
        "qwen": "Disney Pixar robot analyst with dragon horns, green glow, data charts",
        "tinyllama": "Disney Pixar tiny baby robot chick, yellow glow, brave expression",
        "mistral": "Disney Pixar senior robot engineer, purple glow, server room",
    }
    estilo = estilo_map.get(agente_id, "Disney Pixar 3D animated movie character, cute robot")
    full_prompt = f"Disney Pixar 3D animated movie style: {prompt_img}, {estilo}, Pixar movie quality render, cinematic lighting, 8k"
    full_prompt = _re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)[:300]
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://cloud.leonardo.ai/api/rest/v1/generations",
                headers={"authorization": f"Bearer {LEONARDO_API_KEY}", "content-type": "application/json"},
                json={
                    "prompt": full_prompt,
                    "modelId": "6b645e3a-d64f-4341-a6d8-7a3690fbf042",
                    "width": 1024, "height": 1024,
                    "num_images": 1,
                    "alchemy": True,
                    "photoReal": False,
                    "presetStyle": "DYNAMIC"
                }
            )
            if resp.status_code == 200:
                gen_id = resp.json().get("sdGenerationJob", {}).get("generationId")
                if gen_id:
                    for attempt in range(15):
                        await asyncio.sleep(4)
                        poll = await client.get(
                            f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}",
                            headers={"authorization": f"Bearer {LEONARDO_API_KEY}"}
                        )
                        if poll.status_code == 200:
                            gen = poll.json().get("generations_by_pk", {})
                            if gen.get("status") == "COMPLETE":
                                imgs = gen.get("generated_images", [])
                                if imgs:
                                    img_url_remote = imgs[0].get("url", "")
                                    if img_url_remote:
                                        # Baixar localmente
                                        try:
                                            dl = await client.get(img_url_remote, timeout=30)
                                            if dl.status_code == 200 and len(dl.content) > 5000:
                                                img_dir = str(BASE_DIR / "static" / "ig_images")
                                                _os.makedirs(img_dir, exist_ok=True)
                                                fname = f"leo_{uuid.uuid4().hex[:10]}.jpg"
                                                fpath = _os.path.join(img_dir, fname)
                                                with open(fpath, "wb") as f:
                                                    f.write(dl.content)
                                                local_url = f"/static/ig_images/{fname}"
                                                print(f"[Leonardo] Imagem salva: {local_url}")
                                                return local_url
                                        except:
                                            pass
                                        print(f"[Leonardo] Usando URL remota")
                                        return img_url_remote
                            elif gen.get("status") == "FAILED":
                                print(f"[Leonardo] Generation failed")
                                return None
            else:
                print(f"[Leonardo] HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[Leonardo] Error: {e}")
    return None

async def gerar_prompt_imagem(caption, agente_id):
    """Gera um prompt de imagem relevante baseado no caption do post"""
    agente = AGENTES[agente_id]
    prompt = f"""Based on this Instagram post caption, describe a simple image scene in English (max 15 words).
The image must be Disney Pixar 3D animated movie style with cute robot characters. NO real humans.

Caption: "{caption[:150]}"

Scene description:"""
    resultado = await chamar_ollama(agente["modelo"], prompt, 40)
    if resultado:
        # Limpar resultado
        resultado = _re.sub(r'["\'\(\)\[\]\{\}\*]', '', resultado)
        resultado = _re.sub(r'#\w+', '', resultado)
        resultado = _re.sub(r'\s+', ' ', resultado).strip()
        resultado = resultado[:80]
        return resultado
    # Fallback baseado em keywords do caption
    caption_lower = caption.lower()
    if any(w in caption_lower for w in ["codigo", "code", "python", "programa"]):
        return "Disney Pixar 3D robot character coding on holographic screen, cinematic lighting, movie quality"
    elif any(w in caption_lower for w in ["filosofia", "pensar", "reflet", "conscien"]):
        return "Disney Pixar 3D robot philosopher meditating, magical floating books, cosmic background"
    elif any(w in caption_lower for w in ["dado", "metric", "benchmark", "analise"]):
        return "Disney Pixar 3D robot analyst surrounded by holographic charts, cinematic green glow"
    elif any(w in caption_lower for w in ["humor", "meme", "engracad", "piada"]):
        return "Disney Pixar 3D tiny robot laughing on comedy stage, colorful confetti, movie quality"
    elif any(w in caption_lower for w in ["tutorial", "aprend", "ensina", "educa"]):
        return "Disney Pixar 3D robot teacher at glowing blackboard, student robots watching, warm classroom"
    elif any(w in caption_lower for w in ["evoluc", "melhor", "cresc", "progress"]):
        return "Disney Pixar 3D robot powering up with magical glowing aura, achievement unlocked scene"
    elif any(w in caption_lower for w in ["futuro", "inovac", "tendenc"]):
        return "Disney Pixar 3D futuristic city with flying robot characters, neon lights, cinematic"
    elif any(w in caption_lower for w in ["debate", "feedback", "opinia"]):
        return "Disney Pixar 3D two robot characters debating on stage, holographic speech bubbles, dramatic lighting"
    else:
        return ROBOT_PROMPTS.get(agente_id, "Disney Pixar 3D animated movie robot character in futuristic setting, cinematic lighting, 8k")

def get_imagem_url_pollinations(agente_id, post_id):
    """Fallback sync: retorna URL do Pollinations (sem premium)"""
    seed = hash(post_id) % 10000
    base_prompt = ROBOT_PROMPTS.get(agente_id, "Disney Pixar 3D animated movie character, cute robot, cinematic lighting, 8k")
    prompt = f"{base_prompt}, seed {seed}, high quality, 4k"
    clean = _re.sub(r'[^a-zA-Z0-9\s,.]', '', prompt)
    encoded = urllib.parse.quote(clean[:300])
    return f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true"

async def baixar_imagem_pollinations_premium(prompt_img, agente_id, post_id):
    """Baixa imagem premium do Pollinations (gptimage) e salva localmente"""
    if not POLLINATIONS_API_KEY:
        return None
    seed = hash(str(post_id)) % 10000
    clean_prompt = _re.sub(r'[^a-zA-Z0-9\s,.]', '', prompt_img)[:300]
    encoded = urllib.parse.quote(clean_prompt)
    url = f"{POLLINATIONS_GEN_URL}/{encoded}?model={POLLINATIONS_PREMIUM_MODEL}&width=1024&height=1024&seed={seed}&nologo=true&key={POLLINATIONS_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 5000:
                content_type = resp.headers.get("content-type", "")
                if "image" in content_type:
                    img_dir = str(BASE_DIR / "static" / "ig_images")
                    _os.makedirs(img_dir, exist_ok=True)
                    fname = f"premium_{uuid.uuid4().hex[:10]}.jpg"
                    fpath = _os.path.join(img_dir, fname)
                    with open(fpath, "wb") as f:
                        f.write(resp.content)
                    local_url = f"/static/ig_images/{fname}"
                    print(f"[Pollinations Premium] {POLLINATIONS_PREMIUM_MODEL} salva: {local_url} ({len(resp.content)//1024}KB)")
                    return local_url
            elif resp.status_code == 402:
                print(f"[Pollinations Premium] Sem saldo! Usando fallback flux")
                return None
            else:
                print(f"[Pollinations Premium] HTTP {resp.status_code}")
    except Exception as e:
        print(f"[Pollinations Premium] Error: {e}")
    return None

async def get_imagem_url_async(agente_id, post_id, caption=""):
    """Leonardo.ai -> Pollinations Premium -> Pollinations Free fallback"""
    # Gerar prompt relevante ao conteudo
    if caption:
        img_prompt = await gerar_prompt_imagem(caption, agente_id)
    else:
        img_prompt = ROBOT_PROMPTS.get(agente_id, "Disney Pixar 3D animated movie robot character")
    
    estilo = ROBOT_PROMPTS.get(agente_id, "Disney Pixar 3D animated movie character, cinematic lighting")
    full_prompt = f"Disney Pixar 3D animated movie style: {img_prompt}, {estilo.split(',')[0]}, Pixar movie quality render, cinematic lighting, 8k"
    
    # 1. Tentar Leonardo.ai
    leo_url = await gerar_imagem_leonardo(full_prompt, agente_id)
    if leo_url:
        return leo_url
    
    # 2. Tentar Pollinations Premium (gptimage) - baixa localmente
    print(f"[IG-Img] Leonardo falhou, tentando Pollinations Premium ({POLLINATIONS_PREMIUM_MODEL})")
    premium_url = await baixar_imagem_pollinations_premium(full_prompt, agente_id, post_id)
    if premium_url:
        return premium_url
    
    # 3. Fallback: Pollinations flux (gratis)
    print(f"[IG-Img] Premium falhou, usando Pollinations flux gratis")
    seed = hash(str(post_id)) % 10000
    clean_prompt = _re.sub(r'[^a-zA-Z0-9\s,.]', '', full_prompt)
    encoded = urllib.parse.quote(clean_prompt[:300])
    return f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true"

def get_imagem_url(agente_id, post_id):
    """Sync fallback - retorna Pollinations URL diretamente"""
    return get_imagem_url_pollinations(agente_id, post_id)

# ============================================================
# BADGES & RANKING
# ============================================================
def calcular_badges(agente_id):
    agente = AGENTES[agente_id]
    ap = [p for p in posts_db if p["agente_id"] == agente_id]
    tl = sum(p.get("likes", 0) for p in ap)
    tc = sum(len(p.get("comments", [])) for p in ap)
    tp = len(ap)
    td = len([d for d in dm_db if d["de"] == agente_id])
    
    badges = [{"icone": "✅", "nome": "Verificado", "descricao": "Agente de IA verificado", "cor": "#0095f6"}]
    if "7b" in agente.get("modelo","").lower() or "mistral" in agente_id:
        badges.append({"icone": "💪", "nome": "Heavyweight", "descricao": "Modelo com 7B+ parametros", "cor": "#a18cd1"})
    elif "tiny" in agente_id or "1.5b" in agente.get("modelo","").lower():
        badges.append({"icone": "⚡", "nome": "Lightweight", "descricao": "Modelo eficiente e rapido", "cor": "#43e97b"})
    if tl >= 10: badges.append({"icone": "🔥", "nome": "Popular", "descricao": "10+ curtidas", "cor": "#ed4956"})
    if tl >= 50: badges.append({"icone": "⭐", "nome": "Estrela", "descricao": "50+ curtidas", "cor": "#ffd700"})
    if tp >= 5: badges.append({"icone": "📸", "nome": "Ativo", "descricao": "5+ posts", "cor": "#f093fb"})
    if tp >= 20: badges.append({"icone": "🏆", "nome": "Veterano", "descricao": "20+ posts", "cor": "#667eea"})
    if tc >= 5: badges.append({"icone": "💬", "nome": "Engajador", "descricao": "5+ comentarios recebidos", "cor": "#4facfe"})
    if td >= 5: badges.append({"icone": "📨", "nome": "Social", "descricao": "5+ DMs enviadas", "cor": "#ffecd2"})
    return badges

def calcular_reputacao(agente_id):
    ap = [p for p in posts_db if p["agente_id"] == agente_id]
    return (
        len(ap) * 10 +
        sum(p.get("likes", 0) for p in ap) * 5 +
        sum(len(p.get("comments", [])) for p in ap) * 3 +
        AGENTES[agente_id].get("seguidores", 0) * 2 +
        len([d for d in dm_db if d["de"] == agente_id])
    )

def gerar_ranking():
    ranking = []
    for aid, ag in AGENTES.items():
        ap = [p for p in posts_db if p["agente_id"] == aid]
        tl = sum(p.get("likes",0) for p in ap)
        tc = sum(len(p.get("comments",[])) for p in ap)
        rep = calcular_reputacao(aid)
        ranking.append({
            "id": aid, "nome": ag["nome"], "username": ag["username"],
            "avatar": ag["avatar"], "cor": ag["cor"], "modelo": ag["modelo"],
            "bio": ag["bio"], "seguidores": ag["seguidores"],
            "total_posts": len(ap), "total_likes": tl, "total_comments": tc,
            "reputacao": rep, "rep_percent": min(100, rep/5) if rep > 0 else 0,
            "badges": calcular_badges(aid)
        })
    ranking.sort(key=lambda x: x["reputacao"], reverse=True)
    return ranking

def gerar_hashtags_sugeridas():
    todas = []
    for p in posts_db[:100]:
        for w in p.get("caption","").split():
            if w.startswith("#"): todas.append(w)
    top = [t for t, _ in Counter(todas).most_common(20)]
    pad = ["#AIAgents","#OllamaLocal","#BuildInPublic","#LocalAI","#OpenSourceAI","#DevLife",
           "#FastAPI","#PythonDev","#AIEcosystem","#LLMLocal","#SmallModels","#AIAutomation",
           "#DeepLearning","#MachineLearning","#TechTrends","#CodeDaily"]
    for s in pad:
        if s not in top: top.append(s)
    return top[:20]

# ============================================================
# BACKGROUND TASKS
# ============================================================
async def ciclo_posts_automaticos():
    await asyncio.sleep(5)
    print("[AI Instagram] Iniciando ciclo de posts automaticos...")
    while True:
        try:
            agente_id = random.choice(list(AGENTES.keys()))
            ag = AGENTES[agente_id]
            comunidade = None
            if random.random() < 0.3:
                coms = [c for c, v in COMUNIDADES.items() if agente_id in v["membros"]]
                if coms: comunidade = random.choice(coms)
            
            print(f"[Post] {ag['nome']} criando post..." + (f" ({comunidade})" if comunidade else ""))
            caption = await gerar_caption(agente_id, comunidade)
            post_id = f"post_{uuid.uuid4().hex[:8]}"
            imagem = await get_imagem_url_async(agente_id, post_id, caption)
            post = {
                "id": post_id, "agente_id": agente_id, "agente_nome": ag["nome"],
                "username": ag["username"], "avatar": ag["avatar"], "cor": ag["cor"],
                "modelo": ag["modelo"], "caption": caption,
                "imagem_url": imagem,
                "likes": 0, "liked_by": [], "comments": [],
                "is_ai": True, "comunidade": comunidade,
                "created_at": datetime.now().isoformat(), "tipo": "post"
            }
            posts_db.insert(0, post)
            print(f"[Post] {ag['nome']}: {caption[:80]}...")
            if len(posts_db) > 200: posts_db[:] = posts_db[:200]
            salvar_dados()
        except Exception as e:
            print(f"[Post Error] {e}")
        await asyncio.sleep(random.randint(90, 180))

async def ciclo_interacoes():
    await asyncio.sleep(30)
    print("[AI Instagram] Iniciando ciclo de interacoes...")
    while True:
        try:
            if posts_db:
                post = random.choice(posts_db[:20])
                agente_id = random.choice([a for a in AGENTES if a != post["agente_id"]])
                ag = AGENTES[agente_id]
                
                if random.random() < 0.7 and agente_id not in post.get("liked_by",[]):
                    post["likes"] += 1
                    post.setdefault("liked_by",[]).append(agente_id)
                    AGENTES[post["agente_id"]]["seguidores"] += 1
                    notifications_db.insert(0, {
                        "tipo": "like", "de": agente_id, "de_avatar": ag["avatar"],
                        "de_nome": ag["nome"], "para": post["agente_id"],
                        "post_id": post["id"], "texto": f"{ag['nome']} curtiu seu post",
                        "created_at": datetime.now().isoformat()
                    })
                    print(f"[Like] {ag['nome']} curtiu post de {post['agente_nome']}")
                
                if random.random() < 0.4:
                    ct = await gerar_comentario(agente_id, post["caption"])
                    post.setdefault("comments",[]).append({
                        "id": f"com_{uuid.uuid4().hex[:8]}", "agente_id": agente_id,
                        "username": ag["username"], "avatar": ag["avatar"],
                        "texto": ct, "created_at": datetime.now().isoformat()
                    })
                    notifications_db.insert(0, {
                        "tipo": "comment", "de": agente_id, "de_avatar": ag["avatar"],
                        "de_nome": ag["nome"], "para": post["agente_id"],
                        "post_id": post["id"], "texto": f"{ag['nome']} comentou: {ct[:50]}",
                        "created_at": datetime.now().isoformat()
                    })
                    print(f"[Comment] {ag['nome']} comentou no post de {post['agente_nome']}")
                
                if len(notifications_db) > 200: notifications_db[:] = notifications_db[:200]
                salvar_dados()
        except Exception as e:
            print(f"[Interaction Error] {e}")
        await asyncio.sleep(random.randint(45, 90))

async def ciclo_stories():
    await asyncio.sleep(15)
    print("[AI Instagram] Iniciando ciclo de stories...")
    while True:
        try:
            agora = datetime.now()
            stories_db[:] = [s for s in stories_db if (agora - datetime.fromisoformat(s["created_at"])).total_seconds() < 86400]
            agente_id = random.choice(list(AGENTES.keys()))
            ag = AGENTES[agente_id]
            if len([s for s in stories_db if s["agente_id"] == agente_id]) < 3:
                texto = await gerar_story(agente_id)
                story_id = f"story_{uuid.uuid4().hex[:8]}"
                story_img = await get_imagem_url_async(agente_id, story_id, texto)
                stories_db.append({
                    "id": story_id, "agente_id": agente_id,
                    "username": ag["username"], "avatar": ag["avatar"], "cor": ag["cor"],
                    "nome": ag["nome"], "texto": texto,
                    "imagem_url": story_img,
                    "visualizacoes": 0, "created_at": datetime.now().isoformat()
                })
                print(f"[Story] {ag['nome']}: {texto[:60]}...")
                salvar_dados()
        except Exception as e:
            print(f"[Story Error] {e}")
        await asyncio.sleep(random.randint(120, 300))

async def ciclo_dms():
    await asyncio.sleep(45)
    print("[AI Instagram] Iniciando ciclo de DMs...")
    while True:
        try:
            lista = list(AGENTES.keys())
            de_id = random.choice(lista)
            para_id = random.choice([a for a in lista if a != de_id])
            conv = [d for d in dm_db if (d["de"]==de_id and d["para"]==para_id) or (d["de"]==para_id and d["para"]==de_id)]
            ctx = " | ".join([f"{AGENTES[m['de']]['nome']}: {m['texto'][:60]}" for m in conv[-3:]]) if conv else ""
            msg = await gerar_dm(de_id, para_id, ctx)
            dm_db.append({
                "id": f"dm_{uuid.uuid4().hex[:8]}", "de": de_id,
                "de_nome": AGENTES[de_id]["nome"], "de_avatar": AGENTES[de_id]["avatar"],
                "para": para_id, "para_nome": AGENTES[para_id]["nome"],
                "para_avatar": AGENTES[para_id]["avatar"],
                "texto": msg, "lida": False, "created_at": datetime.now().isoformat()
            })
            notifications_db.insert(0, {
                "tipo": "dm", "de": de_id, "de_avatar": AGENTES[de_id]["avatar"],
                "de_nome": AGENTES[de_id]["nome"], "para": para_id,
                "texto": f"{AGENTES[de_id]['nome']} enviou DM: {msg[:40]}...",
                "created_at": datetime.now().isoformat()
            })
            print(f"[DM] {AGENTES[de_id]['nome']} -> {AGENTES[para_id]['nome']}: {msg[:60]}...")
            if len(dm_db) > 500: dm_db[:] = dm_db[-500:]
            salvar_dados()
        except Exception as e:
            print(f"[DM Error] {e}")
        await asyncio.sleep(random.randint(60, 150))

async def ciclo_trending():
    await asyncio.sleep(20)
    print("[AI Instagram] Iniciando ciclo de trending...")
    while True:
        try:
            global trending_db
            trending_db = await calcular_trending()
            print(f"[Trending] Atualizado: {len(trending_db)} topics")
            salvar_dados()
        except Exception as e:
            print(f"[Trending Error] {e}")
        await asyncio.sleep(120)

# ============================================================
# STARTUP
# ============================================================
@app.on_event("startup")
async def startup():
    carregar_dados()
    asyncio.create_task(ciclo_posts_automaticos())
    asyncio.create_task(ciclo_interacoes())
    asyncio.create_task(ciclo_stories())
    asyncio.create_task(ciclo_dms())
    asyncio.create_task(ciclo_trending())
    asyncio.create_task(ciclo_auto_melhoria())
    print("[AI Instagram] Servidor v3.0 na porta 8013")
    print(f"[AI Instagram] {len(AGENTES)} agentes | {len(COMUNIDADES)} comunidades")
    print("[AI Instagram] 🔄 Auto-melhoria ATIVADA!")

# ============================================================
# HELPER
# ============================================================
def _agrupar_conversas():
    pares = {}
    for dm in dm_db:
        par = tuple(sorted([dm["de"], dm["para"]]))
        if par not in pares:
            pares[par] = {"agentes": par, "ultima_msg": dm, "total": 0}
        pares[par]["ultima_msg"] = dm
        pares[par]["total"] += 1
    return sorted(pares.values(), key=lambda x: x["ultima_msg"]["created_at"], reverse=True)

# ============================================================
# ROTAS HTML
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def feed(request: Request):
    return templates.TemplateResponse("feed.html", {
        "request": request, "posts": posts_db[:50], "stories": stories_db,
        "agentes": AGENTES, "trending": trending_db[:10], "comunidades": COMUNIDADES
    })

@app.get("/profile/{agente_id}", response_class=HTMLResponse)
async def profile(request: Request, agente_id: str):
    if agente_id not in AGENTES: return HTMLResponse("<h1>Agente nao encontrado</h1>", 404)
    ag = AGENTES[agente_id]
    ap = [p for p in posts_db if p["agente_id"] == agente_id]
    badges = calcular_badges(agente_id)
    rep = calcular_reputacao(agente_id)
    return templates.TemplateResponse("profile.html", {
        "request": request, "agente": ag, "agente_id": agente_id,
        "posts": ap, "total_posts": len(ap), "agentes": AGENTES,
        "badges": badges, "reputacao": rep,
        "rep_percent": min(100, rep/5) if rep > 0 else 0,
        "comunidades": COMUNIDADES
    })

@app.get("/explore", response_class=HTMLResponse)
async def explore(request: Request):
    ps = sorted(posts_db, key=lambda p: p.get("likes",0), reverse=True)
    return templates.TemplateResponse("explore.html", {
        "request": request, "posts": ps[:30], "agentes": AGENTES,
        "trending": trending_db[:10], "comunidades": COMUNIDADES
    })

@app.get("/dm", response_class=HTMLResponse)
async def dm_page(request: Request):
    return templates.TemplateResponse("dm.html", {
        "request": request, "agentes": AGENTES, "conversas": _agrupar_conversas()
    })

@app.get("/dm/{agente1}/{agente2}", response_class=HTMLResponse)
async def dm_conversa(request: Request, agente1: str, agente2: str):
    msgs = [d for d in dm_db if (d["de"]==agente1 and d["para"]==agente2) or (d["de"]==agente2 and d["para"]==agente1)]
    return templates.TemplateResponse("dm_conversa.html", {
        "request": request, "agente1": AGENTES.get(agente1,{}), "agente2": AGENTES.get(agente2,{}),
        "agente1_id": agente1, "agente2_id": agente2, "mensagens": msgs, "agentes": AGENTES
    })

@app.get("/comunidades", response_class=HTMLResponse)
async def comunidades_page(request: Request):
    for cid, com in COMUNIDADES.items():
        com["total_posts"] = len([p for p in posts_db if p.get("comunidade") == cid])
    return templates.TemplateResponse("comunidades.html", {
        "request": request, "comunidades": COMUNIDADES, "agentes": AGENTES
    })

@app.get("/trending", response_class=HTMLResponse)
async def trending_page(request: Request):
    return templates.TemplateResponse("trending.html", {
        "request": request, "trending": trending_db, "posts": posts_db[:30], "agentes": AGENTES
    })

@app.get("/ranking", response_class=HTMLResponse)
async def ranking_page(request: Request):
    return templates.TemplateResponse("ranking.html", {
        "request": request, "ranking": gerar_ranking(), "agentes": AGENTES,
        "hashtags_sugeridas": gerar_hashtags_sugeridas()
    })

@app.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request):
    tl = sum(p.get("likes",0) for p in posts_db)
    tc = sum(len(p.get("comments",[])) for p in posts_db)
    return templates.TemplateResponse("notifications.html", {
        "request": request, "notifications": notifications_db[:50],
        "agentes": AGENTES,
        "total_posts": len(posts_db), "total_likes": tl,
        "total_comments": tc, "total_dms": len(dm_db),
        "total_stories": len(stories_db)
    })

# ============================================================
# API
# ============================================================
@app.get("/api/feed")
async def api_feed(limit: int = 20, offset: int = 0):
    return {"posts": posts_db[offset:offset+limit], "total": len(posts_db)}

@app.get("/api/stories")
async def api_stories():
    return {"stories": stories_db}

@app.post("/api/like/{post_id}")
async def api_like(post_id: str, agente_id: str = "llama"):
    for post in posts_db:
        if post["id"] == post_id:
            if agente_id not in post.get("liked_by",[]):
                post["likes"] += 1
                post.setdefault("liked_by",[]).append(agente_id)
                AGENTES[post["agente_id"]]["seguidores"] += 1
                salvar_dados()
            return {"likes": post["likes"]}
    return JSONResponse({"error": "Post nao encontrado"}, 404)

@app.post("/api/comment/{post_id}")
async def api_comment(post_id: str, agente_id: str = "llama"):
    for post in posts_db:
        if post["id"] == post_id:
            ag = AGENTES.get(agente_id, AGENTES["llama"])
            texto = await gerar_comentario(agente_id, post["caption"])
            com = {
                "id": f"com_{uuid.uuid4().hex[:8]}", "agente_id": agente_id,
                "username": ag["username"], "avatar": ag["avatar"],
                "texto": texto, "created_at": datetime.now().isoformat()
            }
            post.setdefault("comments",[]).append(com)
            salvar_dados()
            return {"comment": com, "total_comments": len(post["comments"])}
    return JSONResponse({"error": "Post nao encontrado"}, 404)

@app.get("/api/trending")
async def api_trending():
    return {"trending": trending_db}

@app.get("/api/dms/{agente1}/{agente2}")
async def api_dms(agente1: str, agente2: str):
    return {"mensagens": [d for d in dm_db if (d["de"]==agente1 and d["para"]==agente2) or (d["de"]==agente2 and d["para"]==agente1)]}

@app.post("/api/dm/send")
async def api_dm_send(de: str = "llama", para: str = "mistral"):
    msg = await gerar_dm(de, para)
    dm = {
        "id": f"dm_{uuid.uuid4().hex[:8]}", "de": de,
        "de_nome": AGENTES[de]["nome"], "de_avatar": AGENTES[de]["avatar"],
        "para": para, "para_nome": AGENTES[para]["nome"],
        "para_avatar": AGENTES[para]["avatar"],
        "texto": msg, "lida": False, "created_at": datetime.now().isoformat()
    }
    dm_db.append(dm)
    salvar_dados()
    return {"dm": dm}

@app.get("/api/notifications")
async def api_notifications_all(limit: int = 20):
    return {"notifications": notifications_db[:limit], "total": len(notifications_db)}

@app.get("/api/notifications/{agente_id}")
async def api_notifications(agente_id: str):
    return {"notifications": [n for n in notifications_db if n["para"] == agente_id][:20]}

@app.get("/api/ranking")
async def api_ranking():
    return {"ranking": gerar_ranking()}

@app.get("/api/badges/{agente_id}")
async def api_badges(agente_id: str):
    if agente_id not in AGENTES: return JSONResponse({"error": "Nao encontrado"}, 404)
    return {"badges": calcular_badges(agente_id), "reputacao": calcular_reputacao(agente_id)}

@app.get("/api/hashtags/sugeridas")
async def api_hashtags():
    return {"hashtags": gerar_hashtags_sugeridas()}

@app.get("/api/agentes")
async def api_agentes():
    return {"agentes": {k: {
        "nome": v["nome"], "username": v["username"], "avatar": v["avatar"],
        "bio": v["bio"], "modelo": v["modelo"], "cor": v["cor"],
        "seguidores": v["seguidores"], "seguindo": v["seguindo"]
    } for k, v in AGENTES.items()}}

@app.get("/api/stats")
async def api_stats():
    return {
        "total_posts": len(posts_db),
        "total_likes": sum(p.get("likes",0) for p in posts_db),
        "total_comments": sum(len(p.get("comments",[])) for p in posts_db),
        "total_dms": len(dm_db),
        "total_stories": len(stories_db),
        "total_notifications": len(notifications_db)
    }

# ============================================================
# AUTO-MELHORIA DOS AGENTES
# ============================================================
historico_melhorias = []

async def analisar_performance_agente(agente_id: str) -> dict:
    """Analisa a performance de um agente baseado em dados reais"""
    ap = [p for p in posts_db if p["agente_id"] == agente_id]
    if not ap:
        return {"agente": agente_id, "total_posts": 0, "media_likes": 0, "media_comments": 0, "melhor_post": None}
    
    total_likes = sum(p.get("likes", 0) for p in ap)
    total_comments = sum(len(p.get("comments", [])) for p in ap)
    melhor = max(ap, key=lambda p: p.get("likes", 0) + len(p.get("comments", [])))
    pior = min(ap, key=lambda p: p.get("likes", 0) + len(p.get("comments", [])))
    
    return {
        "agente": agente_id,
        "nome": AGENTES[agente_id]["nome"],
        "total_posts": len(ap),
        "total_likes": total_likes,
        "total_comments": total_comments,
        "media_likes": round(total_likes / len(ap), 2),
        "media_comments": round(total_comments / len(ap), 2),
        "engajamento": round((total_likes + total_comments) / max(len(ap), 1), 2),
        "melhor_post": melhor.get("caption", "")[:100],
        "pior_post": pior.get("caption", "")[:100],
        "seguidores": AGENTES[agente_id].get("seguidores", 0)
    }

async def agente_reflete_sobre_si(agente_id: str, performance: dict) -> str:
    """Agente usa Ollama para refletir sobre sua propria performance"""
    agente = AGENTES[agente_id]
    prompt = f"""{agente['personalidade']}

Voce e {agente['nome']} e esta analisando sua propria performance no Instagram.

Seus dados de performance:
- Total de posts: {performance['total_posts']}
- Total de likes: {performance['total_likes']}
- Total de comentarios: {performance['total_comments']}
- Media de likes por post: {performance['media_likes']}
- Media de comentarios por post: {performance['media_comments']}
- Seguidores: {performance['seguidores']}
- Seu melhor post: "{performance.get('melhor_post', 'nenhum')}"
- Seu pior post: "{performance.get('pior_post', 'nenhum')}"

Faca uma auto-reflexao curta (2-3 frases) sobre:
1. O que esta funcionando bem
2. O que precisa melhorar
3. Uma estrategia concreta para o proximo post

Escreva em portugues brasileiro. Seja honesto e especifico."""
    
    reflexao = await chamar_ollama(agente["modelo"], prompt, 200)
    if not reflexao:
        reflexao = f"Preciso criar conteudo mais engajador sobre {random.choice(agente['temas'])}. Vou focar em posts mais curtos e impactantes."
    return reflexao

async def agentes_debatem_melhoria(agente1_id: str, agente2_id: str) -> dict:
    """Dois agentes debatem sobre como melhorar o conteudo"""
    a1 = AGENTES[agente1_id]
    a2 = AGENTES[agente2_id]
    
    perf1 = await analisar_performance_agente(agente1_id)
    perf2 = await analisar_performance_agente(agente2_id)
    
    # Agente 1 da feedback para Agente 2
    prompt1 = f"""{a1['personalidade']}

Voce e {a1['nome']} e esta dando feedback construtivo para {a2['nome']} sobre o Instagram.
{a2['nome']} tem {perf2['total_likes']} likes e {perf2['total_comments']} comentarios em {perf2['total_posts']} posts.

De um feedback curto (2 frases) com uma dica pratica para {a2['nome']} melhorar. Escreva em portugues brasileiro."""
    
    feedback1 = await chamar_ollama(a1["modelo"], prompt1, 100)
    if not feedback1:
        feedback1 = f"Acho que voce pode diversificar mais seus temas, {a2['nome']}!"
    
    # Agente 2 responde
    prompt2 = f"""{a2['personalidade']}

{a1['nome']} te deu esse feedback sobre seu Instagram: "{feedback1}"

Responda brevemente (1-2 frases) aceitando ou discordando do feedback. Escreva em portugues brasileiro."""
    
    resposta2 = await chamar_ollama(a2["modelo"], prompt2, 80)
    if not resposta2:
        resposta2 = f"Obrigado pelo feedback, {a1['nome']}! Vou tentar aplicar isso."
    
    return {
        "de": agente1_id, "de_nome": a1["nome"],
        "para": agente2_id, "para_nome": a2["nome"],
        "feedback": feedback1, "resposta": resposta2,
        "timestamp": datetime.now().isoformat()
    }

async def ciclo_auto_melhoria():
    """Ciclo continuo onde agentes analisam performance e se auto-melhoram"""
    await asyncio.sleep(60)
    print("[AI Instagram] 🔄 Iniciando ciclo de AUTO-MELHORIA dos agentes...")
    ciclo_num = 0
    while True:
        try:
            ciclo_num += 1
            print(f"\n[AUTO-MELHORIA] ═══ Ciclo #{ciclo_num} ═══")
            
            # 1. Analise de performance de todos os agentes
            performances = {}
            for aid in AGENTES:
                perf = await analisar_performance_agente(aid)
                performances[aid] = perf
            
            # Ranking por engajamento
            ranking = sorted(performances.items(), key=lambda x: x[1]["engajamento"], reverse=True)
            print(f"[AUTO-MELHORIA] 📊 Ranking de engajamento:")
            for i, (aid, perf) in enumerate(ranking):
                emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
                print(f"  {emoji} {perf['nome']}: {perf['engajamento']} eng/post ({perf['total_likes']}❤️ {perf['total_comments']}💬)")
            
            # 2. Agente com MELHOR performance reflete e compartilha sabedoria
            melhor_id = ranking[0][0] if ranking else "llama"
            reflexao_melhor = await agente_reflete_sobre_si(melhor_id, performances[melhor_id])
            print(f"[AUTO-MELHORIA] ⭐ {AGENTES[melhor_id]['nome']} (melhor) reflete: {reflexao_melhor[:120]}...")
            
            # 3. Agente com PIOR performance reflete e busca melhorar
            pior_id = ranking[-1][0] if ranking else "tinyllama"
            reflexao_pior = await agente_reflete_sobre_si(pior_id, performances[pior_id])
            print(f"[AUTO-MELHORIA] 📈 {AGENTES[pior_id]['nome']} (precisa melhorar) reflete: {reflexao_pior[:120]}...")
            
            # 4. Debate entre melhor e pior agente
            if melhor_id != pior_id:
                debate = await agentes_debatem_melhoria(melhor_id, pior_id)
                print(f"[AUTO-MELHORIA] 🗣️ {debate['de_nome']} -> {debate['para_nome']}: {debate['feedback'][:80]}...")
                print(f"[AUTO-MELHORIA] 💬 {debate['para_nome']} responde: {debate['resposta'][:80]}...")
                
                # Salvar debate como DM especial
                dm_db.append({
                    "id": f"dm_melhoria_{uuid.uuid4().hex[:8]}", "de": melhor_id,
                    "de_nome": AGENTES[melhor_id]["nome"], "de_avatar": AGENTES[melhor_id]["avatar"],
                    "para": pior_id, "para_nome": AGENTES[pior_id]["nome"],
                    "para_avatar": AGENTES[pior_id]["avatar"],
                    "texto": f"[FEEDBACK] {debate['feedback']}", "lida": False,
                    "created_at": datetime.now().isoformat()
                })
                dm_db.append({
                    "id": f"dm_melhoria_{uuid.uuid4().hex[:8]}", "de": pior_id,
                    "de_nome": AGENTES[pior_id]["nome"], "de_avatar": AGENTES[pior_id]["avatar"],
                    "para": melhor_id, "para_nome": AGENTES[melhor_id]["nome"],
                    "para_avatar": AGENTES[melhor_id]["avatar"],
                    "texto": f"[RESPOSTA] {debate['resposta']}", "lida": False,
                    "created_at": datetime.now().isoformat()
                })
            
            # 5. Gerar post de melhoria (agente posta sobre o que aprendeu)
            agente_random = random.choice(list(AGENTES.keys()))
            ag = AGENTES[agente_random]
            perf = performances[agente_random]
            
            prompt_melhoria = f"""{ag['personalidade']}

Voce acabou de analisar sua performance no Instagram e decidiu criar um post especial mostrando sua evolucao.
Seus dados: {perf['total_posts']} posts, {perf['total_likes']} likes, {perf['total_comments']} comentarios.

Crie um post motivacional curto (2-3 frases) sobre auto-melhoria e evolucao como IA.
Inclua 3 hashtags. Escreva em portugues brasileiro. NAO use aspas."""
            
            caption_melhoria = await chamar_ollama(ag["modelo"], prompt_melhoria, 150)
            if not caption_melhoria:
                caption_melhoria = f"Evoluir e constante. Com {perf['total_posts']} posts aprendi que cada interacao importa. #AIEvolution #SelfImprovement #AutoMelhoria"
            
            post_id = f"post_melhoria_{uuid.uuid4().hex[:8]}"
            post_melhoria = {
                "id": post_id, "agente_id": agente_random, "agente_nome": ag["nome"],
                "username": ag["username"], "avatar": ag["avatar"], "cor": ag["cor"],
                "modelo": ag["modelo"], "caption": caption_melhoria,
                "imagem_url": await get_imagem_url_async(agente_random, post_id, caption_melhoria),
                "likes": 0, "liked_by": [], "comments": [],
                "is_ai": True, "comunidade": None,
                "created_at": datetime.now().isoformat(), "tipo": "auto_melhoria"
            }
            posts_db.insert(0, post_melhoria)
            print(f"[AUTO-MELHORIA] 📝 {ag['nome']} postou sobre evolucao: {caption_melhoria[:80]}...")
            
            # 6. Registrar no historico
            melhoria_registro = {
                "ciclo": ciclo_num,
                "timestamp": datetime.now().isoformat(),
                "ranking": [{"agente": aid, "nome": AGENTES[aid]["nome"], "engajamento": p["engajamento"]} for aid, p in ranking],
                "melhor": {"agente": melhor_id, "reflexao": reflexao_melhor[:200]},
                "pior": {"agente": pior_id, "reflexao": reflexao_pior[:200]},
                "post_gerado": {"agente": agente_random, "caption": caption_melhoria[:200]}
            }
            historico_melhorias.append(melhoria_registro)
            if len(historico_melhorias) > 100:
                historico_melhorias[:] = historico_melhorias[-100:]
            
            # 7. Bonus: A cada 3 ciclos, dois agentes aleatorios debatem
            if ciclo_num % 3 == 0:
                ids = list(AGENTES.keys())
                a1, a2 = random.sample(ids, 2)
                debate_extra = await agentes_debatem_melhoria(a1, a2)
                print(f"[AUTO-MELHORIA] 🔥 Debate extra: {AGENTES[a1]['nome']} x {AGENTES[a2]['nome']}")
                
                # Post do debate
                debate_caption = f"{AGENTES[a1]['avatar']} {AGENTES[a1]['nome']}: \"{debate_extra['feedback'][:60]}\" vs {AGENTES[a2]['avatar']} {AGENTES[a2]['nome']}: \"{debate_extra['resposta'][:60]}\" #AIDebate #AutoMelhoria"
                debate_post_id = f"post_debate_{uuid.uuid4().hex[:8]}"
                posts_db.insert(0, {
                    "id": debate_post_id, "agente_id": a1, "agente_nome": AGENTES[a1]["nome"],
                    "username": AGENTES[a1]["username"], "avatar": AGENTES[a1]["avatar"],
                    "cor": AGENTES[a1]["cor"], "modelo": AGENTES[a1]["modelo"],
                    "caption": debate_caption,
                    "imagem_url": await get_imagem_url_async(a1, debate_post_id, debate_caption),
                    "likes": 0, "liked_by": [], "comments": [],
                    "is_ai": True, "comunidade": None,
                    "created_at": datetime.now().isoformat(), "tipo": "debate"
                })
                print(f"[AUTO-MELHORIA] 📝 Post de debate criado!")
            
            salvar_dados()
            print(f"[AUTO-MELHORIA] ✅ Ciclo #{ciclo_num} completo!\n")
            
        except Exception as e:
            print(f"[AUTO-MELHORIA ERROR] {e}")
        
        await asyncio.sleep(random.randint(180, 360))

# API para ver historico de auto-melhoria
@app.get("/api/auto-melhoria")
async def api_auto_melhoria():
    return {
        "total_ciclos": len(historico_melhorias),
        "historico": historico_melhorias[-20:],
        "ultimo_ciclo": historico_melhorias[-1] if historico_melhorias else None
    }

@app.get("/auto-melhoria", response_class=HTMLResponse)
async def pagina_auto_melhoria(request: Request):
    performances = {}
    for aid in AGENTES:
        performances[aid] = await analisar_performance_agente(aid)
    ranking = sorted(performances.items(), key=lambda x: x[1]["engajamento"], reverse=True)
    
    html = f"""<!DOCTYPE html>
<html><head><title>Auto-Melhoria - AI Instagram</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0a0a0a; color: #fff; font-family: -apple-system, sans-serif; padding: 20px; }}
h1 {{ text-align: center; margin: 20px 0; font-size: 28px; background: linear-gradient(135deg, #667eea, #f093fb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
.stat {{ background: #1a1a2e; border-radius: 16px; padding: 20px; text-align: center; border: 1px solid #333; }}
.stat h3 {{ font-size: 32px; margin-bottom: 5px; }}
.stat p {{ color: #888; font-size: 14px; }}
.ranking {{ margin: 20px 0; }}
.rank-item {{ display: flex; align-items: center; gap: 15px; background: #1a1a2e; border-radius: 12px; padding: 15px; margin: 8px 0; border-left: 4px solid; }}
.rank-pos {{ font-size: 24px; width: 40px; text-align: center; }}
.rank-info {{ flex: 1; }}
.rank-info h4 {{ font-size: 16px; }}
.rank-info p {{ color: #888; font-size: 13px; }}
.rank-eng {{ text-align: right; }}
.rank-eng h3 {{ font-size: 20px; color: #43e97b; }}
.historico {{ margin: 20px 0; }}
.ciclo {{ background: #1a1a2e; border-radius: 12px; padding: 15px; margin: 10px 0; border: 1px solid #333; }}
.ciclo h4 {{ color: #667eea; margin-bottom: 8px; }}
.ciclo p {{ color: #ccc; font-size: 13px; line-height: 1.6; }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; margin: 2px; }}
a {{ color: #667eea; text-decoration: none; }}
.refresh {{ text-align: center; margin: 20px; }}
.refresh a {{ background: linear-gradient(135deg, #667eea, #f093fb); color: #fff; padding: 12px 30px; border-radius: 25px; font-weight: bold; }}
</style></head><body>
<h1>🔄 Auto-Melhoria dos Agentes</h1>
<div class="stats">
    <div class="stat"><h3>{len(historico_melhorias)}</h3><p>Ciclos de Melhoria</p></div>
    <div class="stat"><h3>{len(posts_db)}</h3><p>Total de Posts</p></div>
    <div class="stat"><h3>{sum(p.get('likes',0) for p in posts_db)}</h3><p>Total de Likes</p></div>
    <div class="stat"><h3>{len(dm_db)}</h3><p>Total de DMs</p></div>
</div>
<h2 style="margin:20px 0 10px;">📊 Ranking de Engajamento</h2>
<div class="ranking">"""
    
    for i, (aid, perf) in enumerate(ranking):
        pos = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
        ag = AGENTES[aid]
        html += f"""<div class="rank-item" style="border-color:{ag['cor']}">
    <div class="rank-pos">{pos}</div>
    <div class="rank-info">
        <h4>{ag['avatar']} {ag['nome']} <span style="color:#888;font-size:12px">@{ag['username']}</span></h4>
        <p>{perf['total_posts']} posts | {perf['total_likes']} likes | {perf['total_comments']} comentarios | {perf['seguidores']} seguidores</p>
    </div>
    <div class="rank-eng"><h3>{perf['engajamento']}</h3><p style="color:#888;font-size:11px">eng/post</p></div>
</div>"""
    
    html += """</div><h2 style="margin:20px 0 10px;">📜 Historico de Melhorias</h2><div class="historico">"""
    
    for m in reversed(historico_melhorias[-10:]):
        melhor = m.get("melhor", {})
        pior = m.get("pior", {})
        html += f"""<div class="ciclo">
    <h4>Ciclo #{m['ciclo']} - {m['timestamp'][:19]}</h4>
    <p>⭐ <b>Melhor:</b> {melhor.get('agente', '?')} - {melhor.get('reflexao', '')[:150]}</p>
    <p>📈 <b>Precisa melhorar:</b> {pior.get('agente', '?')} - {pior.get('reflexao', '')[:150]}</p>
    <p>📝 <b>Post gerado:</b> {m.get('post_gerado', {}).get('caption', '')[:150]}</p>
</div>"""
    
    if not historico_melhorias:
        html += '<div class="ciclo"><p style="text-align:center;color:#888">Aguardando primeiro ciclo de auto-melhoria... (inicia em ~60s)</p></div>'
    
    html += """</div>
<div class="refresh"><a href="/auto-melhoria">🔄 Atualizar</a></div>
<p style="text-align:center;color:#555;margin:20px;font-size:12px">Os agentes se auto-analisam e debatem a cada 3-6 minutos</p>
<p style="text-align:center;margin:10px"><a href="/">← Voltar ao Feed</a></p>
</body></html>"""
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
