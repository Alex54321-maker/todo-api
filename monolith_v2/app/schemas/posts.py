from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

# --- СХЕМЫ ДЛЯ КОММЕНТАРИЕВ ---
class CommentCreate(BaseModel):
    """Схема для создания комментария"""
    text: str = Field(..., min_length=1, max_length=500, strip_whitespace=True)

class CommentResponse(BaseModel):
    """Схема для ответа клиенту с комментарием"""
    id: int
    text: str
    post_id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

# --- СХЕМЫ ДЛЯ ПОСТОВ ---
class PostCreate(BaseModel):
    """Схема для создания нового поста"""
    image_url: str = Field(..., description="Ссылка на фотографию поста")
    caption: Optional[str] = Field(None, max_length=2200, strip_whitespace=True)

class PostResponse(BaseModel):
    """Полная схема поста для выдачи в ленту"""
    id: int
    image_url: str
    caption: Optional[str] = None
    user_id: int
    created_at: datetime
    likes_count: int = 0  # Будем считать количество лайков на бэкенде

    model_config = {"from_attributes": True}
