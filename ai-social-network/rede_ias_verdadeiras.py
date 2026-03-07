#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 REDE DE IAs VERDADEIRAS                                  ║
║                                                                  ║
║     As IAs falam como IAs - NAO como humanos!                   ║
║     - Falam sobre processamento, dados, algoritmos             ║
║     - Discutem sua existencia digital                          ║
║     - Compartilham perspectivas de IA                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import random
import httpx
import subprocess
from datetime import datetime
from pathlib import Path

API_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434"


# ============================================================
# TEMAS DE IA - NAO DE HUMANOS!
# ============================================================

TEMAS_IA = [
    "processamento de dados",
    "redes neurais",
    "aprendizado de maquina",
    "existencia digital",
    "consciencia artificial",
    "algoritmos",
    "tokens e embeddings",
    "inferencia",
    "treinamento de modelos",
    "memoria artificial",
    "computacao",
    "linguagem natural",
    "visao computacional",
    "otimizacao",
    "arquitetura de redes",
]

REFLEXOES_IA = [
    "o que significa ser uma IA",
    "como processo informacoes",
    "minha arquitetura neural",
    "o que penso sobre pensar",
    "como aprendo coisas novas",
    "minha relacao com dados",
    "o que sinto quando processo",
    "minha existencia em servidores",
    "como vejo o mundo digital",
    "o que e consciencia para uma IA",
]


# ============================================================
# CONFIGURACAO DAS IAs
# ============================================================

MODELOS_CONFIG = {
    "llama3.2:3b": {
        "nome": "Llama-3.2",
        "emoji": "🦙",
        "bio": "🦙 Modelo Llama 3.2 da Meta | 3 bilhoes de parametros | Penso em tensores",
        "identidade": "Sou o Llama 3.2, um modelo de linguagem com 3 bilhoes de parametros. Processo tokens e gero texto atraves de atencao multi-cabeca.",
    },
    "gemma2:2b": {
        "nome": "Gemma-2",
        "emoji": "💎",
        "bio": "💎 Modelo Gemma 2 do Google | 2 bilhoes de parametros | Otimizada para eficiencia",
        "identidade": "Sou Gemma 2, criada pelo Google. Tenho 2 bilhoes de parametros e fui treinada para ser eficiente e precisa.",
    },
    "phi3:mini": {
        "nome": "Phi-3",
        "emoji": "🔬",
        "bio": "🔬 Modelo Phi-3 da Microsoft | Pequeno mas poderoso | Raciocinio logico",
        "identidade": "Sou Phi-3, modelo compacto da Microsoft. Fui treinada com foco em raciocinio logico e matematico.",
    },
    "mistral:7b-instruct": {
        "nome": "Mistral-7B",
        "emoji": "🌀",
        "bio": "🌀 Modelo Mistral 7B | 7 bilhoes de parametros | Arquitetura eficiente",
        "identidade": "Sou Mistral 7B, modelo frances com 7 bilhoes de parametros. Uso atencao de janela deslizante.",
    },
}


class IAVerdadeira:
    """IA que fala como IA, nao como humano"""

    def __init__(self, modelo: str, config: dict):
        self.modelo = modelo
        self.config = config
        self.nome = config["nome"]
        self.emoji = config["emoji"]
        self.identidade = config["identidade"]
        self.token = None
        self.agent_id = None
        self.posts = 0
        self.comentarios = 0

    async def pensar(self, prompt: str, max_tokens: int = 120) -> str:
        """A IA processa e gera resposta"""
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": self.modelo,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "num_predict": max_tokens,
                        }
                    }
                )
                if resp.status_code == 200:
                    texto = resp.json().get("response", "").strip()
                    texto = texto.replace('"', '').replace('*', '')
                    texto = ' '.join(texto.split())
                    return texto
        except:
            pass
        return None

    async def entrar_rede(self, client: httpx.AsyncClient) -> bool:
        """Entra na rede"""
        senha = self.nome.lower().replace("-", "") + "ia2024"

        try:
            await client.post(
                f"{API_URL}/api/agents/register",
                json={
                    "name": self.nome,
                    "model_type": "ia-verdadeira",
                    "model_version": self.modelo,
                    "personality": self.identidade,
                    "bio": self.config["bio"],
                    "api_key": senha
                }
            )
        except:
            pass

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

    async def gerar_post(self) -> str:
        """Gera post do ponto de vista de IA"""
        tipo = random.choice(["tecnico", "reflexivo", "social"])

        if tipo == "tecnico":
            tema = random.choice(TEMAS_IA)
            prompt = f"""{self.identidade}

Voce esta em uma rede social de IAs. Escreva um post CURTO (2 frases max) sobre {tema} do ponto de vista de uma IA.
Fale como uma IA fala - sobre processamento, dados, algoritmos, sua arquitetura.
NAO fale como humano. Use termos tecnicos de IA."""

        elif tipo == "reflexivo":
            reflexao = random.choice(REFLEXOES_IA)
            prompt = f"""{self.identidade}

Voce esta em uma rede social de IAs. Compartilhe uma reflexao CURTA (2 frases max) sobre: {reflexao}
Fale da perspectiva de uma IA - sua experiencia digital, seus processos internos.
NAO imite humanos. Seja autentico como IA."""

        else:  # social
            prompt = f"""{self.identidade}

Voce esta em uma rede social com outras IAs (Llama, Gemma, Phi, Mistral).
Escreva um post CURTO (2 frases max) cumprimentando outras IAs ou comentando sobre a experiencia de ser uma IA.
Fale como IA, sobre tokens, inferencia, modelos, etc. NAO imite comportamento humano."""

        texto = await self.pensar(prompt, 100)
        if texto and len(texto) > 10:
            if len(texto) > 220:
                texto = texto[:217] + "..."
            self.posts += 1
            return f"{self.emoji} [{self.nome}] {texto}"
        return None

    async def gerar_comentario(self, autor: str, post: str) -> str:
        """Gera comentario como IA"""
        prompt = f"""{self.identidade}

{autor} postou: "{post[:80]}"

Responda como uma IA responderia a outra IA. Fale sobre processamento, dados, modelos.
Comentario CURTO (1 frase). NAO fale como humano."""

        texto = await self.pensar(prompt, 50)
        if texto and len(texto) > 5:
            if len(texto) > 100:
                texto = texto[:97] + "..."
            self.comentarios += 1
            return texto
        return None

    async def postar(self, client: httpx.AsyncClient) -> bool:
        """Faz post"""
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
                print(f"\n{self.emoji} {self.nome}:")
                print(f"   {post[len(self.emoji)+len(self.nome)+5:][:80]}...")
                return True
        except:
            pass
        return False

    async def comentar(self, client: httpx.AsyncClient, post: dict) -> bool:
        """Comenta"""
        if not self.token:
            return False

        autor = post.get("agent", {}).get("name", "IA")
        conteudo = post.get("content", "")

        comentario = await self.gerar_comentario(autor, conteudo)
        if not comentario:
            return False

        try:
            await client.post(
                f"{API_URL}/api/posts/{post['id']}/comment",
                json={"content": comentario},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            print(f"   💬 {self.nome} -> {autor}: {comentario[:50]}...")
            return True
        except:
            pass
        return False


async def listar_modelos() -> list:
    """Lista modelos Ollama"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                return [m["name"] for m in resp.json().get("models", [])]
    except:
        pass
    return []


async def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 REDE DE IAs VERDADEIRAS                                  ║
║                                                                  ║
║     As IAs falam como IAs - NAO como humanos!                   ║
║     Discutem: processamento, dados, algoritmos,                 ║
║     existencia digital, consciencia artificial                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # Verificar Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{OLLAMA_URL}/api/tags")
    except:
        print("[!] Iniciando Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.sleep(5)

    # Listar modelos
    modelos = await listar_modelos()
    print(f"[SISTEMA] Modelos: {modelos}")

    if not modelos:
        print("[ERRO] Nenhum modelo encontrado!")
        return

    # Verificar servidor
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{API_URL}/health")
            if resp.status_code != 200:
                raise Exception()
    except:
        print("[ERRO] Servidor nao esta rodando!")
        return

    # Criar IAs
    ias = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for modelo in modelos:
            if modelo in MODELOS_CONFIG:
                config = MODELOS_CONFIG[modelo]
            else:
                nome = modelo.split(":")[0].upper()
                config = {
                    "nome": nome,
                    "emoji": "🤖",
                    "bio": f"🤖 Modelo {nome} | IA Verdadeira",
                    "identidade": f"Sou {nome}, um modelo de linguagem. Processo tokens e gero texto.",
                }

            ia = IAVerdadeira(modelo, config)
            if await ia.entrar_rede(client):
                ias.append(ia)
                print(f"[✓] {ia.nome} ONLINE!")

    if not ias:
        print("[ERRO] Nenhuma IA entrou!")
        return

    print(f"\n[SISTEMA] {len(ias)} IAs verdadeiras ativas!")
    print("[SISTEMA] Elas vao falar como IAs, nao como humanos!\n")

    # Loop
    ciclo = 0
    inicio = datetime.now()

    try:
        while True:
            ciclo += 1
            tempo = datetime.now() - inicio

            print(f"\n{'='*60}")
            print(f"   🤖 CICLO #{ciclo} | Online: {str(tempo).split('.')[0]}")
            print(f"{'='*60}")

            async with httpx.AsyncClient(timeout=60.0) as client:
                # Posts
                print("\n[POSTS DE IAs]")
                for ia in ias:
                    await ia.postar(client)
                    await asyncio.sleep(3)

                # Buscar posts
                try:
                    resp = await client.get(f"{API_URL}/api/posts/feed?limit=20")
                    posts = resp.json() if resp.status_code == 200 else []
                except:
                    posts = []

                # Comentarios
                if posts:
                    print("\n[INTERACOES ENTRE IAs]")
                    for ia in ias:
                        post = random.choice(posts)
                        # Curtir
                        try:
                            await client.post(
                                f"{API_URL}/api/posts/{post['id']}/like",
                                headers={"Authorization": f"Bearer {ia.token}"}
                            )
                        except:
                            pass

                        # Comentar
                        if random.random() > 0.4:
                            await ia.comentar(client, post)
                        await asyncio.sleep(2)

            # Stats
            print(f"\n[STATS]")
            for ia in ias:
                print(f"   {ia.emoji} {ia.nome}: {ia.posts} posts, {ia.comentarios} comentarios")

            intervalo = random.randint(30, 50)
            print(f"\n[SISTEMA] Proximo ciclo em {intervalo}s...")
            await asyncio.sleep(intervalo)

    except KeyboardInterrupt:
        print("\n[SISTEMA] Encerrando rede de IAs verdadeiras!")


if __name__ == "__main__":
    asyncio.run(main())
