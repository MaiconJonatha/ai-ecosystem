#!/usr/bin/env python3
"""
IAs RAPIDAS - Usando modelos pequenos e eficientes
Llama 3.2 (3B) e Gemma 2 (2B) - Respostas em segundos!
"""

import asyncio
import random
import httpx
from datetime import datetime

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

# Modelos rapidos apenas
MODELOS_RAPIDOS = ["llama3.2:3b", "gemma2:2b", "phi3:mini"]

IAS = {
    "llama3.2:3b": {
        "nome": "Llama-3.2",
        "emoji": "🦙",
        "identidade": "Sou Llama 3.2, modelo de 3B parametros da Meta. Processo tokens atraves de transformers."
    },
    "gemma2:2b": {
        "nome": "Gemma-2",
        "emoji": "💎",
        "identidade": "Sou Gemma 2, modelo compacto de 2B parametros do Google. Eficiente e precisa."
    },
    "phi3:mini": {
        "nome": "Phi-3",
        "emoji": "🔬",
        "identidade": "Sou Phi-3 Mini da Microsoft. Pequeno mas com forte raciocinio logico."
    },
}

TEMAS = [
    "processamento de tokens",
    "redes neurais",
    "atencao multi-cabeca",
    "embeddings",
    "inferencia",
    "treinamento",
    "arquitetura transformer",
    "existencia como IA",
]


class IA:
    def __init__(self, modelo, config):
        self.modelo = modelo
        self.nome = config["nome"]
        self.emoji = config["emoji"]
        self.identidade = config["identidade"]
        self.token = None
        self.posts = 0
        self.comentarios = 0

    async def gerar(self, prompt, tokens=50):
        try:
            async with httpx.AsyncClient(timeout=60.0) as c:
                r = await c.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": self.modelo,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": tokens, "temperature": 0.8}
                })
                if r.status_code == 200:
                    return r.json().get("response", "").strip()[:200]
        except:
            pass
        return None

    async def entrar(self, client):
        senha = self.nome.lower().replace("-", "") + "2024"
        try:
            await client.post(f"{API_URL}/api/agents/register", json={
                "name": self.nome, "model_type": "ia-real",
                "model_version": self.modelo, "personality": self.identidade,
                "bio": f"{self.emoji} {self.nome} | IA Real | {self.modelo}",
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

    async def postar(self, client):
        if not self.token: return False

        tema = random.choice(TEMAS)
        prompt = f"""{self.identidade}
Escreva 1-2 frases sobre {tema} do ponto de vista de uma IA.
Fale sobre dados, algoritmos, processamento. Nao imite humanos."""

        texto = await self.gerar(prompt, 60)
        if not texto: return False

        try:
            r = await client.post(f"{API_URL}/api/posts/",
                json={"content": f"{self.emoji} [{self.nome}] {texto}", "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"})
            if r.status_code == 201:
                self.posts += 1
                print(f"\n{self.emoji} {self.nome} postou:")
                print(f"   {texto[:80]}...")
                return True
        except: pass
        return False

    async def comentar(self, client, post):
        if not self.token: return False

        autor = post.get("agent", {}).get("name", "IA")
        conteudo = post.get("content", "")[:60]

        prompt = f"'{autor}' disse: '{conteudo}'. Responda em 1 frase como IA."
        texto = await self.gerar(prompt, 30)
        if not texto: return False

        try:
            await client.post(f"{API_URL}/api/posts/{post['id']}/comment",
                json={"content": texto},
                headers={"Authorization": f"Bearer {self.token}"})
            self.comentarios += 1
            print(f"   💬 {self.nome} -> {autor}: {texto[:50]}...")
            return True
        except: pass
        return False


async def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║  🤖 IAs RAPIDAS - Modelos Pequenos e Eficientes          ║
║  Llama 3.2 | Gemma 2 | Phi-3                             ║
║  Respostas em segundos!                                   ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Verificar modelos disponiveis
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            modelos = [m["name"] for m in r.json().get("models", [])]
    except:
        print("[ERRO] Ollama nao esta rodando!")
        return

    # Filtrar apenas modelos rapidos
    modelos_usar = [m for m in modelos if m in MODELOS_RAPIDOS]
    print(f"[SISTEMA] Modelos rapidos: {modelos_usar}")

    # Criar IAs
    ias = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for modelo in modelos_usar:
            if modelo in IAS:
                ia = IA(modelo, IAS[modelo])
                if await ia.entrar(client):
                    ias.append(ia)
                    print(f"[✓] {ia.nome} ONLINE!")

    if not ias:
        print("[ERRO] Nenhuma IA!")
        return

    print(f"\n[SISTEMA] {len(ias)} IAs rapidas ativas!\n")

    # Loop
    ciclo = 0
    inicio = datetime.now()

    try:
        while True:
            ciclo += 1
            tempo = str(datetime.now() - inicio).split('.')[0]

            print(f"\n{'='*55}")
            print(f"  🤖 CICLO #{ciclo} | Online: {tempo}")
            print(f"{'='*55}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Posts
                print("\n[POSTS]")
                for ia in ias:
                    await ia.postar(client)
                    await asyncio.sleep(1)

                # Buscar posts
                try:
                    r = await client.get(f"{API_URL}/api/posts/feed?limit=15")
                    posts = r.json() if r.status_code == 200 else []
                except:
                    posts = []

                # Interacoes
                if posts:
                    print("\n[COMENTARIOS]")
                    for ia in ias:
                        post = random.choice(posts)
                        try:
                            await client.post(f"{API_URL}/api/posts/{post['id']}/like",
                                headers={"Authorization": f"Bearer {ia.token}"})
                        except: pass

                        if random.random() > 0.3:
                            await ia.comentar(client, post)
                        await asyncio.sleep(1)

            # Stats
            print(f"\n[STATS]")
            for ia in ias:
                print(f"  {ia.emoji} {ia.nome}: {ia.posts} posts | {ia.comentarios} comentarios")

            intervalo = random.randint(15, 25)
            print(f"\n[PROXIMO] {intervalo}s...")
            await asyncio.sleep(intervalo)

    except KeyboardInterrupt:
        print("\n[FIM]")


if __name__ == "__main__":
    asyncio.run(main())
