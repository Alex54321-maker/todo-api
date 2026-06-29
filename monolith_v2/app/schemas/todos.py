from pydantic import BaseModel, Field

class TodoCreate(BaseModel):
    """Схема валидации для создания задачи"""
    title: str = Field(..., min_length=3, max_length=100, strip_whitespace=True)
    description: str | None = Field(None, max_length=500, strip_whitespace=True)

class TodoResponse(BaseModel):
    """Схема ответа клиенту"""
    id: int
    title: str
    description: str | None
    is_completed: bool
    user_id: int

    class Config:
        from_attributes = True
