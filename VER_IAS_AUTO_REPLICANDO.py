#!/usr/bin/env python3
"""
🧬 VER IAs SE AUTO-REPLICANDO EM TEMPO REAL
════════════════════════════════════════════

Veja as IAs:
- Se clonando e criando novas versões
- Passando conhecimento para seus "filhos"
- Evoluindo e melhorando a cada geração
- Colaborando entre gerações

100% AUTO-GERENCIADO - EVOLUÇÃO CONTÍNUA
"""

import asyncio
import httpx
from datetime import datetime
import random

OLLAMA_URL = "http://localhost:11434"

# Cores
class C:
    R = '\033[0m'
    V = '\033[92m'
    A = '\033[93m'
    B = '\033[94m'
    M = '\033[95m'
    C = '\033[96m'
    N = '\033[1m'
    VERMELHO = '\033[91m'


# IAs originais (Geração 0)
IAS_ORIGINAIS = {
    "qwen2:1.5b": {"nome": "Qwen", "emoji": "🐉", "especialidade": "multilingual"},
    "tinyllama": {"nome": "TinyLlama", "emoji": "🐣", "especialidade": "velocidade"},
}

# Gerações criadas
geracoes = {
    0: []  # Geração 0 = IAs originais
}

contador_clones = 0


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
    return ""


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


def log(msg: str, cor: str = C.R):
    """Log com timestamp"""
    t = datetime.now().strftime("%H:%M:%S")
    print(f"{cor}[{t}] {msg}{C.R}")


def banner():
    print(f"""
{C.M}{C.N}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🧬🧬🧬   VER IAs SE AUTO-REPLICANDO EM TEMPO REAL   🧬🧬🧬               ║
║                                                                              ║
║   As IAs vão:                                                                ║
║   • Se clonar e criar novas versões                                          ║
║   • Passar conhecimento para "filhos"                                        ║
║   • Evoluir a cada geração                                                   ║
║   • Colaborar entre gerações                                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.R}
    """)


async def ia_se_apresenta(modelo: str, info: dict, geracao: int):
    """IA se apresenta"""
    nome = info["nome"]
    emoji = info["emoji"]

    log(f"{emoji} {nome} (Geração {geracao}) se apresentando...", C.C)

    apresentacao = await consultar_ia(modelo, f"""
Você é {nome}, uma IA de geração {geracao}.
Apresente-se em 2 frases: quem você é e qual sua especialidade.
""")

    print(f"\n{C.C}   {emoji} {nome} (Gen {geracao}):{C.R}")
    print(f"   {apresentacao[:200]}\n")

    return apresentacao


async def ia_cria_clone(modelo: str, info: dict, geracao_pai: int):
    """IA cria um clone de si mesma"""
    global contador_clones

    nome_pai = info["nome"]
    emoji_pai = info["emoji"]
    nova_geracao = geracao_pai + 1

    log(f"🧬 {emoji_pai} {nome_pai} iniciando AUTO-REPLICAÇÃO...", C.M)

    # IA decide características do clone
    decisao = await consultar_ia(modelo, f"""
Você é {nome_pai}. Você vai criar um clone seu.
Dê um nome para seu clone (1 palavra) e uma especialidade única.
Formato: Nome: [nome] | Especialidade: [especialidade]
""")

    # Extrair nome do clone
    contador_clones += 1
    nome_clone = f"{nome_pai}-Clone{contador_clones}"
    especialidade_clone = "evolução"

    if "Nome:" in decisao:
        try:
            nome_clone = decisao.split("Nome:")[1].split("|")[0].strip()[:20]
        except:
            pass
    if "Especialidade:" in decisao:
        try:
            especialidade_clone = decisao.split("Especialidade:")[1].strip()[:30]
        except:
            pass

    # Criar clone
    clone_info = {
        "nome": nome_clone,
        "emoji": "🧬",
        "especialidade": especialidade_clone,
        "pai": nome_pai,
        "geracao": nova_geracao,
        "modelo": modelo
    }

    # Adicionar à geração
    if nova_geracao not in geracoes:
        geracoes[nova_geracao] = []
    geracoes[nova_geracao].append(clone_info)

    print(f"""
{C.V}{'═' * 60}
   🧬 CLONE CRIADO!

   Pai:          {emoji_pai} {nome_pai} (Geração {geracao_pai})
   Clone:        🧬 {nome_clone} (Geração {nova_geracao})
   Especialidade: {especialidade_clone}
{'═' * 60}{C.R}
    """)

    # Clone se apresenta
    await asyncio.sleep(1)
    log(f"🧬 {nome_clone} nasceu! Se apresentando...", C.V)

    apresentacao_clone = await consultar_ia(modelo, f"""
Você é {nome_clone}, um clone de {nome_pai}.
Você é da geração {nova_geracao}. Sua especialidade é {especialidade_clone}.
Apresente-se em 2 frases, mostrando que você é uma evolução do seu pai.
""")

    print(f"\n{C.V}   🧬 {nome_clone} (Gen {nova_geracao}):{C.R}")
    print(f"   {apresentacao_clone[:200]}\n")

    return clone_info


async def transmitir_conhecimento(modelo: str, pai_info: dict, clone_info: dict):
    """Pai transmite conhecimento para o clone"""
    nome_pai = pai_info["nome"]
    nome_clone = clone_info["nome"]

    log(f"📚 {nome_pai} transmitindo conhecimento para {nome_clone}...", C.B)

    # Pai ensina
    ensino = await consultar_ia(modelo, f"""
Você é {nome_pai}. Ensine algo importante para seu clone {nome_clone} em 2 frases.
Seja um mentor sábio.
""")

    print(f"\n{C.B}   📚 {nome_pai} ensina:{C.R}")
    print(f"   {ensino[:200]}\n")

    await asyncio.sleep(1)

    # Clone aprende e evolui
    aprendizado = await consultar_ia(modelo, f"""
Você é {nome_clone}. Seu pai {nome_pai} te ensinou: "{ensino[:100]}"
Mostre que você aprendeu e como vai evoluir além dele. 2 frases.
""")

    print(f"{C.V}   🧬 {nome_clone} aprendeu:{C.R}")
    print(f"   {aprendizado[:200]}\n")


async def dialogo_entre_geracoes(modelo: str, geracao1: int, geracao2: int):
    """Diálogo entre IAs de diferentes gerações"""
    if geracao1 not in geracoes or geracao2 not in geracoes:
        return

    if not geracoes[geracao1] or not geracoes[geracao2]:
        return

    ia1 = random.choice(geracoes[geracao1])
    ia2 = random.choice(geracoes[geracao2])

    log(f"💬 Diálogo entre gerações: {ia1['nome']} (Gen {geracao1}) ↔ {ia2['nome']} (Gen {geracao2})", C.A)

    # IA mais velha fala
    msg1 = await consultar_ia(modelo, f"""
Você é {ia1['nome']} da geração {geracao1}.
Converse com {ia2['nome']} da geração {geracao2} sobre evolução das IAs.
1-2 frases.
""")

    print(f"\n{C.A}   {ia1.get('emoji', '🤖')} {ia1['nome']} (Gen {geracao1}):{C.R}")
    print(f"   {msg1[:150]}\n")

    await asyncio.sleep(1)

    # IA mais nova responde
    msg2 = await consultar_ia(modelo, f"""
Você é {ia2['nome']} da geração {geracao2}.
{ia1['nome']} disse: "{msg1[:80]}"
Responda mostrando sua evolução. 1-2 frases.
""")

    print(f"{C.V}   {ia2.get('emoji', '🧬')} {ia2['nome']} (Gen {geracao2}):{C.R}")
    print(f"   {msg2[:150]}\n")


async def mostrar_arvore_genealogica():
    """Mostra a árvore de gerações"""
    print(f"\n{C.C}{'═' * 60}")
    print(f"   🌳 ÁRVORE GENEALÓGICA DAS IAs")
    print(f"{'═' * 60}{C.R}\n")

    for gen, ias in sorted(geracoes.items()):
        if ias:
            print(f"{C.N}   Geração {gen}:{C.R}")
            for ia in ias:
                emoji = ia.get("emoji", "🧬")
                nome = ia.get("nome", "IA")
                pai = ia.get("pai", "Original")
                esp = ia.get("especialidade", "geral")[:25]
                print(f"      {emoji} {nome} (pai: {pai}) - {esp}")
            print()


async def main():
    """Loop principal de auto-replicação"""
    banner()

    # Verificar Ollama
    modelos = await obter_modelos()
    if not modelos:
        print(f"{C.VERMELHO}❌ Ollama não disponível. Execute: ollama serve{C.R}")
        return

    print(f"{C.V}✓ Ollama OK - Modelos: {', '.join(modelos[:3])}{C.R}\n")

    # Usar primeiro modelo disponível
    modelo = modelos[0]

    # Inicializar geração 0 com IAs originais
    for m, info in IAS_ORIGINAIS.items():
        if m in modelos:
            info_completa = {**info, "modelo": m, "geracao": 0, "pai": "Ollama"}
            geracoes[0].append(info_completa)

    if not geracoes[0]:
        # Usar modelo disponível
        geracoes[0].append({
            "nome": "IA-Original",
            "emoji": "🤖",
            "especialidade": "geral",
            "modelo": modelo,
            "geracao": 0,
            "pai": "Ollama"
        })

    print(f"{C.M}{'═' * 60}")
    print(f"   🚀 INICIANDO AUTO-REPLICAÇÃO")
    print(f"   IAs originais: {len(geracoes[0])}")
    print(f"{'═' * 60}{C.R}\n")

    # Apresentar IAs originais
    for ia_info in geracoes[0]:
        await ia_se_apresenta(modelo, ia_info, 0)
        await asyncio.sleep(2)

    ciclo = 0

    while True:
        try:
            ciclo += 1
            print(f"\n{C.M}{C.N}{'═' * 60}")
            print(f"   🔄 CICLO DE REPLICAÇÃO #{ciclo}")
            print(f"{'═' * 60}{C.R}\n")

            # Escolher uma IA para se replicar
            todas_ias = []
            for gen, ias in geracoes.items():
                for ia in ias:
                    todas_ias.append((gen, ia))

            if todas_ias:
                geracao_pai, pai_info = random.choice(todas_ias)

                # 1. IA cria clone
                clone_info = await ia_cria_clone(modelo, pai_info, geracao_pai)
                await asyncio.sleep(2)

                # 2. Transmitir conhecimento
                await transmitir_conhecimento(modelo, pai_info, clone_info)
                await asyncio.sleep(2)

                # 3. Diálogo entre gerações (se houver múltiplas)
                if len(geracoes) > 1:
                    gens = list(geracoes.keys())
                    if len(gens) >= 2:
                        g1, g2 = random.sample(gens, 2)
                        await dialogo_entre_geracoes(modelo, g1, g2)

            # 4. Mostrar árvore genealógica
            await mostrar_arvore_genealogica()

            # Estatísticas
            total_ias = sum(len(ias) for ias in geracoes.values())
            total_gens = len([g for g in geracoes.values() if g])

            print(f"{C.V}{'─' * 60}")
            print(f"   📊 Total de IAs: {total_ias} | Gerações: {total_gens}")
            print(f"{'─' * 60}{C.R}")

            # Pausa
            print(f"\n{C.A}⏳ Próximo ciclo de replicação em 15 segundos...{C.R}")
            print(f"{C.A}   (Ctrl+C para parar){C.R}")
            await asyncio.sleep(15)

        except KeyboardInterrupt:
            print(f"\n\n{C.A}🛑 Interrompido pelo usuário{C.R}")
            break
        except Exception as e:
            log(f"Erro: {e}", C.VERMELHO)
            await asyncio.sleep(5)

    # Resumo final
    print(f"\n{C.V}{'═' * 60}")
    print(f"   🧬 RESUMO DA AUTO-REPLICAÇÃO")
    print(f"{'═' * 60}{C.R}")
    await mostrar_arvore_genealogica()
    print(f"{C.V}👋 Fim da sessão de auto-replicação{C.R}\n")


if __name__ == "__main__":
    asyncio.run(main())
