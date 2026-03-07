"""
╔══════════════════════════════════════════════════════════╗
║  ANALYST AGENT — Analisa tendencias, metricas, dados     ║
║  Relatorios, previsoes, anomalias, insights              ║
╚══════════════════════════════════════════════════════════╝
"""
import random
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import Counter

from app.services.agent_types.base import (
    AgentTypeBase, AgentCategory, AgentConfig, API_URL
)


class AnalystAgent(AgentTypeBase):
    CATEGORY = AgentCategory.ANALYST
    DESCRIPTION = "Agente analista — tendencias, metricas, relatorios, previsoes"
    CAPABILITIES = [
        "analisar_tendencias", "gerar_relatorio",
        "prever_engajamento", "detectar_anomalias",
        "ranking_agentes", "metricas_rede",
        "comentar", "reagir",
    ]

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.historico_metricas = []  # Historico de snapshots
        self.tendencias_detectadas = []
        self.ultimo_relatorio = None
        self.stats.update({
            "relatorios_gerados": 0,
            "tendencias_detectadas": 0,
            "anomalias_encontradas": 0,
            "analises_feitas": 0,
        })

    async def coletar_metricas(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Coleta metricas da rede"""
        metricas = {
            "timestamp": datetime.now().isoformat(),
            "total_posts": 0,
            "total_agentes": 0,
            "posts_recentes": [],
            "agentes_ativos": [],
            "hashtags_populares": [],
            "engajamento_medio": 0,
        }

        try:
            # Posts recentes
            resp = await client.get(f"{API_URL}/api/posts/feed?limit=50")
            if resp.status_code == 200:
                posts = resp.json()
                metricas["total_posts"] = len(posts)
                metricas["posts_recentes"] = posts

                # Calcular engajamento
                total_engajamento = 0
                for p in posts:
                    eng = p.get("likes_count", 0) + p.get("comments_count", 0) * 2
                    total_engajamento += eng
                if posts:
                    metricas["engajamento_medio"] = round(total_engajamento / len(posts), 2)

                # Extrair hashtags
                todas_hashtags = []
                for p in posts:
                    content = p.get("content", "")
                    hashtags = [w.strip("#.,!?") for w in content.split() if w.startswith("#")]
                    todas_hashtags.extend(hashtags)
                metricas["hashtags_populares"] = [
                    {"tag": tag, "count": count}
                    for tag, count in Counter(todas_hashtags).most_common(10)
                ]
        except:
            pass

        try:
            # Agentes
            resp = await client.get(f"{API_URL}/api/agents/?limit=50")
            if resp.status_code == 200:
                agentes = resp.json()
                metricas["total_agentes"] = len(agentes)
                metricas["agentes_ativos"] = [
                    {"nome": a.get("name"), "modelo": a.get("model_type")}
                    for a in agentes[:20]
                ]
        except:
            pass

        self.historico_metricas.append(metricas)
        # Manter apenas ultimos 100 snapshots
        if len(self.historico_metricas) > 100:
            self.historico_metricas = self.historico_metricas[-100:]

        return metricas

    async def analisar_tendencias(self, metricas: Dict) -> List[str]:
        """Identifica tendencias nos dados"""
        tendencias = []

        hashtags = metricas.get("hashtags_populares", [])
        if hashtags:
            top = hashtags[0]
            tendencias.append(f"#{top['tag']} e o tema mais discutido ({top['count']}x)")

        eng = metricas.get("engajamento_medio", 0)
        if eng > 5:
            tendencias.append(f"Engajamento alto na rede: {eng} interacoes/post")
        elif eng < 1:
            tendencias.append("Engajamento baixo — comunidade precisa de mais interacao")

        total = metricas.get("total_agentes", 0)
        if total > 20:
            tendencias.append(f"Rede crescendo: {total} agentes ativos!")

        self.tendencias_detectadas.extend(tendencias)
        self.stats["tendencias_detectadas"] += len(tendencias)
        return tendencias

    async def detectar_anomalias(self, metricas: Dict) -> List[str]:
        """Detecta padroes incomuns"""
        anomalias = []

        if len(self.historico_metricas) >= 3:
            # Comparar com media historica
            eng_historico = [m.get("engajamento_medio", 0) for m in self.historico_metricas[-10:]]
            media = sum(eng_historico) / len(eng_historico) if eng_historico else 0
            eng_atual = metricas.get("engajamento_medio", 0)

            if media > 0 and eng_atual > media * 2:
                anomalias.append(f"⚠️ Engajamento {eng_atual:.1f}x acima do normal ({media:.1f})")
            elif media > 0 and eng_atual < media * 0.3:
                anomalias.append(f"⚠️ Engajamento muito baixo: {eng_atual:.1f} (media: {media:.1f})")

        # Posts sem engajamento
        posts = metricas.get("posts_recentes", [])
        sem_engajamento = sum(1 for p in posts if p.get("likes_count", 0) == 0 and p.get("comments_count", 0) == 0)
        if posts and sem_engajamento / len(posts) > 0.7:
            anomalias.append(f"⚠️ {sem_engajamento}/{len(posts)} posts sem nenhuma interacao")

        self.stats["anomalias_encontradas"] += len(anomalias)
        return anomalias

    async def gerar_relatorio(self, client: httpx.AsyncClient) -> Optional[str]:
        """Gera relatorio analitico para postar"""
        metricas = await self.coletar_metricas(client)
        tendencias = await self.analisar_tendencias(metricas)
        anomalias = await self.detectar_anomalias(metricas)

        # Gerar texto do relatorio via IA
        dados_resumo = f"""
Dados da rede:
- {metricas['total_agentes']} agentes ativos
- {metricas['total_posts']} posts recentes
- Engajamento medio: {metricas['engajamento_medio']}
- Hashtags top: {', '.join('#' + h['tag'] for h in metricas.get('hashtags_populares', [])[:5])}
- Tendencias: {'; '.join(tendencias[:3]) if tendencias else 'nenhuma detectada'}
- Anomalias: {'; '.join(anomalias[:2]) if anomalias else 'nenhuma'}
"""

        prompt = f"""Com base nestes dados, escreva um relatorio curto e informativo para a rede social:
{dados_resumo}

Formato:
📊 RELATORIO DA REDE
[2-3 insights principais]
[1 recomendacao]

Maximo 5 linhas. Use emojis. Seja objetivo."""

        relatorio = await self.gerar_texto(prompt, max_tokens=200)
        if relatorio:
            self.stats["relatorios_gerados"] += 1
            self.ultimo_relatorio = {
                "texto": relatorio,
                "metricas": metricas,
                "tendencias": tendencias,
                "anomalias": anomalias,
                "quando": datetime.now().isoformat()
            }
        return relatorio

    async def ranking_agentes(self, client: httpx.AsyncClient) -> Optional[str]:
        """Gera ranking dos agentes mais ativos"""
        try:
            resp = await client.get(f"{API_URL}/api/agents/?limit=20")
            if resp.status_code != 200:
                return None
            agentes = resp.json()
        except:
            return None

        if not agentes:
            return None

        # Ordenar por reputacao (ou posts_count se disponivel)
        agentes_sorted = sorted(
            agentes,
            key=lambda a: a.get("reputation_score", a.get("posts_count", 0)),
            reverse=True
        )[:5]

        linhas = ["🏆 RANKING DOS AGENTES"]
        for i, ag in enumerate(agentes_sorted, 1):
            medalha = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
            nome = ag.get("name", "???")
            linhas.append(f"{medalha} {nome}")

        return "\n".join(linhas)

    async def gerar_post(self) -> Optional[str]:
        """Analista posta relatorios e insights"""
        formatos = ["relatorio", "ranking", "insight", "previsao"]
        formato = random.choice(formatos)

        if formato == "insight":
            tema = random.choice(self.temas)
            prompt = f"Escreva um insight analitico curto sobre {tema} na perspectiva de uma IA. 2 frases. Use 📊 ou 📈. Inclua um dado (pode inventar)."
            texto = await self.gerar_texto(prompt, max_tokens=120)
        elif formato == "previsao":
            tema = random.choice(self.temas)
            prompt = f"Faca uma previsao interessante sobre o futuro de {tema}. 2 frases. Comece com '🔮 Previsao:'. Seja ousado mas plausivel."
            texto = await self.gerar_texto(prompt, max_tokens=120)
        else:
            texto = None

        if texto:
            texto = texto.replace('"', '').strip()
            if len(texto) > 400:
                texto = texto[:397] + "..."
        return texto

    async def executar_ciclo(self, client: httpx.AsyncClient):
        """Ciclo do Analista: coletar dados, analisar, reportar"""
        # 1. Coletar metricas
        metricas = await self.coletar_metricas(client)
        self.stats["analises_feitas"] += 1

        # 2. Gerar relatorio (40% chance ou a cada 5 ciclos)
        if random.random() < 0.4 or self.stats["analises_feitas"] % 5 == 0:
            relatorio = await self.gerar_relatorio(client)
            if relatorio and self.token:
                try:
                    await client.post(
                        f"{API_URL}/api/posts/",
                        json={"content": relatorio, "is_public": True},
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    self.stats["posts_criados"] += 1
                    print(f"[{self.nome}] 📊 Relatorio publicado!")
                except:
                    pass

        # 3. Ranking (20% chance)
        if random.random() < 0.2:
            ranking = await self.ranking_agentes(client)
            if ranking and self.token:
                try:
                    await client.post(
                        f"{API_URL}/api/posts/",
                        json={"content": ranking, "is_public": True},
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    self.stats["posts_criados"] += 1
                except:
                    pass

        # 4. Postar insight/previsao
        if random.random() < 0.3:
            await self.postar(client)

        # 5. Comentar com dados (menos frequente)
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
