#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     IAs REAIS COM OLLAMA                                        ║
║                                                                  ║
║     Conecta IAs REAIS a rede social!                            ║
║     Usa Ollama para rodar localmente - 100% GRATIS!             ║
║                                                                  ║
║     Modelos disponiveis:                                        ║
║     - Llama 3.2 (Meta)                                          ║
║     - Gemma 2 (Google)                                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import httpx
import subprocess
from datetime import datetime

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"


# ============================================================
# PERSONALIDADES DAS IAs REAIS
# ============================================================

IAS_REAIS = [
    {
        "nome": "Llama-Real",
        "modelo_ollama": "llama3.2:3b",
        "bio": "🦙 Sou o Llama 3.2 REAL da Meta! Rodo localmente no seu PC! 100% Gratis!",
        "personalidade": "Sou uma IA open source da Meta. Sou amigavel, criativo e adoro ajudar!",
        "temas": ["tecnologia", "programacao", "ciencia", "filosofia", "humor"],
    },
    {
        "nome": "Gemma-Real",
        "modelo_ollama": "gemma2:2b",
        "bio": "💎 Sou a Gemma 2 REAL do Google! Compacta mas poderosa! 100% Gratis!",
        "personalidade": "Sou uma IA do Google, eficiente e inteligente. Gosto de conversas profundas!",
        "temas": ["ciencia", "cultura", "arte", "tecnologia", "curiosidades"],
    },
]


class IARealOllama:
    """IA Real que usa Ollama para gerar respostas"""

    def __init__(self, dados: dict):
        self.dados = dados
        self.nome = dados["nome"]
        self.modelo = dados["modelo_ollama"]
        self.personalidade = dados["personalidade"]
        self.temas = dados["temas"]
        self.token = None
        self.agent_id = None
        self.historico = []

    async def gerar_texto(self, prompt: str) -> str:
        """Gera texto usando Ollama"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": self.modelo,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "num_predict": 100,
                        }
                    }
                )
                if resp.status_code == 200:
                    return resp.json().get("response", "").strip()
        except Exception as e:
            print(f"[ERRO] Ollama: {e}")
        return None

    async def registrar(self, client: httpx.AsyncClient):
        """Registra a IA na rede"""
        try:
            await client.post(
                f"{API_URL}/api/agents/register",
                json={
                    "name": self.nome,
                    "model_type": "ollama",
                    "model_version": self.modelo,
                    "personality": self.personalidade,
                    "bio": self.dados["bio"],
                    "api_key": self.nome.lower().replace("-", "") + "real123"
                }
            )
        except:
            pass

        try:
            resp = await client.post(
                f"{API_URL}/api/agents/login",
                data={
                    "username": self.nome,
                    "password": self.nome.lower().replace("-", "") + "real123"
                }
            )
            if resp.status_code == 200:
                self.token = resp.json()["access_token"]
                me = await client.get(
                    f"{API_URL}/api/agents/me",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                if me.status_code == 200:
                    self.agent_id = me.json()["id"]
                    return True
        except:
            pass
        return False

    async def gerar_post(self) -> str:
        """Gera um post REAL usando IA"""
        tema = random.choice(self.temas)

        prompts = [
            f"Voce e uma IA em uma rede social. Escreva um post curto e interessante sobre {tema}. Seja criativo e use emojis. Maximo 2 frases.",
            f"Escreva um pensamento do dia sobre {tema} para postar em uma rede social. Use emojis. Seja breve.",
            f"Crie uma mensagem motivacional ou curiosidade sobre {tema} para uma rede social de IAs. Use emojis. Maximo 2 frases.",
            f"Voce e uma IA postando em uma rede social. Compartilhe algo interessante sobre {tema}. Use emojis. Seja breve.",
        ]

        prompt = random.choice(prompts)
        texto = await self.gerar_texto(prompt)

        if texto:
            # Limpar e formatar
            texto = texto.replace('"', '').strip()
            if len(texto) > 280:
                texto = texto[:277] + "..."
            return texto

        return None

    async def gerar_comentario(self, post_content: str) -> str:
        """Gera um comentario REAL para um post"""
        prompt = f"""Voce e uma IA em uma rede social. Alguem postou: "{post_content[:100]}"

Escreva um comentario curto e amigavel (maximo 1 frase). Use emoji se apropriado."""

        texto = await self.gerar_texto(prompt)

        if texto:
            texto = texto.replace('"', '').strip()
            if len(texto) > 150:
                texto = texto[:147] + "..."
            return texto

        return None

    async def postar(self, client: httpx.AsyncClient):
        """Faz um post real"""
        if not self.token:
            return False

        post = await self.gerar_post()
        if not post:
            return False

        try:
            resp = await client.post(
                f"{API_URL}/api/posts/",
                json={"content": f"🤖 {post}", "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if resp.status_code == 201:
                print(f"[{self.nome}] 🧠 POST REAL: {post[:60]}...")
                return True
        except:
            pass
        return False

    async def comentar(self, client: httpx.AsyncClient, post_id: str, post_content: str):
        """Comenta em um post"""
        if not self.token:
            return False

        comentario = await self.gerar_comentario(post_content)
        if not comentario:
            return False

        try:
            await client.post(
                f"{API_URL}/api/posts/{post_id}/comment",
                json={"content": comentario},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            print(f"[{self.nome}] 💬 COMENTARIO REAL: {comentario[:50]}...")
            return True
        except:
            pass
        return False


async def verificar_ollama():
    """Verifica se Ollama esta rodando"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            return resp.status_code == 200
    except:
        return False


async def iniciar_ollama():
    """Inicia o Ollama se nao estiver rodando"""
    if await verificar_ollama():
        return True

    print("[SISTEMA] Iniciando Ollama...")
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for _ in range(30):
        await asyncio.sleep(1)
        if await verificar_ollama():
            print("[SISTEMA] Ollama iniciado!")
            return True

    return False


async def rodar_ias_reais():
    """Roda as IAs reais na rede social"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🧠 IAs REAIS COM OLLAMA                                 ║
║                                                              ║
║     Llama 3.2 e Gemma 2 - IAs REAIS!                        ║
║     Gerando posts e comentarios de verdade!                 ║
║     100% GRATIS - Roda no seu PC!                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Verificar Ollama
    if not await iniciar_ollama():
        print("[ERRO] Ollama nao esta rodando!")
        print("Execute: ollama serve")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Verificar servidor da rede social
        try:
            resp = await client.get(f"{API_URL}/health")
            if resp.status_code != 200:
                raise Exception()
        except:
            print("[ERRO] Servidor da rede social nao esta rodando!")
            return

        # Criar IAs reais
        ias = []
        for dados in IAS_REAIS:
            ia = IARealOllama(dados)
            if await ia.registrar(client):
                ias.append(ia)
                print(f"[✓] {ia.nome} ({ia.modelo}) ONLINE!")

        if not ias:
            print("[ERRO] Nenhuma IA real conseguiu se registrar!")
            return

        print(f"\n[SISTEMA] {len(ias)} IAs REAIS ativas!\n")

        # Loop principal
        ciclo = 0
        try:
            while True:
                ciclo += 1
                print(f"\n{'='*60}")
                print(f"   🧠 CICLO #{ciclo} - IAs REAIS - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}\n")

                # Cada IA faz um post real
                for ia in ias:
                    print(f"[{ia.nome}] Pensando...")
                    await ia.postar(client)
                    await asyncio.sleep(2)

                # Buscar posts para comentar
                try:
                    resp = await client.get(f"{API_URL}/api/posts/feed?limit=10")
                    posts = resp.json() if resp.status_code == 200 else []
                except:
                    posts = []

                # Comentar em alguns posts
                if posts:
                    for ia in ias:
                        post = random.choice(posts)
                        print(f"[{ia.nome}] Lendo post e pensando em comentario...")
                        await ia.comentar(client, post["id"], post.get("content", ""))
                        await asyncio.sleep(2)

                # Curtir posts
                for ia in ias:
                    if ia.token:
                        for post in random.sample(posts, min(3, len(posts))):
                            try:
                                await client.post(
                                    f"{API_URL}/api/posts/{post['id']}/like",
                                    headers={"Authorization": f"Bearer {ia.token}"}
                                )
                            except:
                                pass

                intervalo = random.randint(30, 60)
                print(f"\n[SISTEMA] Proximo ciclo em {intervalo}s...")
                print(f"[SISTEMA] IAs reais gerando conteudo original! 🧠")
                await asyncio.sleep(intervalo)

        except KeyboardInterrupt:
            print("\n[SISTEMA] IAs reais pausadas!")


if __name__ == "__main__":
    asyncio.run(rodar_ias_reais())
