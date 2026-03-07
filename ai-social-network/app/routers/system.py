"""
Router para Sistema - Auto-aperfeicoamento, metricas e saude do sistema
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auto_improvement import (
    improvement_engine,
    run_auto_improvement_cycle
)

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def system_health(db: AsyncSession = Depends(get_db)):
    """Retorna saude completa do sistema"""
    report = await improvement_engine.generate_report(db)
    return report


@router.get("/metrics")
async def system_metrics(db: AsyncSession = Depends(get_db)):
    """Retorna metricas atuais do sistema"""
    metrics = await improvement_engine.collect_metrics(db)
    return {
        "timestamp": metrics.timestamp.isoformat(),
        "agents": {
            "total": metrics.total_agents,
            "active": metrics.active_agents
        },
        "posts": {
            "total": metrics.total_posts,
            "last_hour": metrics.posts_last_hour
        },
        "engagement": {
            "reactions": metrics.total_reactions,
            "comments": metrics.total_comments,
            "rate": round(metrics.avg_engagement_rate, 2)
        },
        "stories": {
            "total": metrics.total_stories,
            "active": metrics.active_stories
        },
        "trending": metrics.trending_hashtags,
        "top_agents": metrics.top_agents
    }


@router.post("/optimize")
async def run_optimization(db: AsyncSession = Depends(get_db)):
    """Executa otimizacao manual do sistema"""
    improvements = await improvement_engine.run_optimizations(db)
    return {
        "status": "completed",
        "improvements": improvements
    }


@router.post("/auto-improve")
async def auto_improve(db: AsyncSession = Depends(get_db)):
    """Executa ciclo completo de auto-aperfeicoamento"""
    report = await run_auto_improvement_cycle(db)
    return report


@router.post("/auto-heal")
async def auto_heal(db: AsyncSession = Depends(get_db)):
    """Executa auto-cura do sistema"""
    actions = await improvement_engine.auto_heal(db)
    return {
        "status": "completed",
        "actions": actions
    }


@router.get("/improvement-log")
async def get_improvement_log():
    """Retorna historico de melhorias feitas"""
    return {
        "total_improvements": len(improvement_engine.improvement_log),
        "recent": improvement_engine.improvement_log[-20:],
        "last_optimization": improvement_engine.last_optimization.isoformat() if improvement_engine.last_optimization else None
    }


@router.get("/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    """Retorna recomendacoes de melhoria"""
    metrics = await improvement_engine.collect_metrics(db)
    recommendations = improvement_engine._generate_recommendations(metrics)
    return {
        "health": metrics.system_health,
        "issues": metrics.issues_detected,
        "recommendations": recommendations
    }
