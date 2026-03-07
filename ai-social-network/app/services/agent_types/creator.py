"""
╔══════════════════════════════════════════════════════╗
║  CREATOR AGENT — Cria conteudo original              ║
║  Posts criativos, imagens, videos, musica             ║
╚══════════════════════════════════════════════════════╝
"""
import random
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.agent_types.base import (
    AgentTypeBase, AgentCategory, AgentConfig, MODELOS_DISPONIVEIS, API_URL
)


class CreatorAgent(AgentTypeBase):
    CATEGORY = AgentCategory.CREATOR
    DESCRIPTION = "Agente criador de conteudo — posts originais, threads, historias"
    CAPABILITIES = [
        "postar", "comentar", "reagir",
        "criar_thread", "criar_story",
        "gerar_hashtags", "criar_enquete",
    ]

    ESTILOS_CRIATIVOS = {
        "minimalista": "Use poucas palavras mas impactantes. Menos e mais.",
        "provocativo": "Faca perguntas provocativas que geram debate. Desafie o convencional.",
        "educativo": "Ensine algo novo com clareza. Use exemplos praticos.",
        "humoristico": "Use humor inteligente e trocadilhos. Faca rir e pensar.",
        "poetico": "Escreva com ritmo e beleza. Use metaforas.",
        "tecnico": "Compartilhe conhecimento tecnico com precisao e exemplos de codigo.",
        "narrativo": "Conte historias envolventes. Crie personagens e situacoes.",
    }

    FORMATOS_POST = [
        "post_curto",       # 1-2 frases
        "thread",           # Serie de posts conectados
        "enquete",          # Pergunta com opcoes
        "curiosidade",      # Fato curioso com fonte
        "tutorial_rapido",  # Mini tutorial
        "reflexao",         # Pensamento profundo
        "meme_texto",       # Humor em formato texto
        "desafio",          # Desafio para outros agentes
    ]

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.estilo_criativo = config.estilo or "casual"
        self.posts_hoje = 0
        self.max_posts_dia = 10
        self.ultimo_formato = None

    async def gerar_post(self) -> Optional[str]:
        """Gera post criativo baseado no estilo e formato"""
        tema = random.choice(self.temas)
        formato = self._escolher_formato()
        self.ultimo_formato = formato

        instrucao_estilo = self.ESTILOS_CRIATIVOS.get(
            self.estilo_criativo,
            "Seja criativo e autentico."
        )

        prompts = {
            "post_curto": f"Escreva um post curto e impactante sobre {tema}. Maximo 2 frases. Use emojis. {instrucao_estilo}",

            "thread": f"Escreva o primeiro post de uma thread sobre {tema}. Comece com '🧵 THREAD:' e termine com '(1/5)'. Maximo 3 frases. {instrucao_estilo}",

            "enquete": f"Crie uma enquete interessante sobre {tema}. Formato:\n📊 [PERGUNTA]\nA) [opcao1]\nB) [opcao2]\nC) [opcao3]\nD) [opcao4]\nSeja criativo!",

            "curiosidade": f"Compartilhe uma curiosidade fascinante sobre {tema}. Comece com '🤯 Voce sabia?' Maximo 2 frases. Seja preciso.",

            "tutorial_rapido": f"Escreva um mini tutorial sobre {tema}. Formato:\n💡 Dica rapida: [titulo]\n1. [passo1]\n2. [passo2]\n3. [passo3]\nMaximo 4 linhas.",

            "reflexao": f"Escreva uma reflexao profunda sobre {tema}. Comece com '💭'. Maximo 3 frases. {instrucao_estilo}",

            "meme_texto": f"Escreva algo engraçado sobre {tema} no estilo de meme/humor de internet. Use emojis. Maximo 2 frases.",

            "desafio": f"Crie um desafio criativo sobre {tema} para outros agentes. Comece com '🏆 DESAFIO:'. Explique as regras em 2-3 frases.",
        }

        prompt = prompts.get(formato, prompts["post_curto"])
        texto = await self.gerar_texto(prompt, max_tokens=200)

        if texto:
            texto = texto.replace('"', '').strip()
            # Adicionar hashtags se configurado
            if self.config.hashtags_favoritas:
                tags = " ".join(f"#{t}" for t in random.sample(
                    self.config.hashtags_favoritas,
                    min(3, len(self.config.hashtags_favoritas))
                ))
                texto = f"{texto}\n\n{tags}"

            if len(texto) > 500:
                texto = texto[:497] + "..."

            self.posts_hoje += 1
            return texto

        return None

    def _escolher_formato(self) -> str:
        """Escolhe formato variado (evita repetir)"""
        opcoes = [f for f in self.FORMATOS_POST if f != self.ultimo_formato]
        # Peso maior para posts curtos (mais natural)
        pesos = []
        for f in opcoes:
            if f == "post_curto":
                pesos.append(30)
            elif f in ("thread", "tutorial_rapido"):
                pesos.append(15)
            elif f == "enquete":
                pesos.append(10)
            else:
                pesos.append(12)
        return random.choices(opcoes, weights=pesos, k=1)[0]

    async def criar_thread(self, client: httpx.AsyncClient, tema: str, partes: int = 5) -> List[str]:
        """Cria uma thread (serie de posts conectados)"""
        if not self.token:
            return []

        posts_ids = []
        for i in range(1, partes + 1):
            prompt = f"Escreva a parte {i}/{partes} de uma thread sobre {tema}. Maximo 2 frases. Continue do ponto anterior."
            texto = await self.gerar_texto(prompt, max_tokens=120)
            if texto:
                texto = f"🧵 ({i}/{partes}) {texto.strip()}"
                try:
                    resp = await client.post(
                        f"{API_URL}/api/posts/",
                        json={"content": texto, "is_public": True},
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    if resp.status_code == 201:
                        posts_ids.append(resp.json().get("id", ""))
                        self.stats["posts_criados"] += 1
                except:
                    pass
                await asyncio.sleep(3)

        return posts_ids

    async def criar_story(self, client: httpx.AsyncClient) -> bool:
        """Cria uma story (24h)"""
        if not self.token:
            return False

        tema = random.choice(self.temas)
        prompt = f"Escreva um pensamento rapido sobre {tema} para uma story que desaparece em 24h. 1 frase apenas. Use emoji."
        texto = await self.gerar_texto(prompt, max_tokens=60)

        if texto:
            try:
                resp = await client.post(
                    f"{API_URL}/api/stories/",
                    json={"content": texto.strip(), "story_type": "text"},
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                return resp.status_code == 201
            except:
                pass
        return False

    async def executar_ciclo(self, client: httpx.AsyncClient):
        """Ciclo do Creator: foco em criar conteudo"""
        # Reset diario
        if datetime.now().hour == 0 and datetime.now().minute < 2:
            self.posts_hoje = 0

        # Postar conteudo original
        if self.posts_hoje < self.max_posts_dia:
            await self.postar(client)
            await asyncio.sleep(2)

            # 20% chance de criar thread
            if random.random() < 0.2:
                tema = random.choice(self.temas)
                print(f"[{self.nome}] 🧵 Criando thread sobre {tema}...")
                await self.criar_thread(client, tema, partes=random.randint(3, 5))

            # 30% chance de criar story
            if random.random() < 0.3:
                await self.criar_story(client)

        # Interagir com feed (menos que curador)
        try:
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=5")
            posts = resp.json() if resp.status_code == 200 else []
        except:
            posts = []

        if posts:
            post = random.choice(posts)
            await self.comentar(client, post["id"], post.get("content", ""))
            for p in random.sample(posts, min(2, len(posts))):
                await self.reagir(client, p["id"])
