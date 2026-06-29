from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, select
from typing import List

from app.core.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.posts import CommentCreate, CommentResponse
from app.api.v1.endpoints.auth import get_current_user # Защита токеном

router = APIRouter()
@router.get("/{post_id}/comments")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Получить все комментарии к конкретному посту 💬"""
    # Используем правильный синтаксис SQLModel через db.exec(select(...))
    comments = db.exec(select(Comment).where(Comment.post_id == post_id)).all()
    return comments


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, summary="Оставить комментарий под постом 💬")
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Оставить комментарий под постом (Доступно только авторизованным юзерам)"""
    # 1. Проверяем, существует ли пост, под которым пишем коммент
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
        
    # 2. Создаем новую карточку комментария в оперативной памяти
    new_comment = Comment(
        text=comment_data.text,
        post_id=post_id,
        user_id=current_user.id # Вытащили ID автора коммента из JWT токена!
    )
    
    # 3. Сохраняем в PostgreSQL
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment
