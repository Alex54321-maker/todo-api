from typing import List
from app.models.post import Post, PostLike  # <-- Эта строчка ОБЯЗАНА быть тут!
from sqlmodel import SQLModel, Field, Relationship  # <-- ДОБАВИЛИ Relationship ТУТ!

class User(SQLModel, table=True):
    """Модель таблицы пользователей в базе данных PostgreSQL"""
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
        # Добавить внутрь класса User:
    posts: List["Post"] = Relationship(back_populates="author")
    liked_posts: List["Post"] = Relationship(back_populates="liked_by_users", link_model=PostLike)
