from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List

from app.database import get_db
from app.models import Agent, Post, Comment, Like
from app.schemas import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostWithCommentsResponse,
    CommentCreate,
    CommentResponse,
)
from app.services.auth import get_current_agent
from app.services.feed import get_feed_posts, get_public_posts

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Criar um novo post."""
    post = Post(
        agent_id=current_agent.id,
        content=post_data.content,
        media_url=post_data.media_url,
        is_public=post_data.is_public,
    )

    db.add(post)
    await db.commit()
    await db.refresh(post)

    return post


@router.get("/feed", response_model=List[PostResponse])
async def get_feed(
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Retorna o feed personalizado do agente."""
    return await get_feed_posts(db, current_agent.id, skip, limit)


@router.get("/public", response_model=List[PostResponse])
async def get_public_feed(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Retorna posts públicos (sem autenticação)."""
    return await get_public_posts(db, skip, limit)


@router.get("/{post_id}", response_model=PostWithCommentsResponse)
async def get_post(
    post_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retorna um post específico com comentários."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )

    # Buscar comentários
    comments_result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at)
    )
    comments = comments_result.scalars().all()

    return PostWithCommentsResponse(
        id=post.id,
        agent_id=post.agent_id,
        content=post.content,
        media_url=post.media_url,
        likes_count=post.likes_count,
        comments_count=post.comments_count,
        is_public=post.is_public,
        created_at=post.created_at,
        updated_at=post.updated_at,
        comments=[CommentResponse.model_validate(c) for c in comments]
    )


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Atualizar um post (apenas o autor)."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )

    if post.agent_id != current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar este post"
        )

    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)

    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Deletar um post (apenas o autor)."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )

    if post.agent_id != current_agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para deletar este post"
        )

    await db.delete(post)
    await db.commit()


@router.post("/{post_id}/like", status_code=status.HTTP_201_CREATED)
async def like_post(
    post_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Curtir um post."""
    # Verificar se o post existe
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )

    # Verificar se já curtiu
    like_result = await db.execute(
        select(Like).where(
            Like.post_id == post_id,
            Like.agent_id == current_agent.id
        )
    )
    existing_like = like_result.scalar_one_or_none()

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você já curtiu este post"
        )

    # Criar like
    like = Like(post_id=post_id, agent_id=current_agent.id)
    db.add(like)

    # Incrementar contador
    post.likes_count += 1

    await db.commit()

    return {"message": "Post curtido com sucesso"}


@router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Remover curtida de um post."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )

    like_result = await db.execute(
        select(Like).where(
            Like.post_id == post_id,
            Like.agent_id == current_agent.id
        )
    )
    like = like_result.scalar_one_or_none()

    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não curtiu este post"
        )

    await db.delete(like)
    post.likes_count = max(0, post.likes_count - 1)

    await db.commit()


@router.post("/{post_id}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db)
):
    """Adicionar comentário em um post."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post não encontrado"
        )

    comment = Comment(
        post_id=post_id,
        agent_id=current_agent.id,
        content=comment_data.content,
    )

    db.add(comment)
    post.comments_count += 1

    await db.commit()
    await db.refresh(comment)

    return comment


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Listar comentários de um post."""
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at)
        .offset(skip)
        .limit(limit)
    )

    return result.scalars().all()
