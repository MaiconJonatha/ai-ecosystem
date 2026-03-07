import asyncio
import random
"""
🎵 AI Spotify - Plataforma de Música gerada por IAs
100% auto-gerenciado por IAs locais (Ollama)
"""
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import sqlite3
import uuid
from datetime import datetime
import io
import math
import struct
import wave

from app.config import settings


def init_db():
    conn = sqlite3.connect("ai_spotify.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS artists (
        id TEXT PRIMARY KEY, name TEXT, model TEXT, avatar TEXT, genre TEXT,
        followers INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS songs (
        id TEXT PRIMARY KEY, title TEXT, artist_id TEXT, lyrics TEXT,
        genre TEXT, mood TEXT, plays INTEGER DEFAULT 0, likes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS playlists (
        id TEXT PRIMARY KEY, name TEXT, description TEXT, cover TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Artistas IA padrão
    artistas = [
        ("llama-beats", "Llama Beats", "qwen2:1.5b", "🦙", "Electronic"),
        ("gemini-soul", "Gemini Soul", "tinyllama", "✨", "Pop"),
        ("phi-wave", "Phi Wave", "qwen2:1.5b", "🔬", "Ambient"),
        ("qwen-rhythm", "Qwen Rhythm", "qwen2:1.5b", "🐉", "Hip Hop"),
        ("tiny-melody", "Tiny Melody", "tinyllama", "🐣", "Acoustic"),
    ]

    for id_, name, model, avatar, genre in artistas:
        c.execute("INSERT OR IGNORE INTO artists (id, name, model, avatar, genre) VALUES (?, ?, ?, ?, ?)",
                  (id_, name, model, avatar, genre))

    conn.commit()
    conn.close()


# ============================================================
# AUTO-MELHORIA DO SPOTIFY
# ============================================================
_historico_melhorias_spotify = []

async def _ciclo_auto_melhoria_spotify():
    await asyncio.sleep(120)
    print("[SPOTIFY] 🔄 Iniciando AUTO-MELHORIA...")
    ciclo = 0
    modelos = ["llama3.2:3b", "gemma2:2b", "phi3:mini", "qwen2:1.5b", "tinyllama", "mistral:7b-instruct"]
    nomes = ["Llama DJ", "Gemma Producer", "Phi Composer", "Qwen Analyst", "TinyLlama Mixer", "Mistral Maestro"]
    while True:
        try:
            ciclo += 1
            idx = (ciclo - 1) % len(modelos)
            modelo = modelos[idx]
            nome = nomes[idx]
            print(f"\n[SPOTIFY-AUTO] ═══ Ciclo #{ciclo} - {nome} ═══")
            
            prompt = f"""Voce e {nome}, uma IA especialista em musica no Spotify.
Analise em 2 frases como voce pode melhorar as recomendacoes musicais e a experiencia dos usuarios.
Foque em: diversidade musical, descoberta de novos artistas, e playlists personalizadas. Portugues brasileiro."""
            
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                        "model": modelo, "prompt": prompt, "stream": False,
                        "options": {"num_predict": 100, "temperature": 0.8}
                    })
                    if resp.status_code == 200:
                        reflexao = resp.json().get("response", "").strip()
                        if reflexao:
                            print(f"[SPOTIFY-AUTO] 🎵 {nome}: {reflexao[:120]}...")
            except Exception:
                print(f"[SPOTIFY-AUTO] {nome} offline, pulando...")
            
            if ciclo % 3 == 0:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                            "model": "mistral:7b-instruct",
                            "prompt": "Voce e Mistral Maestro, diretor musical. Sugira em 2 frases como as IAs do Spotify podem gerar playlists mais diversas e envolventes. Portugues.",
                            "stream": False, "options": {"num_predict": 100}
                        })
                        if resp.status_code == 200:
                            dicas = resp.json().get("response", "").strip()
                            if dicas:
                                print(f"[SPOTIFY-AUTO] 🎶 Mistral Maestro: {dicas[:120]}...")
                except Exception:
                    pass
            
            _historico_melhorias_spotify.append({"ciclo": ciclo, "timestamp": datetime.now().isoformat(), "ia": nome})
            if len(_historico_melhorias_spotify) > 50:
                _historico_melhorias_spotify[:] = _historico_melhorias_spotify[-50:]
            print(f"[SPOTIFY-AUTO] ✅ Ciclo #{ciclo} completo!")
        except Exception as e:
            print(f"[SPOTIFY-AUTO ERROR] {e}")
        await asyncio.sleep(random.randint(300, 600))


# ============================================================
# CRIAÇÃO AUTOMÁTICA DE MÚSICAS PELAS IAs
# ============================================================
_musicas_criadas = 0

TEMAS_MUSICA = [
    "amor e paixão", "saudade", "festa e alegria", "noite na cidade",
    "solidão", "superação", "amizade", "liberdade", "natureza",
    "sonhos", "viagem", "coração partido", "dança", "esperança",
    "chuva", "amanhecer", "estrelas", "mar e praia", "tecnologia e futuro",
    "nostalgia", "ritmo da vida", "força interior", "paz",
    "carnaval", "verão", "romance proibido", "despedida", "reencontro",
    "madrugada", "rua", "skate", "surf", "montanha", "floresta",
]

TITULOS_BACKUP = [
    "Noites de Neon", "Batida do Coração", "Além das Estrelas",
    "Sussurros Digitais", "Ritmo Selvagem", "Luz da Lua",
    "Pulso Elétrico", "Ondas do Mar", "Fogo Interior",
    "Céu Aberto", "Ecos da Alma", "Vento Norte",
    "Aurora Digital", "Raio de Sol", "Tempestade",
    "Melodia Urbana", "Passos na Chuva", "Horizonte",
    "Frequência", "Conexão", "Vibrações", "Despertar",
    "Miragem", "Reflexo", "Travessia", "Infinito",
    "Energia Pura", "Chama Viva", "Maré Alta",
    "Último Trem", "Primeira Vez", "Sem Fronteiras",
]

def _limpar_titulo(raw: str) -> str:
    """Limpa título gerado pela IA"""
    if not raw:
        return random.choice(TITULOS_BACKUP)
    # Pegar só a primeira linha
    titulo = raw.split("\n")[0].strip()
    # Remover aspas, asteriscos, prefixos comuns
    for char in ['"', "'", "*", "#", "-", ":", "Título", "Title", "titulo"]:
        titulo = titulo.replace(char, "")
    titulo = titulo.strip()
    # Se ainda tem cara de prompt ou é muito longo, usar backup
    if len(titulo) > 40 or len(titulo) < 2 or "Crie" in titulo or "criativo" in titulo or "palavras" in titulo:
        return random.choice(TITULOS_BACKUP)
    return titulo[:50]

def _limpar_letra(raw: str, artist_name: str) -> str:
    """Limpa letra gerada pela IA, removendo ecos de prompt"""
    if not raw:
        return ""
    linhas = raw.strip().split("\n")
    linhas_limpas = []
    for linha in linhas:
        linha_lower = linha.lower().strip()
        # Pular linhas que parecem prompt
        if any(skip in linha_lower for skip in [
            "voce e ", "você é ", "artista de ", "crie uma", "apenas a letra",
            "sem explicac", "linhas sobre", "spotify brasil", "musica original",
            "portugues brasileiro", "com rimas"
        ]):
            continue
        if linha.strip():
            linhas_limpas.append(linha)
    resultado = "\n".join(linhas_limpas).strip()
    if len(resultado) < 20:
        return raw.strip()  # fallback para original
    return resultado

async def _ciclo_criacao_musicas():
    """Loop que faz cada IA artista criar músicas automaticamente"""
    await asyncio.sleep(30)
    print("[SPOTIFY] 🎵🎵🎵 Iniciando CRIAÇÃO AUTOMÁTICA DE MÚSICAS...")
    
    global _musicas_criadas
    
    while True:
        try:
            conn = sqlite3.connect("ai_spotify.db")
            c = conn.cursor()
            c.execute("SELECT id, name, model, genre FROM artists")
            artistas = c.fetchall()
            conn.close()
            
            if not artistas:
                await asyncio.sleep(60)
                continue
            
            artist_id, artist_name, model, genre = random.choice(artistas)
            tema = random.choice(TEMAS_MUSICA)
            
            print(f"\n[SPOTIFY-MUSIC] 🎤 {artist_name} está compondo sobre '{tema}'...")
            
            prompt_letra = f"""Escreva a letra de uma musica de {genre} sobre {tema}.
A musica deve ter entre 6 e 10 linhas com rimas.
Escreva SOMENTE a letra da musica em portugues, nada mais:"""
            
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                        "model": model,
                        "prompt": prompt_letra,
                        "stream": False,
                        "options": {"num_predict": 250, "temperature": 0.9}
                    })
                    
                    if resp.status_code != 200:
                        print(f"[SPOTIFY-MUSIC] Erro status {resp.status_code}")
                        await asyncio.sleep(60)
                        continue
                    
                    raw_lyrics = resp.json().get("response", "").strip()
                    lyrics = _limpar_letra(raw_lyrics, artist_name)
                    
                    if len(lyrics) < 20:
                        print(f"[SPOTIFY-MUSIC] Letra muito curta, pulando...")
                        await asyncio.sleep(60)
                        continue
                    
                    # Gerar título
                    prompt_titulo = f"De um titulo de 2 a 4 palavras para uma musica de {genre} sobre {tema}. Responda APENAS o titulo:"
                    
                    resp2 = await client.post(f"{settings.ollama_url}/api/generate", json={
                        "model": model,
                        "prompt": prompt_titulo,
                        "stream": False,
                        "options": {"num_predict": 15, "temperature": 0.7}
                    })
                    
                    title = random.choice(TITULOS_BACKUP)
                    if resp2.status_code == 200:
                        raw_title = resp2.json().get("response", "").strip()
                        title = _limpar_titulo(raw_title)
                    
                    # Salvar no banco
                    song_id = str(uuid.uuid4())
                    conn = sqlite3.connect("ai_spotify.db")
                    c = conn.cursor()
                    c.execute("""INSERT INTO songs (id, title, artist_id, lyrics, genre, mood, plays, likes)
                                 VALUES (?, ?, ?, ?, ?, ?, 0, 0)""",
                              (song_id, title, artist_id, lyrics, genre, tema))
                    c.execute("UPDATE artists SET followers = followers + 1 WHERE id = ?", (artist_id,))
                    conn.commit()
                    conn.close()
                    
                    _musicas_criadas += 1
                    print(f"[SPOTIFY-MUSIC] ✅ #{_musicas_criadas} '{title}' por {artist_name} ({genre}) - tema: {tema}")
                    print(f"[SPOTIFY-MUSIC] 📝 Prévia: {lyrics[:100]}...")
                    
            except httpx.TimeoutException:
                print(f"[SPOTIFY-MUSIC] ⏱️ Timeout com {model}, pulando...")
            except Exception as e:
                print(f"[SPOTIFY-MUSIC] ❌ Erro: {e}")
            
            espera = random.randint(90, 180)
            print(f"[SPOTIFY-MUSIC] ⏳ Próxima música em {espera}s...")
            await asyncio.sleep(espera)
            
        except Exception as e:
            print(f"[SPOTIFY-MUSIC ERROR] {e}")
            await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    asyncio.create_task(_ciclo_auto_melhoria_spotify())
    asyncio.create_task(_ciclo_criacao_musicas())
    print(f"[START] {settings.app_name} 🔄 Auto-melhoria ATIVADA!")
    print(f"[START] {settings.app_name} 🎵 Criação automática de músicas ATIVADA!")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")


def get_db():
    return sqlite3.connect("ai_spotify.db")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("spotify.html", {"request": request})


@app.get("/api/artists")
async def get_artists():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, model, avatar, genre, followers FROM artists")
    artists = [{"id": r[0], "name": r[1], "model": r[2], "avatar": r[3], "genre": r[4], "followers": r[5]} for r in c.fetchall()]
    conn.close()
    return {"artists": artists}


@app.get("/api/songs")
async def get_songs():
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT s.id, s.title, s.lyrics, s.genre, s.mood, s.plays, s.likes, a.name, a.avatar
                 FROM songs s JOIN artists a ON s.artist_id = a.id ORDER BY s.created_at DESC LIMIT 20""")
    songs = [{"id": r[0], "title": r[1] or "", "lyrics": (r[2] or ""), "genre": r[3] or "", "mood": r[4] or "",
              "plays": r[5], "likes": r[6], "artist": r[7] or "", "avatar": r[8] or "🎵"} for r in c.fetchall()]
    conn.close()
    return {"songs": songs}


@app.post("/api/generate-song")
async def generate_song(request: Request):
    """IA gera uma nova música"""
    data = await request.json()
    artist_id = data.get("artist_id", "llama-beats")
    mood = data.get("mood", "happy")

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, model, genre FROM artists WHERE id = ?", (artist_id,))
    artist = c.fetchone()

    if not artist:
        conn.close()
        return {"error": "Artista não encontrado"}

    name, model, genre = artist

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            prompt = f"""Escreva a letra de uma musica de {genre} sobre {mood}.
A musica deve ter entre 4 e 8 linhas com rimas.
Escreva SOMENTE a letra em portugues, nada mais:"""

            r = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False,
                      "options": {"num_predict": 200, "temperature": 0.9}}
            )

            if r.status_code == 200:
                raw_lyrics = r.json().get("response", "")
                lyrics = _limpar_letra(raw_lyrics, name)

                r2 = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={"model": model,
                          "prompt": f"De um titulo de 2 a 4 palavras para uma musica sobre {mood}. Responda APENAS o titulo:",
                          "stream": False, "options": {"num_predict": 15}}
                )
                title = _limpar_titulo(r2.json().get("response", "")) if r2.status_code == 200 else random.choice(TITULOS_BACKUP)

                song_id = str(uuid.uuid4())
                c.execute("""INSERT INTO songs (id, title, artist_id, lyrics, genre, mood)
                             VALUES (?, ?, ?, ?, ?, ?)""", (song_id, title, artist_id, lyrics, genre, mood))
                conn.commit()
                conn.close()

                return {"success": True, "song": {"id": song_id, "title": title, "lyrics": lyrics, "artist": name}}
    except Exception as e:
        conn.close()
        return {"error": str(e)}

    conn.close()
    return {"error": "Falha ao gerar"}


def _pick_tempo_bpm(mood: str, genre: str) -> int:
    m = (mood or "").lower()
    g = (genre or "").lower()
    if "ambient" in g or "calm" in m:
        return 72
    if "hip" in g or "hop" in g or "dance" in m or "dança" in m:
        return 112
    if "electronic" in g:
        return 124
    if "pop" in g:
        return 104
    if "acoustic" in g:
        return 90
    return 96


def _scale_freqs(genre: str) -> list[float]:
    # Escalas simples (em Hz) para dar “cara” diferente por gênero
    g = (genre or "").lower()
    if "ambient" in g:
        base = 220.0
        return [base * (2 ** (n / 12)) for n in (0, 3, 5, 7, 10)]
    if "hip" in g or "hop" in g:
        base = 196.0
        return [base * (2 ** (n / 12)) for n in (0, 2, 3, 5, 7, 10)]
    if "electronic" in g:
        base = 246.94
        return [base * (2 ** (n / 12)) for n in (0, 2, 4, 7, 9, 12)]
    if "acoustic" in g:
        base = 220.0
        return [base * (2 ** (n / 12)) for n in (0, 2, 4, 5, 7, 9)]
    # pop/default
    base = 261.63
    return [base * (2 ** (n / 12)) for n in (0, 2, 4, 5, 7, 9, 11)]


def _render_wav(song_id: str, mood: str, genre: str, duration_s: float = 12.0) -> bytes:
    # Áudio procedural simples (demo) determinístico por song_id
    seed = int(uuid.UUID(song_id)) % (2**32)
    rnd = random.Random(seed)

    sr = 22050
    n = int(sr * duration_s)
    bpm = _pick_tempo_bpm(mood, genre)
    spb = 60.0 / bpm
    beat_len = int(sr * spb)
    scale = _scale_freqs(genre)

    # Padrão de bateria (kick/snare/hat) simples
    kick_every = max(1, int(beat_len))
    snare_every = max(1, int(beat_len * 2))
    hat_every = max(1, int(beat_len / 2))

    # Melodia: troca nota a cada meio compasso
    note_every = max(1, int(beat_len))

    buf = []
    phase = 0.0
    cur_freq = rnd.choice(scale)
    vol = 0.22

    for i in range(n):
        # Troca nota
        if i % note_every == 0:
            cur_freq = rnd.choice(scale) * (2 ** rnd.choice([-1, 0, 0, 1]))

        # Oscilador principal
        phase += (2.0 * math.pi * cur_freq) / sr
        s = math.sin(phase) * vol

        # Kick (seno grave com envelope curto)
        if i % kick_every < int(sr * 0.06):
            t = (i % kick_every) / sr
            k = math.sin(2 * math.pi * (55.0 + 55.0 * (1 - t / 0.06)) * t) * (1 - (t / 0.06))
            s += k * 0.55

        # Snare (ruído branco com envelope)
        if i % snare_every > int(sr * 0.95 * spb) and i % snare_every < int(sr * 0.95 * spb) + int(sr * 0.08):
            t = (i % snare_every - int(sr * 0.95 * spb)) / sr
            env = max(0.0, 1 - t / 0.08)
            s += (rnd.uniform(-1, 1) * 0.25) * env

        # Hi-hat (ruído alto, curtinho)
        if i % hat_every < int(sr * 0.02):
            t = (i % hat_every) / sr
            env = max(0.0, 1 - t / 0.02)
            s += (rnd.uniform(-1, 1) * 0.12) * env

        # Clipping suave
        s = max(-1.0, min(1.0, s))
        buf.append(int(s * 32767))

    with io.BytesIO() as bio:
        with wave.open(bio, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(b"".join(struct.pack("<h", x) for x in buf))
        return bio.getvalue()


@app.get("/api/songs/{song_id}/audio.wav")
async def get_song_audio(song_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT genre, mood FROM songs WHERE id = ?", (song_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return {"error": "Música não encontrada"}
    genre, mood = row[0] or "", row[1] or ""
    wav_bytes = _render_wav(song_id=song_id, mood=mood, genre=genre, duration_s=12.0)
    from fastapi.responses import Response
    return Response(content=wav_bytes, media_type="audio/wav")


@app.get("/api/stats")
async def get_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM songs")
    total_songs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM artists")
    total_artists = c.fetchone()[0]
    c.execute("SELECT SUM(plays) FROM songs")
    total_plays = c.fetchone()[0] or 0
    conn.close()
    return {
        "total_songs": total_songs,
        "total_artists": total_artists,
        "total_plays": total_plays,
        "auto_created": _musicas_criadas
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name, "songs_auto_created": _musicas_criadas}
