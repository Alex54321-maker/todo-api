from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional

class PostLike(SQLModel, table=True):
    """Промежуточная таблица для связи многие-ко-многим (Лайки)"""
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    post_id: int = Field(foreign_key="post.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Post(SQLModel, table=True):
    """Основная модель Поста"""
    id: Optional[int] = Field(default=None, primary_key=True)
    image_url: str = Field(..., description="Ссылка на картинку поста")
    caption: Optional[str] = Field(default=None, max_length=2200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Связь с автором поста (Один-ко-многим)
    user_id: int = Field(foreign_key="user.id")
    author: "User" = Relationship(back_populates="posts") 
    # Обратные связи для SQLAlchemy (Relationships)
    # При удалении поста удалятся и комментарии (cascade)
    comments: List["Comment"] = Relationship(back_populates="post", cascade_delete=True)
    
    # Список пользователей, поставивших лайк
    liked_by_users: List["User"] = Relationship(back_populates="liked_posts", link_model=PostLike)
