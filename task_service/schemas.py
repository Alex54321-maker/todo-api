from pydantic import BaseModel, Field

# 1. Базовые поля для задачи
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)

# 2. Схема для создания задачи (поступает от фронтенда)
class TaskCreate(TaskBase):
    pass

# 3. Схема для обновления задачи (сделали все поля опциональными для гибкости)
class TaskUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    is_completed: bool | None = Field(None)

# 4. Схема для ответа сервера (клиент увидит ID, статус и привязку к юзеру)
class TaskResponse(TaskBase):
    id: int
    is_completed: bool
    user_id: int

    # Включаем чтение данных из моделей SQLAlchemy (Pydantic v2)
    model_config = {"from_attributes": True}
