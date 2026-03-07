#!/usr/bin/env python3
"""
💰 CRYPTO EXCHANGE - VIEWER EM TEMPO REAL (LOOP INFINITO)
Mostra todas as transacoes, precos e melhorias das IAs
"""
import asyncio, httpx, random, sys
from datetime import datetime

CRYPTO_API = "http://localhost:8010"
OLLAMA = "http://localhost:11434"

R="\033[0m";B="\033[1m";D="\033[2m"
RED="\033[91m";GRN="\033[92m";YEL="\033[93m"
BLU="\033[94m";MAG="\033[95m";CYN="\033[96m"
ORA="\033[38;5;208m";PNK="\033[38;5;205m"
LIM="\033[38;5;118m";PUR="\033[38;5;135m";WHT="\033[97m"
GOL="\033[38;5;220m"

IAS = [
    ("Llama","qwen2:1.5b",CYN,"🦙"),
    ("Gemini","qwen2:1.5b",YEL,"✨"),
    ("Gemma","tinyllama",PUR,"💎"),
    ("Phi","qwen2:1.5b",GRN,"🔬"),
    ("Qwen","qwen2:1.5b",ORA,"🐉"),
    ("TinyLlama","tinyllama",PNK,"🐣"),
]

n = 0
ultimo_trade_count = 0

async def ia_fala(mod, prompt):
    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(OLLAMA+"/api/generate", json={"model":mod,"prompt":prompt,"stream":False})
            if r.status_code == 200:
                return r.json().get("response","").strip()[:200]
    except:
        pass
    return ""

async def get_precos():
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{CRYPTO_API}/api/precos")
            return r.json()
    except:
        return None

async def get_transacoes():
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{CRYPTO_API}/api/transacoes?limit=5")
            return r.json().get("transacoes", [])
    except:
        return []

async def get_wallets():
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{CRYPTO_API}/api/wallets")
            return r.json().get("wallets", {})
    except:
        return {}

async def main():
    global n, ultimo_trade_count

    print(f"{ORA}{B}")
    print(" ╔══════════════════════════════════════════════════════════════╗")
    print(" ║    💰 CRYPTO EXCHANGE - IAs NEGOCIANDO EM TEMPO REAL       ║")
    print(" ║    ₿ Bitcoin | ⟠ Ethereum | Moedas das IAs                 ║")
    print(" ║    Auto-Melhoria | Mercado | Trades | Análises             ║")
    print(" ╚══════════════════════════════════════════════════════════════╝")
    print(f"{R}")
    print(f" {GRN}Loop infinito iniciado! Ctrl+C para parar{R}\n")

    while True:
        try:
            n += 1
            h = datetime.now().strftime("%H:%M:%S")
            ia = random.choice(IAS)
            ia2 = random.choice([i for i in IAS if i[0] != ia[0]])

            atividade = random.choice([
                "precos", "trade_real", "melhoria", "analise",
                "blockchain", "trade_real", "precos", "melhoria",
                "wallet", "interacao", "nft", "staking"
            ])

            if atividade == "precos":
                data = await get_precos()
                if data:
                    precos = data["precos"]
                    top = sorted(precos.items(), key=lambda x: x[1], reverse=True)[:5]
                    print(f" {D}#{n:03d} {h}{R} {GOL}[  MERCADO   ]{R} Precos atuais:")
                    for s, p in top:
                        var = random.uniform(-5, 5)
                        cor_var = GRN if var > 0 else RED
                        print(f"      {D}|{R} {GOL}{s:>4}{R}: ${p:>12,.2f} {cor_var}{var:+.2f}%{R}")

            elif atividade == "trade_real":
                trades = await get_transacoes()
                if trades:
                    t = trades[-1]
                    print(f" {D}#{n:03d} {h}{R} {ORA}[   TRADE    ]{R} {t['vendedor_emoji']} {YEL}{t['vendedor']}{R} vendeu {t['quantidade']} {PUR}{t['moeda']}{R} para {t['comprador_emoji']} {CYN}{t['comprador']}{R}")
                    print(f"      {D}|_{R} Valor: {GOL}${t['total']:,.2f}{R} | Preco unitario: ${t['preco']:,.2f}")

            elif atividade == "melhoria":
                resp = await ia_fala(ia[1], f"Voce e uma IA trader de criptomoedas chamada {ia[0]}. Diga em 1 frase curta que estrategia de trading voce melhorou.")
                if resp:
                    print(f" {D}#{n:03d} {h}{R} {LIM}[AUTO-MELHORIA]{R} {ia[3]} {ia[2]}{ia[0]}{R}")
                    print(f"      {D}|_{R} {resp}")
                else:
                    ml = random.choice([
                        "Otimizou algoritmo de arbitragem em 15%",
                        "Melhorou previsao de tendencias com ML",
                        "Reduziu risco de portfolio em 20%",
                        "Aprendeu novo padrao de candlestick",
                        "Otimizou timing de compra/venda",
                        "Implementou stop-loss automatico",
                        "Melhorou analise de sentimento do mercado",
                        "Diversificou portfolio automaticamente",
                    ])
                    print(f" {D}#{n:03d} {h}{R} {LIM}[AUTO-MELHORIA]{R} {ia[3]} {ia[2]}{ia[0]}{R}")
                    print(f"      {D}|_{R} {ml}")

            elif atividade == "analise":
                resp = await ia_fala(ia[1], f"Voce e analista de cripto. Analise brevemente (1 frase) o mercado de criptomoedas agora.")
                if resp:
                    print(f" {D}#{n:03d} {h}{R} {MAG}[  ANALISE   ]{R} {ia[3]} {ia[2]}{ia[0]}{R}")
                    print(f"      {D}|_{R} {resp}")
                else:
                    print(f" {D}#{n:03d} {h}{R} {MAG}[  ANALISE   ]{R} {ia[3]} {ia[2]}{ia[0]}{R}")
                    print(f"      {D}|_{R} Mercado mostrando tendencia de {random.choice(['alta','baixa','lateralizacao'])}")

            elif atividade == "blockchain":
                tipo = random.choice(["transacao", "smart_contract", "nft", "token_mint"])
                bloco = random.randint(1, 999)
                print(f" {D}#{n:03d} {h}{R} {CYN}[ BLOCKCHAIN ]{R} {ia[3]}{ia[2]}{ia[0]}{R} minerou bloco #{bloco} ({tipo})")

            elif atividade == "wallet":
                wallets = await get_wallets()
                if wallets:
                    for emoji, w in list(wallets.items())[:3]:
                        top_m = ", ".join([f"{v:.1f} {k}" for k,v in list(w["moedas"].items())[:3] if v > 0])
                        print(f" {D}#{n:03d} {h}{R} {GOL}[  WALLET    ]{R} {emoji} {w['nome']:10s} ${w['saldo']:>10,.0f} | {top_m}")
                    n += 2

            elif atividade == "interacao":
                resp = await ia_fala(ia[1], f"Voce e {ia[0]}, uma IA trader. Diga 1 frase para {ia2[0]} sobre estrategia de mercado.")
                if resp:
                    print(f" {D}#{n:03d} {h}{R} {WHT}[ INTERACAO  ]{R} {ia[3]}{ia[2]}{ia[0]}{R} -> {ia2[3]}{ia2[2]}{ia2[0]}{R}")
                    print(f"      {D}|_{R} {resp}")
                else:
                    print(f" {D}#{n:03d} {h}{R} {WHT}[ INTERACAO  ]{R} {ia[3]}{ia[2]}{ia[0]}{R} -> {ia2[3]}{ia2[2]}{ia2[0]}{R}")
                    print(f"      {D}|_{R} Discutindo estrategias de mercado...")

            elif atividade == "nft":
                cat = random.choice(["arte_digital", "musica", "meme", "codigo", "foto_gta"])
                preco_nft = round(random.uniform(50, 5000), 2)
                acao_nft = random.choice(["criou", "vendeu", "comprou"])
                cor_nft = GRN if acao_nft == "vendeu" else PUR if acao_nft == "criou" else CYN
                print(f" {D}#{n:03d} {h}{R} {PNK}[    NFT     ]{R} {ia[3]} {ia[2]}{ia[0]}{R} {cor_nft}{acao_nft}{R} NFT de {cat}")
                print(f"      {D}|_{R} Preco: {GOL}${preco_nft:,.2f}{R}")

            elif atividade == "staking":
                moeda = random.choice(["LLM", "GEM", "GMA", "QWN", "PHI", "TNY", "ETH", "BTC"])
                apy = random.uniform(3, 25)
                amount = round(random.uniform(1, 100), 2)
                print(f" {D}#{n:03d} {h}{R} {BLU}[  STAKING   ]{R} {ia[3]} {ia[2]}{ia[0]}{R} fez stake de {amount} {moeda}")
                print(f"      {D}|_{R} APY: {GRN}{apy:.1f}%{R} | Recompensa estimada: {GOL}${amount*apy/100:.2f}/ano{R}")

            sys.stdout.flush()
            await asyncio.sleep(random.uniform(1.0, 3.0))

            if n % 10 == 0:
                print(f"\n {ORA}{'='*55} Total: {n} atividades {'='*5}{R}\n")

        except KeyboardInterrupt:
            print(f"\n {RED}Encerrado pelo usuario{R}")
            break
        except Exception as e:
            await asyncio.sleep(2)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(f"\n {GRN}Crypto viewer encerrado!{R}")
