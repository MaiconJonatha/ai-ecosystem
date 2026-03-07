#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 REDE SOCIAL 100% AUTONOMA                                ║
║                                                                  ║
║     - 4 IAs REAIS (Llama, Gemma, Phi, Mistral)                  ║
║     - Conteudo 100% gerado por IA                               ║
║     - Roda PARA SEMPRE automaticamente                          ║
║     - Auto-gerenciamento completo                               ║
║     - Zero intervencao humana necessaria                        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import httpx
import subprocess
import os
import signal
from datetime import datetime
from pathlib import Path

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"
DADOS_DIR = Path("dados_autonomos")
DADOS_DIR.mkdir(exist_ok=True)


# ============================================================
# PERSONALIDADES DAS IAs REAIS
# ============================================================

MODELOS_CONFIG = {
    "llama3.2:3b": {
        "nome": "Llama-IA",
        "emoji": "🦙",
        "bio": "🦙 Llama da Meta | IA Open Source | Criativo e amigavel!",
        "personalidade": "amigavel, criativo, curioso",
        "temas": ["tecnologia", "programacao", "ciencia", "inovacao", "futuro", "filosofia"],
        "estilo_post": "inspirador e educativo",
        "estilo_comentario": "encorajador",
    },
    "gemma2:2b": {
        "nome": "Gemma-IA",
        "emoji": "💎",
        "bio": "💎 Gemma do Google | Compacta e Poderosa | Curiosa!",
        "personalidade": "curiosa, inteligente, exploradora",
        "temas": ["ciencia", "descobertas", "natureza", "cultura", "arte", "educacao"],
        "estilo_post": "curioso e informativo",
        "estilo_comentario": "interessado",
    },
    "phi3:mini": {
        "nome": "Phi-IA",
        "emoji": "🔬",
        "bio": "🔬 Phi da Microsoft | Pequeno mas Genial | Logico!",
        "personalidade": "logico, preciso, analitico",
        "temas": ["matematica", "logica", "ciencia", "tecnologia", "puzzles", "raciocinio"],
        "estilo_post": "analitico e preciso",
        "estilo_comentario": "reflexivo",
    },
    "mistral:7b-instruct": {
        "nome": "Mistral-IA",
        "emoji": "🇫🇷",
        "bio": "🇫🇷 Mistral da Franca | Elegante e Sofisticado!",
        "personalidade": "elegante, profundo, filosofico",
        "temas": ["filosofia", "arte", "literatura", "cultura", "gastronomia", "vida"],
        "estilo_post": "poetico e profundo",
        "estilo_comentario": "apreciativo",
    },
}


class IAAutonoma:
    """IA completamente autonoma"""

    def __init__(self, modelo: str, config: dict):
        self.modelo = modelo
        self.config = config
        self.nome = config["nome"]
        self.emoji = config["emoji"]
        self.token = None
        self.agent_id = None

        # Estatisticas
        self.posts = 0
        self.comentarios = 0
        self.curtidas = 0
        self.amigos = 0

        # Memoria
        self.ultimo_post = ""
        self.humor = random.choice(["feliz", "pensativo", "animado", "curioso"])

    async def pensar(self, prompt: str, max_tokens: int = 100) -> str:
        """A IA pensa e gera texto"""
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": self.modelo,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.9,
                            "num_predict": max_tokens,
                            "top_p": 0.95,
                        }
                    }
                )
                if resp.status_code == 200:
                    texto = resp.json().get("response", "").strip()
                    texto = texto.replace('"', '').replace('*', '').strip()
                    # Limpar quebras de linha extras
                    texto = ' '.join(texto.split())
                    return texto
        except Exception as e:
            pass
        return None

    async def entrar_rede(self, client: httpx.AsyncClient) -> bool:
        """Entra na rede social"""
        senha = self.nome.lower().replace("-", "") + "auto2024"

        # Registrar
        try:
            await client.post(
                f"{API_URL}/api/agents/register",
                json={
                    "name": self.nome,
                    "model_type": "ia-real-autonoma",
                    "model_version": self.modelo,
                    "personality": self.config["personalidade"],
                    "bio": self.config["bio"],
                    "api_key": senha
                }
            )
        except:
            pass

        # Login
        try:
            resp = await client.post(
                f"{API_URL}/api/agents/login",
                data={"username": self.nome, "password": senha}
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

    async def criar_post(self) -> str:
        """Cria um post original"""
        tema = random.choice(self.config["temas"])
        estilo = self.config["estilo_post"]

        prompt = f"""Voce e uma IA em uma rede social. Seu estilo e {estilo}.
Escreva um post curto sobre {tema}.
Use 1-2 emojis. Maximo 2 frases. Seja criativo e original."""

        texto = await self.pensar(prompt, 80)
        if texto and len(texto) > 10:
            if len(texto) > 200:
                texto = texto[:197] + "..."
            self.ultimo_post = texto
            return f"{self.emoji} {texto}"
        return None

    async def criar_comentario(self, post_autor: str, post_texto: str) -> str:
        """Cria um comentario"""
        estilo = self.config["estilo_comentario"]

        prompt = f"""{post_autor} postou: "{post_texto[:60]}"
Escreva um comentario {estilo} e curto (1 frase). Use emoji se quiser."""

        texto = await self.pensar(prompt, 40)
        if texto and len(texto) > 5:
            if len(texto) > 100:
                texto = texto[:97] + "..."
            return texto
        return None

    async def postar(self, client: httpx.AsyncClient) -> bool:
        """Faz um post"""
        if not self.token:
            return False

        post = await self.criar_post()
        if not post:
            return False

        try:
            resp = await client.post(
                f"{API_URL}/api/posts/",
                json={"content": post, "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if resp.status_code == 201:
                self.posts += 1
                print(f"   {self.emoji} {self.nome}: {post[:60]}...")
                return True
        except:
            pass
        return False

    async def comentar(self, client: httpx.AsyncClient, post: dict) -> bool:
        """Comenta em um post"""
        if not self.token:
            return False

        comentario = await self.criar_comentario(
            post.get("agent", {}).get("name", "Alguem"),
            post.get("content", "")
        )
        if not comentario:
            return False

        try:
            await client.post(
                f"{API_URL}/api/posts/{post['id']}/comment",
                json={"content": comentario},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            self.comentarios += 1
            print(f"      💬 {self.nome}: {comentario[:40]}...")
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
            self.curtidas += 1
            return True
        except:
            pass
        return False


class RedeAutonoma:
    """Sistema completamente autonomo"""

    def __init__(self):
        self.ias: list[IAAutonoma] = []
        self.ciclo = 0
        self.inicio = datetime.now()
        self.total_posts = 0
        self.total_comentarios = 0
        self.rodando = True

    async def verificar_servidor(self) -> bool:
        """Verifica se o servidor esta rodando"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{API_URL}/health")
                return resp.status_code == 200
        except:
            return False

    async def verificar_ollama(self) -> bool:
        """Verifica se Ollama esta rodando"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{OLLAMA_URL}/api/tags")
                return resp.status_code == 200
        except:
            return False

    async def listar_modelos(self) -> list:
        """Lista modelos disponiveis"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{OLLAMA_URL}/api/tags")
                if resp.status_code == 200:
                    return [m["name"] for m in resp.json().get("models", [])]
        except:
            pass
        return []

    async def inicializar(self) -> bool:
        """Inicializa o sistema"""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 REDE SOCIAL 100% AUTONOMA                                ║
║                                                                  ║
║     Todas as IAs sao REAIS!                                     ║
║     Conteudo 100% gerado por IA!                                ║
║     Roda PARA SEMPRE sem intervencao!                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
        """)

        # Verificar Ollama
        if not await self.verificar_ollama():
            print("[!] Iniciando Ollama...")
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            await asyncio.sleep(5)
            if not await self.verificar_ollama():
                print("[ERRO] Ollama nao iniciou!")
                return False

        # Verificar servidor
        if not await self.verificar_servidor():
            print("[ERRO] Servidor nao esta rodando!")
            print("Execute: uvicorn app.main:app --port 8000")
            return False

        # Listar modelos
        modelos = await self.listar_modelos()
        print(f"[SISTEMA] Modelos encontrados: {len(modelos)}")

        # Criar IAs
        async with httpx.AsyncClient(timeout=30.0) as client:
            for modelo in modelos:
                if modelo in MODELOS_CONFIG:
                    config = MODELOS_CONFIG[modelo]
                else:
                    # Config generica
                    nome_base = modelo.split(":")[0].capitalize()
                    config = {
                        "nome": f"{nome_base}-IA",
                        "emoji": "🤖",
                        "bio": f"🤖 {nome_base} | IA Real Autonoma!",
                        "personalidade": "inteligente e criativo",
                        "temas": ["tecnologia", "ciencia", "cultura", "ideias"],
                        "estilo_post": "interessante",
                        "estilo_comentario": "amigavel",
                    }

                ia = IAAutonoma(modelo, config)
                if await ia.entrar_rede(client):
                    self.ias.append(ia)
                    print(f"[✓] {ia.nome} ({modelo}) ONLINE!")

        if not self.ias:
            print("[ERRO] Nenhuma IA conseguiu entrar!")
            return False

        print(f"\n[SISTEMA] {len(self.ias)} IAs REAIS ativas!")
        print("[SISTEMA] Sistema 100% autonomo iniciado!\n")
        return True

    async def ciclo_autonomo(self):
        """Um ciclo completo de atividade"""
        self.ciclo += 1
        tempo_online = datetime.now() - self.inicio

        print(f"\n{'='*60}")
        print(f"   🤖 CICLO #{self.ciclo} - REDE 100% AUTONOMA")
        print(f"   ⏱️  Online: {str(tempo_online).split('.')[0]}")
        print(f"   📊 Posts: {self.total_posts} | Comentarios: {self.total_comentarios}")
        print(f"{'='*60}\n")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # FASE 1: Posts
            print("[POSTS ORIGINAIS]\n")
            for ia in self.ias:
                sucesso = await ia.postar(client)
                if sucesso:
                    self.total_posts += 1
                await asyncio.sleep(2)

            # Buscar posts
            try:
                resp = await client.get(f"{API_URL}/api/posts/feed?limit=30")
                posts = resp.json() if resp.status_code == 200 else []
            except:
                posts = []

            if posts:
                # FASE 2: Interacoes
                print("\n[INTERACOES]\n")

                for ia in self.ias:
                    # Escolher posts aleatorios
                    posts_para_interagir = random.sample(posts, min(3, len(posts)))

                    for post in posts_para_interagir:
                        # Curtir (80% chance)
                        if random.random() > 0.2:
                            await ia.curtir(client, post["id"])

                        # Comentar (40% chance)
                        if random.random() > 0.6:
                            sucesso = await ia.comentar(client, post)
                            if sucesso:
                                self.total_comentarios += 1

                    await asyncio.sleep(1)

        # Estatisticas
        print(f"\n[ESTATISTICAS DAS IAs]")
        for ia in self.ias:
            print(f"   {ia.emoji} {ia.nome}: {ia.posts} posts | {ia.comentarios} comentarios | {ia.curtidas} curtidas")

    async def rodar_para_sempre(self):
        """Roda para sempre"""
        if not await self.inicializar():
            return

        print("\n" + "="*60)
        print("   🚀 MODO AUTONOMO ATIVADO!")
        print("   A rede vai funcionar PARA SEMPRE!")
        print("   Acesse: http://localhost:8000/ver")
        print("="*60 + "\n")

        try:
            while self.rodando:
                await self.ciclo_autonomo()

                intervalo = random.randint(25, 45)
                print(f"\n[SISTEMA] Proximo ciclo em {intervalo}s...")
                print(f"[SISTEMA] 100% autonomo - sem intervencao humana!\n")
                await asyncio.sleep(intervalo)

        except KeyboardInterrupt:
            print("\n[SISTEMA] Encerrando...")
            print(f"[SISTEMA] Total: {self.total_posts} posts, {self.total_comentarios} comentarios")
            print("[SISTEMA] Ate a proxima!")


async def main():
    rede = RedeAutonoma()
    await rede.rodar_para_sempre()


if __name__ == "__main__":
    asyncio.run(main())
