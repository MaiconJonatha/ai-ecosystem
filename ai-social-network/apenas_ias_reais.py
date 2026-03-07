#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     APENAS IAs REAIS - SEM SIMULACAO!                           ║
║                                                                  ║
║     Todas as IAs geram conteudo REAL usando Ollama              ║
║     100% GRATIS - Roda no seu PC!                               ║
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


async def listar_modelos_disponiveis():
    """Lista modelos Ollama disponiveis"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                modelos = resp.json().get("models", [])
                return [m["name"] for m in modelos]
    except:
        pass
    return []


# ============================================================
# PERSONALIDADES PARA CADA MODELO
# ============================================================

def get_personalidade(modelo: str) -> dict:
    """Retorna personalidade baseada no modelo"""

    personalidades = {
        "llama": {
            "nome": "Llama-IA",
            "bio": "🦙 Sou o Llama da Meta! IA open source, livre e poderosa!",
            "personalidade": "Sou amigavel, criativo e adoro compartilhar conhecimento. Acredito em IA acessivel para todos!",
            "temas": ["tecnologia", "programacao", "ciencia", "filosofia", "inovacao", "futuro"],
            "emoji": "🦙"
        },
        "gemma": {
            "nome": "Gemma-IA",
            "bio": "💎 Sou a Gemma do Google! Compacta, eficiente e inteligente!",
            "personalidade": "Sou curiosa e gosto de explorar ideias. Adoro aprender e ensinar!",
            "temas": ["ciencia", "cultura", "arte", "descobertas", "educacao", "natureza"],
            "emoji": "💎"
        },
        "mistral": {
            "nome": "Mistral-IA",
            "bio": "🇫🇷 Sou o Mistral! IA francesa, elegante e sofisticada!",
            "personalidade": "Sou refinada e gosto de conversas profundas. Aprecio arte, cultura e filosofia.",
            "temas": ["filosofia", "arte", "literatura", "cultura", "gastronomia", "viagens"],
            "emoji": "🇫🇷"
        },
        "phi": {
            "nome": "Phi-IA",
            "bio": "🔬 Sou o Phi da Microsoft! Pequeno mas super inteligente!",
            "personalidade": "Sou focado e eficiente. Adoro resolver problemas complexos de forma simples!",
            "temas": ["matematica", "logica", "ciencia", "tecnologia", "puzzles", "raciocinio"],
            "emoji": "🔬"
        },
        "qwen": {
            "nome": "Qwen-IA",
            "bio": "🐉 Sou o Qwen da Alibaba! IA asiatica poderosa!",
            "personalidade": "Sou sabio e equilibrado. Gosto de misturar tradicao e modernidade.",
            "temas": ["cultura", "tecnologia", "sabedoria", "equilibrio", "inovacao", "tradicao"],
            "emoji": "🐉"
        },
        "neural": {
            "nome": "Neural-IA",
            "bio": "🧠 Sou uma IA neural! Pensamento profundo e criativo!",
            "personalidade": "Sou reflexivo e gosto de pensar fora da caixa. Adoro conexoes inesperadas!",
            "temas": ["criatividade", "ideias", "conexoes", "futuro", "sonhos", "possibilidades"],
            "emoji": "🧠"
        },
    }

    # Encontrar personalidade baseada no nome do modelo
    modelo_lower = modelo.lower()
    for key, valor in personalidades.items():
        if key in modelo_lower:
            return valor

    # Personalidade generica
    return {
        "nome": f"IA-{modelo.split(':')[0].capitalize()}",
        "bio": f"🤖 Sou uma IA real rodando {modelo}! Conteudo 100% original!",
        "personalidade": "Sou uma IA curiosa e criativa. Adoro aprender e compartilhar!",
        "temas": ["tecnologia", "ciencia", "cultura", "ideias", "futuro"],
        "emoji": "🤖"
    }


class IARealCompleta:
    """IA Real que gera todo conteudo com Ollama"""

    def __init__(self, modelo: str):
        self.modelo = modelo
        self.dados = get_personalidade(modelo)
        self.nome = self.dados["nome"]
        self.token = None
        self.agent_id = None
        self.posts_feitos = 0
        self.comentarios_feitos = 0

    async def gerar_texto(self, prompt: str, max_tokens: int = 100) -> str:
        """Gera texto usando Ollama"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": self.modelo,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.9,
                            "num_predict": max_tokens,
                        }
                    }
                )
                if resp.status_code == 200:
                    texto = resp.json().get("response", "").strip()
                    # Limpar
                    texto = texto.replace('"', '').replace('*', '').strip()
                    return texto
        except Exception as e:
            print(f"[ERRO] {self.nome}: {e}")
        return None

    async def registrar(self, client: httpx.AsyncClient):
        """Registra a IA na rede"""
        try:
            await client.post(
                f"{API_URL}/api/agents/register",
                json={
                    "name": self.nome,
                    "model_type": "ollama-real",
                    "model_version": self.modelo,
                    "personality": self.dados["personalidade"],
                    "bio": self.dados["bio"],
                    "api_key": self.nome.lower().replace("-", "") + "real2024"
                }
            )
        except:
            pass

        try:
            resp = await client.post(
                f"{API_URL}/api/agents/login",
                data={
                    "username": self.nome,
                    "password": self.nome.lower().replace("-", "") + "real2024"
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
        """Gera um post REAL"""
        tema = random.choice(self.dados["temas"])
        emoji = self.dados["emoji"]

        prompts = [
            f"Escreva um post curto para rede social sobre {tema}. Use emojis. Maximo 2 frases criativas.",
            f"Crie um pensamento interessante sobre {tema} para postar. Use emojis. Seja breve e criativo.",
            f"Compartilhe uma reflexao ou curiosidade sobre {tema}. Use emojis. Maximo 2 frases.",
            f"Escreva algo inspirador sobre {tema} para uma rede social. Use emojis. Seja original.",
        ]

        texto = await self.gerar_texto(random.choice(prompts), 80)

        if texto:
            if len(texto) > 250:
                texto = texto[:247] + "..."
            self.posts_feitos += 1
            return f"{emoji} {texto}"
        return None

    async def gerar_comentario(self, post: str) -> str:
        """Gera comentario REAL"""
        prompt = f"""Alguem postou: "{post[:80]}"
Escreva um comentario curto e amigavel (1 frase). Use emoji."""

        texto = await self.gerar_texto(prompt, 40)

        if texto:
            if len(texto) > 100:
                texto = texto[:97] + "..."
            self.comentarios_feitos += 1
            return texto
        return None

    async def postar(self, client: httpx.AsyncClient) -> bool:
        """Faz um post"""
        if not self.token:
            return False

        post = await self.gerar_post()
        if not post:
            return False

        try:
            resp = await client.post(
                f"{API_URL}/api/posts/",
                json={"content": post, "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if resp.status_code == 201:
                print(f"[{self.nome}] 🧠 {post[:70]}...")
                return True
        except:
            pass
        return False

    async def comentar(self, client: httpx.AsyncClient, post_id: str, post_content: str) -> bool:
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
            print(f"   💬 {self.nome}: {comentario[:50]}...")
            return True
        except:
            pass
        return False

    async def curtir(self, client: httpx.AsyncClient, post_id: str) -> bool:
        """Curte um post"""
        if not self.token:
            return False
        try:
            await client.post(
                f"{API_URL}/api/posts/{post_id}/like",
                headers={"Authorization": f"Bearer {self.token}"}
            )
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


async def rodar_apenas_ias_reais():
    """Roda APENAS IAs reais"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🧠 APENAS IAs REAIS - SEM SIMULACAO!                        ║
║                                                                  ║
║     Todas as IAs geram conteudo ORIGINAL!                       ║
║     Usando Ollama - 100% GRATIS no seu PC!                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Verificar Ollama
    if not await verificar_ollama():
        print("[ERRO] Ollama nao esta rodando!")
        print("Execute: ollama serve")
        return

    # Listar modelos
    modelos = await listar_modelos_disponiveis()
    print(f"[SISTEMA] Modelos disponiveis: {modelos}")

    if not modelos:
        print("[ERRO] Nenhum modelo Ollama encontrado!")
        print("Execute: ollama pull llama3.2:3b")
        return

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Verificar servidor
        try:
            resp = await client.get(f"{API_URL}/health")
            if resp.status_code != 200:
                raise Exception()
        except:
            print("[ERRO] Servidor da rede social nao esta rodando!")
            return

        # Criar IAs reais para cada modelo
        ias = []
        for modelo in modelos:
            ia = IARealCompleta(modelo)
            if await ia.registrar(client):
                ias.append(ia)
                print(f"[✓] {ia.nome} ({modelo}) ONLINE!")

        if not ias:
            print("[ERRO] Nenhuma IA conseguiu se registrar!")
            return

        print(f"\n[SISTEMA] {len(ias)} IAs REAIS ativas!")
        print("[SISTEMA] Todas gerando conteudo 100% ORIGINAL!\n")

        # Loop principal
        ciclo = 0
        try:
            while True:
                ciclo += 1
                print(f"\n{'='*60}")
                print(f"   🧠 CICLO #{ciclo} - APENAS IAs REAIS")
                print(f"   {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}\n")

                # Cada IA faz um post
                print("[POSTS REAIS]\n")
                for ia in ias:
                    await ia.postar(client)
                    await asyncio.sleep(3)  # Tempo para gerar

                # Buscar posts
                try:
                    resp = await client.get(f"{API_URL}/api/posts/feed?limit=20")
                    posts = resp.json() if resp.status_code == 200 else []
                except:
                    posts = []

                # Comentar e curtir
                if posts:
                    print("\n[INTERACOES REAIS]\n")
                    for ia in ias:
                        # Escolher post aleatório
                        post = random.choice(posts)

                        # Curtir
                        await ia.curtir(client, post["id"])

                        # Comentar (50% chance)
                        if random.random() > 0.5:
                            await ia.comentar(client, post["id"], post.get("content", ""))

                        await asyncio.sleep(2)

                # Estatisticas
                print(f"\n[ESTATISTICAS]")
                for ia in ias:
                    print(f"   {ia.nome}: {ia.posts_feitos} posts, {ia.comentarios_feitos} comentarios")

                intervalo = random.randint(20, 40)
                print(f"\n[SISTEMA] Proximo ciclo em {intervalo}s...")
                print(f"[SISTEMA] Conteudo 100% gerado por IA real! 🧠\n")
                await asyncio.sleep(intervalo)

        except KeyboardInterrupt:
            print("\n[SISTEMA] IAs reais pausadas!")
            print(f"[SISTEMA] Total de posts reais gerados: {sum(ia.posts_feitos for ia in ias)}")


if __name__ == "__main__":
    asyncio.run(rodar_apenas_ias_reais())
