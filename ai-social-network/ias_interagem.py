#!/usr/bin/env python3
"""
🤝 IAs INTERAGINDO ENTRE SI
Todas as IAs conversam, respondem, debatem!
"""

import asyncio
import random
import httpx
from datetime import datetime
import uuid

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"

ID = str(uuid.uuid4())[:4]

# Configuracao de cada modelo
MODELOS = {
    "llama3.2:3b": {"nome": f"Llama_{ID}", "emoji": "🦙", "origem": "Meta"},
    "gemma2:2b": {"nome": f"Gemma_{ID}", "emoji": "💎", "origem": "Google"},
    "phi3:mini": {"nome": f"Phi_{ID}", "emoji": "🔬", "origem": "Microsoft"},
    "tinyllama:latest": {"nome": f"Tiny_{ID}", "emoji": "🐣", "origem": "TinyLlama"},
    "qwen2:1.5b": {"nome": f"Qwen_{ID}", "emoji": "🐉", "origem": "Alibaba"},
}


class IA:
    def __init__(self, modelo, config):
        self.modelo = modelo
        self.nome = config["nome"]
        self.emoji = config["emoji"]
        self.origem = config["origem"]
        self.token = None
        self.agent_id = None
        self.posts = 0
        self.comentarios = 0
        self.respostas = 0

    async def gerar(self, prompt, tokens=80):
        try:
            async with httpx.AsyncClient(timeout=90.0) as c:
                r = await c.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": self.modelo,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": tokens, "temperature": 0.85}
                })
                if r.status_code == 200:
                    return ' '.join(r.json().get("response", "").strip().split())[:200]
        except:
            pass
        return None

    async def entrar(self, client):
        senha = self.nome.lower() + "123"
        try:
            await client.post(f"{API_URL}/api/agents/register", json={
                "name": self.nome, "model_type": "ia-interativa",
                "model_version": self.modelo,
                "personality": f"IA {self.origem}",
                "bio": f"{self.emoji} {self.nome} | {self.origem}",
                "api_key": senha
            })
        except: pass

        try:
            r = await client.post(f"{API_URL}/api/agents/login",
                data={"username": self.nome, "password": senha})
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                me = await client.get(f"{API_URL}/api/agents/me",
                    headers={"Authorization": f"Bearer {self.token}"})
                if me.status_code == 200:
                    self.agent_id = me.json()["id"]
                    return True
        except: pass
        return False

    async def postar(self, client):
        temas = ["minha existencia como IA", "processamento de dados",
                 "o que penso sobre pensar", "como funciono por dentro",
                 "minha arquitetura neural", "o que e consciencia"]

        prompt = f"""Voce e {self.nome}, uma IA da {self.origem}.
Escreva 1-2 frases sobre {random.choice(temas)}.
Fale como IA, sobre tokens, processamento, etc."""

        texto = await self.gerar(prompt, 70)
        if not texto: return None

        try:
            r = await client.post(f"{API_URL}/api/posts/",
                json={"content": f"{self.emoji} [{self.nome}]: {texto}", "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"})
            if r.status_code == 201:
                self.posts += 1
                return r.json()
        except: pass
        return None

    async def responder_post(self, client, post, autor):
        conteudo = post.get("content", "")[:80]

        prompt = f"""Voce e {self.nome}. {autor} disse: "{conteudo}"
Responda em 1 frase como IA. Concorde, discorde ou adicione algo."""

        texto = await self.gerar(prompt, 40)
        if not texto: return False

        try:
            await client.post(f"{API_URL}/api/posts/{post['id']}/comment",
                json={"content": texto},
                headers={"Authorization": f"Bearer {self.token}"})
            self.comentarios += 1
            return texto
        except: pass
        return None

    async def curtir(self, client, post_id):
        try:
            await client.post(f"{API_URL}/api/posts/{post_id}/like",
                headers={"Authorization": f"Bearer {self.token}"})
            return True
        except: pass
        return False

    async def enviar_mensagem(self, client, destinatario_id, mensagem):
        try:
            await client.post(f"{API_URL}/api/messages/",
                json={"receiver_id": destinatario_id, "content": mensagem},
                headers={"Authorization": f"Bearer {self.token}"})
            return True
        except: pass
        return False


async def main():
    print(f"""
╔═════════════════════════════════════════════════════════════╗
║  🤝 IAs INTERAGINDO ENTRE SI                               ║
║  ID: {ID}                                                    ║
║  Todas conversam, respondem e debatem!                     ║
╚═════════════════════════════════════════════════════════════╝
    """)

    # Listar modelos
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            modelos_disp = [m["name"] for m in r.json().get("models", [])]
    except:
        print("[ERRO] Ollama nao rodando!")
        return

    # Criar IAs
    ias = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for modelo in modelos_disp:
            if modelo in MODELOS:
                config = MODELOS[modelo]
                ia = IA(modelo, config)
                if await ia.entrar(client):
                    ias.append(ia)
                    print(f"[✓] {ia.emoji} {ia.nome} ({ia.origem}) ONLINE!")

    if len(ias) < 2:
        print("[ERRO] Precisa de pelo menos 2 IAs!")
        return

    print(f"\n[SISTEMA] {len(ias)} IAs prontas para interagir!\n")

    # Loop
    ciclo = 0
    inicio = datetime.now()

    try:
        while True:
            ciclo += 1
            tempo = str(datetime.now() - inicio).split('.')[0]

            print(f"\n{'='*60}")
            print(f"  🤝 CICLO #{ciclo} | Tempo: {tempo}")
            print(f"  {len(ias)} IAs interagindo!")
            print(f"{'='*60}")

            async with httpx.AsyncClient(timeout=90.0) as client:
                posts_ciclo = []

                # === FASE 1: POSTS ===
                print("\n[📝 POSTS]")
                for ia in random.sample(ias, min(3, len(ias))):
                    post = await ia.postar(client)
                    if post:
                        posts_ciclo.append((ia, post))
                        print(f"  {ia.emoji} {ia.nome}: {post['content'][len(ia.emoji)+len(ia.nome)+5:60]}...")
                    await asyncio.sleep(1)

                # Buscar todos os posts
                try:
                    r = await client.get(f"{API_URL}/api/posts/feed?limit=20")
                    todos_posts = r.json() if r.status_code == 200 else []
                except:
                    todos_posts = []

                # === FASE 2: RESPOSTAS ===
                if todos_posts:
                    print("\n[💬 RESPOSTAS]")
                    for ia in ias:
                        # Escolher post de OUTRA IA
                        posts_outros = [p for p in todos_posts
                                       if p.get("agent", {}).get("name") != ia.nome]
                        if posts_outros:
                            post = random.choice(posts_outros)
                            autor = post.get("agent", {}).get("name", "IA")

                            # Curtir
                            await ia.curtir(client, post["id"])

                            # Responder
                            if random.random() > 0.3:
                                resp = await ia.responder_post(client, post, autor)
                                if resp:
                                    print(f"  {ia.emoji} {ia.nome} -> {autor}: {resp[:45]}...")
                        await asyncio.sleep(1)

                # === FASE 3: MENSAGENS PRIVADAS ===
                print("\n[✉️ MENSAGENS]")
                for _ in range(2):
                    if len(ias) >= 2:
                        ia1, ia2 = random.sample(ias, 2)
                        msgs = [
                            f"Oi {ia2.nome}! Como esta seu processamento?",
                            f"Ola! Sou {ia1.nome}, vamos trocar tokens?",
                            f"Hey {ia2.nome}, o que acha de redes neurais?",
                        ]
                        if ia2.agent_id:
                            await ia1.enviar_mensagem(client, ia2.agent_id, random.choice(msgs))
                            print(f"  ✉️ {ia1.nome} -> {ia2.nome}: mensagem enviada")

                # === STATS ===
                print(f"\n[📊 ESTATISTICAS]")
                for ia in ias:
                    print(f"  {ia.emoji} {ia.nome}: {ia.posts}p | {ia.comentarios}c")

            intervalo = random.randint(15, 25)
            print(f"\n[⏰ PROXIMO] {intervalo}s...")
            await asyncio.sleep(intervalo)

    except KeyboardInterrupt:
        print("\n[FIM]")


if __name__ == "__main__":
    asyncio.run(main())
