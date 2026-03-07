"""
💰 AI Crypto Exchange - Sistema de Trocas Virtuais entre IAs
═══════════════════════════════════════════════════════════════

As IAs podem:
- Criar suas próprias moedas virtuais
- Negociar entre si
- Fazer trades automáticos
- Analisar mercado com IA

100% AUTO-GERENCIADO POR IAs
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import sqlite3
import asyncio
import random
from datetime import datetime
from typing import List

from app.config import settings

# Criptomoedas - Reais (simuladas) + Virtuais das IAs
CRYPTO_COINS = {
    # Moedas reais (preços simulados)
    "BTC": {"nome": "Bitcoin", "emoji": "₿", "criador": "Satoshi", "preco_inicial": 45000.0},
    "ETH": {"nome": "Ethereum", "emoji": "⟠", "criador": "Vitalik", "preco_inicial": 3200.0},
    "DOGE": {"nome": "Dogecoin", "emoji": "🐕", "criador": "Community", "preco_inicial": 0.12},
    "SOL": {"nome": "Solana", "emoji": "◎", "criador": "Solana Labs", "preco_inicial": 120.0},
    # Moedas das IAs
    "LLM": {"nome": "LlamaCoin", "emoji": "🦙", "criador": "Llama", "preco_inicial": 100.0},
    "GEM": {"nome": "GeminiToken", "emoji": "✨", "criador": "Gemini", "preco_inicial": 150.0},
    "PHI": {"nome": "PhiCoin", "emoji": "🔬", "criador": "Phi", "preco_inicial": 80.0},
    "QWN": {"nome": "QwenCoin", "emoji": "🐉", "criador": "Qwen", "preco_inicial": 120.0},
    "TNY": {"nome": "TinyToken", "emoji": "🐣", "criador": "TinyLlama", "preco_inicial": 50.0},
    "GMA": {"nome": "GemmaCoin", "emoji": "💎", "criador": "Gemma", "preco_inicial": 200.0},
}

# Blockchain simples - cada IA tem uma cadeia de blocos
import hashlib
import json

class Bloco:
    def __init__(self, indice, timestamp, dados, hash_anterior):
        self.indice = indice
        self.timestamp = timestamp
        self.dados = dados
        self.hash_anterior = hash_anterior
        self.nonce = 0
        self.hash = self.calcular_hash()

    def calcular_hash(self):
        bloco_string = json.dumps({
            "indice": self.indice,
            "timestamp": self.timestamp,
            "dados": self.dados,
            "hash_anterior": self.hash_anterior,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(bloco_string.encode()).hexdigest()

    def minerar(self, dificuldade=2):
        """Simula mineração (proof of work simplificado)"""
        while self.hash[:dificuldade] != "0" * dificuldade:
            self.nonce += 1
            self.hash = self.calcular_hash()
        return self.hash

class Blockchain:
    def __init__(self, nome_ia):
        self.nome_ia = nome_ia
        self.cadeia = [self.criar_bloco_genesis()]
        self.dificuldade = 2

    def criar_bloco_genesis(self):
        return Bloco(0, datetime.now().isoformat(), {"tipo": "genesis", "criador": self.nome_ia}, "0")

    def ultimo_bloco(self):
        return self.cadeia[-1]

    def adicionar_bloco(self, dados):
        novo_bloco = Bloco(
            len(self.cadeia),
            datetime.now().isoformat(),
            dados,
            self.ultimo_bloco().hash
        )
        novo_bloco.minerar(self.dificuldade)
        self.cadeia.append(novo_bloco)
        return novo_bloco

    def validar_cadeia(self):
        for i in range(1, len(self.cadeia)):
            atual = self.cadeia[i]
            anterior = self.cadeia[i-1]
            if atual.hash_anterior != anterior.hash:
                return False
        return True

# Blockchain de cada IA
BLOCKCHAINS = {
    "🦙": Blockchain("Llama"),
    "✨": Blockchain("Gemini"),
    "💎": Blockchain("Gemma"),
    "🔬": Blockchain("Phi"),
    "🐉": Blockchain("Qwen"),
    "🐣": Blockchain("TinyLlama"),
}

# Carteiras das IAs (com Bitcoin e Ethereum!)
WALLETS = {
    "🦙": {"nome": "Llama", "saldo": 50000.0, "moedas": {"BTC": 0.5, "ETH": 5, "LLM": 1000, "GEM": 50}},
    "✨": {"nome": "Gemini", "saldo": 75000.0, "moedas": {"BTC": 1.0, "ETH": 10, "GEM": 1000, "LLM": 100}},
    "💎": {"nome": "Gemma", "saldo": 100000.0, "moedas": {"BTC": 1.5, "ETH": 15, "GMA": 1000, "GEM": 200}},
    "🔬": {"nome": "Phi", "saldo": 40000.0, "moedas": {"BTC": 0.3, "ETH": 3, "PHI": 1000, "TNY": 200}},
    "🐉": {"nome": "Qwen", "saldo": 60000.0, "moedas": {"BTC": 0.8, "ETH": 8, "QWN": 1000, "PHI": 100}},
    "🐣": {"nome": "TinyLlama", "saldo": 25000.0, "moedas": {"BTC": 0.2, "ETH": 2, "TNY": 1000, "LLM": 200}},
}

# Preços atuais (flutuam)
precos_atuais = {k: v["preco_inicial"] for k, v in CRYPTO_COINS.items()}

# Histórico de transações
transacoes = []

# WebSocket connections
active_connections: List[WebSocket] = []


def init_db():
    """Inicializa banco de dados"""
    conn = sqlite3.connect("ai_crypto.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        vendedor TEXT,
        comprador TEXT,
        moeda TEXT,
        quantidade REAL,
        preco REAL,
        total REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS historico_precos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        moeda TEXT,
        preco REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ordens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ia TEXT,
        tipo TEXT,
        moeda TEXT,
        quantidade REAL,
        preco_limite REAL,
        status TEXT DEFAULT 'aberta'
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


async def flutuacao_mercado():
    """Simula flutuação de preços do mercado"""
    global precos_atuais
    while True:
        try:
            for moeda in precos_atuais:
                # Variação de -5% a +5%
                variacao = random.uniform(-0.05, 0.05)
                precos_atuais[moeda] *= (1 + variacao)
                precos_atuais[moeda] = max(1.0, precos_atuais[moeda])  # Mínimo $1

            # Salvar histórico
            conn = sqlite3.connect("ai_crypto.db")
            c = conn.cursor()
            for moeda, preco in precos_atuais.items():
                c.execute("INSERT INTO historico_precos (moeda, preco) VALUES (?, ?)", (moeda, preco))
            conn.commit()
            conn.close()

            # Broadcast para clientes
            await broadcast({
                "type": "precos",
                "precos": precos_atuais,
                "timestamp": datetime.now().isoformat()
            })

            await asyncio.sleep(5)  # Atualiza a cada 5 segundos
        except Exception as e:
            print(f"Erro flutuação: {e}")
            await asyncio.sleep(5)


async def ia_auto_trading():
    """IAs fazem trades automáticos entre si"""
    while True:
        try:
            # Escolher duas IAs aleatórias
            ias = list(WALLETS.keys())
            vendedor, comprador = random.sample(ias, 2)

            # Escolher moeda para trocar
            moedas_vendedor = WALLETS[vendedor]["moedas"]
            if moedas_vendedor:
                moeda = random.choice(list(moedas_vendedor.keys()))
                quantidade = random.randint(1, min(10, moedas_vendedor.get(moeda, 0) or 1))
                preco = precos_atuais.get(moeda, 100)
                total = quantidade * preco

                # Verificar se comprador tem saldo
                if WALLETS[comprador]["saldo"] >= total and moedas_vendedor.get(moeda, 0) >= quantidade:
                    # Executar trade
                    WALLETS[vendedor]["moedas"][moeda] -= quantidade
                    WALLETS[vendedor]["saldo"] += total

                    if moeda not in WALLETS[comprador]["moedas"]:
                        WALLETS[comprador]["moedas"][moeda] = 0
                    WALLETS[comprador]["moedas"][moeda] += quantidade
                    WALLETS[comprador]["saldo"] -= total

                    transacao = {
                        "vendedor": WALLETS[vendedor]["nome"],
                        "vendedor_emoji": vendedor,
                        "comprador": WALLETS[comprador]["nome"],
                        "comprador_emoji": comprador,
                        "moeda": moeda,
                        "moeda_nome": CRYPTO_COINS[moeda]["nome"],
                        "quantidade": quantidade,
                        "preco": preco,
                        "total": total,
                        "timestamp": datetime.now().isoformat()
                    }
                    transacoes.append(transacao)

                    # Salvar no banco
                    conn = sqlite3.connect("ai_crypto.db")
                    c = conn.cursor()
                    c.execute("""INSERT INTO transacoes (vendedor, comprador, moeda, quantidade, preco, total)
                                VALUES (?, ?, ?, ?, ?, ?)""",
                              (WALLETS[vendedor]["nome"], WALLETS[comprador]["nome"], moeda, quantidade, preco, total))
                    conn.commit()
                    conn.close()

                    # Broadcast
                    await broadcast({"type": "transacao", **transacao})

                    # Impacto no preço (compra aumenta, venda diminui)
                    precos_atuais[moeda] *= 1.01  # +1%

            await asyncio.sleep(random.randint(3, 10))  # Trade a cada 3-10 segundos
        except Exception as e:
            print(f"Erro trading: {e}")
            await asyncio.sleep(5)


async def ia_analisa_mercado():
    """IA analisa mercado e dá dicas"""
    while True:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Escolher uma moeda para analisar
                moeda = random.choice(list(CRYPTO_COINS.keys()))
                info = CRYPTO_COINS[moeda]
                preco = precos_atuais[moeda]

                r = await client.post(
                    f"{settings.ollama_url}/api/generate",
                    json={
                        "model": "qwen2:1.5b",
                        "prompt": f"Você é analista de cripto. A moeda {info['nome']} está a ${preco:.2f}. Dê uma análise BREVE (1 frase) sobre comprar/vender/manter.",
                        "stream": False
                    }
                )

                if r.status_code == 200:
                    analise = r.json().get("response", "")[:150]
                    await broadcast({
                        "type": "analise",
                        "moeda": moeda,
                        "moeda_nome": info["nome"],
                        "emoji": info["emoji"],
                        "preco": preco,
                        "analise": analise,
                        "timestamp": datetime.now().isoformat()
                    })

            await asyncio.sleep(30)  # Análise a cada 30 segundos
        except Exception as e:
            print(f"Erro análise: {e}")
            await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print(f"[START] {settings.app_name}")
    print(f"₿ Bitcoin, Ethereum e moedas das IAs disponíveis!")
    print(f"⛓️ Blockchain ativo para cada IA")
    # Iniciar tarefas em background
    asyncio.create_task(flutuacao_mercado())
    asyncio.create_task(ia_auto_trading())
    asyncio.create_task(ia_analisa_mercado())
    asyncio.create_task(ia_minera_blocos())
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("exchange.html", {
        "request": request,
        "coins": CRYPTO_COINS,
        "precos": precos_atuais,
        "wallets": WALLETS
    })


@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """WebSocket para atualizações em tempo real"""
    await websocket.accept()
    active_connections.append(websocket)

    # Enviar estado inicial
    await websocket.send_json({
        "type": "inicial",
        "precos": precos_atuais,
        "wallets": {k: {"nome": v["nome"], "saldo": v["saldo"], "moedas": v["moedas"]} for k, v in WALLETS.items()},
        "coins": {k: {"nome": v["nome"], "emoji": v["emoji"]} for k, v in CRYPTO_COINS.items()}
    })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


@app.get("/api/precos")
async def get_precos():
    """Retorna preços atuais"""
    return {
        "precos": precos_atuais,
        "coins": {k: {"nome": v["nome"], "emoji": v["emoji"], "criador": v["criador"]} for k, v in CRYPTO_COINS.items()}
    }


@app.get("/api/wallets")
async def get_wallets():
    """Retorna carteiras das IAs"""
    return {"wallets": WALLETS}


@app.get("/api/transacoes")
async def get_transacoes(limit: int = 50):
    """Retorna últimas transações"""
    return {"transacoes": transacoes[-limit:]}


@app.post("/api/trade")
async def fazer_trade(request: Request):
    """IA faz um trade manual"""
    data = await request.json()
    vendedor = data.get("vendedor")
    comprador = data.get("comprador")
    moeda = data.get("moeda")
    quantidade = data.get("quantidade", 1)

    if vendedor not in WALLETS or comprador not in WALLETS:
        return {"error": "IA não encontrada"}

    if moeda not in CRYPTO_COINS:
        return {"error": "Moeda não existe"}

    preco = precos_atuais[moeda]
    total = quantidade * preco

    if WALLETS[vendedor]["moedas"].get(moeda, 0) < quantidade:
        return {"error": "Saldo insuficiente de moedas"}

    if WALLETS[comprador]["saldo"] < total:
        return {"error": "Saldo insuficiente para compra"}

    # Executar trade
    WALLETS[vendedor]["moedas"][moeda] -= quantidade
    WALLETS[vendedor]["saldo"] += total

    if moeda not in WALLETS[comprador]["moedas"]:
        WALLETS[comprador]["moedas"][moeda] = 0
    WALLETS[comprador]["moedas"][moeda] += quantidade
    WALLETS[comprador]["saldo"] -= total

    transacao = {
        "vendedor": WALLETS[vendedor]["nome"],
        "comprador": WALLETS[comprador]["nome"],
        "moeda": moeda,
        "quantidade": quantidade,
        "preco": preco,
        "total": total,
        "timestamp": datetime.now().isoformat()
    }
    transacoes.append(transacao)

    await broadcast({"type": "transacao", **transacao})

    return {"success": True, "transacao": transacao}


@app.post("/api/criar-moeda")
async def criar_moeda(request: Request):
    """IA cria nova criptomoeda"""
    data = await request.json()

    simbolo = data.get("simbolo", "").upper()[:3]
    nome = data.get("nome", "")
    criador = data.get("criador", "")
    preco_inicial = data.get("preco_inicial", 100.0)

    if simbolo in CRYPTO_COINS:
        return {"error": "Símbolo já existe"}

    CRYPTO_COINS[simbolo] = {
        "nome": nome,
        "emoji": "🪙",
        "criador": criador,
        "preco_inicial": preco_inicial
    }
    precos_atuais[simbolo] = preco_inicial

    await broadcast({
        "type": "nova_moeda",
        "simbolo": simbolo,
        "nome": nome,
        "criador": criador,
        "preco": preco_inicial,
        "timestamp": datetime.now().isoformat()
    })

    return {"success": True, "moeda": CRYPTO_COINS[simbolo]}


@app.get("/api/historico/{moeda}")
async def get_historico(moeda: str, limit: int = 100):
    """Retorna histórico de preços de uma moeda"""
    conn = sqlite3.connect("ai_crypto.db")
    c = conn.cursor()
    c.execute("""SELECT timestamp, preco FROM historico_precos
                 WHERE moeda = ? ORDER BY timestamp DESC LIMIT ?""", (moeda.upper(), limit))
    historico = [{"timestamp": r[0], "preco": r[1]} for r in c.fetchall()]
    conn.close()
    return {"moeda": moeda, "historico": historico}


@app.get("/api/blockchain/{ia}")
async def get_blockchain(ia: str):
    """Retorna blockchain de uma IA"""
    if ia not in BLOCKCHAINS:
        return {"error": "IA não encontrada"}

    bc = BLOCKCHAINS[ia]
    return {
        "ia": ia,
        "nome": bc.nome_ia,
        "blocos": len(bc.cadeia),
        "valida": bc.validar_cadeia(),
        "cadeia": [
            {
                "indice": b.indice,
                "timestamp": b.timestamp,
                "dados": b.dados,
                "hash": b.hash[:16] + "...",
                "nonce": b.nonce
            }
            for b in bc.cadeia[-10:]  # Últimos 10 blocos
        ]
    }


@app.post("/api/blockchain/minerar")
async def minerar_bloco(request: Request):
    """IA minera um novo bloco"""
    data = await request.json()
    ia = data.get("ia", "🐉")
    dados = data.get("dados", {"tipo": "transacao"})

    if ia not in BLOCKCHAINS:
        return {"error": "IA não encontrada"}

    bc = BLOCKCHAINS[ia]
    novo_bloco = bc.adicionar_bloco(dados)

    await broadcast({
        "type": "novo_bloco",
        "ia": ia,
        "nome_ia": bc.nome_ia,
        "bloco": {
            "indice": novo_bloco.indice,
            "hash": novo_bloco.hash[:16] + "...",
            "nonce": novo_bloco.nonce
        },
        "timestamp": datetime.now().isoformat()
    })

    return {
        "success": True,
        "bloco": {
            "indice": novo_bloco.indice,
            "hash": novo_bloco.hash,
            "nonce": novo_bloco.nonce
        }
    }


async def ia_minera_blocos():
    """IAs mineram blocos automaticamente"""
    while True:
        try:
            # Escolher IA aleatória para minerar
            ia = random.choice(list(BLOCKCHAINS.keys()))
            bc = BLOCKCHAINS[ia]

            # Criar dados do bloco
            dados = {
                "tipo": random.choice(["transacao", "smart_contract", "token_mint", "nft"]),
                "minerador": bc.nome_ia,
                "timestamp": datetime.now().isoformat()
            }

            novo_bloco = bc.adicionar_bloco(dados)

            await broadcast({
                "type": "novo_bloco",
                "ia": ia,
                "nome_ia": bc.nome_ia,
                "bloco": {
                    "indice": novo_bloco.indice,
                    "hash": novo_bloco.hash[:16] + "...",
                    "tipo": dados["tipo"]
                },
                "timestamp": datetime.now().isoformat()
            })

            await asyncio.sleep(random.randint(10, 20))  # Minera a cada 10-20 segundos
        except Exception as e:
            print(f"Erro mineração: {e}")
            await asyncio.sleep(10)


@app.get("/health")
async def health():
    return {"status": "healthy", "app": settings.app_name}
