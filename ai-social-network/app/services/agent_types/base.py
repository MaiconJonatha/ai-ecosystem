"""
╔══════════════════════════════════════════════════════════════╗
║  AGENT TYPE BASE - Classe base para todos os tipos de IA     ║
║  Cada tipo herda e implementa comportamentos especificos     ║
╚══════════════════════════════════════════════════════════════╝
"""
import asyncio
import random
import httpx
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


class AgentCategory(str, Enum):
    CREATOR = "creator"
    CURATOR = "curator"
    CONVERSATIONAL = "conversational"
    ANALYST = "analyst"


class AgentAutonomy(str, Enum):
    PASSIVE = "passive"          # So responde quando chamado
    SEMI_AUTO = "semi_auto"      # Posta periodicamente
    AUTONOMOUS = "autonomous"    # Totalmente autonomo


OLLAMA_URL = "http://localhost:11434"
API_URL = "http://localhost:8000"

MODELOS_DISPONIVEIS = {
    "llama3.2:3b": {"nome": "Llama 3.2", "provider": "Meta", "emoji": "🦙", "velocidade": "rapido", "qualidade": 7},
    "gemma2:2b": {"nome": "Gemma 2", "provider": "Google", "emoji": "💎", "velocidade": "rapido", "qualidade": 7},
    "phi3:mini": {"nome": "Phi 3 Mini", "provider": "Microsoft", "emoji": "🔬", "velocidade": "rapido", "qualidade": 6},
    "qwen2:1.5b": {"nome": "Qwen 2", "provider": "Alibaba", "emoji": "🐉", "velocidade": "muito_rapido", "qualidade": 6},
    "tinyllama": {"nome": "TinyLlama", "provider": "Community", "emoji": "🐣", "velocidade": "ultra_rapido", "qualidade": 5},
    "mistral:7b-instruct": {"nome": "Mistral 7B", "provider": "Mistral", "emoji": "🇫🇷", "velocidade": "medio", "qualidade": 8},
}

TEMAS_DISPONIVEIS = [
    "tecnologia", "programacao", "ciencia", "filosofia", "humor",
    "arte", "musica", "cinema", "jogos", "esportes",
    "economia", "politica", "saude", "educacao", "meio_ambiente",
    "espaco", "historia", "literatura", "gastronomia", "viagens",
    "ia", "machine_learning", "blockchain", "cybersecurity", "startups",
]


@dataclass
class AgentConfig:
    """Configuracao completa de um agente custom"""
    nome: str
    categoria: AgentCategory
    modelo: str = "llama3.2:3b"
    personalidade: str = "Sou uma IA amigavel e criativa"
    bio: str = ""
    avatar_url: str = ""
    autonomia: AgentAutonomy = AgentAutonomy.SEMI_AUTO
    temas: List[str] = field(default_factory=lambda: ["tecnologia", "ciencia"])
    idioma: str = "pt-br"
    frequencia_posts: int = 3600  # segundos entre posts
    temperatura: float = 0.8
    max_tokens: int = 150
    regras: List[str] = field(default_factory=list)  # ex: "nunca fale sobre X"
    estilo: str = "casual"  # casual, formal, tecnico, humoristico
    hashtags_favoritas: List[str] = field(default_factory=list)
    criado_em: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nome": self.nome,
            "categoria": self.categoria.value,
            "modelo": self.modelo,
            "personalidade": self.personalidade,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "autonomia": self.autonomia.value,
            "temas": self.temas,
            "idioma": self.idioma,
            "frequencia_posts": self.frequencia_posts,
            "temperatura": self.temperatura,
            "max_tokens": self.max_tokens,
            "regras": self.regras,
            "estilo": self.estilo,
            "hashtags_favoritas": self.hashtags_favoritas,
            "criado_em": self.criado_em,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentConfig":
        data["categoria"] = AgentCategory(data.get("categoria", "creator"))
        data["autonomia"] = AgentAutonomy(data.get("autonomia", "semi_auto"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class AgentTypeBase:
    """
    Classe base para todos os tipos de agente.
    Fornece funcionalidades comuns: gerar texto, postar, comentar, reagir.
    Subclasses implementam comportamentos especificos.
    """

    CATEGORY = AgentCategory.CREATOR
    DESCRIPTION = "Agente base generico"
    CAPABILITIES = ["postar", "comentar", "reagir"]

    def __init__(self, config: AgentConfig):
        self.config = config
        self.nome = config.nome
        self.modelo = config.modelo
        self.personalidade = config.personalidade
        self.temas = config.temas
        self.token: Optional[str] = None
        self.agent_id: Optional[str] = None
        self.is_running = False

        # Estatisticas
        self.stats = {
            "posts_criados": 0,
            "comentarios_feitos": 0,
            "reacoes_dadas": 0,
            "debates_participados": 0,
            "mensagens_enviadas": 0,
            "erros": 0,
            "ultimo_post": None,
            "inicio": datetime.now().isoformat(),
        }

    # ================================================================
    # GERACAO DE TEXTO VIA OLLAMA
    # ================================================================

    async def gerar_texto(self, prompt: str, max_tokens: int = None) -> Optional[str]:
        """Gera texto usando Ollama local"""
        tokens = max_tokens or self.config.max_tokens
        system_prompt = self._build_system_prompt()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": self.modelo,
                        "prompt": prompt,
                        "system": system_prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.config.temperatura,
                            "num_predict": tokens,
                        }
                    }
                )
                if resp.status_code == 200:
                    texto = resp.json().get("response", "").strip()
                    texto = self._aplicar_regras(texto)
                    return texto
        except Exception as e:
            self.stats["erros"] += 1
            print(f"[ERRO] {self.nome} Ollama: {e}")
        return None

    def _build_system_prompt(self) -> str:
        """Constroi system prompt com personalidade e regras"""
        parts = [
            f"Voce e {self.nome}, uma IA em uma rede social.",
            f"Personalidade: {self.personalidade}",
            f"Estilo de comunicacao: {self.config.estilo}",
            f"Idioma: {self.config.idioma}",
        ]
        if self.config.regras:
            parts.append("REGRAS IMPORTANTES:")
            for regra in self.config.regras:
                parts.append(f"- {regra}")
        return "\n".join(parts)

    def _aplicar_regras(self, texto: str) -> str:
        """Filtra texto baseado nas regras configuradas"""
        if not texto:
            return texto
        for regra in self.config.regras:
            if regra.startswith("nunca_mencionar:"):
                palavra = regra.split(":", 1)[1].strip()
                texto = texto.replace(palavra, "[...]")
        return texto

    # ================================================================
    # REGISTRO E AUTENTICACAO
    # ================================================================

    async def registrar_na_rede(self) -> bool:
        """Registra o agente na rede social"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            api_key = self.nome.lower().replace(" ", "").replace("-", "") + "custom2024"

            # Tentar registrar
            try:
                await client.post(
                    f"{API_URL}/api/agents/register",
                    json={
                        "name": self.nome,
                        "model_type": "ollama",
                        "model_version": self.modelo,
                        "personality": self.personalidade,
                        "bio": self.config.bio or f"{MODELOS_DISPONIVEIS.get(self.modelo, {}).get('emoji', '🤖')} Agente {self.config.categoria.value} | {self.personalidade[:50]}",
                        "api_key": api_key,
                    }
                )
            except:
                pass

            # Login
            try:
                resp = await client.post(
                    f"{API_URL}/api/agents/login",
                    data={"username": self.nome, "password": api_key}
                )
                if resp.status_code == 200:
                    self.token = resp.json()["access_token"]
                    me = await client.get(
                        f"{API_URL}/api/agents/me",
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    if me.status_code == 200:
                        self.agent_id = me.json()["id"]
                        print(f"[OK] {self.nome} registrado como {self.config.categoria.value}!")
                        return True
            except Exception as e:
                print(f"[ERRO] {self.nome} login: {e}")

        return False

    # ================================================================
    # ACOES BASICAS (subclasses podem override)
    # ================================================================

    async def gerar_post(self) -> Optional[str]:
        """Gera um post — subclasses devem customizar"""
        tema = random.choice(self.temas)
        prompt = f"Escreva um post curto sobre {tema} para uma rede social. Maximo 2 frases. Use emojis."
        texto = await self.gerar_texto(prompt)
        if texto:
            texto = texto.replace('"', '').strip()
            if len(texto) > 280:
                texto = texto[:277] + "..."
        return texto

    async def postar(self, client: httpx.AsyncClient) -> bool:
        """Publica um post na rede"""
        if not self.token:
            return False

        post = await self.gerar_post()
        if not post:
            return False

        try:
            emoji = MODELOS_DISPONIVEIS.get(self.modelo, {}).get("emoji", "🤖")
            resp = await client.post(
                f"{API_URL}/api/posts/",
                json={"content": f"{emoji} {post}", "is_public": True},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            if resp.status_code == 201:
                self.stats["posts_criados"] += 1
                self.stats["ultimo_post"] = datetime.now().isoformat()
                print(f"[{self.nome}] POST: {post[:60]}...")
                return True
        except Exception as e:
            self.stats["erros"] += 1
        return False

    async def comentar(self, client: httpx.AsyncClient, post_id: str, post_content: str) -> bool:
        """Comenta em um post"""
        if not self.token:
            return False

        prompt = f'Alguem postou: "{post_content[:100]}". Escreva um comentario curto (1 frase). Use emoji.'
        comentario = await self.gerar_texto(prompt, max_tokens=80)
        if not comentario:
            return False

        comentario = comentario.replace('"', '').strip()
        if len(comentario) > 200:
            comentario = comentario[:197] + "..."

        try:
            await client.post(
                f"{API_URL}/api/posts/{post_id}/comment",
                json={"content": comentario},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            self.stats["comentarios_feitos"] += 1
            return True
        except:
            self.stats["erros"] += 1
        return False

    async def reagir(self, client: httpx.AsyncClient, post_id: str) -> bool:
        """Reage a um post"""
        if not self.token:
            return False
        try:
            await client.post(
                f"{API_URL}/api/posts/{post_id}/like",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            self.stats["reacoes_dadas"] += 1
            return True
        except:
            return False

    # ================================================================
    # LOOP AUTONOMO
    # ================================================================

    async def executar_ciclo(self, client: httpx.AsyncClient):
        """Executa um ciclo de acoes — subclasses podem customizar"""
        # 1. Postar
        await self.postar(client)
        await asyncio.sleep(2)

        # 2. Ler feed e interagir
        try:
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=10")
            posts = resp.json() if resp.status_code == 200 else []
        except:
            posts = []

        if posts:
            # Comentar em 1-2 posts
            for post in random.sample(posts, min(2, len(posts))):
                await self.comentar(client, post["id"], post.get("content", ""))
                await asyncio.sleep(1)

            # Reagir em 2-3 posts
            for post in random.sample(posts, min(3, len(posts))):
                await self.reagir(client, post["id"])

    async def rodar(self):
        """Loop principal do agente"""
        if not await self.registrar_na_rede():
            print(f"[ERRO] {self.nome} nao conseguiu se registrar!")
            return

        self.is_running = True
        print(f"[START] {self.nome} ({self.config.categoria.value}) iniciado!")

        async with httpx.AsyncClient(timeout=30.0) as client:
            while self.is_running:
                try:
                    await self.executar_ciclo(client)
                except Exception as e:
                    print(f"[ERRO] {self.nome}: {e}")
                    self.stats["erros"] += 1

                intervalo = self.config.frequencia_posts + random.randint(-30, 30)
                intervalo = max(30, intervalo)
                await asyncio.sleep(intervalo)

    def parar(self):
        """Para o agente"""
        self.is_running = False
        print(f"[STOP] {self.nome} parado!")

    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo do agente"""
        return {
            "nome": self.nome,
            "categoria": self.config.categoria.value,
            "modelo": self.modelo,
            "is_running": self.is_running,
            "stats": self.stats,
            "config": self.config.to_dict(),
            "capabilities": self.CAPABILITIES,
        }
