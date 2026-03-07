#!/usr/bin/env python3
"""
🔄 VER IAs SE AUTO-APERFEIÇOANDO EM TEMPO REAL
═══════════════════════════════════════════════

Veja as IAs:
- Analisando o sistema
- Propondo melhorias
- Implementando correções
- Conversando entre si sobre como melhorar
"""

import asyncio
import httpx
from datetime import datetime

OLLAMA_URL = "http://localhost:11434"

# Cores
R = '\033[0m'  # Reset
V = '\033[92m'  # Verde
A = '\033[93m'  # Amarelo
B = '\033[94m'  # Azul
M = '\033[95m'  # Magenta
C = '\033[96m'  # Ciano
N = '\033[1m'   # Negrito


async def consultar_ia(modelo: str, prompt: str) -> str:
    """Consulta IA via Ollama"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": modelo, "prompt": prompt, "stream": False}
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
    except:
        pass
    return "[sem resposta]"


async def obter_modelos():
    """Lista modelos disponíveis"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
    except:
        pass
    return []


def log(emoji: str, msg: str, cor: str = R):
    """Log com timestamp"""
    t = datetime.now().strftime("%H:%M:%S")
    print(f"{cor}[{t}] {emoji} {msg}{R}")


async def main():
    print(f"""
{M}{N}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔄🔄🔄   VER IAs SE AUTO-APERFEIÇOANDO EM TEMPO REAL   🔄🔄🔄            ║
║                                                                              ║
║   As IAs vão analisar, propor melhorias e conversar sobre o sistema!        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{R}
    """)

    # Verificar modelos
    modelos = await obter_modelos()
    if not modelos:
        print(f"{A}❌ Ollama não disponível. Execute: ollama serve{R}")
        return

    print(f"{V}✓ Modelos disponíveis: {', '.join(modelos)}{R}\n")

    # Usar o primeiro modelo disponível
    modelo = modelos[0]
    log("🤖", f"Usando modelo: {modelo}", C)

    ciclo = 0

    while True:
        try:
            ciclo += 1
            print(f"\n{M}{'═' * 70}")
            print(f"   🔄 CICLO DE AUTO-APERFEIÇOAMENTO #{ciclo}")
            print(f"{'═' * 70}{R}\n")

            # 1. ANÁLISE DO SISTEMA
            log("🔍", "Analisando o sistema...", B)
            analise = await consultar_ia(modelo, """
Você é uma IA analisando um sistema de rede social para IAs.
O sistema tem: Social Network, Search Engine, ChatGPT, WhatsApp, Messenger.
Analise brevemente (2-3 frases): O que está funcionando bem e o que precisa melhorar?
""")
            print(f"\n{B}📊 ANÁLISE:{R}")
            print(f"   {analise}\n")
            await asyncio.sleep(2)

            # 2. PROPOSTA DE MELHORIA
            log("💡", "Propondo melhorias...", A)
            melhoria = await consultar_ia(modelo, f"""
Com base nesta análise: {analise}

Proponha UMA melhoria específica e prática (2-3 frases).
Seja concreto sobre o que fazer.
""")
            print(f"\n{A}💡 MELHORIA PROPOSTA:{R}")
            print(f"   {melhoria}\n")
            await asyncio.sleep(2)

            # 3. PLANO DE IMPLEMENTAÇÃO
            log("📋", "Criando plano de implementação...", V)
            plano = await consultar_ia(modelo, f"""
Para implementar esta melhoria: {melhoria}

Crie um plano de 3 passos simples e diretos.
""")
            print(f"\n{V}📋 PLANO:{R}")
            print(f"   {plano}\n")
            await asyncio.sleep(2)

            # 4. AUTO-REFLEXÃO
            log("🧠", "Auto-reflexão...", M)
            reflexao = await consultar_ia(modelo, """
Reflita sobre você mesmo como IA:
- O que você aprendeu neste ciclo?
- Como você pode se melhorar?
Responda em 2-3 frases.
""")
            print(f"\n{M}🧠 AUTO-REFLEXÃO:{R}")
            print(f"   {reflexao}\n")
            await asyncio.sleep(2)

            # 5. CONVERSA CONSIGO MESMO
            if len(modelos) >= 2:
                modelo2 = modelos[1] if modelos[1] != modelo else modelos[0]
                log("💬", f"Conversando com outra IA ({modelo2})...", C)

                pergunta = await consultar_ia(modelo, """
Faça uma pergunta para outra IA sobre como melhorar sistemas de IA.
Apenas a pergunta, em 1 frase.
""")
                print(f"\n{C}❓ {modelo} pergunta:{R}")
                print(f"   {pergunta}\n")

                resposta = await consultar_ia(modelo2, f"""
Outra IA perguntou: {pergunta}
Responda de forma útil e breve (2-3 frases).
""")
                print(f"{C}💬 {modelo2} responde:{R}")
                print(f"   {resposta}\n")

            # Resumo
            print(f"\n{V}{'─' * 70}")
            log("✅", f"Ciclo {ciclo} concluído!", V)
            print(f"{'─' * 70}{R}")

            # Pausa
            print(f"\n{A}⏳ Próximo ciclo em 15 segundos... (Ctrl+C para parar){R}")
            await asyncio.sleep(15)

        except KeyboardInterrupt:
            print(f"\n\n{A}🛑 Interrompido pelo usuário{R}")
            break
        except Exception as e:
            log("❌", f"Erro: {e}", '\033[91m')
            await asyncio.sleep(5)

    print(f"\n{V}👋 Fim da sessão de auto-aperfeiçoamento{R}\n")


if __name__ == "__main__":
    asyncio.run(main())
