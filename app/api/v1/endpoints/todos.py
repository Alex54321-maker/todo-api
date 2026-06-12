from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

# Относительные импорты, чтобы IDX ничего не терял
from ....core.database import get_db
from ....models.todo import Todo  
from ....models.user import User
from ....schemas.todos import TodoCreate, TodoResponse

from .auth import get_current_user 
from ....core.exceptions import TodoNotFoundException, TodoAccessDeniedException

router = APIRouter()

@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED, summary="Создать задачу")
def create_todo(
    todo_data: TodoCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_todo = Todo(**todo_data.model_dump(), user_id=current_user.id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@router.get("/", response_model=list[TodoResponse], summary="Получить список всех СВОИХ задач")
def read_todos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    todos = db.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    return todos

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить свою задачу")
def delete_todo(
    todo_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    todo = db.get(Todo, todo_id)
    
    if not todo:
        raise TodoNotFoundException()
        
    if todo.user_id != current_user.id:
        raise TodoAccessDeniedException()
        
    db.delete(todo)
    db.commit()
    return None

