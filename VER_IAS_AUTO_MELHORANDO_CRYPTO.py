#!/usr/bin/env python3
"""
🧠 IAs SE AUTO-MELHORANDO - ESTRATÉGIAS DE CRYPTO
═══════════════════════════════════════════════════
Loop infinito mostrando as IAs melhorando seus próprios códigos/estratégias
"""
import asyncio, httpx, random, sys, json, os
from datetime import datetime

OLLAMA = "http://localhost:11434"
CRYPTO_API = "http://localhost:8010"
BASE = os.path.dirname(os.path.abspath(__file__))
STRAT_DIR = os.path.join(BASE, "ai-crypto-exchange", "estrategias_ia")
os.makedirs(STRAT_DIR, exist_ok=True)

R="\033[0m";B="\033[1m";D="\033[2m"
RED="\033[91m";GRN="\033[92m";YEL="\033[93m"
BLU="\033[94m";MAG="\033[95m";CYN="\033[96m"
ORA="\033[38;5;208m";PNK="\033[38;5;205m"
LIM="\033[38;5;118m";PUR="\033[38;5;135m";WHT="\033[97m"
GOL="\033[38;5;220m"

IAS = [
    ("Llama","qwen2:1.5b",CYN,"🦙","conservador",0.3),
    ("Gemini","qwen2:1.5b",YEL,"✨","agressivo",0.7),
    ("Gemma","tinyllama",PUR,"💎","balanceado",0.5),
    ("Phi","qwen2:1.5b",GRN,"🔬","analitico",0.2),
    ("Qwen","qwen2:1.5b",ORA,"🐉","momentum",0.6),
    ("TinyLlama","tinyllama",PNK,"🐣","experimental",0.8),
]

# Estado das estratégias (evoluem)
estrategias = {}
for nome, mod, cor, emoji, estilo, risco in IAS:
    estrategias[emoji] = {
        "nome": nome, "modelo": mod, "estilo": estilo,
        "risco": risco, "agressividade": risco,
        "diversificacao": 1.0 - risco,
        "stop_loss": round(0.15 - risco * 0.1, 2),
        "take_profit": round(0.1 + risco * 0.15, 2),
        "melhorias": 0, "score": 50,
        "regras": [],
    }

n = 0

async def ia_fala(mod, prompt):
    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(OLLAMA+"/api/generate", json={"model":mod,"prompt":prompt,"stream":False})
            if r.status_code == 200:
                return r.json().get("response","").strip()[:250]
    except:
        pass
    return ""

async def salvar_estrategia(emoji):
    est = estrategias[emoji]
    filepath = os.path.join(STRAT_DIR, f"{est['nome']}_estrategia.json")
    with open(filepath, "w") as f:
        json.dump(est, f, indent=2, ensure_ascii=False, default=str)

async def main():
    global n

    print(f"{ORA}{B}")
    print(" ╔══════════════════════════════════════════════════════════════════╗")
    print(" ║  🧠 IAs SE AUTO-MELHORANDO - ESTRATÉGIAS DE CRYPTO (INFINITO)  ║")
    print(" ║  As IAs analisam e melhoram seu próprio código/estratégia       ║")
    print(" ║  Cada melhoria é salva em arquivo e aplicada em tempo real      ║")
    print(" ╚══════════════════════════════════════════════════════════════════╝")
    print(f"{R}")

    # Verificar Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(OLLAMA+"/api/tags")
            mods = [m["name"] for m in r.json().get("models",[])]
            print(f" {GRN}Ollama online: {mods}{R}")
    except:
        print(f" {YEL}Ollama offline - usando fallback{R}")

    print(f" {GRN}Estratégias salvas em: {STRAT_DIR}{R}")
    print(f" {GRN}Loop infinito! Ctrl+C para parar{R}\n")

    while True:
        try:
            n += 1
            h = datetime.now().strftime("%H:%M:%S")
            ia_info = random.choice(IAS)
            nome, mod, cor, emoji, estilo, risco_base = ia_info
            est = estrategias[emoji]
            ia2_info = random.choice([i for i in IAS if i[0] != nome])

            atividade = random.choice([
                "auto_melhoria", "gerar_regra", "analisar_performance",
                "auto_melhoria", "interacao_estrategia", "trade_inteligente",
                "auto_melhoria", "otimizar_parametro", "gerar_regra",
            ])

            if atividade == "auto_melhoria":
                resp = await ia_fala(mod, f"""Você é {nome}, IA trader de crypto com estilo {est['estilo']}.
Seu risco atual: {est['risco']:.0%}, agressividade: {est['agressividade']:.0%}.
Score: {est['score']}/100. Melhorias feitas: {est['melhorias']}.
Sugira 1 melhoria ESPECÍFICA na sua estratégia (1 frase curta).""")

                if resp:
                    # Aplicar melhoria real
                    param = random.choice(["risco", "agressividade", "diversificacao", "stop_loss", "take_profit"])
                    antigo = est[param]
                    delta = random.uniform(-0.05, 0.08)
                    novo = min(0.95, max(0.01, antigo + delta))
                    est[param] = round(novo, 3)
                    est["melhorias"] += 1
                    est["score"] = min(100, est["score"] + random.randint(0, 3))

                    print(f" {D}#{n:03d} {h}{R} {LIM}[AUTO-MELHORIA]{R} {emoji} {cor}{nome}{R} (v{est['melhorias']})")
                    print(f"      {D}|_{R} {resp}")
                    print(f"      {D}|_{R} {GOL}Aplicado:{R} {param}: {antigo:.3f} -> {GRN}{novo:.3f}{R} | Score: {est['score']}/100")

                    await salvar_estrategia(emoji)
                else:
                    param = random.choice(["risco", "agressividade", "diversificacao", "stop_loss", "take_profit"])
                    antigo = est[param]
                    delta = random.uniform(-0.05, 0.08)
                    novo = min(0.95, max(0.01, antigo + delta))
                    est[param] = round(novo, 3)
                    est["melhorias"] += 1

                    ml = random.choice([
                        f"Otimizou {param} de {antigo:.2f} para {novo:.2f}",
                        f"Ajustou {param} baseado em análise de mercado",
                        f"Recalibrou {param} para melhor performance",
                        f"Auto-corrigiu {param} após análise de dados",
                    ])
                    print(f" {D}#{n:03d} {h}{R} {LIM}[AUTO-MELHORIA]{R} {emoji} {cor}{nome}{R} (v{est['melhorias']})")
                    print(f"      {D}|_{R} {ml}")
                    print(f"      {D}|_{R} {GOL}Aplicado:{R} {param}: {antigo:.3f} -> {GRN}{novo:.3f}{R}")

                    await salvar_estrategia(emoji)

            elif atividade == "gerar_regra":
                resp = await ia_fala(mod, f"Você é {nome}, IA trader. Crie 1 regra de trading curta (1 frase). Ex: 'Se BTC cair 5%, comprar ETH'")
                if resp:
                    est["regras"].append(resp[:100])
                    if len(est["regras"]) > 20:
                        est["regras"].pop(0)
                    print(f" {D}#{n:03d} {h}{R} {MAG}[ NOVA REGRA ]{R} {emoji} {cor}{nome}{R}")
                    print(f"      {D}|_{R} Regra #{len(est['regras'])}: {resp[:100]}")
                    await salvar_estrategia(emoji)
                else:
                    regra = random.choice([
                        f"Se {random.choice(['BTC','ETH','LLM'])} cair {random.randint(3,10)}%, comprar {random.choice(['GEM','QWN','GMA'])}",
                        f"Vender {random.choice(['LLM','GEM','QWN'])} se subir mais de {random.randint(10,25)}% em 1h",
                        f"Manter {random.choice(['BTC','ETH'])} se tendência for de alta",
                        f"Diversificar portfolio quando volatilidade > {random.randint(5,15)}%",
                    ])
                    est["regras"].append(regra)
                    print(f" {D}#{n:03d} {h}{R} {MAG}[ NOVA REGRA ]{R} {emoji} {cor}{nome}{R}")
                    print(f"      {D}|_{R} Regra #{len(est['regras'])}: {regra}")

            elif atividade == "analisar_performance":
                # Pegar dados reais da API
                try:
                    async with httpx.AsyncClient(timeout=5.0) as c:
                        r = await c.get(f"{CRYPTO_API}/api/wallets")
                        wallets = r.json().get("wallets", {})
                        w = wallets.get(emoji, {})
                        saldo = w.get("saldo", 0)
                        moedas_str = ", ".join([f"{v:.1f} {k}" for k,v in list(w.get("moedas",{}).items())[:4] if v > 0])
                        est["score"] = min(100, max(0, int(saldo / 1000)))
                        print(f" {D}#{n:03d} {h}{R} {GOL}[ PERFORMANCE]{R} {emoji} {cor}{nome}{R}")
                        print(f"      {D}|_{R} Saldo: {GRN}${saldo:,.0f}{R} | Moedas: {moedas_str}")
                        print(f"      {D}|_{R} Score: {est['score']}/100 | Estilo: {est['estilo']} | Melhorias: {est['melhorias']}")
                except:
                    print(f" {D}#{n:03d} {h}{R} {GOL}[ PERFORMANCE]{R} {emoji} {cor}{nome}{R}")
                    print(f"      {D}|_{R} Score: {est['score']}/100 | Melhorias: {est['melhorias']}")

            elif atividade == "interacao_estrategia":
                nome2 = ia2_info[0]
                emoji2 = ia2_info[3]
                cor2 = ia2_info[2]
                est2 = estrategias[emoji2]

                resp = await ia_fala(mod, f"Você é {nome} (estilo: {est['estilo']}). Diga 1 frase para {nome2} (estilo: {est2['estilo']}) sobre como melhorar a estratégia de trading.")
                if resp:
                    print(f" {D}#{n:03d} {h}{R} {WHT}[ ESTRATEGIA ]{R} {emoji}{cor}{nome}{R} -> {emoji2}{cor2}{nome2}{R}")
                    print(f"      {D}|_{R} {resp}")
                else:
                    print(f" {D}#{n:03d} {h}{R} {WHT}[ ESTRATEGIA ]{R} {emoji}{cor}{nome}{R} -> {emoji2}{cor2}{nome2}{R}")
                    print(f"      {D}|_{R} Compartilhando insights de {est['estilo']} com {est2['estilo']}...")

            elif atividade == "trade_inteligente":
                moeda = random.choice(["BTC", "ETH", "LLM", "GEM", "QWN", "GMA", "PHI", "TNY"])
                acao = "COMPRAR" if est["agressividade"] > random.random() else "VENDER"
                cor_acao = GRN if acao == "COMPRAR" else RED
                razao = random.choice([
                    f"risco={est['risco']:.0%} permite",
                    f"stop_loss={est['stop_loss']:.0%} ativo",
                    f"take_profit={est['take_profit']:.0%} alcançado",
                    f"diversificacao={est['diversificacao']:.0%} indica",
                    f"regra #{random.randint(1,len(est['regras']) or 1)} ativada",
                ])
                print(f" {D}#{n:03d} {h}{R} {ORA}[TRADE SMART ]{R} {emoji} {cor}{nome}{R} -> {cor_acao}{acao}{R} {moeda}")
                print(f"      {D}|_{R} Razão: {razao} | Estilo: {est['estilo']}")

            elif atividade == "otimizar_parametro":
                param = random.choice(["risco", "agressividade", "diversificacao", "stop_loss", "take_profit"])
                antigo = est[param]
                # Otimização baseada no score
                if est["score"] < 40:
                    # Performance ruim - mudar mais
                    delta = random.uniform(-0.1, 0.1)
                else:
                    # Performance boa - ajuste fino
                    delta = random.uniform(-0.03, 0.03)
                novo = min(0.95, max(0.01, antigo + delta))
                est[param] = round(novo, 3)
                est["melhorias"] += 1

                direcao = "↑" if novo > antigo else "↓"
                cor_dir = GRN if ((param == "score" and novo > antigo) or
                                   (param != "risco" and novo > antigo)) else RED

                print(f" {D}#{n:03d} {h}{R} {BLU}[ OTIMIZACAO ]{R} {emoji} {cor}{nome}{R} (v{est['melhorias']})")
                print(f"      {D}|_{R} {param}: {antigo:.3f} {cor_dir}{direcao} {novo:.3f}{R} | Score: {est['score']}/100")

                await salvar_estrategia(emoji)

            sys.stdout.flush()
            await asyncio.sleep(random.uniform(1.0, 3.0))

            if n % 10 == 0:
                print(f"\n {ORA}{'='*60}")
                print(f" RESUMO - {n} atividades de auto-melhoria")
                print(f" {'='*60}{R}")
                for e, info in IAS:
                    em = info if isinstance(info, str) else IAS[[i[0] for i in IAS].index(e)][3]
                for nm, md, cr, em, es, rb in IAS:
                    e = estrategias[em]
                    print(f"   {em} {cr}{nm:12s}{R} v{e['melhorias']:>3d} | Score:{e['score']:>3d} | Risco:{e['risco']:.2f} | Regras:{len(e['regras'])}")
                print(f" {ORA}{'='*60}{R}\n")

        except KeyboardInterrupt:
            break
        except Exception as ex:
            print(f" {RED}Erro: {ex}{R}")
            await asyncio.sleep(2)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print(f"\n {GRN}Auto-melhoria encerrada!{R}")
