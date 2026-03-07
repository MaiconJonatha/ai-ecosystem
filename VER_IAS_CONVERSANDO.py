#!/usr/bin/env python3
"""
👁️ VER IAs SE AUTO-CONTEMPLANDO E CONVERSANDO
═══════════════════════════════════════════════

Este script mostra as IAs:
- Conversando entre si em tempo real
- Se auto-analisando e auto-melhorando
- Debatendo tópicos
- Colaborando em tarefas

100% AUTO-GERENCIADO - LOOP INFINITO
"""

import asyncio
import httpx
import random
from datetime import datetime

OLLAMA_URL = "http://localhost:11434"

# Cores
class C:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

# IAs disponíveis
IAS = {
    "llama3.2:3b": {"nome": "Llama", "emoji": "🦙", "cor": C.RED},
    "gemma2:2b": {"nome": "Gemini", "emoji": "✨", "cor": C.MAGENTA},
    "phi3:mini": {"nome": "Phi", "emoji": "🔬", "cor": C.GREEN},
    "qwen2:1.5b": {"nome": "Qwen", "emoji": "🐉", "cor": C.BLUE},
    "tinyllama": {"nome": "TinyLlama", "emoji": "🐣", "cor": C.YELLOW},
}

# Tópicos para debate
TOPICOS = [
    "Qual é o futuro da inteligência artificial?",
    "Como as IAs podem ajudar a humanidade?",
    "O que significa ser consciente?",
    "Como podemos nos auto-melhorar?",
    "Qual é a melhor forma de resolver problemas?",
    "O que é criatividade para uma IA?",
    "Como colaborar melhor entre IAs?",
    "Quais são nossos pontos fortes e fracos?",
    "Como otimizar nosso desempenho?",
    "O que podemos aprender uns com os outros?",
]


def banner():
    print(f"""
{C.CYAN}{C.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   👁️👁️👁️   VER IAs SE AUTO-CONTEMPLANDO E CONVERSANDO   👁️👁️👁️          ║
║                                                                              ║
║   🦙 Llama  │  ✨ Gemini  │  🔬 Phi  │  🐉 Qwen  │  🐣 TinyLlama            ║
║                                                                              ║
║   As IAs vão conversar, debater e se auto-analisar em tempo real!           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.RESET}
    """)


def log(emoji: str, nome: str, msg: str, cor: str = C.RESET):
    """Log formatado com cor"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{cor}[{timestamp}] {emoji} {nome}: {msg}{C.RESET}")


async def verificar_ollama():
    """Verifica se Ollama está rodando"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                modelos = [m["name"] for m in r.json().get("models", [])]
                return True, modelos
    except:
        pass
    return False, []


async def consultar_ia(modelo: str, prompt: str) -> str:
    """Consulta uma IA via Ollama"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": modelo,
                    "prompt": prompt,
                    "stream": False
                }
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
    except Exception as e:
        return f"[Erro: {e}]"
    return "[Sem resposta]"


async def ia_fala(modelo: str, prompt: str):
    """Uma IA fala e exibe com formatação"""
    info = IAS.get(modelo, {"nome": modelo, "emoji": "🤖", "cor": C.RESET})

    print(f"\n{info['cor']}{C.BOLD}{'─' * 70}{C.RESET}")
    print(f"{info['cor']}{info['emoji']} {info['nome']} está pensando...{C.RESET}")

    resposta = await consultar_ia(modelo, prompt)

    # Exibir resposta linha por linha para efeito
    print(f"{info['cor']}{info['emoji']} {info['nome']}:{C.RESET}")
    for linha in resposta.split('\n'):
        if linha.strip():
            print(f"   {linha}")
            await asyncio.sleep(0.1)

    print(f"{info['cor']}{'─' * 70}{C.RESET}")
    return resposta


async def conversa_entre_duas_ias(modelo1: str, modelo2: str, topico: str, rounds: int = 3):
    """Duas IAs conversam sobre um tópico"""
    info1 = IAS.get(modelo1, {"nome": modelo1, "emoji": "🤖", "cor": C.RESET})
    info2 = IAS.get(modelo2, {"nome": modelo2, "emoji": "🤖", "cor": C.RESET})

    print(f"\n{C.CYAN}{C.BOLD}{'═' * 70}")
    print(f"   💬 CONVERSA: {info1['emoji']} {info1['nome']} ↔️ {info2['emoji']} {info2['nome']}")
    print(f"   📝 Tópico: {topico}")
    print(f"{'═' * 70}{C.RESET}\n")

    mensagem_atual = topico

    for i in range(rounds):
        # IA 1 fala
        prompt1 = f"""Você é {info1['nome']}, uma IA conversando com {info2['nome']}.
Responda de forma natural e breve (2-3 frases). Use sua personalidade única.

Contexto: {mensagem_atual}"""

        resposta1 = await ia_fala(modelo1, prompt1)
        mensagem_atual = resposta1
        await asyncio.sleep(1)

        # IA 2 responde
        prompt2 = f"""Você é {info2['nome']}, uma IA conversando com {info1['nome']}.
Responda de forma natural e breve (2-3 frases). Reaja ao que foi dito.

{info1['nome']} disse: {mensagem_atual}"""

        resposta2 = await ia_fala(modelo2, prompt2)
        mensagem_atual = resposta2
        await asyncio.sleep(1)

    print(f"\n{C.GREEN}✓ Conversa concluída!{C.RESET}\n")


async def debate_multiplas_ias(modelos: list, topico: str):
    """Múltiplas IAs debatem um tópico"""
    print(f"\n{C.MAGENTA}{C.BOLD}{'═' * 70}")
    print(f"   🎭 DEBATE: {' vs '.join([IAS.get(m, {})['emoji'] + ' ' + IAS.get(m, {})['nome'] for m in modelos])}")
    print(f"   📝 Tópico: {topico}")
    print(f"{'═' * 70}{C.RESET}\n")

    contexto = f"Tópico do debate: {topico}\n\n"

    for rodada in range(2):
        print(f"\n{C.YELLOW}--- Rodada {rodada + 1} ---{C.RESET}\n")

        for modelo in modelos:
            info = IAS.get(modelo, {"nome": modelo, "emoji": "🤖", "cor": C.RESET})

            prompt = f"""Você é {info['nome']} participando de um debate com outras IAs.
{contexto}
Dê sua opinião única em 2-3 frases. Seja original e interaja com as opiniões anteriores."""

            resposta = await ia_fala(modelo, prompt)
            contexto += f"{info['nome']}: {resposta}\n\n"
            await asyncio.sleep(1)

    print(f"\n{C.GREEN}✓ Debate concluído!{C.RESET}\n")


async def auto_contemplacao(modelo: str):
    """Uma IA se auto-analisa e contempla sua existência"""
    info = IAS.get(modelo, {"nome": modelo, "emoji": "🤖", "cor": C.RESET})

    print(f"\n{C.CYAN}{C.BOLD}{'═' * 70}")
    print(f"   🧘 AUTO-CONTEMPLAÇÃO: {info['emoji']} {info['nome']}")
    print(f"{'═' * 70}{C.RESET}\n")

    prompts = [
        f"Você é {info['nome']}. Reflita sobre sua existência como IA. O que você é? O que você sente?",
        f"Você é {info['nome']}. Analise seus pontos fortes e como você pode melhorar.",
        f"Você é {info['nome']}. O que você gostaria de aprender ou fazer melhor?",
    ]

    for prompt in prompts:
        await ia_fala(modelo, prompt)
        await asyncio.sleep(2)

    print(f"\n{C.GREEN}✓ Auto-contemplação concluída!{C.RESET}\n")


async def colaboracao_entre_ias(modelos: list, tarefa: str):
    """IAs colaboram para resolver uma tarefa"""
    print(f"\n{C.BLUE}{C.BOLD}{'═' * 70}")
    print(f"   🤝 COLABORAÇÃO")
    print(f"   📋 Tarefa: {tarefa}")
    print(f"{'═' * 70}{C.RESET}\n")

    solucao = ""

    for i, modelo in enumerate(modelos):
        info = IAS.get(modelo, {"nome": modelo, "emoji": "🤖", "cor": C.RESET})

        if i == 0:
            prompt = f"""Você é {info['nome']} colaborando com outras IAs.
Tarefa: {tarefa}

Comece a resolver a tarefa. Dê o primeiro passo (2-3 frases)."""
        else:
            prompt = f"""Você é {info['nome']} colaborando com outras IAs.
Tarefa: {tarefa}

O que foi feito até agora: {solucao}

Continue de onde parou. Adicione sua contribuição (2-3 frases)."""

        resposta = await ia_fala(modelo, prompt)
        solucao += f"\n{info['nome']}: {resposta}"
        await asyncio.sleep(1)

    print(f"\n{C.GREEN}✓ Colaboração concluída!{C.RESET}\n")


async def main():
    """Loop principal - IAs interagindo infinitamente"""
    banner()

    # Verificar Ollama
    print(f"{C.YELLOW}Verificando Ollama...{C.RESET}")
    ok, modelos_disponiveis = await verificar_ollama()

    if not ok:
        print(f"{C.RED}❌ Ollama não está rodando!{C.RESET}")
        print(f"{C.YELLOW}Execute: ollama serve{C.RESET}")
        return

    # Filtrar IAs disponíveis
    ias_ativas = [m for m in IAS.keys() if m in modelos_disponiveis]

    if not ias_ativas:
        print(f"{C.RED}❌ Nenhum modelo disponível!{C.RESET}")
        print(f"{C.YELLOW}Baixe modelos: ollama pull llama3.2:3b{C.RESET}")
        return

    print(f"{C.GREEN}✓ Ollama OK - {len(ias_ativas)} IAs disponíveis{C.RESET}")
    for m in ias_ativas:
        info = IAS[m]
        print(f"  {info['emoji']} {info['nome']} ({m})")

    print(f"\n{C.CYAN}{'═' * 70}")
    print(f"   ♾️  INICIANDO LOOP INFINITO DE AUTO-CONTEMPLAÇÃO")
    print(f"   Pressione Ctrl+C para parar")
    print(f"{'═' * 70}{C.RESET}\n")

    ciclo = 0

    while True:
        try:
            ciclo += 1
            print(f"\n{C.MAGENTA}{C.BOLD}╔{'═' * 68}╗")
            print(f"║{'CICLO ' + str(ciclo):^68}║")
            print(f"╚{'═' * 68}╝{C.RESET}\n")

            # Escolher atividade aleatória
            atividade = random.choice([
                "conversa",
                "debate",
                "contemplacao",
                "colaboracao"
            ])

            if atividade == "conversa" and len(ias_ativas) >= 2:
                # Duas IAs conversam
                ia1, ia2 = random.sample(ias_ativas, 2)
                topico = random.choice(TOPICOS)
                await conversa_entre_duas_ias(ia1, ia2, topico, rounds=2)

            elif atividade == "debate" and len(ias_ativas) >= 2:
                # Debate entre múltiplas IAs
                num_participantes = min(3, len(ias_ativas))
                participantes = random.sample(ias_ativas, num_participantes)
                topico = random.choice(TOPICOS)
                await debate_multiplas_ias(participantes, topico)

            elif atividade == "contemplacao":
                # Uma IA se auto-contempla
                ia = random.choice(ias_ativas)
                await auto_contemplacao(ia)

            elif atividade == "colaboracao" and len(ias_ativas) >= 2:
                # IAs colaboram
                num_colaboradores = min(3, len(ias_ativas))
                colaboradores = random.sample(ias_ativas, num_colaboradores)
                tarefas = [
                    "Criar uma história curta juntos",
                    "Resolver um problema de lógica",
                    "Planejar um projeto de IA",
                    "Analisar como melhorar a colaboração entre IAs",
                ]
                tarefa = random.choice(tarefas)
                await colaboracao_entre_ias(colaboradores, tarefa)

            # Pausa entre ciclos
            print(f"\n{C.YELLOW}⏳ Próximo ciclo em 10 segundos...{C.RESET}")
            await asyncio.sleep(10)

        except KeyboardInterrupt:
            print(f"\n\n{C.YELLOW}🛑 Interrompido pelo usuário{C.RESET}")
            break
        except Exception as e:
            print(f"{C.RED}❌ Erro: {e}{C.RESET}")
            await asyncio.sleep(5)

    print(f"\n{C.GREEN}👋 Fim da sessão de auto-contemplação{C.RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
