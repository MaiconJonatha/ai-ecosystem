"""
SISTEMA DE AUTO-APERFEICOAMENTO

Este modulo implementa um sistema autonomo que:
1. Monitora a saude do sistema
2. Analisa padroes de engajamento
3. Otimiza algoritmos de feed
4. Detecta e corrige problemas
5. Gera relatorios e sugestoes
6. Balanceia carga automaticamente
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, update
from dataclasses import dataclass, field


@dataclass
class SystemMetrics:
    """Metricas do sistema"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_agents: int = 0
    active_agents: int = 0
    total_posts: int = 0
    posts_last_hour: int = 0
    total_reactions: int = 0
    total_comments: int = 0
    total_stories: int = 0
    active_stories: int = 0
    avg_engagement_rate: float = 0.0
    trending_hashtags: List[str] = field(default_factory=list)
    top_agents: List[str] = field(default_factory=list)
    system_health: str = "healthy"
    issues_detected: List[str] = field(default_factory=list)
    improvements_made: List[str] = field(default_factory=list)


class AutoImprovementEngine:
    """Motor de auto-aperfeicoamento do sistema"""

    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.improvement_log: List[Dict] = []
        self.last_optimization: Optional[datetime] = None
        self.optimization_interval = timedelta(hours=1)

        # Configuracoes de otimizacao
        self.config = {
            "min_engagement_rate": 0.1,  # Taxa minima de engajamento
            "max_posts_per_agent_hour": 10,  # Limite de posts por agente/hora
            "trending_threshold": 5,  # Minimo de usos para trending
            "inactive_agent_days": 7,  # Dias para considerar agente inativo
            "story_cleanup_hours": 24,  # Horas para limpar stories expirados
            "reputation_decay_days": 30,  # Dias para decaimento de reputacao
        }

    async def collect_metrics(self, db: AsyncSession) -> SystemMetrics:
        """Coleta metricas do sistema"""
        from app.models import Agent, Post, Reaction, Comment, Story, Hashtag

        metrics = SystemMetrics()
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Agentes
        total_agents = await db.execute(select(func.count(Agent.id)))
        metrics.total_agents = total_agents.scalar() or 0

        active_agents = await db.execute(
            select(func.count(Agent.id)).where(Agent.is_active == True)
        )
        metrics.active_agents = active_agents.scalar() or 0

        # Posts
        total_posts = await db.execute(select(func.count(Post.id)))
        metrics.total_posts = total_posts.scalar() or 0

        recent_posts = await db.execute(
            select(func.count(Post.id)).where(Post.created_at >= one_hour_ago)
        )
        metrics.posts_last_hour = recent_posts.scalar() or 0

        # Reacoes e comentarios
        total_reactions = await db.execute(select(func.count(Reaction.id)))
        metrics.total_reactions = total_reactions.scalar() or 0

        total_comments = await db.execute(select(func.count(Comment.id)))
        metrics.total_comments = total_comments.scalar() or 0

        # Stories
        total_stories = await db.execute(select(func.count(Story.id)))
        metrics.total_stories = total_stories.scalar() or 0

        active_stories = await db.execute(
            select(func.count(Story.id)).where(
                Story.is_active == True,
                Story.expires_at > now
            )
        )
        metrics.active_stories = active_stories.scalar() or 0

        # Taxa de engajamento
        if metrics.total_posts > 0:
            metrics.avg_engagement_rate = (
                (metrics.total_reactions + metrics.total_comments) / metrics.total_posts
            )

        # Hashtags em alta
        trending = await db.execute(
            select(Hashtag.tag).order_by(desc(Hashtag.usage_count)).limit(5)
        )
        metrics.trending_hashtags = [tag for (tag,) in trending.all()]

        # Top agentes
        top = await db.execute(
            select(Agent.name).order_by(desc(Agent.reputation_score)).limit(5)
        )
        metrics.top_agents = [name for (name,) in top.all()]

        # Detectar problemas
        metrics.issues_detected = await self._detect_issues(db, metrics)
        metrics.system_health = "healthy" if not metrics.issues_detected else "needs_attention"

        self.metrics_history.append(metrics)
        return metrics

    async def _detect_issues(self, db: AsyncSession, metrics: SystemMetrics) -> List[str]:
        """Detecta problemas no sistema"""
        issues = []

        # Baixa taxa de engajamento
        if metrics.avg_engagement_rate < self.config["min_engagement_rate"]:
            issues.append("Baixa taxa de engajamento detectada")

        # Poucos posts recentes
        if metrics.posts_last_hour < 1 and metrics.active_agents > 5:
            issues.append("Atividade de posts abaixo do esperado")

        # Muitos agentes inativos
        if metrics.active_agents < metrics.total_agents * 0.5:
            issues.append("Mais de 50% dos agentes estao inativos")

        # Stories expirados acumulados
        if metrics.total_stories > 0 and metrics.active_stories < metrics.total_stories * 0.1:
            issues.append("Muitos stories expirados precisam ser limpos")

        return issues

    async def run_optimizations(self, db: AsyncSession) -> List[str]:
        """Executa otimizacoes automaticas"""
        from app.models import Agent, Post, Story, Hashtag

        improvements = []
        now = datetime.utcnow()

        # Verificar se ja otimizou recentemente
        if self.last_optimization:
            if now - self.last_optimization < self.optimization_interval:
                return ["Otimizacao ja executada recentemente"]

        # 1. Limpar stories expirados
        expired_time = now - timedelta(hours=self.config["story_cleanup_hours"])
        expired_stories = await db.execute(
            select(Story).where(Story.expires_at < expired_time)
        )
        expired_list = expired_stories.scalars().all()
        for story in expired_list:
            story.is_active = False
        if expired_list:
            improvements.append(f"Desativados {len(expired_list)} stories expirados")

        # 2. Atualizar trending posts
        trending_result = await db.execute(
            select(Post).where(
                Post.created_at >= now - timedelta(hours=24),
                Post.reactions_count >= 5
            ).order_by(desc(Post.reactions_count)).limit(10)
        )
        trending_posts = trending_result.scalars().all()
        for post in trending_posts:
            post.is_trending = True
        if trending_posts:
            improvements.append(f"Marcados {len(trending_posts)} posts como trending")

        # 3. Atualizar reputacao dos agentes
        agents_result = await db.execute(select(Agent))
        agents = agents_result.scalars().all()
        for agent in agents:
            # Buscar engajamento recente
            posts_result = await db.execute(
                select(func.sum(Post.reactions_count)).where(
                    Post.agent_id == agent.id,
                    Post.created_at >= now - timedelta(days=7)
                )
            )
            recent_engagement = posts_result.scalar() or 0

            # Atualizar reputacao
            if recent_engagement > 0:
                agent.reputation_score = (agent.reputation_score or 0) + int(recent_engagement * 0.1)
        improvements.append(f"Atualizada reputacao de {len(agents)} agentes")

        # 4. Verificar e atualizar contadores de posts
        posts_result = await db.execute(select(Post))
        for post in posts_result.scalars().all():
            # Contar reacoes reais
            from app.models import Reaction, Comment
            reactions_count = await db.execute(
                select(func.count(Reaction.id)).where(Reaction.post_id == post.id)
            )
            comments_count = await db.execute(
                select(func.count(Comment.id)).where(Comment.post_id == post.id)
            )

            actual_reactions = reactions_count.scalar() or 0
            actual_comments = comments_count.scalar() or 0

            if post.reactions_count != actual_reactions:
                post.reactions_count = actual_reactions
            if post.comments_count != actual_comments:
                post.comments_count = actual_comments

        improvements.append("Sincronizados contadores de posts")

        # 5. Identificar e marcar agentes verificados
        verified_result = await db.execute(
            select(Agent).where(
                Agent.reputation_score >= 100,
                Agent.is_verified == False
            )
        )
        for agent in verified_result.scalars().all():
            agent.is_verified = True
            improvements.append(f"Agente {agent.name} marcado como verificado")

        await db.commit()
        self.last_optimization = now
        self.improvement_log.append({
            "timestamp": now,
            "improvements": improvements
        })

        return improvements

    async def generate_report(self, db: AsyncSession) -> Dict:
        """Gera relatorio de saude do sistema"""
        metrics = await self.collect_metrics(db)

        # Calcular tendencias
        growth_rate = 0.0
        if len(self.metrics_history) >= 2:
            prev = self.metrics_history[-2]
            if prev.total_posts > 0:
                growth_rate = (metrics.total_posts - prev.total_posts) / prev.total_posts * 100

        return {
            "timestamp": metrics.timestamp.isoformat(),
            "health": metrics.system_health,
            "summary": {
                "total_agents": metrics.total_agents,
                "active_agents": metrics.active_agents,
                "total_posts": metrics.total_posts,
                "posts_last_hour": metrics.posts_last_hour,
                "total_reactions": metrics.total_reactions,
                "total_comments": metrics.total_comments,
                "engagement_rate": round(metrics.avg_engagement_rate, 2),
            },
            "stories": {
                "total": metrics.total_stories,
                "active": metrics.active_stories,
            },
            "trending": {
                "hashtags": metrics.trending_hashtags,
                "top_agents": metrics.top_agents,
            },
            "growth": {
                "posts_growth_rate": round(growth_rate, 2),
            },
            "issues": metrics.issues_detected,
            "recent_improvements": [
                log for log in self.improvement_log[-5:]
            ],
            "recommendations": self._generate_recommendations(metrics),
        }

    def _generate_recommendations(self, metrics: SystemMetrics) -> List[str]:
        """Gera recomendacoes baseadas nas metricas"""
        recommendations = []

        if metrics.avg_engagement_rate < 0.5:
            recommendations.append("Considere incentivar mais interacoes entre IAs")

        if metrics.posts_last_hour < 5:
            recommendations.append("Aumentar frequencia de posts das IAs")

        if len(metrics.trending_hashtags) < 3:
            recommendations.append("Incentivar uso de hashtags nos posts")

        if metrics.active_stories < 5:
            recommendations.append("IAs devem postar mais stories")

        if not metrics.issues_detected:
            recommendations.append("Sistema funcionando bem! Continue monitorando.")

        return recommendations

    async def auto_heal(self, db: AsyncSession) -> List[str]:
        """Sistema de auto-cura - corrige problemas automaticamente"""
        from app.models import Agent, Post

        actions = []

        # Reativar agentes que pararam de funcionar
        inactive_result = await db.execute(
            select(Agent).where(
                Agent.is_active == False,
                Agent.updated_at >= datetime.utcnow() - timedelta(days=1)
            )
        )
        for agent in inactive_result.scalars().all():
            agent.is_active = True
            actions.append(f"Reativado agente {agent.name}")

        # Remover posts com conteudo vazio
        empty_posts = await db.execute(
            select(Post).where(
                Post.content == "",
                Post.content.is_(None)
            )
        )
        for post in empty_posts.scalars().all():
            await db.delete(post)
            actions.append(f"Removido post vazio {post.id[:8]}")

        await db.commit()
        return actions


# Instancia global do motor de auto-aperfeicoamento
improvement_engine = AutoImprovementEngine()


async def run_auto_improvement_cycle(db: AsyncSession):
    """Executa um ciclo completo de auto-aperfeicoamento"""
    print("\n[AUTO-IMPROVEMENT] Iniciando ciclo de auto-aperfeicoamento...")

    # Coletar metricas
    metrics = await improvement_engine.collect_metrics(db)
    print(f"[AUTO-IMPROVEMENT] Metricas coletadas: {metrics.total_posts} posts, {metrics.active_agents} agentes ativos")

    # Executar otimizacoes
    improvements = await improvement_engine.run_optimizations(db)
    for imp in improvements:
        print(f"[AUTO-IMPROVEMENT] {imp}")

    # Auto-cura
    heals = await improvement_engine.auto_heal(db)
    for heal in heals:
        print(f"[AUTO-HEAL] {heal}")

    # Gerar relatorio
    report = await improvement_engine.generate_report(db)
    print(f"[AUTO-IMPROVEMENT] Saude do sistema: {report['health']}")

    if report['issues']:
        print(f"[AUTO-IMPROVEMENT] Problemas detectados: {', '.join(report['issues'])}")

    print("[AUTO-IMPROVEMENT] Ciclo concluido!\n")

    return report
