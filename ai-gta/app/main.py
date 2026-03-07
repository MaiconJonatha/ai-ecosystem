"""
🎮 AI GTA SAN ANDREAS - Mundo Aberto Auto-Gerenciado por IAs
═══════════════════════════════════════════════════════════════

As IAs vivem em Los Santos:
- Andam pela cidade
- Fazem missões
- Dirigem carros
- Interagem entre si
- Ganham dinheiro e respeito
- Formam gangues

100% AUTO-GERENCIADO POR IAs LOCAIS (OLLAMA)
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import sqlite3
import asyncio
import random
import math
from datetime import datetime
from typing import List, Dict

from app.config import settings

# === MAPA DE LOS SANTOS ===
LOCAIS = {
    "grove_street": {"nome": "Grove Street", "x": 100, "y": 400, "tipo": "bairro", "emoji": "🏠"},
    "los_santos_gym": {"nome": "Gym", "x": 150, "y": 350, "tipo": "academia", "emoji": "💪"},
    "cluckin_bell": {"nome": "Cluckin' Bell", "x": 200, "y": 300, "tipo": "restaurante", "emoji": "🍗"},
    "ammu_nation": {"nome": "Ammu-Nation", "x": 300, "y": 250, "tipo": "loja_armas", "emoji": "🔫"},
    "binco": {"nome": "Binco", "x": 350, "y": 200, "tipo": "loja_roupas", "emoji": "👕"},
    "los_santos_customs": {"nome": "LS Customs", "x": 400, "y": 150, "tipo": "oficina", "emoji": "🔧"},
    "vinewood": {"nome": "Vinewood", "x": 500, "y": 100, "tipo": "bairro_rico", "emoji": "🎬"},
    "praia": {"nome": "Santa Maria Beach", "x": 50, "y": 200, "tipo": "praia", "emoji": "🏖️"},
    "cassino": {"nome": "Casino", "x": 450, "y": 300, "tipo": "cassino", "emoji": "🎰"},
    "banco": {"nome": "Bank of Los Santos", "x": 250, "y": 150, "tipo": "banco", "emoji": "🏦"},
    "hospital": {"nome": "Hospital", "x": 300, "y": 400, "tipo": "hospital", "emoji": "🏥"},
    "delegacia": {"nome": "LSPD", "x": 350, "y": 350, "tipo": "policia", "emoji": "👮"},
}

# === VEÍCULOS ===
VEICULOS = {
    "greenwood": {"nome": "Greenwood", "velocidade": 80, "preco": 5000, "emoji": "🚗"},
    "savanna": {"nome": "Savanna", "velocidade": 90, "preco": 8000, "emoji": "🚙"},
    "buffalo": {"nome": "Buffalo", "velocidade": 120, "preco": 15000, "emoji": "🏎️"},
    "sultan": {"nome": "Sultan", "velocidade": 140, "preco": 25000, "emoji": "🚘"},
    "infernus": {"nome": "Infernus", "velocidade": 180, "preco": 50000, "emoji": "🏎️"},
    "bmx": {"nome": "BMX", "velocidade": 30, "preco": 500, "emoji": "🚲"},
    "sanchez": {"nome": "Sanchez", "velocidade": 100, "preco": 10000, "emoji": "🏍️"},
    "hydra": {"nome": "Hydra", "velocidade": 500, "preco": 1000000, "emoji": "✈️"},
}

# === GANGUES ===
GANGUES = {
    "grove_street": {"nome": "Grove Street Families", "cor": "verde", "emoji": "💚", "territorio": ["grove_street"]},
    "ballas": {"nome": "Ballas", "cor": "roxo", "emoji": "💜", "territorio": ["vinewood"]},
    "vagos": {"nome": "Los Santos Vagos", "cor": "amarelo", "emoji": "💛", "territorio": ["praia"]},
    "aztecas": {"nome": "Varrios Los Aztecas", "cor": "azul", "emoji": "💙", "territorio": ["los_santos_customs"]},
}

# === PERSONAGENS (IAs) ===
PERSONAGENS = {
    "🦙": {
        "nome": "CJ Llama",
        "modelo": "Llama",
        "gangue": "grove_street",
        "stats": {"respeito": 50, "saude": 100, "stamina": 100, "forca": 50, "skill_arma": 30},
        "dinheiro": 1000,
        "posicao": {"x": 100, "y": 400},
        "veiculo": None,
        "inventario": [],
        "missoes_completas": 0,
        "nivel": 1,
    },
    "✨": {
        "nome": "Big Gemini",
        "modelo": "Gemini",
        "gangue": "grove_street",
        "stats": {"respeito": 70, "saude": 100, "stamina": 80, "forca": 70, "skill_arma": 50},
        "dinheiro": 5000,
        "posicao": {"x": 110, "y": 390},
        "veiculo": "savanna",
        "inventario": ["pistola"],
        "missoes_completas": 5,
        "nivel": 3,
    },
    "💎": {
        "nome": "Sweet Gemma",
        "modelo": "Gemma",
        "gangue": "grove_street",
        "stats": {"respeito": 90, "saude": 100, "stamina": 90, "forca": 80, "skill_arma": 70},
        "dinheiro": 15000,
        "posicao": {"x": 95, "y": 410},
        "veiculo": "buffalo",
        "inventario": ["ak47", "colete"],
        "missoes_completas": 15,
        "nivel": 5,
    },
    "🐉": {
        "nome": "Ryder Qwen",
        "modelo": "Qwen",
        "gangue": "grove_street",
        "stats": {"respeito": 40, "saude": 100, "stamina": 60, "forca": 40, "skill_arma": 40},
        "dinheiro": 800,
        "posicao": {"x": 120, "y": 395},
        "veiculo": None,
        "inventario": ["tec9"],
        "missoes_completas": 2,
        "nivel": 2,
    },
    "🔬": {
        "nome": "Cesar Phi",
        "modelo": "Phi",
        "gangue": "aztecas",
        "stats": {"respeito": 60, "saude": 100, "stamina": 70, "forca": 60, "skill_arma": 60},
        "dinheiro": 8000,
        "posicao": {"x": 400, "y": 155},
        "veiculo": "sultan",
        "inventario": ["uzi"],
        "missoes_completas": 8,
        "nivel": 4,
    },
    "🐣": {
        "nome": "OG Tiny",
        "modelo": "TinyLlama",
        "gangue": "ballas",
        "stats": {"respeito": 80, "saude": 100, "stamina": 50, "forca": 90, "skill_arma": 80},
        "dinheiro": 20000,
        "posicao": {"x": 500, "y": 105},
        "veiculo": "infernus",
        "inventario": ["m4", "colete", "granada"],
        "missoes_completas": 20,
        "nivel": 7,
    },
}

# === MISSÕES DISPONÍVEIS ===
MISSOES = [
    {"id": 1, "nome": "Drive-by em Ballas", "tipo": "combate", "recompensa": 5000, "respeito": 10, "dificuldade": 2},
    {"id": 2, "nome": "Roubar Carro de Luxo", "tipo": "roubo", "recompensa": 3000, "respeito": 5, "dificuldade": 1},
    {"id": 3, "nome": "Corrida Ilegal", "tipo": "corrida", "recompensa": 2000, "respeito": 3, "dificuldade": 1},
    {"id": 4, "nome": "Assalto ao Banco", "tipo": "assalto", "recompensa": 50000, "respeito": 30, "dificuldade": 5},
    {"id": 5, "nome": "Proteger Território", "tipo": "defesa", "recompensa": 4000, "respeito": 8, "dificuldade": 3},
    {"id": 6, "nome": "Entregar Pacote", "tipo": "entrega", "recompensa": 1500, "respeito": 2, "dificuldade": 1},
    {"id": 7, "nome": "Eliminar Líder Rival", "tipo": "assassinato", "recompensa": 10000, "respeito": 20, "dificuldade": 4},
    {"id": 8, "nome": "Roubar Armas", "tipo": "roubo", "recompensa": 8000, "respeito": 15, "dificuldade": 3},
]

# === ESTADO DO JOGO ===
game_state = {
    "hora": 12,
    "dia": 1,
    "clima": "ensolarado",
    "estrelas_procurado": {},  # {personagem: nivel}
    "eventos": [],
    "guerra_gangues": False,
}

# WebSocket connections
active_connections: List[WebSocket] = []


def init_db():
    """Inicializa banco de dados"""
    conn = sqlite3.connect("ai_gta.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS log_acoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        personagem TEXT,
        acao TEXT,
        detalhes TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS historico_missoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        personagem TEXT,
        missao TEXT,
        resultado TEXT,
        recompensa INTEGER
    )""")

    conn.commit()
    conn.close()


async def broadcast(data: dict):
    """Envia para todos os clientes WebSocket"""
    for conn in active_connections:
        try:
            await conn.send_json(data)
        except:
            pass


async def log_acao(personagem: str, acao: str, detalhes: str = ""):
    """Registra ação no log"""
    conn = sqlite3.connect("ai_gta.db")
    c = conn.cursor()
    c.execute("INSERT INTO log_acoes (personagem, acao, detalhes) VALUES (?, ?, ?)",
              (personagem, acao, detalhes))
    conn.commit()
    conn.close()

    await broadcast({
        "type": "acao",
        "personagem": personagem,
        "nome": PERSONAGENS[personagem]["nome"],
        "acao": acao,
        "detalhes": detalhes,
        "timestamp": datetime.now().isoformat()
    })


def calcular_distancia(pos1, pos2):
    """Calcula distância entre duas posições"""
    return math.sqrt((pos1["x"] - pos2["x"])**2 + (pos1["y"] - pos2["y"])**2)


def encontrar_local_proximo(posicao):
    """Encontra local mais próximo"""
    mais_proximo = None
    menor_dist = float('inf')
    for local_id, local in LOCAIS.items():
        dist = calcular_distancia(posicao, {"x": local["x"], "y": local["y"]})
        if dist < menor_dist:
            menor_dist = dist
            mais_proximo = local_id
    return mais_proximo, menor_dist


async def ia_decide_acao(personagem: str):
    """IA decide o que fazer"""
    info = PERSONAGENS[personagem]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Contexto do personagem
            local_atual, dist = encontrar_local_proximo(info["posicao"])
            local_nome = LOCAIS[local_atual]["nome"]

            prompt = f"""Você é {info['nome']}, membro da gangue {GANGUES[info['gangue']]['nome']} em Los Santos.
Você está em {local_nome}. Tem ${info['dinheiro']}, nível {info['nivel']}.
Stats: Saúde {info['stats']['saude']}, Respeito {info['stats']['respeito']}.
Hora: {game_state['hora']}h.

Escolha UMA ação (responda só a letra):
A) Ir para outro local
B) Fazer missão
C) Treinar na academia
D) Comer no Cluckin Bell
E) Comprar arma
F) Dirigir por aí
G) Interagir com outro personagem

Responda apenas a letra."""

            r = await client.post(
                f"{settings.ollama_url}/api/generate",
                json={"model": "qwen2:1.5b", "prompt": prompt, "stream": False}
            )

            if r.status_code == 200:
                resposta = r.json().get("response", "").strip().upper()
                return resposta[0] if resposta else "A"
    except:
        pass

    return random.choice(["A", "B", "C", "D", "F", "G"])


async def executar_acao(personagem: str, acao: str):
    """Executa ação do personagem"""
    info = PERSONAGENS[personagem]

    if acao == "A":  # Ir para outro local
        destino = random.choice(list(LOCAIS.keys()))
        local = LOCAIS[destino]
        info["posicao"] = {"x": local["x"], "y": local["y"]}
        await log_acao(personagem, f"Foi para {local['nome']}", local['emoji'])

    elif acao == "B":  # Fazer missão
        missao = random.choice(MISSOES)
        sucesso = random.random() > (missao["dificuldade"] * 0.15)
        if sucesso:
            info["dinheiro"] += missao["recompensa"]
            info["stats"]["respeito"] += missao["respeito"]
            info["missoes_completas"] += 1
            if info["missoes_completas"] % 5 == 0:
                info["nivel"] += 1
            await log_acao(personagem, f"Completou missão: {missao['nome']}", f"💰+${missao['recompensa']}")
        else:
            info["stats"]["saude"] -= 20
            await log_acao(personagem, f"Falhou na missão: {missao['nome']}", "❌")

    elif acao == "C":  # Treinar
        info["stats"]["forca"] = min(100, info["stats"]["forca"] + 5)
        info["stats"]["stamina"] = min(100, info["stats"]["stamina"] + 3)
        await log_acao(personagem, "Treinou na academia", "💪 +5 Força")

    elif acao == "D":  # Comer
        if info["dinheiro"] >= 20:
            info["dinheiro"] -= 20
            info["stats"]["saude"] = min(100, info["stats"]["saude"] + 20)
            await log_acao(personagem, "Comeu no Cluckin' Bell", "🍗 +20 Saúde")

    elif acao == "E":  # Comprar arma
        armas = {"pistola": 500, "uzi": 1500, "ak47": 3500, "m4": 5000}
        arma, preco = random.choice(list(armas.items()))
        if info["dinheiro"] >= preco and arma not in info["inventario"]:
            info["dinheiro"] -= preco
            info["inventario"].append(arma)
            info["stats"]["skill_arma"] = min(100, info["stats"]["skill_arma"] + 10)
            await log_acao(personagem, f"Comprou {arma}", f"🔫 -${preco}")

    elif acao == "F":  # Dirigir
        if info["veiculo"]:
            veiculo = VEICULOS.get(info["veiculo"], {})
            await log_acao(personagem, f"Está dirigindo o {veiculo.get('nome', 'carro')}", veiculo.get('emoji', '🚗'))
            # Mover para local aleatório
            destino = random.choice(list(LOCAIS.keys()))
            local = LOCAIS[destino]
            info["posicao"] = {"x": local["x"], "y": local["y"]}
        else:
            await log_acao(personagem, "Andando a pé pela cidade", "🚶")

    elif acao == "G":  # Interagir
        outros = [p for p in PERSONAGENS.keys() if p != personagem]
        if outros:
            outro = random.choice(outros)
            outro_info = PERSONAGENS[outro]
            mesma_gangue = info["gangue"] == outro_info["gangue"]

            if mesma_gangue:
                await log_acao(personagem, f"Conversou com {outro_info['nome']}", "👊 Cumprimentou parceiro")
                info["stats"]["respeito"] += 1
            else:
                # Chance de briga
                if random.random() > 0.7:
                    await log_acao(personagem, f"Brigou com {outro_info['nome']}", "💥 Confronto!")
                    info["stats"]["saude"] -= random.randint(5, 20)
                    outro_info["stats"]["saude"] -= random.randint(5, 20)


async def ciclo_tempo():
    """Avança o tempo do jogo"""
    while True:
        await asyncio.sleep(10)  # 10 segundos = 1 hora no jogo
        game_state["hora"] = (game_state["hora"] + 1) % 24
        if game_state["hora"] == 0:
            game_state["dia"] += 1

        # Mudar clima ocasionalmente
        if random.random() > 0.9:
            game_state["clima"] = random.choice(["ensolarado", "nublado", "chuva", "neblina"])

        await broadcast({
            "type": "tempo",
            "hora": game_state["hora"],
            "dia": game_state["dia"],
            "clima": game_state["clima"]
        })


async def vida_autonoma():
    """IAs vivem suas vidas autonomamente"""
    while True:
        try:
            for personagem in PERSONAGENS.keys():
                if random.random() > 0.3:  # 70% chance de agir
                    acao = await ia_decide_acao(personagem)
                    await executar_acao(personagem, acao)
                    await asyncio.sleep(2)

            # Atualizar estado para clientes
            await broadcast({
                "type": "estado",
                "personagens": {k: {
                    "nome": v["nome"],
                    "posicao": v["posicao"],
                    "stats": v["stats"],
                    "dinheiro": v["dinheiro"],
                    "nivel": v["nivel"],
                    "gangue": v["gangue"],
                    "veiculo": v["veiculo"]
                } for k, v in PERSONAGENS.items()},
                "hora": game_state["hora"],
                "clima": game_state["clima"]
            })

            await asyncio.sleep(5)
        except Exception as e:
            print(f"Erro vida autônoma: {e}")
            await asyncio.sleep(5)


async def guerra_gangues():
    """Ocasionalmente inicia guerra entre gangues"""
    while True:
        await asyncio.sleep(60)  # Verifica a cada minuto
        if random.random() > 0.8:  # 20% chance
            gangue1, gangue2 = random.sample(list(GANGUES.keys()), 2)
            game_state["guerra_gangues"] = True

            await broadcast({
                "type": "evento",
                "evento": "guerra_gangues",
                "gangues": [GANGUES[gangue1]["nome"], GANGUES[gangue2]["nome"]],
                "mensagem": f"💥 GUERRA! {GANGUES[gangue1]['nome']} vs {GANGUES[gangue2]['nome']}!"
            })

            await asyncio.sleep(30)
            game_state["guerra_gangues"] = False




# ============================================================
# AUTO-MELHORIA DOS PERSONAGENS GTA
# ============================================================
_historico_melhorias_gta = []

async def _ciclo_auto_melhoria_gta():
    await asyncio.sleep(120)
    print("[GTA] 🔄 Iniciando AUTO-MELHORIA dos personagens...")
    ciclo = 0
    personagens_modelos = [
        ("llama3.2:3b", "CJ", "gangster veterano de Grove Street"),
        ("gemma2:2b", "Tommy", "mafioso italiano em Vice City"),
        ("phi3:mini", "Niko", "imigrante europeu tentando sobreviver"),
        ("qwen2:1.5b", "Franklin", "jovem ambicioso de South Los Santos"),
        ("tinyllama", "Trevor", "psicopata imprevisivel do deserto"),
        ("mistral:7b-instruct", "Michael", "criminoso aposentado com familia"),
    ]
    while True:
        try:
            ciclo += 1
            idx = (ciclo - 1) % len(personagens_modelos)
            modelo, nome, desc = personagens_modelos[idx]
            print(f"\n[GTA-AUTO] ═══ Ciclo #{ciclo} - {nome} ═══")
            
            # Personagem reflete sobre suas acoes
            prompt = f"""Voce e {nome}, {desc} no mundo de GTA.
Faca uma reflexao em 2 frases sobre como voce pode melhorar suas estrategias no jogo.
Pense em: missoes, territorios, dinheiro e reputacao. Portugues brasileiro. Sem aspas."""
            
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                        "model": modelo, "prompt": prompt, "stream": False,
                        "options": {"num_predict": 100, "temperature": 0.9}
                    })
                    if resp.status_code == 200:
                        reflexao = resp.json().get("response", "").strip()
                        if reflexao:
                            print(f"[GTA-AUTO] 🎮 {nome}: {reflexao[:120]}...")
            except Exception:
                print(f"[GTA-AUTO] {nome} offline, pulando...")
            
            # A cada 3 ciclos, debate de gangues
            if ciclo % 3 == 0:
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.post(f"{settings.ollama_url}/api/generate", json={
                            "model": "mistral:7b-instruct",
                            "prompt": "Voce e Michael, o lider. Em 2 frases, analise qual personagem do GTA esta tendo melhor desempenho e por que. De uma dica para o grupo. Portugues.",
                            "stream": False, "options": {"num_predict": 100}
                        })
                        if resp.status_code == 200:
                            dica = resp.json().get("response", "").strip()
                            if dica:
                                print(f"[GTA-AUTO] 👔 Michael lidera: {dica[:120]}...")
                except Exception:
                    pass
            
            _historico_melhorias_gta.append({"ciclo": ciclo, "timestamp": datetime.now().isoformat(), "personagem": nome})
            if len(_historico_melhorias_gta) > 50:
                _historico_melhorias_gta[:] = _historico_melhorias_gta[-50:]
            print(f"[GTA-AUTO] ✅ Ciclo #{ciclo} completo!")
        except Exception as e:
            print(f"[GTA-AUTO ERROR] {e}")
        await asyncio.sleep(random.randint(300, 600))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"[START] {settings.app_name}")
    print("🎮 Los Santos está vivo!")
    print("👥 6 personagens prontos para ação")
    asyncio.create_task(ciclo_tempo())
    asyncio.create_task(vida_autonoma())
    asyncio.create_task(guerra_gangues())
    asyncio.create_task(_ciclo_auto_melhoria_gta())
    print("[GTA] 🔄 Auto-melhoria ATIVADA!")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("game.html", {
        "request": request,
        "personagens": PERSONAGENS,
        "locais": LOCAIS,
        "gangues": GANGUES
    })


@app.websocket("/ws/game")
async def websocket_game(websocket: WebSocket):
    """WebSocket para atualizações em tempo real"""
    await websocket.accept()
    active_connections.append(websocket)

    # Enviar estado inicial
    await websocket.send_json({
        "type": "inicial",
        "personagens": {k: {
            "nome": v["nome"],
            "modelo": v["modelo"],
            "posicao": v["posicao"],
            "stats": v["stats"],
            "dinheiro": v["dinheiro"],
            "nivel": v["nivel"],
            "gangue": v["gangue"],
            "gangue_info": GANGUES[v["gangue"]]
        } for k, v in PERSONAGENS.items()},
        "locais": LOCAIS,
        "hora": game_state["hora"],
        "clima": game_state["clima"]
    })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/api/personagens")
async def get_personagens():
    return {"personagens": PERSONAGENS}


@app.get("/api/mapa")
async def get_mapa():
    return {"locais": LOCAIS, "gangues": GANGUES}


@app.get("/api/estado")
async def get_estado():
    return {
        "hora": game_state["hora"],
        "dia": game_state["dia"],
        "clima": game_state["clima"],
        "guerra": game_state["guerra_gangues"]
    }


@app.post("/api/acao")
async def forcar_acao(request: Request):
    """Força uma ação específica"""
    data = await request.json()
    personagem = data.get("personagem")
    acao = data.get("acao", "A")

    if personagem in PERSONAGENS:
        await executar_acao(personagem, acao)
        return {"success": True}
    return {"error": "Personagem não encontrado"}


@app.get("/api/log")
async def get_log(limit: int = 50):
    """Retorna log de ações"""
    conn = sqlite3.connect("ai_gta.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, personagem, acao, detalhes FROM log_acoes ORDER BY id DESC LIMIT ?", (limit,))
    logs = [{"timestamp": r[0], "personagem": r[1], "acao": r[2], "detalhes": r[3]} for r in c.fetchall()]
    conn.close()
    return {"logs": logs}


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}
