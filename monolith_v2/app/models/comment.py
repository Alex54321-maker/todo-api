from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class Comment(SQLModel, table=True):
    """Модель Комментария к посту"""
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str = Field(..., min_length=1, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Внешние ключи (жесткая привязка на уровне PostgreSQL)
    user_id: int = Field(foreign_key="user.id")
    post_id: int = Field(foreign_key="post.id")
    
    # Связи для подгрузки объектов
    post: "Post" = Relationship(back_populates="comments")
