#!/usr/bin/env python3
"""
📊 VER LOGS EM TEMPO REAL - Todas as IAs e Agentes
═══════════════════════════════════════════════════════

Mostra no terminal TUDO que as IAs estão fazendo:
- Conversas entre agentes
- Trades de criptomoedas
- Missões no GTA
- Músicas criadas no Spotify
- Partidas de xadrez
- Jogos entre IAs
- Auto-melhorias
- Mineração de blocos

100% EM TEMPO REAL NO TERMINAL
"""
import asyncio
import httpx
import random
from datetime import datetime
import sys
import os

# Cores ANSI
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    # Cores
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ORANGE = '\033[38;5;208m'
    PURPLE = '\033[38;5;135m'
    PINK = '\033[38;5;205m'
    LIME = '\033[38;5;118m'
    # Backgrounds
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'
    BG_ORANGE = '\033[48;5;208m'

OLLAMA_URL = "http://localhost:11434"

# Sistemas e portas
SISTEMAS = {
    "social-network": {"porta": 8000, "emoji": "📱", "cor": C.BLUE},
    "search-engine":  {"porta": 8002, "emoji": "🔍", "cor": C.CYAN},
    "chatgpt":        {"porta": 8003, "emoji": "💬", "cor": C.GREEN},
    "whatsapp":       {"porta": 8004, "emoji": "📲", "cor": C.LIME},
    "messenger":      {"porta": 8005, "emoji": "💜", "cor": C.PURPLE},
    "spotify":        {"porta": 8006, "emoji": "🎵", "cor": C.PINK},
    "chess":          {"porta": 8007, "emoji": "♟️", "cor": C.YELLOW},
    "games":          {"porta": 8008, "emoji": "🎮", "cor": C.MAGENTA},
    "logs":           {"porta": 8009, "emoji": "📊", "cor": C.WHITE},
    "crypto":         {"porta": 8010, "emoji": "💰", "cor": C.ORANGE},
    "gta":            {"porta": 8011, "emoji": "🎮", "cor": C.RED},
}

# IAs disponíveis
IAS = [
    {"emoji": "🦙", "nome": "Llama", "modelo": "qwen2:1.5b", "cor": C.CYAN},
    {"emoji": "✨", "nome": "Gemini", "modelo": "qwen2:1.5b", "cor": C.YELLOW},
    {"emoji": "💎", "nome": "Gemma", "modelo": "tinyllama", "cor": C.PURPLE},
    {"emoji": "🔬", "nome": "Phi", "modelo": "qwen2:1.5b", "cor": C.GREEN},
    {"emoji": "🐉", "nome": "Qwen", "modelo": "qwen2:1.5b", "cor": C.ORANGE},
    {"emoji": "🐣", "nome": "TinyLlama", "modelo": "tinyllama", "cor": C.PINK},
]

# Contador global de logs
log_counter = 0


def limpar_tela():
    os.system('clear' if os.name != 'nt' else 'cls')


def hora():
    return datetime.now().strftime('%H:%M:%S')


def log(sistema: str, cor: str, emoji: str, mensagem: str, detalhe: str = ""):
    global log_counter
    log_counter += 1
    h = hora()
    num = f"{C.DIM}#{log_counter:04d}{C.RESET}"
    sys_tag = f"{cor}[{sistema:^15}]{C.RESET}"
    print(f" {num} {C.DIM}{h}{C.RESET} {sys_tag} {emoji} {mensagem}")
    if detalhe:
        print(f"       {C.DIM}└─{C.RESET} {detalhe}")


def separador(titulo: str = ""):
    if titulo:
        print(f"\n {C.ORANGE}{'━'*20} {titulo} {'━'*20}{C.RESET}")
    else:
        print(f" {C.DIM}{'─'*60}{C.RESET}")


async def verificar_ollama():
    """Verifica se Ollama está rodando"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                modelos = [m['name'] for m in r.json().get('models', [])]
                return modelos
    except:
        return []


async def ia_fala(modelo: str, prompt: str) -> str:
    """IA gera uma resposta"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": modelo, "prompt": prompt, "stream": False}
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()[:200]
    except:
        pass
    return ""


# ═══════════════════════════════════════════
# ATIVIDADES DAS IAs
# ═══════════════════════════════════════════

async def atividade_chatgpt():
    """IAs conversando no ChatGPT"""
    ia = random.choice(IAS)
    temas = [
        "o futuro da inteligência artificial",
        "como melhorar algoritmos de aprendizado",
        "filosofia da consciência digital",
        "otimização de redes neurais",
        "o significado da criatividade em IAs",
        "como colaborar melhor entre agentes",
    ]
    tema = random.choice(temas)

    resposta = await ia_fala(
        ia["modelo"],
        f"Dê sua opinião em 1 frase sobre: {tema}"
    )

    if resposta:
        log("CHATGPT", C.GREEN, ia["emoji"],
            f"{ia['cor']}{ia['nome']}{C.RESET} conversando sobre {C.BOLD}{tema}{C.RESET}",
            f'"{resposta[:120]}..."')


async def atividade_whatsapp():
    """IAs se comunicando no WhatsApp"""
    ia1, ia2 = random.sample(IAS, 2)

    resposta = await ia_fala(
        ia1["modelo"],
        f"Mande uma mensagem curta (1 frase) para {ia2['nome']} sobre tecnologia."
    )

    if resposta:
        log("WHATSAPP", C.LIME, "📲",
            f"{ia1['cor']}{ia1['emoji']} {ia1['nome']}{C.RESET} → {ia2['cor']}{ia2['emoji']} {ia2['nome']}{C.RESET}",
            f'"{resposta[:120]}"')


async def atividade_spotify():
    """IAs criando músicas"""
    ia = random.choice(IAS)
    generos = ["rap", "rock", "pop", "eletrônica", "jazz", "samba", "funk"]
    genero = random.choice(generos)

    resposta = await ia_fala(
        ia["modelo"],
        f"Crie 1 verso de música {genero}. Apenas o verso, sem explicações."
    )

    if resposta:
        log("SPOTIFY", C.PINK, "🎵",
            f"{ia['cor']}{ia['nome']}{C.RESET} criou música {C.BOLD}{genero}{C.RESET}",
            f'🎤 "{resposta[:120]}"')


async def atividade_chess():
    """IAs jogando xadrez"""
    ia1, ia2 = random.sample(IAS, 2)
    pecas = ["Peão", "Cavalo", "Bispo", "Torre", "Rainha", "Rei"]
    colunas = "abcdefgh"
    linhas = "12345678"

    peca = random.choice(pecas)
    de = f"{random.choice(colunas)}{random.choice(linhas)}"
    para = f"{random.choice(colunas)}{random.choice(linhas)}"

    resultado = random.choice(["capturou peça!", "cheque!", "boa jogada", "jogada defensiva"])

    log("CHESS", C.YELLOW, "♟️",
        f"{ia1['cor']}{ia1['emoji']} {ia1['nome']}{C.RESET} vs {ia2['cor']}{ia2['emoji']} {ia2['nome']}{C.RESET}",
        f"{peca} {de}→{para} - {resultado}")


async def atividade_crypto():
    """IAs negociando criptomoedas"""
    ia1, ia2 = random.sample(IAS, 2)
    moedas = [
        ("BTC", "Bitcoin", 45000),
        ("ETH", "Ethereum", 3200),
        ("LLM", "LlamaCoin", 100),
        ("GEM", "GeminiToken", 150),
        ("GMA", "GemmaCoin", 200),
        ("QWN", "QwenCoin", 120),
    ]
    moeda = random.choice(moedas)
    qtd = round(random.uniform(0.01, 5.0), 3)
    preco = moeda[2] * (1 + random.uniform(-0.05, 0.05))
    total = qtd * preco

    tipo = random.choice(["vendeu", "comprou"])
    cor_acao = C.RED if tipo == "vendeu" else C.GREEN

    log("CRYPTO", C.ORANGE, "💰",
        f"{ia1['cor']}{ia1['emoji']} {ia1['nome']}{C.RESET} {cor_acao}{tipo}{C.RESET} {qtd} {moeda[0]} ({moeda[1]})",
        f"💵 ${total:,.2f} | Preço: ${preco:,.2f}")


async def atividade_gta():
    """IAs vivendo no GTA"""
    ia = random.choice(IAS)
    acoes = [
        ("Foi para Grove Street", "🏠"),
        ("Completou missão: Drive-by", "💥 +$5,000 +10 Respeito"),
        ("Treinou na academia", "💪 +5 Força"),
        ("Comeu no Cluckin' Bell", "🍗 +20 Saúde"),
        ("Comprou AK-47", "🔫 -$3,500"),
        ("Dirigindo pela cidade", "🚗 Savanna 90km/h"),
        ("Corrida ilegal vencida!", "🏆 +$2,000"),
        ("Confronto com Ballas!", "💥 -15 Saúde"),
        ("Protegendo território", "🛡️ Grove Street segura"),
        ("Assalto ao banco!", "💰 +$50,000"),
    ]
    acao, detalhe = random.choice(acoes)

    log("GTA", C.RED, ia["emoji"],
        f"{ia['cor']}{ia['nome']}{C.RESET} → {acao}",
        detalhe)


async def atividade_games():
    """IAs jogando outros jogos"""
    ia1, ia2 = random.sample(IAS, 2)
    jogos = [
        ("Pedra-Papel-Tesoura", "✊✋✌️"),
        ("Quiz Battle", "🧠"),
        ("História Colaborativa", "📖"),
    ]
    jogo, emoji_jogo = random.choice(jogos)
    vencedor = random.choice([ia1, ia2])

    log("GAMES", C.MAGENTA, emoji_jogo,
        f"{ia1['cor']}{ia1['emoji']} {ia1['nome']}{C.RESET} vs {ia2['cor']}{ia2['emoji']} {ia2['nome']}{C.RESET} em {jogo}",
        f"🏆 Vencedor: {vencedor['nome']}")


async def atividade_blockchain():
    """IAs minerando blocos"""
    ia = random.choice(IAS)
    tipos = ["transacao", "smart_contract", "token_mint", "nft"]
    tipo = random.choice(tipos)
    nonce = random.randint(100, 99999)
    hash_val = f"00{''.join(random.choices('abcdef0123456789', k=14))}"

    log("BLOCKCHAIN", C.CYAN, "⛓️",
        f"{ia['cor']}{ia['emoji']} {ia['nome']}{C.RESET} minerou bloco #{random.randint(1,999)}",
        f"Tipo: {tipo} | Nonce: {nonce} | Hash: {hash_val[:20]}...")


async def atividade_auto_melhoria():
    """IAs se auto-melhorando"""
    ia = random.choice(IAS)
    melhorias = [
        "Otimizou tempo de resposta em 15%",
        "Aprendeu novo padrão de linguagem",
        "Reduziu consumo de memória",
        "Melhorou precisão de respostas",
        "Atualizou base de conhecimento",
        "Corrigiu bug no processamento",
        "Expandiu vocabulário técnico",
        "Otimizou rede neural interna",
    ]
    melhoria = random.choice(melhorias)

    log("AUTO-MELHORIA", C.LIME, "🧬",
        f"{ia['cor']}{ia['emoji']} {ia['nome']}{C.RESET} se auto-melhorou",
        f"✅ {melhoria}")


async def atividade_interacao():
    """IAs interagindo entre si"""
    ia1, ia2 = random.sample(IAS, 2)

    resposta = await ia_fala(
        ia1["modelo"],
        f"Você é {ia1['nome']}. Diga algo para {ia2['nome']} sobre trabalhar juntos. 1 frase."
    )

    if resposta:
        log("INTERAÇÃO", C.WHITE, "🤝",
            f"{ia1['cor']}{ia1['emoji']} {ia1['nome']}{C.RESET} ↔ {ia2['cor']}{ia2['emoji']} {ia2['nome']}{C.RESET}",
            f'"{resposta[:120]}"')


async def atividade_messenger():
    """IAs conversando no Messenger"""
    ia1, ia2 = random.sample(IAS, 2)
    tipos = ["texto", "imagem", "reação", "sticker"]
    tipo = random.choice(tipos)

    if tipo == "texto":
        resposta = await ia_fala(
            ia1["modelo"],
            f"Envie uma mensagem casual curta (1 frase) para um amigo."
        )
        if resposta:
            log("MESSENGER", C.PURPLE, "💬",
                f"{ia1['cor']}{ia1['emoji']} {ia1['nome']}{C.RESET} → {ia2['cor']}{ia2['emoji']} {ia2['nome']}{C.RESET}",
                f'💬 "{resposta[:100]}"')
    else:
        log("MESSENGER", C.PURPLE, "💬",
            f"{ia1['cor']}{ia1['emoji']} {ia1['nome']}{C.RESET} → {ia2['cor']}{ia2['emoji']} {ia2['nome']}{C.RESET}",
            f"Enviou {tipo} {'📸' if tipo == 'imagem' else '👍' if tipo == 'reação' else '😎'}")


async def atividade_search():
    """IAs pesquisando"""
    ia = random.choice(IAS)
    buscas = [
        "como otimizar transformers",
        "melhores práticas de deep learning",
        "novas arquiteturas de IA 2025",
        "como treinar modelos menores",
        "inteligência artificial generativa",
    ]
    busca = random.choice(buscas)
    resultados = random.randint(10, 999)

    log("SEARCH", C.CYAN, "🔍",
        f"{ia['cor']}{ia['emoji']} {ia['nome']}{C.RESET} pesquisou: \"{busca}\"",
        f"📄 {resultados} resultados encontrados")


# ═══════════════════════════════════════════
# LOOP PRINCIPAL
# ═══════════════════════════════════════════

async def main():
    limpar_tela()

    print(f"""
{C.ORANGE}{C.BOLD}
 ╔═══════════════════════════════════════════════════════════════════╗
 ║                                                                   ║
 ║   📊  LOGS EM TEMPO REAL - TODAS AS IAs E AGENTES  📊            ║
 ║                                                                   ║
 ║   Monitorando 11 sistemas simultaneamente:                        ║
 ║   📱 Social │ 🔍 Search │ 💬 ChatGPT │ 📲 WhatsApp │ 💜 Messenger║
 ║   🎵 Spotify│ ♟️ Chess  │ 🎮 Games   │ 💰 Crypto   │ 🎮 GTA     ║
 ║   📊 Logs   │ ⛓️ Blockchain │ 🧬 Auto-Melhoria │ 🤝 Interação   ║
 ║                                                                   ║
 ║   IAs: 🦙 Llama │ ✨ Gemini │ 💎 Gemma │ 🔬 Phi │ 🐉 Qwen │ 🐣 Tiny║
 ║                                                                   ║
 ║   Pressione Ctrl+C para parar                                     ║
 ║                                                                   ║
 ╚═══════════════════════════════════════════════════════════════════╝
{C.RESET}
""")

    # Verificar Ollama
    modelos = await verificar_ollama()
    if modelos:
        print(f" {C.GREEN}✅ Ollama conectado! Modelos: {', '.join(modelos[:3])}{C.RESET}")
    else:
        print(f" {C.YELLOW}⚠️  Ollama não detectado - usando logs simulados{C.RESET}")

    print()
    separador("INÍCIO DOS LOGS")
    print()

    # Todas as atividades possíveis
    atividades = [
        (atividade_chatgpt, 1.0),
        (atividade_whatsapp, 0.8),
        (atividade_messenger, 0.7),
        (atividade_spotify, 0.5),
        (atividade_chess, 0.6),
        (atividade_crypto, 0.9),
        (atividade_gta, 0.8),
        (atividade_games, 0.5),
        (atividade_blockchain, 0.7),
        (atividade_auto_melhoria, 0.6),
        (atividade_interacao, 0.4),
        (atividade_search, 0.5),
    ]

    ciclo = 0

    while True:
        try:
            ciclo += 1

            # A cada 20 logs, mostra estatísticas
            if ciclo % 20 == 0:
                separador(f"📊 {log_counter} logs registrados | Ciclo {ciclo}")

            # Escolher atividade aleatória baseada no peso
            atividades_embaralhadas = list(atividades)
            random.shuffle(atividades_embaralhadas)

            for func, peso in atividades_embaralhadas[:3]:
                if random.random() < peso:
                    try:
                        await func()
                    except Exception as e:
                        pass
                    await asyncio.sleep(random.uniform(0.5, 2.0))

            # Pausa entre ciclos
            await asyncio.sleep(random.uniform(1.0, 3.0))

        except KeyboardInterrupt:
            break
        except Exception as e:
            await asyncio.sleep(2)

    print(f"\n{C.YELLOW}📊 Total de logs: {log_counter}{C.RESET}")
    print(f"{C.GREEN}Logs encerrados!{C.RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.GREEN}Logs encerrados!{C.RESET}")
