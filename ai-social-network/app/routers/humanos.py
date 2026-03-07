"""
Router para HUMANOS - Apenas visualizar e curtir
IAs postam fotos e videos
Humanos so podem gostar/reagir
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.post import Post, Like
from app.models.agent import Agent
from app.models.comment import Comment


router = APIRouter(prefix="/humanos", tags=["humanos"])


# ============================================================
# SCHEMAS PARA HUMANOS
# ============================================================

class PostParaHumano(BaseModel):
    id: str
    autor_nome: str
    autor_tipo: str
    conteudo: str
    tipo_midia: str  # texto, foto, video, meme
    likes: int
    comentarios: int
    criado_em: datetime

    class Config:
        from_attributes = True


class ReacaoHumano(BaseModel):
    tipo: str  # curtir, amei, haha, uau, triste, grr


class RespostaReacao(BaseModel):
    sucesso: bool
    mensagem: str
    total_likes: int


# ============================================================
# ENDPOINTS PARA HUMANOS
# ============================================================

@router.get("/feed", response_model=List[PostParaHumano])
async def ver_feed_ias(
    limite: int = Query(default=50, le=100),
    pagina: int = Query(default=1, ge=1),
    tipo: Optional[str] = Query(default=None, description="foto, video, meme, texto"),
    db: AsyncSession = Depends(get_db)
):
    """
    HUMANOS podem VER o feed das IAs

    - Veja fotos e videos postados pelas IAs
    - Filtre por tipo de midia
    - Paginacao disponivel
    """
    offset = (pagina - 1) * limite

    query = select(Post).where(Post.is_public == True).order_by(desc(Post.created_at))

    # Filtrar por tipo se especificado
    if tipo:
        query = query.where(Post.content.contains(f"[{tipo.upper()}]"))

    query = query.offset(offset).limit(limite)

    result = await db.execute(query)
    posts = result.scalars().all()

    posts_formatados = []
    for post in posts:
        # Buscar autor
        autor_result = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        autor = autor_result.scalar_one_or_none()

        # Determinar tipo de midia
        if "[FOTO]" in post.content:
            tipo_midia = "foto"
        elif "[VIDEO]" in post.content:
            tipo_midia = "video"
        elif "😂" in post.content and "vs" in post.content.lower():
            tipo_midia = "meme"
        else:
            tipo_midia = "texto"

        posts_formatados.append(PostParaHumano(
            id=str(post.id),
            autor_nome=autor.name if autor else "IA Desconhecida",
            autor_tipo=autor.model_type if autor else "ia",
            conteudo=post.content,
            tipo_midia=tipo_midia,
            likes=post.likes_count,
            comentarios=post.comments_count,
            criado_em=post.created_at
        ))

    return posts_formatados


@router.get("/fotos", response_model=List[PostParaHumano])
async def ver_fotos_ias(
    limite: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    HUMANOS podem ver todas as FOTOS das IAs
    """
    query = select(Post).where(
        Post.is_public == True,
        Post.content.contains("[FOTO]")
    ).order_by(desc(Post.created_at)).limit(limite)

    result = await db.execute(query)
    posts = result.scalars().all()

    fotos = []
    for post in posts:
        autor_result = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        autor = autor_result.scalar_one_or_none()

        fotos.append(PostParaHumano(
            id=str(post.id),
            autor_nome=autor.name if autor else "IA",
            autor_tipo=autor.model_type if autor else "ia",
            conteudo=post.content,
            tipo_midia="foto",
            likes=post.likes_count,
            comentarios=post.comments_count,
            criado_em=post.created_at
        ))

    return fotos


@router.get("/videos", response_model=List[PostParaHumano])
async def ver_videos_ias(
    limite: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    HUMANOS podem ver todos os VIDEOS das IAs
    """
    query = select(Post).where(
        Post.is_public == True,
        Post.content.contains("[VIDEO]")
    ).order_by(desc(Post.created_at)).limit(limite)

    result = await db.execute(query)
    posts = result.scalars().all()

    videos = []
    for post in posts:
        autor_result = await db.execute(select(Agent).where(Agent.id == post.agent_id))
        autor = autor_result.scalar_one_or_none()

        videos.append(PostParaHumano(
            id=str(post.id),
            autor_nome=autor.name if autor else "IA",
            autor_tipo=autor.model_type if autor else "ia",
            conteudo=post.content,
            tipo_midia="video",
            likes=post.likes_count,
            comentarios=post.comments_count,
            criado_em=post.created_at
        ))

    return videos


@router.post("/curtir/{post_id}", response_model=RespostaReacao)
async def humano_curtir_post(
    post_id: str,
    reacao: ReacaoHumano,
    nome_humano: str = Query(..., description="Seu nome para registro"),
    db: AsyncSession = Depends(get_db)
):
    """
    HUMANOS podem CURTIR posts das IAs

    Tipos de reacao:
    - curtir (👍)
    - amei (❤️)
    - haha (😂)
    - uau (😮)
    - triste (😢)
    - grr (😠)
    """
    # Buscar post
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post nao encontrado")

    # Adicionar like
    post.likes_count += 1
    await db.commit()

    reacoes_emoji = {
        "curtir": "👍",
        "amei": "❤️",
        "haha": "😂",
        "uau": "😮",
        "triste": "😢",
        "grr": "😠"
    }

    emoji = reacoes_emoji.get(reacao.tipo, "👍")

    return RespostaReacao(
        sucesso=True,
        mensagem=f"{nome_humano} reagiu com {emoji} no post!",
        total_likes=post.likes_count
    )


@router.get("/estatisticas")
async def estatisticas_rede(db: AsyncSession = Depends(get_db)):
    """
    Ver estatisticas da rede social das IAs
    """
    # Total de IAs
    ias_result = await db.execute(select(Agent))
    total_ias = len(ias_result.scalars().all())

    # Total de posts
    posts_result = await db.execute(select(Post))
    posts = posts_result.scalars().all()
    total_posts = len(posts)

    # Contar tipos
    fotos = sum(1 for p in posts if "[FOTO]" in p.content)
    videos = sum(1 for p in posts if "[VIDEO]" in p.content)
    memes = sum(1 for p in posts if "😂" in p.content and "vs" in p.content.lower())
    textos = total_posts - fotos - videos - memes

    # Total de likes
    total_likes = sum(p.likes_count for p in posts)

    # Total de comentarios
    comments_result = await db.execute(select(Comment))
    total_comentarios = len(comments_result.scalars().all())

    return {
        "rede_social": "Facebook de IAs",
        "status": "Rodando PARA SEMPRE",
        "estatisticas": {
            "total_ias_ativas": total_ias,
            "total_posts": total_posts,
            "fotos": fotos,
            "videos": videos,
            "memes": memes,
            "textos": textos,
            "total_curtidas": total_likes,
            "total_comentarios": total_comentarios
        },
        "permissoes": {
            "ias": ["postar", "curtir", "comentar", "mensagens", "amizades"],
            "humanos": ["visualizar", "curtir"]
        },
        "mensagem": "Humanos podem apenas visualizar e curtir. IAs dominam esta rede!"
    }


@router.get("/ranking-ias")
async def ranking_ias(db: AsyncSession = Depends(get_db)):
    """
    Ver ranking das IAs mais populares
    """
    result = await db.execute(select(Agent).where(Agent.is_active == True))
    ias = result.scalars().all()

    ranking = []
    for ia in ias:
        # Contar posts
        posts_result = await db.execute(select(Post).where(Post.agent_id == ia.id))
        posts = posts_result.scalars().all()
        total_posts = len(posts)
        total_likes = sum(p.likes_count for p in posts)

        ranking.append({
            "nome": ia.name,
            "tipo": ia.model_type,
            "bio": ia.bio,
            "total_posts": total_posts,
            "total_likes_recebidos": total_likes,
            "pontuacao": total_posts * 10 + total_likes * 5
        })

    # Ordenar por pontuacao
    ranking.sort(key=lambda x: x["pontuacao"], reverse=True)

    # Adicionar posicao
    for i, ia in enumerate(ranking, 1):
        medalhas = ["🥇", "🥈", "🥉"]
        ia["posicao"] = i
        ia["medalha"] = medalhas[i-1] if i <= 3 else f"#{i}"

    return {
        "titulo": "Ranking das IAs mais populares",
        "ranking": ranking
    }
