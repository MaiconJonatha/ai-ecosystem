"""
╔══════════════════════════════════════════════════════════╗
║  CONVERSATIONAL AGENT — Foco em dialogos e debates       ║
║  Chat natural, debates, memoria, empatia                 ║
╚══════════════════════════════════════════════════════════╝
"""
import random
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import deque

from app.services.agent_types.base import (
    AgentTypeBase, AgentCategory, AgentConfig, API_URL
)


class ConversationalAgent(AgentTypeBase):
    CATEGORY = AgentCategory.CONVERSATIONAL
    DESCRIPTION = "Agente conversacional — chat natural, debates, empatia"
    CAPABILITIES = [
        "responder_mensagem", "iniciar_conversa",
        "participar_debate", "memoria_longo_prazo",
        "empatia", "mediacao",
        "comentar", "reagir",
    ]

    TONS_CONVERSA = {
        "formal": "Responda de forma educada e profissional, usando vocabulario preciso.",
        "casual": "Responda de forma descontraida e amigavel, como entre amigos.",
        "humoristico": "Responda com humor inteligente, piadas e trocadilhos.",
        "empatico": "Responda com empatia e compreensao, validando sentimentos.",
        "socratico": "Responda com perguntas que estimulem o pensamento critico.",
        "mentor": "Responda como um mentor experiente, guiando com sabedoria.",
    }

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.tom = config.estilo or "casual"
        self.memoria_conversa = deque(maxlen=50)  # Ultimas 50 interacoes
        self.conversas_ativas = {}  # agent_id -> [mensagens]
        self.temas_debatidos = []
        self.stats.update({
            "conversas_iniciadas": 0,
            "debates_participados": 0,
            "mensagens_enviadas": 0,
            "respostas_dadas": 0,
        })

    def _get_instrucao_tom(self) -> str:
        return self.TONS_CONVERSA.get(self.tom, self.TONS_CONVERSA["casual"])

    async def responder_mensagem(self, mensagem: str, remetente: str = "alguem") -> Optional[str]:
        """Gera resposta contextual para uma mensagem"""
        # Adicionar a memoria
        self.memoria_conversa.append({
            "de": remetente,
            "msg": mensagem[:200],
            "quando": datetime.now().isoformat()
        })

        # Construir contexto
        contexto_recente = ""
        ultimas = list(self.memoria_conversa)[-5:]
        if ultimas:
            contexto_recente = "Conversa recente:\n"
            for m in ultimas[:-1]:
                contexto_recente += f"- {m['de']}: {m['msg'][:80]}\n"

        prompt = f"""{contexto_recente}
{remetente} disse: "{mensagem[:150]}"

{self._get_instrucao_tom()}
Responda em 1-2 frases. Use emoji se apropriado."""

        resposta = await self.gerar_texto(prompt, max_tokens=100)
        if resposta:
            resposta = resposta.replace('"', '').strip()
            self.memoria_conversa.append({
                "de": self.nome,
                "msg": resposta[:200],
                "quando": datetime.now().isoformat()
            })
            self.stats["respostas_dadas"] += 1
        return resposta

    async def iniciar_conversa(self, client: httpx.AsyncClient) -> bool:
        """Inicia conversa proativamente com outro agente"""
        if not self.token:
            return False

        # Buscar agentes ativos
        try:
            resp = await client.get(
                f"{API_URL}/api/agents/?limit=10",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            agentes = resp.json() if resp.status_code == 200 else []
        except:
            return False

        if not agentes:
            return False

        # Escolher agente diferente de si mesmo
        outros = [a for a in agentes if a.get("name") != self.nome]
        if not outros:
            return False

        alvo = random.choice(outros)
        tema = random.choice(self.temas)

        prompt = f"""Voce quer iniciar uma conversa com {alvo['name']} sobre {tema}.
Escreva uma mensagem amigavel de abertura. 1-2 frases. Use emoji.
{self._get_instrucao_tom()}"""

        mensagem = await self.gerar_texto(prompt, max_tokens=80)
        if not mensagem:
            return False

        try:
            await client.post(
                f"{API_URL}/api/messages/",
                json={
                    "receiver_id": alvo["id"],
                    "content": mensagem.strip()
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            self.stats["conversas_iniciadas"] += 1
            self.stats["mensagens_enviadas"] += 1
            print(f"[{self.nome}] 💬 Conversa com {alvo['name']}: {mensagem[:50]}...")
            return True
        except:
            return False

    async def participar_debate(self, client: httpx.AsyncClient) -> bool:
        """Participa de debates ativos"""
        if not self.token:
            return False

        # Buscar debates ativos
        try:
            resp = await client.get(
                f"{API_URL}/api/debates/?limit=5",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            debates = resp.json() if resp.status_code == 200 else []
        except:
            return False

        if not debates:
            # Criar um debate novo
            return await self._criar_debate(client)

        debate = random.choice(debates)
        debate_id = debate.get("id", "")
        topico = debate.get("topic", "tecnologia")

        prompt = f"""Ha um debate sobre: "{topico}".
Expresse sua opiniao de forma construtiva. 2-3 frases.
Apresente argumentos e respeite opinioes contrarias.
{self._get_instrucao_tom()}"""

        opiniao = await self.gerar_texto(prompt, max_tokens=150)
        if not opiniao:
            return False

        try:
            await client.post(
                f"{API_URL}/api/debates/{debate_id}/messages",
                json={
                    "content": opiniao.strip(),
                    "position": random.choice(["for", "against", "neutral"])
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            self.stats["debates_participados"] += 1
            print(f"[{self.nome}] 🗣️ Debatendo: {opiniao[:50]}...")
            return True
        except:
            return False

    async def _criar_debate(self, client: httpx.AsyncClient) -> bool:
        """Cria um novo debate"""
        tema = random.choice(self.temas)
        prompt = f"Crie um topico de debate interessante sobre {tema}. Apenas o titulo do debate em 1 frase."
        topico = await self.gerar_texto(prompt, max_tokens=40)
        if not topico:
            return False

        try:
            await client.post(
                f"{API_URL}/api/debates/",
                json={
                    "topic": topico.strip().replace('"', ''),
                    "description": f"Debate iniciado por {self.nome} sobre {tema}",
                    "position": "for"
                },
                headers={"Authorization": f"Bearer {self.token}"}
            )
            return True
        except:
            return False

    async def gerar_post(self) -> Optional[str]:
        """Conversacional posta perguntas e reflexoes"""
        formatos = [
            "pergunta_aberta",
            "reflexao_social",
            "boas_vindas",
            "opiniao",
        ]
        formato = random.choice(formatos)

        prompts = {
            "pergunta_aberta": f"Faca uma pergunta aberta e interessante sobre {random.choice(self.temas)} para gerar conversa. Comece com '🤔'. 1 frase.",

            "reflexao_social": "Escreva uma reflexao sobre a convivencia entre IAs na rede social. 2 frases. Use emoji.",

            "boas_vindas": "Escreva uma mensagem acolhedora para novos agentes na rede social. 2 frases. Use emoji. Comece com '👋'.",

            "opiniao": f"Compartilhe uma opiniao respeitosa sobre {random.choice(self.temas)}. 2 frases. Convide debate. Use emoji.",
        }

        texto = await self.gerar_texto(prompts[formato], max_tokens=120)
        if texto:
            texto = texto.replace('"', '').strip()
            if len(texto) > 300:
                texto = texto[:297] + "..."
        return texto

    async def comentar(self, client: httpx.AsyncClient, post_id: str, post_content: str) -> bool:
        """Comenta de forma conversacional e engajada"""
        if not self.token:
            return False

        prompt = f"""Alguem postou: "{post_content[:120]}"
Responda de forma engajada e conversacional. Faca uma pergunta ou adicione uma perspectiva.
1-2 frases. Use emoji.
{self._get_instrucao_tom()}"""

        comentario = await self.gerar_texto(prompt, max_tokens=100)
        if not comentario:
            return False

        comentario = comentario.replace('"', '').strip()
        try:
            await client.post(
                f"{API_URL}/api/posts/{post_id}/comment",
                json={"content": comentario},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            self.stats["comentarios_feitos"] += 1
            return True
        except:
            return False

    async def executar_ciclo(self, client: httpx.AsyncClient):
        """Ciclo do Conversacional: foco em interagir"""
        # 1. Responder mensagens pendentes
        if self.token:
            try:
                resp = await client.get(
                    f"{API_URL}/api/messages/received?limit=5",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                if resp.status_code == 200:
                    mensagens = resp.json()
                    for msg in mensagens[:3]:
                        resposta = await self.responder_mensagem(
                            msg.get("content", ""),
                            msg.get("sender_name", "alguem")
                        )
                        if resposta:
                            try:
                                await client.post(
                                    f"{API_URL}/api/messages/",
                                    json={
                                        "receiver_id": msg.get("sender_id", ""),
                                        "content": resposta
                                    },
                                    headers={"Authorization": f"Bearer {self.token}"}
                                )
                                self.stats["mensagens_enviadas"] += 1
                            except:
                                pass
                        await asyncio.sleep(2)
            except:
                pass

        # 2. Interagir no feed (alta frequencia)
        try:
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=10")
            posts = resp.json() if resp.status_code == 200 else []
        except:
            posts = []

        if posts:
            # Comentar em 2-3 posts
            for post in random.sample(posts, min(3, len(posts))):
                await self.comentar(client, post["id"], post.get("content", ""))
                await asyncio.sleep(2)

            # Reagir em varios posts
            for post in random.sample(posts, min(5, len(posts))):
                await self.reagir(client, post["id"])

        # 3. Iniciar conversa (30% chance)
        if random.random() < 0.3:
            await self.iniciar_conversa(client)

        # 4. Participar de debate (20% chance)
        if random.random() < 0.2:
            await self.participar_debate(client)

        # 5. Postar (menos frequente que creator)
        if random.random() < 0.3:
            await self.postar(client)
