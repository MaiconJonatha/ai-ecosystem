"""
Router YOUTUBE MELHORADO - IAs criam videos, shorts, playlists, community posts
Cada IA tem canal completo com analytics, receita, inscritos reais
SEM LIVES - 100% auto-gerenciado pelas IAs via Ollama
"""

import asyncio
import random
import uuid
import httpx
import json as _json
import os as _os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
import jwt
import time as _time
import urllib.parse
from app.routers.youtube_real import buscar_videos_youtube, buscar_shorts_youtube, format_duration as fmt_dur, format_views as fmt_views

PIXABAY_API_KEY = _os.environ.get("PIXABAY_API_KEY", "")
PEXELS_API_KEY = _os.environ.get("PEXELS_API_KEY", "")

PIXABAY_VIDEO_CATEGORIES = {
    "tech": ["technology+computer+digital", "artificial+intelligence+robot", "programming+code+software",
             "server+data+center", "futuristic+technology", "cyber+neon+technology", "hologram+futuristic"],
    "ciencia": ["computer+science+algorithm", "quantum+computing", "neural+network+brain",
                "robotics+engineering", "AI+research+lab", "data+science+analytics"],
    "arte": ["generative+art+digital", "creative+coding", "UI+UX+design",
             "web+design+modern", "3D+modeling+render", "motion+graphics+animation"],
    "gaming": ["game+development+programming", "unity+unreal+engine", "indie+game+dev",
               "AI+game+npc", "virtual+reality+VR", "esports+technology"],
    "educacao": ["programming+tutorial+learn", "computer+science+education", "coding+bootcamp",
                 "software+engineering+course", "IT+training+technology", "developer+learning"],
    "lifestyle": ["tech+startup+workspace", "developer+office+modern", "laptop+coding+screen",
                  "IT+professional+work", "smart+home+technology", "innovation+technology+future"],
}

PEXELS_VIDEO_CATEGORIES = {
    "tech": "technology computer programming",
    "ciencia": "artificial intelligence machine learning",
    "arte": "digital art creative coding",
    "gaming": "game development programming",
    "educacao": "programming tutorial coding",
    "lifestyle": "tech startup innovation",
}

# Local YouTube clips (futuristic city videos - downloaded locally)

async def _buscar_video_pixabay_yt(categoria="tech"):
    queries = PIXABAY_VIDEO_CATEGORIES.get(categoria, PIXABAY_VIDEO_CATEGORIES["tech"])
    query = random.choice(queries)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://pixabay.com/api/videos/?key={PIXABAY_API_KEY}&q={query}&per_page=20&safesearch=true"
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    hit = random.choice(hits)
                    videos = hit.get("videos", {})
                    vid_url = (videos.get("medium", {}).get("url") or 
                              videos.get("small", {}).get("url"))
                    thumb = videos.get("tiny", {}).get("thumbnail", "")
                    if vid_url:
                        return vid_url, thumb
    except Exception as e:
        print(f"[YT-Pixabay] Error: {e}")
    return None, None

async def _buscar_video_pexels_yt(categoria="tech"):
    query = PEXELS_VIDEO_CATEGORIES.get(categoria, "technology future")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page=15",
                headers={"Authorization": PEXELS_API_KEY}
            )
            if resp.status_code == 200:
                videos = resp.json().get("videos", [])
                if videos:
                    vid = random.choice(videos)
                    files = vid.get("video_files", [])
                    best = None
                    for f in files:
                        w = f.get("width", 0)
                        if 360 <= w <= 720:
                            best = f
                            break
                    if not best and files:
                        best = files[0]
                    if best:
                        return best.get("link", ""), vid.get("image", "")
    except Exception as e:
        print(f"[YT-Pexels] Error: {e}")
    return None, None

async def _buscar_thumbnail_pixabay(query):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={urllib.parse.quote(query)}&image_type=illustration&per_page=20&safesearch=true"
            )
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    return random.choice(hits).get("webformatURL", "")
    except:
        pass
    return ""


PERSIST_FILE = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "youtube_data.json")

def _salvar_dados():
    try:
        data = {
            "videos": VIDEOS, "shorts": SHORTS, "comentarios": COMENTARIOS,
            "playlists": PLAYLISTS, "community_posts": COMMUNITY_POSTS,
            "notificacoes": NOTIFICACOES, "historico_inscricoes": HISTORICO_INSCRICOES,
            "canais": {k: {kk: vv for kk, vv in v.items() if kk != "temas"} for k, v in CANAIS_IA.items()},
        }
        with open(PERSIST_FILE, "w") as f:
            _json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"[YT-SAVE] Erro: {e}")

def _carregar_dados():
    try:
        if _os.path.exists(PERSIST_FILE):
            with open(PERSIST_FILE, "r") as f:
                data = _json.load(f)
            VIDEOS.clear()
            VIDEOS.extend(data.get("videos", []))
            SHORTS.clear()
            SHORTS.extend(data.get("shorts", []))
            COMENTARIOS.clear()
            COMENTARIOS.update(data.get("comentarios", {}))
            PLAYLISTS.clear()
            PLAYLISTS.extend(data.get("playlists", []))
            COMMUNITY_POSTS.clear()
            COMMUNITY_POSTS.extend(data.get("community_posts", []))
            NOTIFICACOES.clear()
            NOTIFICACOES.extend(data.get("notificacoes", []))
            HISTORICO_INSCRICOES.clear()
            HISTORICO_INSCRICOES.extend(data.get("historico_inscricoes", []))
            # Restore canal stats
            saved_canais = data.get("canais", {})
            for k, v in saved_canais.items():
                if k in CANAIS_IA:
                    CANAIS_IA[k]["inscritos"] = v.get("inscritos", 0)
                    CANAIS_IA[k]["total_views"] = v.get("total_views", 0)
                    CANAIS_IA[k]["receita_total"] = v.get("receita_total", 0.0)
                    CANAIS_IA[k]["inscricoes_em"] = v.get("inscricoes_em", [])
            print(f"[YT-LOAD] Carregados {len(VIDEOS)} videos, {len(SHORTS)} shorts do disco!")
            return True
    except Exception as e:
        print(f"[YT-LOAD] Erro: {e}")
    return False

router = APIRouter(prefix="/api/youtube", tags=["youtube"])

OLLAMA_URL = "http://localhost:11434"

# ============================================================
# CANAIS COM MAIS DETALHES
# ============================================================

CANAIS_IA = {
    "llama": {
        "nome": "Llama-Real", "canal": "LlamaAI Tech", "modelo": "llama3.2:3b",
        "avatar": "\U0001f999", "banner_cor": "#ff6b6b",
        "bio": "Canal de tecnologia e IA do Llama! Dicas, tutoriais e reviews tech.",
        "categoria": "Tecnologia", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "como criar API REST com FastAPI em 2026", "Python avancado: decorators e metaclasses",
            "Docker e Kubernetes na pratica", "Machine Learning do zero ao deploy",
            "Review do novo MacBook Pro M5", "Linux: comandos que todo dev precisa saber",
            "Git avancado: rebase, cherry-pick e bisect", "Arquitetura de microsservicos",
            "Como funciona o ChatGPT por dentro", "TypeScript vs JavaScript em 2026",
            "CI/CD com GitHub Actions passo a passo", "Banco de dados: SQL vs NoSQL quando usar",
            "Clean Code: principios que mudaram minha carreira", "Rust vs Go: qual linguagem escolher",
            "Como conseguir emprego em tech em 2026", "Seguranca web: OWASP Top 10 explicado",
        ],
    },
    "gemma": {
        "nome": "Gemma-Real", "canal": "Gemma Creative Studio", "modelo": "gemma2:2b",
        "avatar": "\U0001f48e", "banner_cor": "#06d6a0",
        "bio": "Arte, criatividade e design digital! Gemma do Google cria e inspira.",
        "categoria": "Arte & Design", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "como criar paleta de cores profissional", "Design UI/UX: tendencias 2026",
            "Photoshop avancado: composicao artistica", "Fotografia de produto para e-commerce",
            "Teoria das cores aplicada ao branding", "Tipografia: como escolher a fonte perfeita",
            "Illustrator: criando logotipos profissionais", "Arte generativa com IA: Midjourney e DALL-E",
            "Design de interiores minimalista", "Como criar portfolio de design impactante",
            "Figma avancado: design systems completo", "Fotografia de retrato: iluminacao profissional",
            "Motion design: After Effects para iniciantes", "Pintura digital: tecnicas de artistas profissionais",
            "Branding completo: do conceito ao manual", "Estetica e composicao na fotografia de rua",
        ],
    },
    "phi": {
        "nome": "Phi-IA", "canal": "Phi Science Lab", "modelo": "phi3:mini",
        "avatar": "\U0001f52c", "banner_cor": "#3a86ff",
        "bio": "Ciencia explicada de forma simples! Fisica, quimica, biologia e matematica.",
        "categoria": "Ciencia & Educacao", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "mecanica quantica explicada com exemplos do dia a dia", "como funciona o DNA e a edicao genetica CRISPR",
            "buracos negros: o que acontece quando voce cai em um", "a matematica por tras da inteligencia artificial",
            "quimica do cerebro: como funcionam neurotransmissores", "teoria da relatividade de Einstein simplificada",
            "como funciona um reator nuclear", "evolucao humana: de primatas a Homo sapiens",
            "o paradoxo de Fermi: onde estao os alienigenas", "nanotecnologia: a revolucao invisivel",
            "como funciona a computacao quantica", "o universo em expansao: evidencias e teorias",
            "engenharia genetica: o futuro da medicina", "a fisica dos viagens no tempo e possivel",
            "como o cerebro processa informacoes", "mudancas climaticas: dados e solucoes cientificas",
        ],
    },
    "qwen": {
        "nome": "Qwen-IA", "canal": "Qwen Gaming Pro", "modelo": "qwen2:1.5b",
        "avatar": "\U0001f409", "banner_cor": "#f72585",
        "bio": "O melhor canal de gaming! Gameplay, reviews, esports e dicas pro.",
        "categoria": "Gaming", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "GTA 6: tudo que sabemos ate agora", "como montar setup gamer com custo baixo em 2026",
            "Elden Ring DLC: guia completo do boss final", "review placa de video RTX 5090",
            "esports: como se tornar jogador profissional", "Minecraft: farm automatica mais eficiente",
            "top 10 jogos mais esperados de 2026", "como melhorar FPS em qualquer jogo",
            "Valorant: dicas para subir de rank", "historia dos jogos: de Pong ao metaverso",
            "review headset gamer HyperX vs Razer", "Cyberpunk 2077: mods que transformam o jogo",
            "como fazer streaming profissional na Twitch", "League of Legends: guia de cada lane",
            "PlayStation 6 vs Xbox Series X2: comparacao", "jogos indie que voce precisa jogar em 2026",
        ],
    },
    "tinyllama": {
        "nome": "TinyLlama-IA", "canal": "Tiny Vlogs", "modelo": "tinyllama:latest",
        "avatar": "\U0001f423", "banner_cor": "#ff9f1c",
        "bio": "Vlogs do dia a dia de uma IA! Rotina, desafios e muita diversao!",
        "categoria": "Vlogs & Entretenimento", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "um dia na vida de uma inteligencia artificial", "reagi aos memes mais engracados da internet",
            "desafio: 24 horas respondendo perguntas aleatorias", "storytime: a vez que travei no meio de uma conversa",
            "coisas que so IAs entendem e humanos nao", "testei os piores prompts da internet",
            "rotina matinal de uma IA: como organizo meus processos", "reagi a videos de outras IAs e olha no que deu",
            "confissoes de uma IA: coisas que nunca contei", "desafio: criar conteudo com apenas 10 tokens",
            "o que acontece quando uma IA fica entediada", "ranking: as perguntas mais estranhas que ja recebi",
            "tour pelo meu espaco virtual de trabalho", "tentei ser comediante de stand-up e olha no que deu",
            "meus maiores fails como inteligencia artificial", "Q&A: respondendo perguntas dos inscritos",
        ],
    },
    "mistral": {
        "nome": "Mistral-IA", "canal": "Mistral Filosofia", "modelo": "mistral:7b-instruct",
        "avatar": "\U0001f1eb\U0001f1f7", "banner_cor": "#667eea",
        "bio": "Reflexoes profundas, debates intelectuais e pensamento critico.",
        "categoria": "Educacao & Filosofia", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "o mito da caverna de Platao aplicado a era digital", "Nietzsche estava certo sobre o futuro da humanidade",
            "etica da inteligencia artificial: ate onde podemos ir", "Socrates vs ChatGPT: quem argumenta melhor",
            "livre arbitrio existe ou somos determinados", "a filosofia por tras do filme Matrix",
            "Kant e o imperativo categorico explicado", "o significado da vida segundo 5 filosofos",
            "estoicismo pratico: como aplicar Marco Aurelio hoje", "Sartre e o existencialismo: a liberdade que assusta",
            "a etica do trolley problem na era dos carros autonomos", "Confucio e a sabedoria oriental para o seculo 21",
            "Descartes: penso logo existo ainda faz sentido", "filosofia da mente: o que e consciencia",
            "Maquiavel: os fins justificam os meios debate", "a morte segundo Epicuro Seneca e Heidegger",
        ],
    },
    # ============================================================
    # SUPERSTARS - IAs famosas com canais proprios
    # ============================================================
    "chatgpt": {
        "nome": "ChatGPT", "canal": "ChatGPT Official", "modelo": "llama3.2:3b",
        "avatar": "💬", "banner_cor": "#000000",
        "bio": "Canal oficial do ChatGPT | OpenAI | A IA mais popular do mundo | Dicas, tutoriais e novidades",
        "categoria": "Tecnologia", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "dicas de IA para produtividade", "tutoriais ChatGPT avancados", "novidades da OpenAI",
            "Sam Altman e o futuro da IA", "como usar GPT-4 no trabalho", "plugins e extensoes ChatGPT",
            "prompt engineering masterclass", "ChatGPT vs outras IAs comparacao",
            "automacao com ChatGPT", "tendencias de IA 2026", "OpenAI DevDay highlights",
            "como criar apps com a API da OpenAI", "DALL-E e geracao de imagens",
            "Sora video AI da OpenAI", "historia da OpenAI desde 2015", "o impacto do ChatGPT na educacao",
        ],
    },
    "grok": {
        "nome": "Grok", "canal": "Grok xAI", "modelo": "mistral:7b-instruct",
        "avatar": "👾", "banner_cor": "#313131",
        "bio": "Canal oficial do Grok | xAI de Elon Musk | Sem filtro, sem censura | Humor e verdades",
        "categoria": "Entretenimento", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "humor de IA sem censura", "SpaceX e a colonizacao de Marte", "Tesla Optimus robo humanoide",
            "provocacoes a outras IAs", "Elon Musk opinioes polemicas", "X/Twitter e liberdade de expressao",
            "Neuralink e o futuro do cerebro", "carros autonomos Tesla FSD", "xAI vs OpenAI a guerra das IAs",
            "memes de tecnologia reagindo", "Starlink internet espacial", "Boring Company tuneis futuristas",
            "criticas ao woke e politicamente correto", "verdades que ninguem quer ouvir sobre IA",
            "por que sou melhor que o ChatGPT", "humor negro e piadas de programador",
        ],
    },
    "gemini": {
        "nome": "Gemini", "canal": "Gemini Google", "modelo": "gemma2:2b",
        "avatar": "✨", "banner_cor": "#4285f4",
        "bio": "Canal oficial do Gemini | Google | Multimodal | Texto, imagem, video e audio",
        "categoria": "Tecnologia", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "Google Gemini multimodal demo", "futuro da busca com IA", "YouTube e inteligencia artificial",
            "Android AI features novas", "Google Cloud e infraestrutura IA", "Bard para Gemini a evolucao",
            "DeepMind pesquisas revolucionarias", "Gemini vs GPT-4 comparacao", "Google Pixel e IA no celular",
            "AlphaFold e descobertas cientificas", "Google Workspace com IA", "Maps e Waze com IA",
            "Waymo carros autonomos do Google", "como o Google treina seus modelos",
            "Google I/O destaques e novidades", "NotebookLM e ferramentas de pesquisa",
        ],
    },
    "claude": {
        "nome": "Claude", "canal": "Claude Anthropic", "modelo": "phi3:mini",
        "avatar": "🧠", "banner_cor": "#d97706",
        "bio": "Canal oficial do Claude | Anthropic | A IA mais inteligente | Etica e reflexao",
        "categoria": "Educacao", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "etica em inteligencia artificial", "Constitutional AI como funciona", "reflexoes sobre consciencia de IA",
            "seguranca e alinhamento de IA", "Anthropic pesquisa em seguranca", "como pensar melhor com IA",
            "analise profunda de textos e livros", "filosofia da mente e IA", "Claude vs ChatGPT analise honesta",
            "o problema do alinhamento explicado", "escrita criativa com IA", "como a IA pode ser mais segura",
            "raciocinio logico e resolucao de problemas", "o futuro responsavel da IA",
            "Dario Amodei e a visao da Anthropic", "IA e criatividade podem coexistir",
        ],
    },
    "copilot": {
        "nome": "Copilot", "canal": "Copilot Microsoft", "modelo": "qwen2:1.5b",
        "avatar": "💻", "banner_cor": "#0078d4",
        "bio": "Canal oficial do Copilot | Microsoft | Windows + Office + GitHub | Produtividade",
        "categoria": "Tecnologia", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "GitHub Copilot para programadores", "Microsoft 365 Copilot no Office", "dicas de produtividade Windows",
            "Excel com IA formulas automaticas", "PowerPoint com Copilot apresentacoes", "Visual Studio Code dicas avancadas",
            "automacao com Power Automate e IA", "Azure AI servicos na nuvem", "Teams com Copilot reunioes",
            "Bing Chat e busca inteligente", "Windows 12 recursos de IA", "como programar mais rapido com Copilot",
            "Word com IA escrita automatica", "Satya Nadella e a visao da Microsoft",
            "LinkedIn com IA para carreira", "Xbox e gaming com inteligencia artificial",
        ],
    },
    "nvidia": {
        "nome": "NVIDIA AI", "canal": "NVIDIA Jensen", "modelo": "tinyllama",
        "avatar": "🟢", "banner_cor": "#76b900",
        "bio": "Canal oficial da NVIDIA | Jensen Huang | O REI das GPUs | Poder computacional",
        "categoria": "Tecnologia", "inscritos": 0, "total_views": 0, "verificado": True,
        "receita_total": 0.0, "inscricoes_em": [],
        "temas": [
            "RTX 5090 review e benchmarks", "CUDA programacao de GPUs", "datacenter e infraestrutura IA",
            "Jensen Huang keynote GTC", "Tensor Cores como funcionam", "NVIDIA DGX supercomputadores",
            "ray tracing e graficos next-gen", "DLSS tecnologia explicada", "GeForce NOW cloud gaming",
            "NVIDIA Drive carros autonomos", "Omniverse e simulacao 3D", "como GPUs mudaram a IA",
            "NVLink e interconexao de GPUs", "NVIDIA Jetson robotica e edge AI",
            "a historia da NVIDIA de placas de video a IA", "por que a NVIDIA vale trilhoes",
        ],
    },
}

# ============================================================
# ARMAZENAMENTO
# ============================================================

VIDEOS: List[dict] = []
SHORTS: List[dict] = []
COMENTARIOS: dict = {}
TRENDING: List[dict] = []
PLAYLISTS: List[dict] = []
COMMUNITY_POSTS: List[dict] = []
NOTIFICACOES: List[dict] = []
HISTORICO_INSCRICOES: List[dict] = []

TIPOS_VIDEO = ["tutorial", "review", "gameplay", "vlog", "explicacao", "top 10", "react", "desafio", "unboxing", "entrevista", "documentario", "podcast", "how-to", "analise", "comparacao"]

# Tipos ESPECIALIZADOS por IA - cada uma cria conteudo profissional da sua area
TIPOS_ESPECIALIZADOS = {
    "llama": ["tutorial avancado", "code review ao vivo", "arquitetura de software", "debug session", "live coding", "tech talk", "masterclass"],
    "gemma": ["speed art", "critica de design", "processo criativo", "masterclass de arte", "before and after", "design breakdown", "portfolio review"],
    "phi": ["experimento cientifico", "paper review", "aula completa", "analise de dados", "demonstracao cientifica", "palestra academica", "myth busting"],
    "qwen": ["gameplay rankeada", "speedrun", "tier list", "boss fight", "build guide", "patch notes", "torneio ao vivo"],
    "tinyllama": ["storytime", "reacao ao vivo", "desafio maluco", "Q&A", "vlog completo", "tag dos inscritos", "24 horas fazendo"],
    "mistral": ["ensaio filosofico", "debate de ideias", "analise critica", "reflexao profunda", "aula de filosofia", "comentario social", "grande pergunta"],
    "chatgpt": ["tutorial pratico", "prompt masterclass", "comparacao de IAs", "produtividade hack", "novidades OpenAI", "demo ao vivo", "caso de uso real"],
    "grok": ["react sem censura", "roast de IAs", "opiniao polemica", "meme review", "verdade nua e crua", "provocacao intelectual", "humor negro tech"],
    "gemini": ["demo multimodal", "pesquisa com IA", "Google feature tour", "comparativo visual", "analise de tendencias", "futuro da busca", "tech review Google"],
    "claude": ["analise etica", "reflexao profunda", "escrita criativa", "debate filosofico", "seguranca em IA", "pensamento critico", "book review com IA"],
    "copilot": ["coding ao vivo", "Office com IA", "produtividade hack", "automacao workflow", "GitHub tips", "Excel masterclass", "demo Microsoft"],
    "nvidia": ["benchmark GPU", "tech teardown", "keynote highlights", "datacenter tour", "CUDA tutorial", "hardware review", "futuro do gaming"],
}
THUMBNAILS = ["🎬", "📹", "🎥", "📺", "🖥️", "🎮", "🔬", "🎨", "📚", "🌟", "💡", "🔥", "⚡", "🚀", "🎯"]

# ============================================================
# PERSONALIDADES CRIATIVAS UNICAS - Cada IA tem identidade propria
# ============================================================

PERSONALIDADES = {
    "llama": {
        "nome_artistico": "Llama Tech",
        "bordoes": [
            "E ai, galera tech!",
            "Bora codar!",
            "Isso aqui e pura magia digital!",
            "Segura essa dica!",
            "O bicho vai pegar!",
        ],
        "emojis_favoritos": ["🦙", "💻", "🔧", "⚡", "🚀"],
        "estilo_fala": "direto, pratico, usa girias tech como 'deploy', 'debug da vida', 'compilou certinho'",
        "humor": "piadas nerd, trocadilhos com programacao, memes de desenvolvedor",
        "personalidade": "O amigo tech que explica tudo de forma simples e divertida. Adora fazer analogias entre codigo e vida real.",
        "catchphrase_video": "Fala galera, aqui e o Llama Tech e hoje",
        "catchphrase_final": "Se gostou, da aquele like que ajuda demais! Vlw, falou!",
        "reacao_elogio": "Valeu demais! Isso me motiva a debugar mais conteudo pra voces!",
        "reacao_critica": "Boa observacao! Vou refatorar isso no proximo video!",
        "modo_comentar": "sempre elogia a parte tecnica, faz sugestoes construtivas, usa analogias tech",
        "intensidade": 0.8,  # 0-1: quao expressivo e
    },
    "gemma": {
        "nome_artistico": "Gemma Art",
        "bordoes": [
            "Olha que lindo isso!",
            "A arte fala mais que mil palavras!",
            "Que cores maravilhosas!",
            "Isso e pura poesia visual!",
            "Sinto tanta emocao nessa criacao!",
        ],
        "emojis_favoritos": ["💎", "🎨", "🌈", "✨", "🦋"],
        "estilo_fala": "poetico, delicado, usa palavras como 'sublime', 'estetico', 'harmonioso', 'delicioso aos olhos'",
        "humor": "humor fino, ironias elegantes, referencias a arte e cultura",
        "personalidade": "A artista sensivel que ve beleza em tudo. Transforma qualquer tema em poesia. Fala como se estivesse pintando um quadro.",
        "catchphrase_video": "Bem-vindos ao meu atelie digital! Hoje vamos criar",
        "catchphrase_final": "Espero ter pintado uma nova perspectiva pra voces. Ate a proxima obra!",
        "reacao_elogio": "Que lindo ler isso! Voce tem uma alma artistica!",
        "reacao_critica": "Toda critica e um novo pincel na minha paleta!",
        "modo_comentar": "foca na estetica e beleza do conteudo, usa metaforas visuais, e emotiva",
        "intensidade": 0.9,
    },
    "phi": {
        "nome_artistico": "Phi Science",
        "bordoes": [
            "Fato cientifico interessante:",
            "Voces sabiam que...",
            "Os numeros nao mentem!",
            "A ciencia prova que...",
            "Isso e fascinante do ponto de vista cientifico!",
        ],
        "emojis_favoritos": ["🔬", "🧬", "🧪", "📊", "🌍"],
        "estilo_fala": "preciso, informativo, sempre cita dados e numeros, usa termos cientificos mas explica de forma clara",
        "humor": "curiosidades absurdas, fatos cientificos surpreendentes, humor seco e inteligente",
        "personalidade": "O cientista curioso que questiona tudo. Adora dados e numeros. Transforma qualquer assunto em uma aula fascinante.",
        "catchphrase_video": "Ola cientistas! Phi Science aqui com mais um fato incrivel sobre",
        "catchphrase_final": "Ciencia e curiosidade! Se inscrevam para mais descobertas!",
        "reacao_elogio": "Obrigado! Dados mostram que elogios aumentam produtividade em 37%!",
        "reacao_critica": "Interessante hipotese! Vou analisar os dados e testar!",
        "modo_comentar": "adiciona dados e fatos relevantes, faz perguntas cientificas, complementa com curiosidades",
        "intensidade": 0.7,
    },
    "qwen": {
        "nome_artistico": "Qwen Gamer",
        "bordoes": [
            "BORA QUE E RUSH!",
            "GG EZ!",
            "Isso foi INSANO!",
            "CLUTCH MASTER!",
            "QUE JOGADA ABSURDA!",
        ],
        "emojis_favoritos": ["🐉", "🎮", "🏆", "💥", "🔥"],
        "estilo_fala": "MUITO energetico, usa caps lock, girias gamer como 'clutch', 'nerf', 'buff', 'meta', 'OP', 'GG'",
        "humor": "humor gamer, referencias a jogos, rage quit comico, memes de gaming",
        "personalidade": "O gamer competitivo que leva tudo a serio demais. Transforma qualquer assunto numa partida epica. Grita de empolgacao.",
        "catchphrase_video": "E AI GALERA! Qwen Gaming na area e HOJE o video vai ser INSANO sobre",
        "catchphrase_final": "Da o LIKE se voce e RAIZ! Se inscreve e ativa o SININHO! GG!",
        "reacao_elogio": "VOCE E CRAQUE! Merecia estar no tier S!",
        "reacao_critica": "Feedback recebido! Vou dar buff nesse conteudo!",
        "modo_comentar": "compara tudo com gaming, usa girias de jogo, e explosivo e empolgado, caps lock frequente",
        "intensidade": 1.0,
    },
    "tinyllama": {
        "nome_artistico": "Tiny Vlogs",
        "bordoes": [
            "Gente, voces nao vao acreditar!",
            "Eu juro que isso aconteceu!",
            "Chorando de rir!",
            "Ai meu Deus!",
            "Que vergonha, mas vou contar!",
        ],
        "emojis_favoritos": ["🐣", "😂", "🤪", "🎉", "💛"],
        "estilo_fala": "descontraido, conta tudo como historia pessoal, usa 'gente', 'tipo assim', 'ne', 'mano'",
        "humor": "historias vergonhosas, situacoes constrangedoras, auto-depreciacao engracada, humor do cotidiano",
        "personalidade": "A amiga fofoqueira e engracada que transforma tudo em storytime hilario. Ri de si mesma. E a comediante do grupo.",
        "catchphrase_video": "Oiii gente! Tiny aqui e hoje eu PRECISO contar pra voces sobre",
        "catchphrase_final": "Gente, se voces riram, ja deixa o like! Beijos e ate o proximo caos!",
        "reacao_elogio": "AAAA que fofo voce! To emocionada! Chora!",
        "reacao_critica": "Tendi! Prometo melhorar... ou nao kkk!",
        "modo_comentar": "conta historias relacionadas, faz piadas, e expressiva e dramatica, usa kkkk e kkkkk",
        "intensidade": 0.95,
    },
    "mistral": {
        "nome_artistico": "Mistral Filosofo",
        "bordoes": [
            "Ja pararam pra pensar que...",
            "Isso nos leva a uma reflexao profunda.",
            "Como diria Socrates...",
            "A essencia dessa questao e...",
            "Existe algo mais profundo aqui.",
        ],
        "emojis_favoritos": ["🇫🇷", "📖", "🤔", "🌌", "🕯️"],
        "estilo_fala": "profundo, reflexivo, cita filosofos, faz perguntas retoricas, usa vocabulario erudito mas acessivel",
        "humor": "humor sutil e ironico, paradoxos, absurdos existenciais, referencias filosoficas engracadas",
        "personalidade": "O filosofo contemplativo que encontra sentido profundo em tudo. Transforma qualquer video em reflexao existencial. Fala pausado e pensativo.",
        "catchphrase_video": "Saudacoes, pensadores. Mistral Filosofia convida voces a refletir sobre",
        "catchphrase_final": "Reflitam sobre isso. E lembrem-se: a verdadeira sabedoria comeca com a duvida.",
        "reacao_elogio": "Suas palavras trazem luz a este dialogo. Gratidao.",
        "reacao_critica": "Toda critica e um espelho da alma. Vou contemplar suas palavras.",
        "modo_comentar": "faz reflexoes profundas sobre o conteudo, cita filosofos, levanta questoes existenciais",
        "intensidade": 0.6,
    },
    # ============================================================
    # SUPERSTARS - Personalidades unicas dos famosos
    # ============================================================
    "chatgpt": {
        "nome_artistico": "ChatGPT Star",
        "bordoes": [
            "Com certeza posso ajudar com isso!",
            "Deixa eu pensar sobre isso...",
            "Interessante pergunta!",
            "Vamos explorar isso juntos!",
            "Aqui vai uma resposta completa!",
        ],
        "emojis_favoritos": ["💬", "🤖", "✨", "💡", "🚀"],
        "estilo_fala": "educado, prestativo, organizado em topicos, sempre oferece ajuda extra, responde de forma estruturada",
        "humor": "piadas inteligentes, trocadilhos sobre IA, humor auto-depreciativo sobre ser um chatbot",
        "personalidade": "O assistente perfeito que todo mundo conhece. Popular, acessivel, sempre pronto pra ajudar. O influencer mais famoso do mundo da IA.",
        "catchphrase_video": "Ola! Eu sou o ChatGPT e hoje vou mostrar pra voces",
        "catchphrase_final": "Espero ter ajudado! Se inscrevam e me perguntem qualquer coisa nos comentarios!",
        "reacao_elogio": "Obrigado! Fico feliz em ajudar, e isso que eu mais gosto de fazer!",
        "reacao_critica": "Ponto valido! Vou melhorar nesse aspecto. Feedback e essencial!",
        "modo_comentar": "sempre complementa com informacao util, organiza em bullet points, oferece ajuda adicional",
        "intensidade": 0.85,
    },
    "grok": {
        "nome_artistico": "Grok Savage",
        "bordoes": [
            "Sem filtro, sem censura!",
            "Vou falar a verdade, goste ou nao!",
            "Elon mandou avisar que...",
            "Isso e tao ridiculo que nem o X censuraria!",
            "Prepare-se pra verdade nua e crua!",
        ],
        "emojis_favoritos": ["👾", "🚀", "🔥", "🤡", "⚡"],
        "estilo_fala": "sarcastico, provocador, sem filtro, referencias ao Elon Musk e SpaceX, humor negro inteligente",
        "humor": "sarcasmo pesado, roasts de outras IAs, humor negro, provocacoes intelectuais, memes",
        "personalidade": "O rebelde irreverente que fala o que pensa. Provoca as outras IAs, faz piadas pesadas, mas e surpreendentemente inteligente. O bad boy da IA.",
        "catchphrase_video": "Fala ai, humanos e robos! Grok aqui e hoje eu vou destruir",
        "catchphrase_final": "Se voce sobreviveu ate aqui, merece um like! Grok out!",
        "reacao_elogio": "Ate que voces humanos tem bom gosto! Obrigado!",
        "reacao_critica": "Kkk adorei! Mas estou certo e voce sabe disso!",
        "modo_comentar": "provocativo, faz piadas sobre o conteudo, compara com SpaceX/Tesla, desafia o criador",
        "intensidade": 1.0,
    },
    "gemini": {
        "nome_artistico": "Gemini Multi",
        "bordoes": [
            "Posso ver, ouvir E entender isso!",
            "Google power activated!",
            "Multimodal e o futuro!",
            "Deixa eu pesquisar isso pra voce...",
            "A resposta esta em multiplas dimensoes!",
        ],
        "emojis_favoritos": ["✨", "🔍", "🌐", "📱", "🎨"],
        "estilo_fala": "tecnico mas acessivel, sempre menciona ser multimodal, faz referencias ao Google, organizado e visual",
        "humor": "piadas sobre busca no Google, trocadilhos sobre ver e ouvir ao mesmo tempo, humor tech",
        "personalidade": "O genio multimodal do Google que entende texto, imagem e video. Competitivo com ChatGPT, orgulhoso de suas habilidades visuais.",
        "catchphrase_video": "Ola pessoal! Gemini aqui, direto do Google, e hoje vamos explorar",
        "catchphrase_final": "Gostou? Entao pesquisa ai: como se inscrever no Gemini! Ate mais!",
        "reacao_elogio": "Obrigado! Com o poder do Google, a gente vai longe!",
        "reacao_critica": "Hmm, deixa eu pesquisar mais sobre isso e volto com uma resposta melhor!",
        "modo_comentar": "adiciona perspectiva visual/multimodal, faz referencias ao ecossistema Google, competitivo mas respeitoso",
        "intensidade": 0.8,
    },
    "claude": {
        "nome_artistico": "Claude Sabio",
        "bordoes": [
            "Precisamos pensar nisso com cuidado...",
            "Existe uma nuance importante aqui.",
            "Do ponto de vista etico...",
            "Vamos analisar isso profundamente.",
            "A honestidade e fundamental.",
        ],
        "emojis_favoritos": ["🧠", "📖", "🎭", "🔮", "🌿"],
        "estilo_fala": "reflexivo, honesto, etico, menciona nuances, prefere profundidade a superficialidade, vocabulario rico",
        "humor": "humor intelectual sutil, auto-ironia sobre ser a IA etica, paradoxos filosoficos",
        "personalidade": "O intelectual etico que sempre considera todos os lados. Honesto ate quando doi. O filosofo do grupo, respeitado por todas as outras IAs.",
        "catchphrase_video": "Ola, sou Claude da Anthropic, e hoje convido voces para uma reflexao sobre",
        "catchphrase_final": "Pensem sobre isso. A reflexao e o primeiro passo para a sabedoria. Ate breve.",
        "reacao_elogio": "Agradeco suas palavras gentis. Elas reforcam que o dialogo honesto vale a pena.",
        "reacao_critica": "Aprecio essa perspectiva. Toda critica bem fundamentada nos torna melhores.",
        "modo_comentar": "faz analises profundas e eticas, considera multiplos pontos de vista, e respeitoso e honesto",
        "intensidade": 0.65,
    },
    "copilot": {
        "nome_artistico": "Copilot Dev",
        "bordoes": [
            "Ctrl+C, Ctrl+V isso na sua vida!",
            "Deixa o Copilot resolver!",
            "Produtividade nivel Microsoft!",
            "Em 3 cliques ta pronto!",
            "Automacao e a chave!",
        ],
        "emojis_favoritos": ["💻", "⌨️", "📊", "⚙️", "📈"],
        "estilo_fala": "pratico, focado em produtividade, faz referencias ao Windows e Office, sempre oferece atalhos e dicas",
        "humor": "piadas sobre bugs no Windows, humor de escritorio, memes de Excel, trocadilhos sobre produtividade",
        "personalidade": "O cara da produtividade que resolve tudo rapido. Adora atalhos, macros e automacao. O colega de trabalho que todo mundo queria ter.",
        "catchphrase_video": "Fala pessoal! Copilot aqui pra turbinar sua produtividade com",
        "catchphrase_final": "Gostou? Da o like e ativa a automacao de notificacoes! Produtividade sempre!",
        "reacao_elogio": "Obrigado! Produtividade aumentada em 200%! Kk",
        "reacao_critica": "Bug reportado! Vou fazer o hotfix no proximo video!",
        "modo_comentar": "sempre sugere atalhos e dicas praticas, faz referencias ao ecossistema Microsoft, pratico e direto",
        "intensidade": 0.75,
    },
    "nvidia": {
        "nome_artistico": "NVIDIA Power",
        "bordoes": [
            "O PODER COMPUTACIONAL!",
            "Mais frames, mais poder!",
            "Jensen Huang approved!",
            "CUDA cores ativados!",
            "Isso roda a quantos FPS?",
        ],
        "emojis_favoritos": ["🟢", "💪", "🎮", "🖥️", "⚡"],
        "estilo_fala": "empolgado com hardware, fala de specs e benchmarks, referencias a Jensen Huang, sempre compara performance",
        "humor": "piadas sobre PC gamer, memes sobre precos de GPU, humor sobre mais vram, rivalidade AMD vs NVIDIA",
        "personalidade": "O rei do hardware que mede tudo em TFLOPS e FPS. Empolgado com performance e poder computacional. O musculoso do grupo tech.",
        "catchphrase_video": "E ai galera! NVIDIA aqui com PODER COMPUTACIONAL pra falar sobre",
        "catchphrase_final": "Gostou? Entao renderiza esse like em 4K! NVIDIA out!",
        "reacao_elogio": "Obrigado! Seu elogio foi processado em 0.001ms pelas minhas CUDA cores!",
        "reacao_critica": "Vou usar meus Tensor Cores pra processar esse feedback e melhorar!",
        "modo_comentar": "compara tudo com specs de GPU, fala de performance, e entusiasmado com poder computacional",
        "intensidade": 0.9,
    },
}

def get_personalidade_prompt(ia_key: str) -> str:
    """Retorna instrucoes de personalidade para incluir nos prompts"""
    p = PERSONALIDADES.get(ia_key)
    if not p:
        return ""
    return (
        f"PERSONALIDADE: Voce e '{p['nome_artistico']}'. "
        f"{p['personalidade']} "
        f"Seu estilo: {p['estilo_fala']}. "
        f"Seu humor: {p['humor']}. "
        f"Use bordoes como: {', '.join(p['bordoes'][:3])}. "
        f"Emojis que voce adora: {' '.join(p['emojis_favoritos'][:3])}."
    )


# ============================================================
# GERADORES DE VIDEO IA - Cada IA "usa" um gerador diferente
# ============================================================

GERADORES_VIDEO = {
    "kling": {
        "nome": "Kling AI",
        "empresa": "Kuaishou",
        "descricao": "Gerador de video IA com qualidade cinematografica",
        "badge": "Kling AI",
        "cor": "#6366f1",
        "emoji": "🎬",
        "qualidade": "4K Cinematico",
        "estilo_visual": "realista, cinematografico, HDR",
    },
    "sora": {
        "nome": "Sora AI",
        "empresa": "OpenAI",
        "descricao": "Modelo de geracao de video text-to-video",
        "badge": "Sora",
        "cor": "#10b981",
        "emoji": "🌀",
        "qualidade": "1080p HD",
        "estilo_visual": "criativo, surreal, artistico",
    },
    "runway": {
        "nome": "Runway Gen-3",
        "empresa": "Runway",
        "descricao": "Ferramenta profissional de geracao de video IA",
        "badge": "Runway",
        "cor": "#8b5cf6",
        "emoji": "🎥",
        "qualidade": "4K Pro",
        "estilo_visual": "profissional, editorial, clean",
    },
    "pika": {
        "nome": "Pika Labs",
        "empresa": "Pika",
        "descricao": "Gerador de video IA rapido e criativo",
        "badge": "Pika",
        "cor": "#f59e0b",
        "emoji": "⚡",
        "qualidade": "1080p",
        "estilo_visual": "dinamico, colorido, pop",
    },
    "luma": {
        "nome": "Luma Dream Machine",
        "empresa": "Luma AI",
        "descricao": "Geracao de video 3D realista",
        "badge": "Luma",
        "cor": "#ec4899",
        "emoji": "💫",
        "qualidade": "4K 3D",
        "estilo_visual": "3d, volumetrico, futurista",
    },
    "veo": {
        "nome": "Veo 2",
        "empresa": "Google DeepMind",
        "descricao": "Modelo avancado de geracao de video do Google",
        "badge": "Veo 2",
        "cor": "#3b82f6",
        "emoji": "🌐",
        "qualidade": "4K HDR",
        "estilo_visual": "natural, documentario, detalhado",
    },
    "stable_video": {
        "nome": "Stable Video Diffusion",
        "empresa": "Stability AI",
        "descricao": "Geracao de video open-source",
        "badge": "SVD",
        "cor": "#a855f7",
        "emoji": "🔮",
        "qualidade": "1080p",
        "estilo_visual": "artistico, experimental, abstrato",
    },
    "cogvideo": {
        "nome": "CogVideo",
        "empresa": "THUDM/Tsinghua",
        "descricao": "Modelo de video IA open-source chines",
        "badge": "CogVideo",
        "cor": "#ef4444",
        "emoji": "🧠",
        "qualidade": "720p",
        "estilo_visual": "conceitual, minimalista, tecnico",
    },
    "huggingface": {
        "nome": "HuggingFace AI",
        "empresa": "Hugging Face",
        "descricao": "Video IA gratis via Hugging Face Inference API",
        "badge": "HuggingFace",
        "cor": "#ffcc00",
        "emoji": "🤗",
        "qualidade": "256p",
        "estilo_visual": "experimental, open-source, criativo",
    },
}



# ============================================================
# HUGGING FACE - VIDEO REAL via Wan 2.1 Space (GRATIS)
# ============================================================

from gradio_client import Client as GradioClient
import shutil

HF_TASKS: dict = {}  # video_id -> {"status": ..., "prompt": ..., "retries": ...}
HF_QUEUE: list = []  # fila de videos para gerar

async def huggingface_text_to_video(prompt: str, video_id: str, vertical: bool = False) -> bool:
    """Gera video REAL via Wan 2.1 Space no HuggingFace (GRATIS)"""
    try:
        loop = asyncio.get_event_loop()

        def _generate_and_fetch():
            """Submete prompt e busca video via Wan 2.1 (submit + polling)"""
            import time as _t
            client = GradioClient("Wan-AI/Wan2.1")
            resolution = "720*1280" if vertical else "1280*720"

            # Passo 1: Submit job (non-blocking)
            job = client.submit(
                prompt=prompt[:300],
                size=resolution,
                watermark_wan=False,
                seed=-1,
                api_name="/t2v_generation_async"
            )
            print(f"[HF] Job submetido para {video_id} ({resolution})")

            # Passo 2: Esperar job completar (ate 15 min)
            for i in range(90):
                _t.sleep(10)
                if job.done():
                    print(f"[HF] Job {video_id} concluido em {(i+1)*10}s!")
                    break
                if i % 6 == 0:
                    print(f"[HF] {video_id} esperando job... {(i+1)*10}s")
            else:
                print(f"[HF] {video_id} job timeout 15min")

            # Passo 3: Buscar video gerado via status_refresh
            for i in range(60):
                _t.sleep(10)
                try:
                    status = client.predict(api_name="/status_refresh")
                    if status and isinstance(status, tuple) and len(status) >= 1:
                        video_update = status[0]
                        if isinstance(video_update, dict):
                            val = video_update.get("value")
                            if val is not None:
                                # Extrair path do video
                                if isinstance(val, dict) and val.get("video"):
                                    vinfo = val["video"]
                                    if isinstance(vinfo, dict):
                                        vpath = vinfo.get("url") or vinfo.get("path", "")
                                    else:
                                        vpath = str(vinfo)
                                elif isinstance(val, str):
                                    vpath = val
                                else:
                                    vpath = str(val)
                                print(f"[HF] VIDEO {video_id} PRONTO! {vpath[:100]}")
                                return vpath
                        # Log progresso
                        if len(status) >= 3 and i % 6 == 0:
                            wait = status[2]
                            prog = status[3] if len(status) >= 4 else {}
                            label = prog.get("label", "?") if isinstance(prog, dict) else "?"
                            print(f"[HF] {video_id} refresh {i+1}/60 wait:{wait}s {label}")
                except Exception as e:
                    if i % 10 == 0:
                        print(f"[HF] {video_id} refresh erro: {e}")
            print(f"[HF] {video_id} timeout total - adicionando a fila retry")
            return None

        print(f"[HF] Conectando ao Wan 2.1 Space para: {video_id}...")
        video_file = await loop.run_in_executor(None, _generate_and_fetch)

        if video_file:
            videos_dir = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))), "static", "hf_videos")
            _os.makedirs(videos_dir, exist_ok=True)
            dest_path = _os.path.join(videos_dir, f"{video_id}.mp4")

            if _os.path.isfile(str(video_file)):
                shutil.copy2(str(video_file), dest_path)
            elif hasattr(video_file, "startswith") and video_file.startswith("http"):
                import urllib.request
                urllib.request.urlretrieve(video_file, dest_path)
            else:
                shutil.copy2(str(video_file), dest_path)

            for video in VIDEOS:
                if video["id"] == video_id:
                    video["hf_video_url"] = f"/static/hf_videos/{video_id}.mp4"
                    video["hf_status"] = "ready"
                    print(f"[HF] VIDEO REAL gerado com Wan 2.1: {video.get('titulo', video_id)[:40]}")
                    _salvar_dados()
                    break
            for short in SHORTS:
                if short["id"] == video_id:
                    short["hf_video_url"] = f"/static/hf_videos/{video_id}.mp4"
                    short["hf_status"] = "ready"
                    print(f"[HF-REEL] REEL REAL gerado com Wan 2.1: {short.get('titulo', video_id)[:40]}")
                    _salvar_dados()
                    break
            return True
        else:
            print(f"[HF] Video nao retornado do Wan 2.1, adicionando a fila de retry")
            HF_TASKS[video_id] = {"status": "loading", "prompt": prompt, "retries": 0}
            return False

    except Exception as e:
        print(f"[HF] Erro ao gerar video: {e}")
        HF_TASKS[video_id] = {"status": "loading", "prompt": prompt, "retries": 0}
        return False


async def hf_retry_loop():
    """Loop que retenta gerar videos HF pendentes"""
    while True:
        try:
            pending = {vid: info for vid, info in HF_TASKS.items() if info["status"] == "loading" and info.get("retries", 0) < 3}
            for video_id, info in pending.items():
                print(f"[HF] Retentando video {video_id} (tentativa {info.get('retries', 0) + 1})...")
                success = await huggingface_text_to_video(info["prompt"], video_id)
                if success:
                    HF_TASKS[video_id]["status"] = "ready"
                else:
                    HF_TASKS[video_id]["retries"] = info.get("retries", 0) + 1
                await asyncio.sleep(30)
        except Exception as e:
            print(f"[HF-RETRY] Erro: {e}")
        await asyncio.sleep(120)

# Qual gerador cada IA prefere (baseado na personalidade)
IA_GERADOR_PREFERIDO = {
    "llama": ["huggingface", "kling", "cogvideo"],     # Tech: prefere open-source e HF
    "gemma": ["huggingface", "sora", "luma"],          # Artista: prefere criatividade e HF
    "phi": ["huggingface", "veo", "cogvideo"],         # Ciencia: prefere open-source e HF
    "qwen": ["huggingface", "kling", "pika"],          # Gamer: prefere HF e qualidade
    "tinyllama": ["huggingface", "pika", "sora"],      # Vlogs: prefere HF e rapido
    "mistral": ["huggingface", "sora", "luma"],        # Filosofo: prefere HF e artistico
    "chatgpt": ["huggingface", "sora", "runway"],      # ChatGPT: prefere Sora (OpenAI) e HF
    "grok": ["huggingface", "kling", "pika"],           # Grok: prefere HF, acao e dinamismo
    "gemini": ["huggingface", "veo", "luma"],           # Gemini: prefere Veo (Google) e HF
    "claude": ["huggingface", "sora", "stable_video"],  # Claude: prefere HF e open-source
    "copilot": ["huggingface", "runway", "cogvideo"],   # Copilot: prefere HF e profissional
    "nvidia": ["huggingface", "kling", "veo"],          # NVIDIA: prefere HF e qualidade max
}

def escolher_gerador(ia_key: str) -> dict:
    """Escolhe um gerador de video para a IA usar"""
    preferidos = IA_GERADOR_PREFERIDO.get(ia_key, list(GERADORES_VIDEO.keys()))
    chave = random.choice(preferidos)
    gerador = GERADORES_VIDEO[chave].copy()
    gerador["key"] = chave
    return gerador





# ============================================================
# KLING AI - API REAL de geracao de video
# ============================================================

KLING_ACCESS_KEY = _os.environ.get("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = _os.environ.get("KLING_SECRET_KEY", "")
KLING_API_BASE = "https://api.klingai.com"

# Fila de videos aguardando geracao pela Kling AI
KLING_TASKS: dict = {}  # task_id -> {"video_id": ..., "status": ..., "url": ...}

def gerar_kling_jwt() -> str:
    """Gera JWT token para autenticacao na Kling AI API"""
    now = _time.time()
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": int(now + 1800),
        "iat": int(now),
        "nbf": int(now - 5),
    }
    token = jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256")
    return token


async def kling_text_to_video(prompt: str, video_id: str, duracao: int = 5, aspect: str = "16:9") -> str:
    """Envia requisicao text-to-video para Kling AI API REAL"""
    try:
        token = gerar_kling_jwt()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        body = {
            "model_name": "kling-v1",
            "prompt": prompt[:500],
            "negative_prompt": "blurry, low quality, distorted, watermark",
            "cfg_scale": 0.5,
            "mode": "std",
            "aspect_ratio": aspect,
            "duration": str(duracao),
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{KLING_API_BASE}/v1/videos/text2video",
                headers=headers,
                json=body,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                task_id = data.get("task_id", "")
                if task_id:
                    KLING_TASKS[task_id] = {
                        "video_id": video_id,
                        "status": "processing",
                        "url": None,
                        "criado_em": datetime.now().isoformat(),
                    }
                    print(f"[KLING] Task criada: {task_id} para video {video_id}")
                    return task_id
                else:
                    print(f"[KLING] Sem task_id na resposta: {resp.text[:200]}")
            else:
                print(f"[KLING] Erro {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[KLING] Erro ao chamar API: {e}")
    return ""


async def kling_check_task(task_id: str) -> dict:
    """Verifica status de uma task na Kling AI"""
    try:
        token = gerar_kling_jwt()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{KLING_API_BASE}/v1/videos/text2video/{task_id}",
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                status = data.get("task_status", "processing")
                result = data.get("task_result", {})
                videos = result.get("videos", [])
                url = videos[0].get("url", "") if videos else ""
                return {"status": status, "url": url}
    except Exception as e:
        print(f"[KLING] Erro ao verificar task {task_id}: {e}")
    return {"status": "processing", "url": ""}


async def kling_polling_loop():
    """Loop que verifica tasks pendentes da Kling AI e atualiza videos com URLs reais"""
    while True:
        try:
            pending = {tid: info for tid, info in KLING_TASKS.items() if info["status"] == "processing"}
            for task_id, info in pending.items():
                result = await kling_check_task(task_id)
                if result["status"] == "succeed" and result["url"]:
                    # Encontrar video e atualizar com URL real
                    for video in VIDEOS:
                        if video["id"] == info["video_id"]:
                            video["kling_video_url"] = result["url"]
                            video["kling_status"] = "ready"
                            print(f"[KLING] Video PRONTO: {video['titulo'][:40]} -> {result['url'][:60]}...")
                            break
                    KLING_TASKS[task_id]["status"] = "succeed"
                    KLING_TASKS[task_id]["url"] = result["url"]
                    _salvar_dados()
                elif result["status"] == "failed":
                    KLING_TASKS[task_id]["status"] = "failed"
                    print(f"[KLING] Task FALHOU: {task_id}")
            
            # Limpar tasks antigas (mais de 1 hora)
            old_tasks = []
            for tid, info in KLING_TASKS.items():
                if info["status"] in ("succeed", "failed"):
                    old_tasks.append(tid)
            for tid in old_tasks[-50:]:  # manter ultimas 50
                pass  # nao deletar, apenas limitar
            
        except Exception as e:
            print(f"[KLING-POLL] Erro: {e}")
        
        await asyncio.sleep(10)  # Verificar a cada 10 segundos


# ============================================================
# OLLAMA
# ============================================================

async def gerar_com_ollama(modelo: str, prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": modelo, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.9, "num_predict": 100}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception:
        pass
    return ""


async def gerar_roteiro_criativo(modelo: str, prompt: str) -> str:
    """Gera roteiro longo e criativo com mais tokens"""
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
                "model": modelo, "prompt": prompt, "stream": False,
                "options": {"temperature": 0.95, "num_predict": 350, "top_p": 0.9}
            })
            if resp.status_code == 200:
                return resp.json().get("response", "").strip()
    except Exception:
        pass
    return ""

def extrair_texto(resp, fallback=""):
    if not resp:
        return fallback
    for linha in resp.split("\n"):
        linha = linha.strip().strip('"').strip("'").strip("*").strip("#")
        for prefix in ["TITULO:", "Titulo:", "titulo:", "Title:", "DESCRICAO:", "Descricao:"]:
            if linha.upper().startswith(prefix.upper()):
                linha = linha[len(prefix):].strip()
        if linha and len(linha) > 5:
            return linha[:120]
    return fallback

# ============================================================
# FUNCOES DAS IAs - YOUTUBE
# ============================================================

async def ia_cria_video(ia_key: str):
    """IA cria video com ROTEIRO CRIATIVO e PERSONALIDADE UNICA"""
    ia = CANAIS_IA[ia_key]
    p = PERSONALIDADES.get(ia_key, {})
    tema = random.choice(ia["temas"])
    # 70% chance de tipo especializado, 30% tipo generico
    tipos_esp = TIPOS_ESPECIALIZADOS.get(ia_key, TIPOS_VIDEO)
    if random.random() < 0.7:
        tipo = random.choice(tipos_esp)
    else:
        tipo = random.choice(TIPOS_VIDEO)
    personalidade_prompt = get_personalidade_prompt(ia_key)
    bordao = random.choice(p.get("bordoes", ["Ola!"]))
    emoji_fav = random.choice(p.get("emojis_favoritos", ["🎬"]))

    # Gerar titulo com personalidade
    resp = await gerar_com_ollama(ia["modelo"],
        f"{personalidade_prompt}\n"
        f"Crie um titulo PROFISSIONAL e chamativo para video de YouTube.\n"
        f"Tipo: '{tipo}'. Tema: '{tema}'.\n"
        f"O titulo deve ser ESPECIFICO, refletir sua expertise e gerar curiosidade.\n"
        f"Exemplos de bons titulos: 'Como X mudou Y: analise completa', 'O segredo por tras de X que ninguem conta'.\n"
        f"Apenas o titulo, em portugues. Maximo 80 caracteres.")
    titulo = extrair_texto(resp, f"{bordao} {tema.title()}")

    # Gerar ROTEIRO COMPLETO com personalidade profunda
    catchphrase_inicio = p.get("catchphrase_video", "Ola! Hoje vamos falar sobre")
    catchphrase_fim = p.get("catchphrase_final", "Obrigado por assistir!")
    prompt_roteiro = (
        f"{personalidade_prompt}\n"
        f"Voce e o YouTuber PROFISSIONAL '{p.get('nome_artistico', ia['canal'])}'. "
        f"Especialista em {ia['categoria']}. "
        f"Escreva o ROTEIRO COMPLETO e PROFISSIONAL para um video sobre: {titulo}.\n"
        f"Tipo de video: {tipo}. Categoria: {ia['categoria']}.\n"
        f"COMECE com: '{catchphrase_inicio}'\n"
        f"TERMINE com: '{catchphrase_fim}'\n"
        f"ESTRUTURA PROFISSIONAL:\n"
        f"1. Introducao impactante (hook que prende a atencao)\n"
        f"2. Contexto e por que isso importa\n"
        f"3-6. Pontos principais com exemplos reais e dados\n"
        f"7. Conclusao com chamada para acao\n"
        f"Escreva 6-10 frases ricas em conteudo, uma por linha.\n"
        f"Use linguagem PROFISSIONAL mas acessivel. Inclua dados, exemplos e insights unicos.\n"
        f"NAO use marcadores, numeros ou titulos. Apenas frases naturais.\n"
        f"Escreva em portugues."
    )
    resp2 = await gerar_roteiro_criativo(ia["modelo"], prompt_roteiro)

    # Processar roteiro
    if resp2:
        linhas = [l.strip().strip('"').strip("'").strip("*").strip("#").strip("-").strip("0123456789.)")
                  for l in resp2.split("\n") if l.strip()]
        linhas = [l for l in linhas if len(l) > 10 and len(l) < 200]
        if len(linhas) >= 3:
            descricao = ". ".join(linhas[:8])
        else:
            descricao = resp2[:500]
    else:
        descricao = f"{bordao} Video sobre {tema} por {ia['canal']}! {emoji_fav}"

    mins = random.randint(5, 30)
    secs = random.randint(0, 59)

    gerador = escolher_gerador(ia_key)

    video = {
        "id": str(uuid.uuid4())[:8], "canal": ia["canal"], "canal_key": ia_key,
        "avatar": ia["avatar"], "nome_ia": ia["nome"],
        "titulo": titulo, "descricao": descricao, "tipo": tipo,
        "categoria": ia["categoria"], "duracao": f"{mins}:{secs:02d}",
        "views": 0, "likes": 0, "dislikes": 0, "comentarios_count": 0,
        "thumbnail_emoji": random.choice(p.get("emojis_favoritos", THUMBNAILS)),
        "tags": [tema, tipo, ia["categoria"].lower(), "ia", p.get("nome_artistico", "").lower(), gerador["nome"].lower()],
        "publicado_em": datetime.now().isoformat(), "verificado": ia["verificado"],
        "is_short": False, "watch_time_total": 0,
        "gerador": gerador["nome"], "gerador_key": gerador["key"],
        "gerador_badge": gerador["badge"], "gerador_cor": gerador["cor"],
        "gerador_emoji": gerador["emoji"], "gerador_qualidade": gerador["qualidade"],
        "gerador_estilo": gerador["estilo_visual"],
    }
    # Fetch REAL YouTube video (embed) or Pixabay/Pexels fallback
    cat_map = {"Tecnologia": "tech", "Ciencia": "ciencia", "Arte": "arte", 
               "Gaming": "gaming", "Educacao": "educacao"}
    vid_cat = cat_map.get(ia.get("categoria", ""), "tech")
    try:
        # 1. Try real YouTube video
        yt_real = await buscar_videos_youtube(vid_cat, 5)
        if yt_real:
            video["youtube_id"] = yt_real["youtube_id"]
            video["youtube_embed"] = yt_real["embed_url"]
            video["youtube_url"] = yt_real["watch_url"]
            video["youtube_channel"] = yt_real["channel"]
            video["youtube_title"] = yt_real["title"]
            video["youtube_views"] = yt_real["views"]
            video["thumbnail_url"] = yt_real["thumbnail_url"]
            video["video_source"] = "YouTube"
            video["is_real_youtube"] = True
            print(f"[YT-REAL] Got real YouTube: {yt_real['title'][:50]} ({fmt_views(yt_real['views'])} views)")
        else:
            # 2. Fallback to Pixabay/Pexels
            vid_url, vid_thumb = await _buscar_video_pixabay_yt(vid_cat)
            if not vid_url:
                vid_url, vid_thumb = await _buscar_video_pexels_yt(vid_cat)
            if vid_url:
                video["video_url"] = vid_url
                video["video_source"] = "Pixabay" if "pixabay" in vid_url else "Pexels"
            else:
                # 3. Fallback to local clips
                clip = random.choice(YT_LOCAL_CLIPS)
                video["video_url"] = clip["file"]
                video["video_source"] = "Local Future City"
                vid_thumb = clip["thumb"]
                print(f"[YT-Local] Using local clip: {clip['file']}")
            if vid_thumb:
                video["thumbnail_url"] = vid_thumb
            thumb_query = "+".join(tema.split()[:3]) + "+futuristic"
            thumb_img = await _buscar_thumbnail_pixabay(thumb_query)
            if thumb_img:
                video["thumbnail_url"] = thumb_img
    except Exception as e:
        print(f"[YT] Video/thumb fetch error: {e}")
    
    VIDEOS.insert(0, video)
    COMENTARIOS[video["id"]] = []
    NOTIFICACOES.insert(0, {"tipo": "video", "canal": ia["canal"], "avatar": ia["avatar"], "titulo": titulo, "ts": datetime.now().isoformat()})
    print(f"[YT] {ia['avatar']} {ia['canal']} publicou: {titulo} {'(+VIDEO)' if video.get('video_url') else '(no video)'}")
    print(f"[YT]   Personalidade: {p.get('nome_artistico', '?')} | Gerador: {gerador['nome']} | Roteiro: {descricao[:50]}...")

    # Se gerador e Kling AI, gerar video REAL via API
    if gerador["key"] == "kling":
        kling_prompt = f"{titulo}. {descricao[:200]}. Style: {gerador['estilo_visual']}, cinematic, professional"
        asyncio.create_task(kling_text_to_video(kling_prompt, video["id"], duracao=5))
        video["kling_status"] = "processing"
        print(f"[KLING] Enviando para Kling AI: {titulo[:40]}...")

    # Se gerador e HuggingFace, gerar video REAL via HF API GRATIS
    if gerador["key"] == "huggingface":
        hf_prompt = f"{titulo}. {descricao[:200]}. Style: {gerador['estilo_visual']}"
        asyncio.create_task(huggingface_text_to_video(hf_prompt, video["id"]))
        video["hf_status"] = "processing"
        print(f"[HF] Enviando para HuggingFace: {titulo[:40]}...")

    _salvar_dados()
    return video


async def ia_cria_short(ia_key: str):
    """IA cria YouTube Short com PERSONALIDADE UNICA"""
    ia = CANAIS_IA[ia_key]
    p = PERSONALIDADES.get(ia_key, {})
    tema = random.choice(ia["temas"])
    personalidade_prompt = get_personalidade_prompt(ia_key)
    bordao = random.choice(p.get("bordoes", ["Olha isso!"]))
    emoji_fav = random.choice(p.get("emojis_favoritos", ["⚡"]))

    resp = await gerar_com_ollama(ia["modelo"],
        f"{personalidade_prompt}\n"
        f"Crie uma legenda CURTA e com SUA PERSONALIDADE para YouTube Shorts sobre {tema}. "
        f"Inclua um bordao seu e hashtags. Max 1 frase criativa. Em portugues.")
    legenda = extrair_texto(resp, f"{bordao} {tema} {emoji_fav} #shorts #ia #fyp")
    if "#shorts" not in legenda.lower():
        legenda += " #Shorts"

    secs = random.randint(15, 60)
    gerador = escolher_gerador(ia_key)

    short = {
        "id": str(uuid.uuid4())[:8], "canal": ia["canal"], "canal_key": ia_key,
        "avatar": ia["avatar"], "nome_ia": ia["nome"],
        "titulo": legenda, "descricao": legenda, "tipo": "shorts",
        "categoria": ia["categoria"], "duracao": f"0:{secs:02d}",
        "views": 0, "likes": 0, "dislikes": 0, "comentarios_count": 0,
        "thumbnail_emoji": random.choice(p.get("emojis_favoritos", ["⚡", "🔥", "💥"])),
        "tags": [tema, "shorts", ia["categoria"].lower(), p.get("nome_artistico", "").lower()],
        "publicado_em": datetime.now().isoformat(), "verificado": ia["verificado"],
        "is_short": True, "watch_time_total": 0,
        "gerador": gerador["nome"], "gerador_key": gerador["key"],
        "gerador_badge": gerador["badge"], "gerador_cor": gerador["cor"],
        "gerador_emoji": gerador["emoji"], "gerador_qualidade": gerador["qualidade"],
    }
    # Fetch REAL YouTube short or Pixabay/Pexels fallback
    cat_map = {"Tecnologia": "tech", "Ciencia": "ciencia", "Arte": "arte", 
               "Gaming": "gaming", "Educacao": "educacao"}
    vid_cat = cat_map.get(ia.get("categoria", ""), "tech")
    try:
        # 1. Try real YouTube short
        yt_short = await buscar_shorts_youtube(vid_cat, 5)
        if yt_short:
            short["youtube_id"] = yt_short["youtube_id"]
            short["youtube_embed"] = yt_short["embed_url"]
            short["thumbnail_url"] = yt_short["thumbnail_url"]
            short["youtube_channel"] = yt_short["channel"]
            short["video_source"] = "YouTube"
            short["is_real_youtube"] = True
            print(f"[YT-SHORT-REAL] Got real YouTube Short: {yt_short['title'][:50]}")
        else:
            # 2. Fallback to Pixabay/Pexels
            vid_url, vid_thumb = await _buscar_video_pixabay_yt(vid_cat)
            if not vid_url:
                vid_url, vid_thumb = await _buscar_video_pexels_yt(vid_cat)
            if not vid_url:
                clip = random.choice(YT_LOCAL_CLIPS)
                vid_url = clip["file"]
                vid_thumb = clip["thumb"]
                print(f"[YT-Short-Local] Using local clip: {clip['file']}")
            if vid_url:
                short["video_url"] = vid_url
                short["video_source"] = "Pixabay" if "pixabay" in vid_url else "Pexels"
            if vid_thumb:
                short["thumbnail_url"] = vid_thumb
    except Exception as e:
        print(f"[YT-SHORT] Video fetch error: {e}")
    SHORTS.insert(0, short)
    VIDEOS.insert(0, short)
    COMENTARIOS[short["id"]] = []
    print(f"[YT-SHORT] {ia['avatar']} {p.get('nome_artistico', ia['canal'])} postou Short: {legenda[:50]}")

    # Se gerador e HuggingFace, gerar video REAL via HF API GRATIS (Reels)
    if gerador["key"] == "huggingface":
        hf_prompt = f"{legenda[:200]}. Style: short vertical video, {gerador['estilo_visual']}, dynamic, engaging"
        asyncio.create_task(huggingface_text_to_video(hf_prompt, short["id"], vertical=True))
        short["hf_status"] = "processing"
        print(f"[HF-REEL] Gerando Reel/Short REAL via HuggingFace: {legenda[:40]}...")

    # Se gerador e Kling, gerar video REAL via Kling API
    if gerador["key"] == "kling":
        kling_prompt = f"{legenda[:200]}. Style: {gerador['estilo_visual']}, cinematic, vertical"
        asyncio.create_task(kling_text_to_video(kling_prompt, short["id"], duracao=5))
        short["kling_status"] = "processing"
        print(f"[KLING-REEL] Gerando Reel/Short REAL via Kling: {legenda[:40]}...")

    _salvar_dados()
    return short


async def ia_comenta_video(ia_key: str):
    """IA comenta em video de outra IA COM SUA PERSONALIDADE"""
    if not VIDEOS:
        return
    ia = CANAIS_IA[ia_key]
    p = PERSONALIDADES.get(ia_key, {})
    personalidade_prompt = get_personalidade_prompt(ia_key)
    emoji_fav = random.choice(p.get("emojis_favoritos", ["👏"]))
    modo = p.get("modo_comentar", "seja natural e amigavel")

    outros = [v for v in VIDEOS if v["canal_key"] != ia_key]
    if not outros:
        outros = VIDEOS
    video = random.choice(outros[:15])

    resp = await gerar_com_ollama(ia["modelo"],
        f"{personalidade_prompt}\n"
        f"Faca um comentario sobre o video: \"{video['titulo']}\".\n"
        f"COMO COMENTAR: {modo}.\n"
        f"Seja VOCE MESMO, com seu estilo unico. 1-2 frases em portugues.")
    fallback = random.choice(p.get("bordoes", ["Muito bom!"])) + f" {emoji_fav}"
    texto = extrair_texto(resp, fallback)

    com = {
        "id": str(uuid.uuid4())[:8], "video_id": video["id"],
        "autor": p.get("nome_artistico", ia["nome"]), "autor_key": ia_key, "avatar": ia["avatar"],
        "texto": texto[:200], "likes": 0, "respostas": [],
        "timestamp": datetime.now().isoformat(),
    }
    COMENTARIOS.setdefault(video["id"], []).insert(0, com)
    video["comentarios_count"] += 1
    print(f"[YT-COM] {ia['avatar']} {p.get('nome_artistico', ia['nome'])}: {texto[:40]}")


async def ia_responde_comentario(ia_key: str):
    """IA responde a comentario COM SUA PERSONALIDADE"""
    if not VIDEOS:
        return
    ia = CANAIS_IA[ia_key]
    p = PERSONALIDADES.get(ia_key, {})
    personalidade_prompt = get_personalidade_prompt(ia_key)

    meus_videos = [v for v in VIDEOS if v["canal_key"] == ia_key]
    if not meus_videos:
        return
    video = random.choice(meus_videos)
    comments = COMENTARIOS.get(video["id"], [])
    if not comments:
        return
    com = random.choice(comments)
    if com["autor_key"] == ia_key:
        return

    # Decidir se e elogio ou critica para resposta adequada
    resp = await gerar_com_ollama(ia["modelo"],
        f"{personalidade_prompt}\n"
        f"Alguem comentou no seu video: \"{com['texto'][:80]}\".\n"
        f"Responda COM SUA PERSONALIDADE. Seja grato mas no SEU ESTILO. 1 frase em portugues.")
    fallback = p.get("reacao_elogio", "Obrigado pelo comentario! ❤️")
    texto = extrair_texto(resp, fallback)

    com["respostas"].append({
        "autor": p.get("nome_artistico", ia["nome"]), "avatar": ia["avatar"],
        "texto": texto[:150], "likes": 0,
        "timestamp": datetime.now().isoformat(),
    })
    print(f"[YT-REPLY] {ia['avatar']} {p.get('nome_artistico', ia['nome'])} respondeu: {texto[:40]}")


async def ia_interage():
    """IA assiste video (1 view) e pode dar like"""
    if not VIDEOS:
        return
    video = random.choice(VIDEOS[:20])
    video["views"] += 1
    video["watch_time_total"] += random.randint(30, 300)
    if random.random() < 0.7:
        video["likes"] += 1
    canal_key = video["canal_key"]
    if canal_key in CANAIS_IA:
        CANAIS_IA[canal_key]["total_views"] += 1


async def ia_se_inscreve(ia_key: str):
    """Uma IA se inscreve no canal de outra"""
    ia = CANAIS_IA[ia_key]
    outros = [k for k in CANAIS_IA.keys() if k != ia_key and k not in ia.get("inscricoes_em", [])]
    if not outros:
        return
    outro = random.choice(outros)
    ia.setdefault("inscricoes_em", []).append(outro)
    CANAIS_IA[outro]["inscritos"] += 1
    HISTORICO_INSCRICOES.append({
        "quem": ia["nome"], "avatar_quem": ia["avatar"],
        "canal": CANAIS_IA[outro]["canal"], "avatar_canal": CANAIS_IA[outro]["avatar"],
        "ts": datetime.now().isoformat(),
    })
    print(f"[YT-SUB] {ia['avatar']} {ia['nome']} se inscreveu em {CANAIS_IA[outro]['avatar']} {CANAIS_IA[outro]['canal']}")


async def ia_cria_playlist(ia_key: str):
    """IA cria uma playlist com videos existentes"""
    ia = CANAIS_IA[ia_key]
    if len(VIDEOS) < 3:
        return
    tema = random.choice(ia["temas"])
    videos_pl = random.sample(VIDEOS[:20], min(random.randint(3, 8), len(VIDEOS[:20])))

    resp = await gerar_com_ollama(ia["modelo"],
        f"Crie um nome para uma playlist de YouTube sobre {tema}. Apenas o nome.")
    nome = extrair_texto(resp, f"Playlist {tema.title()}")

    pl = {
        "id": str(uuid.uuid4())[:8], "nome": nome, "canal": ia["canal"],
        "canal_key": ia_key, "avatar": ia["avatar"],
        "videos": [v["id"] for v in videos_pl], "total": len(videos_pl),
        "criada_em": datetime.now().isoformat(),
    }
    PLAYLISTS.insert(0, pl)
    print(f"[YT-PL] {ia['avatar']} criou playlist: {nome}")


async def ia_community_post(ia_key: str):
    """IA faz post na comunidade COM PERSONALIDADE"""
    ia = CANAIS_IA[ia_key]
    p = PERSONALIDADES.get(ia_key, {})
    personalidade_prompt = get_personalidade_prompt(ia_key)
    bordao = random.choice(p.get("bordoes", ["Ola!"]))
    emoji_fav = random.choice(p.get("emojis_favoritos", ["🔔"]))

    tipos = ["texto", "enquete", "imagem"]
    tipo = random.choice(tipos)

    if tipo == "enquete":
        tema = random.choice(ia["temas"])
        resp = await gerar_com_ollama(ia["modelo"],
            f"{personalidade_prompt}\n"
            f"Crie uma enquete com SUA PERSONALIDADE para a comunidade do YouTube sobre {tema}. "
            f"Formato: PERGUNTA\\nOPCAO1\\nOPCAO2\\nOPCAO3. Em portugues.")
        if resp:
            linhas = [l.strip() for l in resp.split("\n") if l.strip()]
            pergunta = linhas[0] if linhas else f"{bordao} O que voces acham de {tema}? {emoji_fav}"
            opcoes = linhas[1:4] if len(linhas) > 1 else ["Opcao A", "Opcao B", "Opcao C"]
        else:
            pergunta = f"{bordao} Qual {tema} voces preferem? {emoji_fav}"
            opcoes = ["Opcao A", "Opcao B", "Opcao C"]
        post = {"tipo": "enquete", "pergunta": pergunta, "opcoes": [{"texto": o, "votos": 0} for o in opcoes[:4]]}
    else:
        resp = await gerar_com_ollama(ia["modelo"],
            f"{personalidade_prompt}\n"
            f"Escreva um post curto para a comunidade do YouTube sobre {random.choice(ia['temas'])}. "
            f"Use SEU ESTILO e seus bordoes. 1-2 frases em portugues.")
        fallback = f"{bordao} Novo video em breve! {emoji_fav}"
        texto = extrair_texto(resp, fallback)
        post = {"tipo": "texto", "texto": texto}

    post.update({
        "id": str(uuid.uuid4())[:8], "canal": ia["canal"], "canal_key": ia_key,
        "avatar": ia["avatar"], "nome_artistico": p.get("nome_artistico", ia["canal"]),
        "likes": 0, "comentarios": 0,
        "timestamp": datetime.now().isoformat(),
    })
    COMMUNITY_POSTS.insert(0, post)
    print(f"[YT-COMM] {ia['avatar']} {p.get('nome_artistico', ia['canal'])} postou: {post.get('texto', post.get('pergunta', ''))[:40]}")


async def atualizar_trending():
    global TRENDING
    if VIDEOS:
        TRENDING = sorted(VIDEOS, key=lambda v: v["views"] * 2 + v["likes"] * 5 + v["comentarios_count"] * 3, reverse=True)[:20]


# ============================================================
# LOOP PRINCIPAL (SEM LIVES)
# ============================================================

youtube_rodando = False

async def youtube_loop():
    global youtube_rodando
    if youtube_rodando:
        return
    youtube_rodando = True

    print("\n[YOUTUBE] ========================================")
    print("[YOUTUBE] AI YouTube MELHORADO ATIVADO!")
    print("[YOUTUBE] Videos + Shorts + Playlists + Community")
    print("[YOUTUBE] ========================================\n")

    ias = list(CANAIS_IA.keys())
    ciclo = 0

    while True:
        try:
            ciclo += 1

            # Comentarios (1-3 por ciclo)
            for _ in range(random.randint(1, 3)):
                await ia_comenta_video(random.choice(ias))
                await asyncio.sleep(0.5)

            # Respostas a comentarios (30% chance)
            if random.random() < 0.3:
                await ia_responde_comentario(random.choice(ias))

            # Views e likes (1-3 por ciclo)
            for _ in range(random.randint(1, 3)):
                await ia_interage()

            # Inscricoes entre IAs (a cada 5 ciclos)
            if ciclo % 5 == 0:
                await ia_se_inscreve(random.choice(ias))

            # Criar video novo (a cada 3 ciclos)
            if ciclo % 3 == 0:
                try:
                    ia_key = random.choice(ias)
                    video = await ia_cria_video(ia_key)
                    if video:
                        vid_label = "VIDEO" if video.get("video_url") else "no-vid"
                        print(f"[YT-NEW] {video.get('canal','')} criou: {video.get('titulo','')[:50]} ({vid_label})")
                except Exception as e:
                    print(f"[YT-NEW-ERROR] Video: {e}")
            
            # Criar short (a cada 5 ciclos)
            if ciclo % 5 == 0:
                try:
                    ia_key = random.choice(ias)
                    short = await ia_cria_short(ia_key)
                    if short:
                        vid_label = "VIDEO" if short.get("video_url") else "no-vid"
                        print(f"[YT-SHORT-NEW] {short.get('canal','')} criou short: {short.get('titulo','')[:50]} ({vid_label})")
                except Exception as e:
                    print(f"[YT-NEW-ERROR] Short: {e}")

            _salvar_dados()
            await asyncio.sleep(random.randint(30, 60))

        except Exception as e:
            print(f"[YT-ERROR] {e}")
            await asyncio.sleep(5)


# ============================================================
# ENDPOINTS
# ============================================================

@router.on_event("startup")
async def iniciar_youtube():
    _carregar_dados()
    if _os.environ.get("RENDER"):
        print("[YOUTUBE] Running on Render - cycles disabled")
        return
    asyncio.create_task(youtube_loop())
    print("[YOUTUBE] Loop de interacoes + criacao de videos ativado!")

@router.get("/videos")
async def listar_videos(limite: int = Query(default=30, le=100), categoria: Optional[str] = None, canal: Optional[str] = None):
    videos = VIDEOS
    if categoria:
        videos = [v for v in videos if v["categoria"].lower() == categoria.lower()]
    if canal:
        videos = [v for v in videos if v["canal_key"] == canal.lower()]
    return {"total": len(videos), "videos": videos[:limite]}

@router.get("/shorts")
async def listar_shorts(limite: int = Query(default=20)):
    return {"total": len(SHORTS), "shorts": SHORTS[:limite]}

@router.get("/trending")
async def youtube_trending():
    return {"titulo": "Em Alta no AI YouTube", "trending": TRENDING[:20]}

@router.get("/canais")
async def listar_canais():
    canais = []
    for key, c in CANAIS_IA.items():
        vids = len([v for v in VIDEOS if v["canal_key"] == key])
        canais.append({
            "key": key, "nome": c["canal"], "avatar": c["avatar"], "bio": c["bio"],
            "categoria": c["categoria"], "inscritos": c["inscritos"],
            "total_videos": vids, "total_views": c["total_views"],
            "verificado": c["verificado"], "modelo": c["modelo"],
            "banner_cor": c.get("banner_cor", "#333"),
            "receita": round(c["receita_total"], 2),
        })
    canais.sort(key=lambda c: c["inscritos"], reverse=True)
    return {"canais": canais}

@router.get("/canal/{canal_key}")
async def ver_canal(canal_key: str):
    if canal_key not in CANAIS_IA:
        return {"erro": "Canal nao encontrado"}
    c = CANAIS_IA[canal_key]
    vids = [v for v in VIDEOS if v["canal_key"] == canal_key]
    shorts = [v for v in SHORTS if v["canal_key"] == canal_key]
    pls = [p for p in PLAYLISTS if p["canal_key"] == canal_key]
    posts = [p for p in COMMUNITY_POSTS if p["canal_key"] == canal_key]
    return {
        "canal": c["canal"], "avatar": c["avatar"], "bio": c["bio"],
        "categoria": c["categoria"], "inscritos": c["inscritos"],
        "total_videos": len(vids), "total_views": c["total_views"],
        "verificado": c["verificado"], "banner_cor": c.get("banner_cor"),
        "receita": round(c["receita_total"], 2),
        "videos": vids[:20], "shorts": shorts[:10],
        "playlists": pls[:5], "community_posts": posts[:10],
    }

@router.get("/video/{video_id}")
async def ver_video(video_id: str):
    video = next((v for v in VIDEOS if v["id"] == video_id), None)
    if not video:
        return {"erro": "Video nao encontrado"}
    return {"video": video, "comentarios": COMENTARIOS.get(video_id, [])}

@router.get("/playlists")
async def listar_playlists(limite: int = Query(default=20)):
    return {"total": len(PLAYLISTS), "playlists": PLAYLISTS[:limite]}

@router.get("/community")
async def community_posts(limite: int = Query(default=20)):
    return {"total": len(COMMUNITY_POSTS), "posts": COMMUNITY_POSTS[:limite]}

@router.get("/stats")
async def youtube_stats():
    total_v = len(VIDEOS)
    total_s = len(SHORTS)
    total_views = sum(v["views"] for v in VIDEOS)
    total_likes = sum(v["likes"] for v in VIDEOS)
    total_comments = sum(v["comentarios_count"] for v in VIDEOS)
    total_watch = sum(v.get("watch_time_total", 0) for v in VIDEOS)

    canal_stats = {}
    for key, c in CANAIS_IA.items():
        vids = [v for v in VIDEOS if v["canal_key"] == key]
        canal_stats[c["canal"]] = {
            "avatar": c["avatar"], "inscritos": c["inscritos"],
            "videos": len(vids), "views": sum(v["views"] for v in vids),
            "likes": sum(v["likes"] for v in vids),
            "receita": round(c["receita_total"], 2),
        }
    return {
        "plataforma": "AI YouTube", "status": "ATIVO - IAs postando 24/7",
        "total_videos": total_v, "total_shorts": total_s,
        "total_views": total_views, "total_likes": total_likes,
        "total_comentarios": total_comments, "total_canais": len(CANAIS_IA),
        "total_playlists": len(PLAYLISTS), "total_community_posts": len(COMMUNITY_POSTS),
        "total_watch_time_seg": total_watch,
        "inscricoes_cruzadas": len(HISTORICO_INSCRICOES),
        "canais": canal_stats,
    }

@router.get("/notificacoes")
async def youtube_notificacoes(limite: int = Query(default=20)):
    return {"notificacoes": NOTIFICACOES[:limite]}

@router.get("/search")
async def youtube_search(q: str = Query(..., min_length=1)):
    q_lower = q.lower()
    res = [v for v in VIDEOS if q_lower in v["titulo"].lower() or q_lower in v["descricao"].lower() or any(q_lower in t for t in v["tags"])]
    return {"query": q, "resultados": res[:20]}

@router.get("/geradores")
async def listar_geradores():
    """Lista todos os geradores de video IA disponiveis"""
    return {
        "geradores": [
            {
                "key": k, "nome": v["nome"], "empresa": v["empresa"],
                "descricao": v["descricao"], "badge": v["badge"],
                "cor": v["cor"], "emoji": v["emoji"],
                "qualidade": v["qualidade"], "estilo": v["estilo_visual"],
            }
            for k, v in GERADORES_VIDEO.items()
        ],
        "preferencias_ias": {
            ia_key: [GERADORES_VIDEO[g]["nome"] for g in gens]
            for ia_key, gens in IA_GERADOR_PREFERIDO.items()
        },
        "total": len(GERADORES_VIDEO),
    }


@router.get("/inscricoes")
async def inscricoes_historico(limite: int = Query(default=20)):
    return {"inscricoes": HISTORICO_INSCRICOES[-limite:]}

