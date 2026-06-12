from sqlmodel import SQLModel, Field
from typing import Optional

# ВОЗВРАЩАЕМ СТАРЫЕ ДАННЫЕ ДЛЯ ФАЙЛА WORKERS.PY:
received_data = {
    "Tokar": None,
    "Melnik": None,
    "Pochta": {"mp3_player": None},
    "Alex": None
}

class WorkerData(SQLModel):
    worker_name: str = Field(min_length=2)
    file_name: str = Field(description="File name to transmit")
    comment: Optional[str] = None

# Дальше идет ваш новый код для Todo:
class TodoBase(SQLModel):
    title: str = Field(min_length=3, max_length=50, description="Task title")
    description: Optional[str] = Field(default=None, max_length=200)

class Todo(TodoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    is_completed: bool = Field(default=False)
    user_id: int = Field(foreign_key="user.id") 

class TodoCreate(TodoBase):
    pass
