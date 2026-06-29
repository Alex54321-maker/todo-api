from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, select, func
from typing import List

from app.core.database import get_db
from app.models.post import Post, PostLike
from app.models.user import User
from app.schemas.posts import PostCreate, PostResponse
from app.api.v1.endpoints.auth import get_current_user # Твой защитник маршрутов!

router = APIRouter()

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_data: PostCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Токен обязателен!
):
    """Создание нового поста авторизованным пользователем"""
    new_post = Post(
        image_url=post_data.image_url,
        caption=post_data.caption,
        user_id=current_user.id  # Вытащили ID из токена!
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/", response_model=List[PostResponse])
def get_posts_feed(db: Session = Depends(get_db)):
    """Получение ленты всех постов"""
    statement = select(Post)
    posts = db.exec(statement).all()
    
    # Подсчитываем лайки для каждого поста перед отправкой клиенту
    response_posts = []
    for post in posts:
        # Считаем записи в таблице-мосте PostLike для этого post_id
        likes_count = db.exec(
            select(func.count()).where(PostLike.post_id == post.id)
        ).one()
        
        # Превращаем в схему ответа и добавляем счетчик
        post_data = PostResponse.model_validate(post)
        post_data.likes_count = likes_count
        response_posts.append(post_data)
        
    return response_posts

@router.post("/{post_id}/like", status_code=status.HTTP_200_OK)
def like_post(
    post_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Защита токеном
):
    """Поставить или убрать лайк (Toggle-логика)"""
    # 1. Проверяем, существует ли вообще такой пост в базе данных
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    # 2. Ищем, вдруг этот пользователь уже лайкал этот пост
    statement = select(PostLike).where(
        PostLike.post_id == post_id, 
        PostLike.user_id == current_user.id
    )
    existing_like = db.exec(statement).first()
    
    # 3. Если лайк уже есть — удаляем его (убираем сердечко)
    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"message": "Лайк успешно убран", "liked": False}
        
    # 4. Если лайка нет — создаем новую запись в таблице-мосте
    new_like = PostLike(post_id=post_id, user_id=current_user.id)
    db.add(new_like)
    db.commit()
    return {"message": "Лайк успешно поставлен", "liked": True}
