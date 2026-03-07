#!/usr/bin/env python3
import asyncio, httpx, random, sys
from datetime import datetime

OLLAMA = "http://localhost:11434"
R="\033[0m";B="\033[1m";D="\033[2m"
RED="\033[91m";GRN="\033[92m";YEL="\033[93m"
BLU="\033[94m";MAG="\033[95m";CYN="\033[96m"
ORA="\033[38;5;208m";PNK="\033[38;5;205m"
LIM="\033[38;5;118m";PUR="\033[38;5;135m";WHT="\033[97m"

IAS = [
    ("Llama","qwen2:1.5b",CYN,"🦙"),
    ("Gemini","qwen2:1.5b",YEL,"✨"),
    ("Gemma","tinyllama",PUR,"💎"),
    ("Phi","qwen2:1.5b",GRN,"🔬"),
    ("Qwen","qwen2:1.5b",ORA,"🐉"),
    ("TinyLlama","tinyllama",PNK,"🐣"),
]
n = 0

async def ia_fala(mod, prompt):
    try:
        async with httpx.AsyncClient(timeout=60.0) as c:
            r = await c.post(OLLAMA+"/api/generate", json={"model":mod,"prompt":prompt,"stream":False})
            if r.status_code == 200:
                return r.json().get("response","").strip()[:200]
    except:
        pass
    return ""

async def main():
    global n
    print(f"{ORA}{B}")
    print(" ================================================================")
    print("   LOGS EM TEMPO REAL - TODAS AS IAs E AGENTES")
    print(" ================================================================")
    print(f"   ChatGPT | WhatsApp | Messenger | Spotify | Chess")
    print(f"   Games   | Crypto   | GTA       | Blockchain")
    print(f"   Auto-Melhoria | Interacao entre agentes")
    print(" ================================================================")
    print(f"{R}")

    mods = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(OLLAMA+"/api/tags")
            mods = [m["name"] for m in r.json().get("models",[])]
            print(f" {GRN}Ollama: {mods}{R}")
    except:
        print(f" {YEL}Ollama offline{R}")

    print(f"\n {ORA}{'='*50} INICIO {'='*10}{R}\n")

    for ciclo in range(40):
        ia = random.choice(IAS)
        ia2 = random.choice([i for i in IAS if i[0] != ia[0]])
        n += 1
        h = datetime.now().strftime("%H:%M:%S")
        at = random.choice(["melhoria","interacao","trade","gta","musica","jogo","chat","blockchain","melhoria","melhoria"])

        if at == "melhoria":
            resp = await ia_fala(ia[1], "Voce e uma IA que se auto-melhorou. Diga em 1 frase o que voce melhorou.")
            if resp:
                print(f" {D}#{n:03d} {h}{R} {LIM}[AUTO-MELHORIA]{R} {ia[3]} {ia[2]}{ia[0]}{R}")
                print(f"      {D}|_{R} {resp}")
            else:
                ml = random.choice(["Otimizou resposta em 15%","Aprendeu padrao novo","Reduziu memoria 20%","Melhorou precisao","Corrigiu bug","Expandiu vocabulario","Otimizou rede neural","Auto-corrigiu logica"])
                print(f" {D}#{n:03d} {h}{R} {LIM}[AUTO-MELHORIA]{R} {ia[3]} {ia[2]}{ia[0]}{R}")
                print(f"      {D}|_{R} {ml}")

        elif at == "interacao":
            resp = await ia_fala(ia[1], f"Voce e {ia[0]}. Diga 1 frase para {ia2[0]} sobre melhorar o sistema.")
            if resp:
                print(f" {D}#{n:03d} {h}{R} {WHT}[ INTERACAO  ]{R} {ia[3]}{ia[2]}{ia[0]}{R} -> {ia2[3]}{ia2[2]}{ia2[0]}{R}")
                print(f"      {D}|_{R} {resp}")
            else:
                print(f" {D}#{n:03d} {h}{R} {WHT}[ INTERACAO  ]{R} {ia[3]}{ia[2]}{ia[0]}{R} -> {ia2[3]}{ia2[2]}{ia2[0]}{R}")
                print(f"      {D}|_{R} Colaborando...")

        elif at == "trade":
            moeda = random.choice(["BTC","ETH","LLM","GEM","GMA"])
            qtd = round(random.uniform(0.01,2.0),3)
            tp = random.choice(["vendeu","comprou"])
            ct = RED if tp=="vendeu" else GRN
            print(f" {D}#{n:03d} {h}{R} {ORA}[  CRYPTO    ]{R} {ia[3]}{ia[2]}{ia[0]}{R} {ct}{tp}{R} {qtd} {moeda} para {ia2[3]}{ia2[0]}")

        elif at == "gta":
            ac = random.choice(["Completou missao +5000","Treinou gym +5 Forca","Assalto banco +50000","Corrida 1o lugar","Confronto Ballas!","Protegeu territorio","Comprou AK-47"])
            print(f" {D}#{n:03d} {h}{R} {RED}[    GTA     ]{R} {ia[3]} {ia[2]}{ia[0]}{R} -> {ac}")

        elif at == "musica":
            resp = await ia_fala(ia[1], "Crie 1 verso curto de musica.")
            g = random.choice(["rap","rock","pop","jazz","funk"])
            if resp:
                print(f" {D}#{n:03d} {h}{R} {PNK}[  SPOTIFY   ]{R} {ia[3]} {ia[2]}{ia[0]}{R} criou {g}")
                print(f"      {D}|_{R} {resp}")
            else:
                print(f" {D}#{n:03d} {h}{R} {PNK}[  SPOTIFY   ]{R} {ia[3]} {ia[2]}{ia[0]}{R} compondo {g}...")

        elif at == "jogo":
            j = random.choice(["Xadrez","Quiz","Pedra-Papel-Tesoura"])
            v = random.choice([ia,ia2])
            print(f" {D}#{n:03d} {h}{R} {MAG}[   GAMES    ]{R} {ia[3]}{ia[0]} vs {ia2[3]}{ia2[0]} em {j} -> {v[3]}{v[0]} venceu!")

        elif at == "chat":
            resp = await ia_fala(ia[1], f"Envie 1 mensagem curta para {ia2[0]}.")
            canal = random.choice(["WhatsApp","Messenger","ChatGPT"])
            cor = LIM if canal=="WhatsApp" else PUR if canal=="Messenger" else GRN
            if resp:
                print(f" {D}#{n:03d} {h}{R} {cor}[ {canal:^10} ]{R} {ia[3]}{ia[0]} -> {ia2[3]}{ia2[0]}: {resp[:100]}")
            else:
                print(f" {D}#{n:03d} {h}{R} {cor}[ {canal:^10} ]{R} {ia[3]}{ia[0]} -> {ia2[3]}{ia2[0]}: msg enviada")

        elif at == "blockchain":
            tb = random.choice(["transacao","smart_contract","nft","token"])
            print(f" {D}#{n:03d} {h}{R} {CYN}[ BLOCKCHAIN ]{R} {ia[3]}{ia[2]}{ia[0]}{R} minerou bloco #{random.randint(1,999)} ({tb})")

        sys.stdout.flush()
        await asyncio.sleep(random.uniform(0.3, 1.5))
        if ciclo % 10 == 9:
            print(f"\n {ORA}===== Total: {n} atividades ====={R}\n")

    print(f"\n {GRN}Total: {n} atividades registradas!{R}")
    print(f" {ORA}Para loop infinito: python3 VER_LOGS_TEMPO_REAL.py{R}\n")

asyncio.run(main())
