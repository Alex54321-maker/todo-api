from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jwt import decode, PyJWTError

from schemas import TaskCreate, TaskResponse, TaskUpdate
from database import engine, Base, get_db
from models import Task

app = FastAPI(title="Task Microservice", version="1.0.0")

# Автоматически создаем таблицу tasks в базе данных при старте
Base.metadata.create_all(bind=engine)

# Секретный ключ должен быть ТОЧНО ТАКИМ ЖЕ, как в auth_service, чтобы расшифровать токен
JWT_SECRET = "super_secret_key_123"
JWT_ALGORITHM = "HS256"

# Функция-зависимость (Dependency) для проверки токена и извлечения user_id
def get_current_user_id(authorization: str = Header(...)) -> int:
    try:
        # Отрезаем слово "Bearer " от заголовка
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        # Расшифровываем токен с помощью общего секретного ключа
        payload = decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token missing user ID")
        return int(user_id)
        
    except (PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# 1. Создание новой задачи для текущего пользователя
@app.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        user_id=user_id # Привязываем задачу к ID юзера из токена
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# 2. Получение списка ВСЕХ задач ТОЛЬКО текущего пользователя
@app.get("/", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return tasks
