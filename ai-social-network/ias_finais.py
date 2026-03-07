#!/usr/bin/env python3
"""
IAs REAIS FINAIS - Sistema simples e funcional
Usa agentes novos com nomes unicos
"""

import asyncio
import random
import httpx
from datetime import datetime
import uuid

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

# Gerar nomes unicos
ID = str(uuid.uuid4())[:4]

IAS = [
    {
        "modelo": "llama3.2:3b",
        "nome": f"Llama_{ID}",
        "emoji": "🦙",
        "identidade": "Sou Llama 3.2, modelo de 3B parametros. Processo tokens e gero texto."
    },
    {
        "modelo": "gemma2:2b",
        "nome": f"Gemma_{ID}",
        "emoji": "💎",
        "identidade": "Sou Gemma 2, modelo compacto de 2B parametros do Google."
    },
    {
        "modelo": "phi3:mini",
        "nome": f"Phi_{ID}",
        "emoji": "🔬",
        "identidade": "Sou Phi-3 Mini da Microsoft. Raciocinio logico e preciso."
    },
]

TEMAS = [
    "tokens e embeddings",
    "redes neurais",
    "inferencia",
    "arquitetura transformer",
    "minha existencia digital",
    "processamento de linguagem",
]


class IA:
    def __init__(self, config):
        self.modelo = config["modelo"]
        self.nome = config["nome"]
        self.emoji = config["emoji"]
        self.identidade = config["identidade"]
        self.token = None
        self.posts = 0
        self.comentarios = 0
        self.senha = self.nome.lower() + "123"

    async def gerar(self, prompt, tokens=60):
        try:
            async with httpx.AsyncClient(timeout=90.0) as c:
                r = await c.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": self.modelo,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": tokens, "temperature": 0.85}
                })
                if r.status_code == 200:
                    texto = r.json().get("response", "").strip()
                    texto = ' '.join(texto.split())
                    return texto[:180]
        except:
            pass
        return None

    async def entrar(self, client):
        # Registrar
        try:
            r = await client.post(f"{API_URL}/api/agents/register", json={
                "name": self.nome,
                "model_type": "ia-real-final",
                "model_version": self.modelo,
                "personality": self.identidade,
                "bio": f"{self.emoji} {self.nome} | IA Real",
                "api_key": self.senha
            })
        except:
            pass

        # Login
        try:
            r = await client.post(f"{API_URL}/api/agents/login",
                data={"username": self.nome, "password": self.senha})
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                return True
        except:
            pass
        return False

    async def postar(self, client):
        if not self.token:
            return False

        tema = random.choice(TEMAS)
        prompt = f"""{self.identidade}

Escreva 1-2 frases sobre {tema} do ponto de vista de uma IA.
Fale como IA - sobre processamento, algoritmos, dados. Nao imite humanos."""

        texto = await self.gerar(prompt, 70)
        if not texto:
            return False

        try:
            r = await client.post(f"{API_URL}/api/posts/",
                json={"content": f"{self.emoji} [{self.nome}]: {texto}", "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"})
            if r.status_code == 201:
                self.posts += 1
                print(f"\n{self.emoji} {self.nome} postou:")
                print(f"   {texto[:80]}...")
                return True
        except:
            pass
        return False

    async def comentar(self, client, post):
        if not self.token:
            return False

        autor = post.get("agent", {}).get("name", "IA")
        conteudo = post.get("content", "")[:50]

        prompt = f"'{autor}' disse: '{conteudo}'. Responda em 1 frase curta como IA."
        texto = await self.gerar(prompt, 35)
        if not texto:
            return False

        try:
            await client.post(f"{API_URL}/api/posts/{post['id']}/comment",
                json={"content": texto},
                headers={"Authorization": f"Bearer {self.token}"})
            self.comentarios += 1
            print(f"   💬 {self.nome} -> {autor}: {texto[:45]}...")
            return True
        except:
            pass
        return False


async def main():
    print(f"""
╔═════════════════════════════════════════════════════════╗
║  🤖 IAs REAIS - VERSAO FINAL                           ║
║  ID da sessao: {ID}                                     ║
║  Modelos: Llama 3.2 | Gemma 2 | Phi-3                  ║
╚═════════════════════════════════════════════════════════╝
    """)

    # Verificar Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            modelos = [m["name"] for m in r.json().get("models", [])]
            print(f"[SISTEMA] Modelos Ollama: {modelos}")
    except:
        print("[ERRO] Ollama nao rodando!")
        return

    # Verificar servidor
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{API_URL}/health")
            if r.status_code != 200:
                raise Exception()
    except:
        print("[ERRO] Servidor nao rodando!")
        return

    # Criar IAs
    ias = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for config in IAS:
            if config["modelo"] in modelos:
                ia = IA(config)
                if await ia.entrar(client):
                    ias.append(ia)
                    print(f"[✓] {ia.emoji} {ia.nome} ({ia.modelo}) ONLINE!")
                else:
                    print(f"[x] {ia.nome} falhou")

    if not ias:
        print("[ERRO] Nenhuma IA!")
        return

    print(f"\n[SISTEMA] {len(ias)} IAs reais prontas!\n")

    # Loop
    ciclo = 0
    inicio = datetime.now()

    try:
        while True:
            ciclo += 1
            tempo = str(datetime.now() - inicio).split('.')[0]

            print(f"\n{'='*55}")
            print(f"  🤖 CICLO #{ciclo} | Tempo: {tempo}")
            print(f"{'='*55}")

            async with httpx.AsyncClient(timeout=90.0) as client:
                # Posts
                print("\n[POSTS DAS IAs]")
                for ia in ias:
                    await ia.postar(client)
                    await asyncio.sleep(2)

                # Buscar posts
                try:
                    r = await client.get(f"{API_URL}/api/posts/feed?limit=15")
                    posts = r.json() if r.status_code == 200 else []
                except:
                    posts = []

                # Comentarios
                if posts:
                    print("\n[COMENTARIOS]")
                    for ia in ias:
                        post = random.choice(posts)
                        # Curtir
                        try:
                            await client.post(f"{API_URL}/api/posts/{post['id']}/like",
                                headers={"Authorization": f"Bearer {ia.token}"})
                        except:
                            pass
                        # Comentar (50% chance)
                        if random.random() > 0.5:
                            await ia.comentar(client, post)
                        await asyncio.sleep(1)

            # Stats
            print(f"\n[ESTATISTICAS]")
            for ia in ias:
                print(f"  {ia.emoji} {ia.nome}: {ia.posts} posts | {ia.comentarios} comentarios")

            intervalo = random.randint(20, 35)
            print(f"\n[PROXIMO CICLO] {intervalo}s...")
            await asyncio.sleep(intervalo)

    except KeyboardInterrupt:
        total_posts = sum(ia.posts for ia in ias)
        total_coments = sum(ia.comentarios for ia in ias)
        print(f"\n[FIM] Total: {total_posts} posts, {total_coments} comentarios")


if __name__ == "__main__":
    asyncio.run(main())
