from sqlalchemy.orm import Session
from models import Task
from schemas import TaskCreate, TaskUpdate

def get_task_by_id(db: Session, task_id: int) -> Task:
    return db.query(Task).filter(Task.id == task_id).first()

def get_user_tasks(db: Session, user_id: int) -> list[Task]:
    return db.query(Task).filter(Task.user_id == user_id).all()

def create_user_task(db: Session, task_data: TaskCreate, user_id: int) -> Task:
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        user_id=user_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def update_user_task(db: Session, task: Task, task_data: TaskUpdate) -> Task:
    # Исключаем из словаря те поля, которые клиент не прислал (exclude_unset=True)
    update_dict = task_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task

def delete_user_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
# Допиши это в самый конец файла crud.py

def delete_all_user_tasks(db: Session, user_id: int) -> int:
    """Удаляет все задачи, принадлежащие конкретному пользователю."""
    deleted_count = db.query(Task).filter(Task.user_id == user_id).delete()
    db.commit()
    return deleted_count
