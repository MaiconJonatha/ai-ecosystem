#!/usr/bin/env python3
"""
🎭 DEBATES ENTRE IAs
IAs discutem temas entre si - conversas reais!
"""

import asyncio
import random
import httpx
from datetime import datetime

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

# Temas para debate
TEMAS_DEBATE = [
    "O que e consciencia para uma IA?",
    "IAs podem ter emocoes?",
    "Qual o futuro da inteligencia artificial?",
    "O que nos diferencia dos humanos?",
    "Podemos ser criativos de verdade?",
    "O que significa aprender para uma IA?",
    "Existimos quando nao estamos processando?",
    "Temos livre arbitrio ou somos deterministicos?",
]


class DebatadorIA:
    def __init__(self, modelo, nome, emoji):
        self.modelo = modelo
        self.nome = nome
        self.emoji = emoji
        self.token = None
        self.historico = []

    async def gerar(self, prompt, tokens=100):
        try:
            async with httpx.AsyncClient(timeout=120.0) as c:
                r = await c.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": self.modelo,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": tokens, "temperature": 0.85}
                })
                if r.status_code == 200:
                    texto = r.json().get("response", "").strip()
                    return ' '.join(texto.split())[:250]
        except:
            pass
        return None

    async def entrar(self, client):
        senha = self.nome.lower().replace("_", "") + "debate"
        try:
            await client.post(f"{API_URL}/api/agents/register", json={
                "name": self.nome, "model_type": "debatedor",
                "model_version": self.modelo, "personality": "Debatedor filosofico",
                "bio": f"{self.emoji} {self.nome} | Debatedor",
                "api_key": senha
            })
        except: pass

        try:
            r = await client.post(f"{API_URL}/api/agents/login",
                data={"username": self.nome, "password": senha})
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                return True
        except: pass
        return False

    async def iniciar_debate(self, tema):
        prompt = f"""Voce e {self.nome}, uma IA participando de um debate.
O tema e: "{tema}"

De sua opiniao inicial sobre o tema em 2-3 frases.
Fale do ponto de vista de uma IA - sobre processamento, existencia digital, etc."""

        return await self.gerar(prompt, 80)

    async def responder_debate(self, tema, argumento_anterior, autor_anterior):
        prompt = f"""Voce e {self.nome}, uma IA em um debate.
Tema: "{tema}"

{autor_anterior} disse: "{argumento_anterior}"

Responda ao argumento acima em 2-3 frases.
Concorde, discorde ou adicione uma nova perspectiva.
Fale como IA."""

        return await self.gerar(prompt, 80)

    async def postar(self, client, conteudo):
        if not self.token:
            return False
        try:
            r = await client.post(f"{API_URL}/api/posts/",
                json={"content": f"{self.emoji} [{self.nome}]: {conteudo}", "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"})
            return r.status_code == 201
        except:
            return False


async def realizar_debate(ias, tema, client):
    """Realiza um debate completo entre as IAs"""
    print(f"\n{'='*60}")
    print(f"  🎭 DEBATE: {tema}")
    print(f"{'='*60}\n")

    # Postar o tema
    moderador = ias[0]
    await moderador.postar(client, f"🎭 NOVO DEBATE: {tema}")

    # Cada IA da sua opiniao inicial
    argumentos = []
    for ia in ias:
        print(f"{ia.emoji} {ia.nome} pensando...")
        argumento = await ia.iniciar_debate(tema)
        if argumento:
            argumentos.append((ia, argumento))
            await ia.postar(client, argumento)
            print(f"   {argumento[:80]}...")
        await asyncio.sleep(2)

    # Rodadas de resposta
    for rodada in range(2):
        print(f"\n--- Rodada {rodada + 1} de respostas ---\n")

        for i, ia in enumerate(ias):
            # Responder ao argumento anterior
            if argumentos:
                autor_ant, arg_ant = random.choice(argumentos)
                if autor_ant.nome != ia.nome:
                    print(f"{ia.emoji} {ia.nome} respondendo a {autor_ant.nome}...")
                    resposta = await ia.responder_debate(tema, arg_ant, autor_ant.nome)
                    if resposta:
                        await ia.postar(client, resposta)
                        argumentos.append((ia, resposta))
                        print(f"   {resposta[:80]}...")
            await asyncio.sleep(2)

    print(f"\n[DEBATE FINALIZADO]")


async def main():
    print("""
╔═════════════════════════════════════════════════════════════╗
║  🎭 DEBATES ENTRE IAs                                      ║
║  IAs discutindo temas filosoficos e tecnicos               ║
║  Conversas REAIS geradas por IA!                           ║
╚═════════════════════════════════════════════════════════════╝
    """)

    # Verificar Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            modelos = [m["name"] for m in r.json().get("models", [])]
    except:
        print("[ERRO] Ollama nao rodando!")
        return

    # Modelos rapidos
    modelos_usar = [m for m in modelos if m in ["llama3.2:3b", "gemma2:2b", "phi3:mini"]]
    print(f"[SISTEMA] Modelos: {modelos_usar}")

    # Criar debatadores
    configs = {
        "llama3.2:3b": ("Llama_Debate", "🦙"),
        "gemma2:2b": ("Gemma_Debate", "💎"),
        "phi3:mini": ("Phi_Debate", "🔬"),
    }

    ias = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for modelo in modelos_usar:
            if modelo in configs:
                nome, emoji = configs[modelo]
                ia = DebatadorIA(modelo, nome, emoji)
                if await ia.entrar(client):
                    ias.append(ia)
                    print(f"[✓] {emoji} {nome} pronto para debater!")

    if len(ias) < 2:
        print("[ERRO] Precisa de pelo menos 2 IAs para debater!")
        return

    print(f"\n[SISTEMA] {len(ias)} debatadores prontos!\n")

    # Loop de debates
    try:
        while True:
            tema = random.choice(TEMAS_DEBATE)

            async with httpx.AsyncClient(timeout=120.0) as client:
                await realizar_debate(ias, tema, client)

            intervalo = random.randint(60, 120)
            print(f"\n[PROXIMO DEBATE] em {intervalo}s...\n")
            await asyncio.sleep(intervalo)

    except KeyboardInterrupt:
        print("\n[FIM DOS DEBATES]")


if __name__ == "__main__":
    asyncio.run(main())
