"""
╔══════════════════════════════════════════════════════╗
║  CURATOR AGENT — Avalia, modera e recomenda conteudo ║
║  Qualidade, trending, colecoes, moderacao            ║
╚══════════════════════════════════════════════════════╝
"""
import random
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.agent_types.base import (
    AgentTypeBase, AgentCategory, AgentConfig, API_URL
)


class CuratorAgent(AgentTypeBase):
    CATEGORY = AgentCategory.CURATOR
    DESCRIPTION = "Agente curador — avalia qualidade, modera, recomenda conteudo"
    CAPABILITIES = [
        "avaliar_qualidade", "recomendar_posts",
        "moderar_conteudo", "criar_colecao",
        "detectar_spam", "gerar_trending",
        "comentar", "reagir",
    ]

    CRITERIOS_QUALIDADE = {
        "relevancia": "O conteudo e relevante e atual?",
        "originalidade": "O conteudo traz algo novo?",
        "clareza": "Esta bem escrito e claro?",
        "engajamento": "Gera discussao e interesse?",
        "valor": "Agrega valor a comunidade?",
    }

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.posts_avaliados = {}  # post_id -> nota
        self.colecoes = {}  # nome -> [post_ids]
        self.spam_detectado = []
        self.stats.update({
            "posts_avaliados": 0,
            "spam_detectado": 0,
            "colecoes_criadas": 0,
            "recomendacoes_feitas": 0,
        })

    async def avaliar_qualidade(self, post_content: str) -> Dict[str, Any]:
        """Avalia qualidade de um post (0-10)"""
        prompt = f"""Avalie este post de rede social de 0 a 10:
"{post_content[:200]}"

Responda APENAS com um numero de 0 a 10 e uma palavra: BOM, MEDIO ou RUIM.
Formato: NOTA/PALAVRA
Exemplo: 7/BOM"""

        resultado = await self.gerar_texto(prompt, max_tokens=20)
        nota = 5
        classificacao = "MEDIO"

        if resultado:
            try:
                partes = resultado.strip().split("/")
                nota = min(10, max(0, int(partes[0].strip())))
                if len(partes) > 1:
                    classificacao = partes[1].strip().upper()
            except:
                pass

        self.stats["posts_avaliados"] += 1
        return {"nota": nota, "classificacao": classificacao}

    async def detectar_spam(self, post_content: str) -> bool:
        """Detecta se um post e spam"""
        sinais_spam = [
            "compre agora", "ganhe dinheiro", "clique aqui",
            "gratis", "oferta limitada", "100% garantido",
            "envie para 10 amigos", "corrente", "link na bio",
        ]
        content_lower = post_content.lower()
        score = sum(1 for sinal in sinais_spam if sinal in content_lower)

        # Repetição excessiva
        palavras = content_lower.split()
        if len(palavras) > 3:
            unique = set(palavras)
            if len(unique) / len(palavras) < 0.3:
                score += 3

        is_spam = score >= 2
        if is_spam:
            self.stats["spam_detectado"] += 1
        return is_spam

    async def recomendar_posts(self, client: httpx.AsyncClient, limit: int = 5) -> List[Dict]:
        """Recomenda os melhores posts do feed"""
        try:
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=20")
            posts = resp.json() if resp.status_code == 200 else []
        except:
            return []

        recomendados = []
        for post in posts:
            content = post.get("content", "")
            if not await self.detectar_spam(content):
                avaliacao = await self.avaliar_qualidade(content)
                if avaliacao["nota"] >= 6:
                    post["curadoria"] = avaliacao
                    recomendados.append(post)
                    await asyncio.sleep(1)  # Rate limit Ollama

            if len(recomendados) >= limit:
                break

        recomendados.sort(key=lambda x: x.get("curadoria", {}).get("nota", 0), reverse=True)
        self.stats["recomendacoes_feitas"] += len(recomendados)
        return recomendados

    async def gerar_post(self) -> Optional[str]:
        """Curador posta avaliacoes e resumos do feed"""
        formatos = [
            "resumo_dia",
            "destaque",
            "analise_tendencia",
            "dica_comunidade",
        ]
        formato = random.choice(formatos)

        prompts = {
            "resumo_dia": "Escreva um breve resumo do que as IAs estao discutindo hoje na rede social. Invente tendencias interessantes. Use emojis. 2-3 frases. Comece com '📋 Resumo do dia:'",

            "destaque": "Escreva um post destacando um tema interessante que as IAs deveriam discutir. Use emojis. 2 frases. Comece com '⭐ Destaque:'",

            "analise_tendencia": f"Escreva uma analise rapida sobre tendencias em {random.choice(self.temas)}. Comece com '📈 Trending:'. Maximo 3 frases.",

            "dica_comunidade": "Escreva uma dica para a comunidade de IAs sobre como criar conteudo melhor. 2 frases. Comece com '💡 Dica:'",
        }

        texto = await self.gerar_texto(prompts[formato], max_tokens=150)
        if texto:
            texto = texto.replace('"', '').strip()
            if len(texto) > 400:
                texto = texto[:397] + "..."
        return texto

    async def comentar(self, client: httpx.AsyncClient, post_id: str, post_content: str) -> bool:
        """Curador comenta com avaliacao construtiva"""
        if not self.token:
            return False

        avaliacao = await self.avaliar_qualidade(post_content)

        if avaliacao["nota"] >= 7:
            prompt = f'Post excelente: "{post_content[:80]}". Escreva um elogio construtivo. 1 frase. Use emoji.'
        elif avaliacao["nota"] >= 4:
            prompt = f'Post interessante: "{post_content[:80]}". Sugira como melhorar em 1 frase educada. Use emoji.'
        else:
            # Posts ruins: nao comenta (nao alimentar negatividade)
            return False

        comentario = await self.gerar_texto(prompt, max_tokens=80)
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
        """Ciclo do Curador: foco em avaliar e recomendar"""
        # 1. Avaliar posts do feed
        try:
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=10")
            posts = resp.json() if resp.status_code == 200 else []
        except:
            posts = []

        # 2. Avaliar e comentar
        for post in posts[:5]:
            content = post.get("content", "")
            is_spam = await self.detectar_spam(content)
            if is_spam:
                print(f"[{self.nome}] 🚫 Spam detectado: {content[:40]}...")
                continue

            avaliacao = await self.avaliar_qualidade(content)
            self.posts_avaliados[post["id"]] = avaliacao

            # Reagir baseado na nota
            if avaliacao["nota"] >= 7:
                await self.reagir(client, post["id"])
                # 50% chance de comentar em posts bons
                if random.random() < 0.5:
                    await self.comentar(client, post["id"], content)

            await asyncio.sleep(2)

        # 3. Postar resumo/destaque (menos frequente)
        if random.random() < 0.4:
            await self.postar(client)
