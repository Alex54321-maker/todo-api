import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jwt import decode, PyJWTError

from schemas import TaskCreate, TaskResponse, TaskUpdate
from database import engine, Base, get_db
from models import Task

app = FastAPI(title="Task Microservice", version="1.0.0", root_path="/api/tasks")


# Автоматически создаем таблицу tasks в базе данных при старте
Base.metadata.create_all(bind=engine)

# Секретный ключ должен быть ТОЧНО ТАКИМ ЖЕ, как в auth_service, чтобы расшифровать токен
JWT_SECRET = "super_secret_key_123"
JWT_ALGORITHM = "HS256"

# URL для внутренних межсервисных запросов в сети Docker Compose
AUTH_SERVICE_URL = "http://auth_service:8000/internal/users"

# Вспомогательная асинхронная функция для проверки пользователя в соседнем сервисе
async def verify_user_exists(user_id: int) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{AUTH_SERVICE_URL}/{user_id}", timeout=2.0)
            return response.status_code == 200
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service is temporarily unavailable"
            )

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

# 1. Создание новой задачи для текущего пользователя (СДЕЛАНА АСИНХРОННОЙ)
@app.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # МИДЛОВСКИЙ КОНТРОЛЬ: Проверяем, существует ли пользователь в auth_service
    user_exists = await verify_user_exists(user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in auth system"
        )

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

# 3. Обновление задачи с жесткой проверкой прав владельца
@app.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Ищем задачу в БД
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
    # МИДЛОВСКИЙ КОНТРОЛЬ: Проверяем, что текущий юзер — хозяин этой задачи
    if task.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this task")
        
    # Обновляем только те поля, которые пришли в запросе
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.is_completed is not None:
        task.is_completed = task_data.is_completed
        
    db.commit()
    db.refresh(task)
    return task

# 4. Удаление задачи с жесткой проверкой прав владельца
@app.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # Ищем задачу в БД
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
    # МИДЛОВСКИЙ КОНТРОЛЬ: Проверяем права на удаление
    if task.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this task")
        
    db.delete(task)
    db.commit()
    return None
