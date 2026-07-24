import httpx
import json
import aio_pika
from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from schemas import TaskCreate, TaskResponse, TaskUpdate
from database import engine, Base, get_db
from models import Task
import asyncio
from contextlib import asynccontextmanager
from worker import start_worker  
import crud  # Подключаем наш CRUD слой

# 🔒 Импортируем вашу функцию декодирования из security.py
from security import decode_access_token  

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(start_worker()) 
    yield
    worker_task.cancel()

app = FastAPI(
    title="Task Microservice", 
    version="1.0.0", 
    root_path="/api/tasks",
    redirect_slashes=False,  # Запрещаем принудительный редирект на слэш
    lifespan=lifespan  
)

Base.metadata.create_all(bind=engine)

AUTH_SERVICE_URL = "http://auth_service:8000/internal/users"
RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

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

# ✨ Переписанная зависимость, которая использует ваш security.py
def get_current_user_id(authorization: str = Header(...)) -> int:
    user_id = decode_access_token(authorization)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials or missing user ID"
        )
    return user_id

# --- ПРОДЮСЕР СОБЫТИЙ (RABBITMQ PRODUCER) ---
async def publish_task_created(task_id: int, user_id: int, title: str):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            
            # Очередь, которую теперь слушает и наш воркер соцсети
            queue = await channel.declare_queue("task_created_queue", durable=True)
            
            message_body = {
                "event": "task.created",
                "id": task_id,        # Передаем как 'id' для совместимости с воркером
                "task_id": task_id,   # На всякий случай оставляем и 'task_id'
                "user_id": user_id,
                "title": title
            }
            
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message_body).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key="task_created_queue",
            )
            print(f"[ПРОДЮСЕР] 🚀 Событие task.created успешно отправлено в очередь для задачи {task_id}")
    except Exception as e:
        print(f"[ПРОДЮСЕР ОШИБКА] ❌ Не удалось отправить событие в RabbitMQ: {e}")

# --- АВТОМАТИЧЕСКАЯ ПРОВЕРКА ПРАВ ---
def get_owned_task(
    task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> Task:
    task = crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No permission")
    return task

# --- ЭНДПОИНТЫ ---

@app.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate, 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)  # 🔒 Авторизация успешно возвращена!
):
    # 1. Создаем задачу в базе данных сервиса задач с реальным user_id из JWT-токена
    new_task = crud.create_user_task(db, task_data, user_id)
    
    # 2. Асинхронно отправляем событие в RabbitMQ для соцсети
    asyncio.create_task(publish_task_created(
        task_id=new_task.id, 
        user_id=new_task.user_id, 
        title=new_task.title
    ))
    
    return new_task

@app.get("/", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return crud.get_user_tasks(db, user_id)

@app.put("/{task_id}", response_model=TaskResponse)
def update_task(task_data: TaskUpdate, db: Session = Depends(get_db), task: Task = Depends(get_owned_task)):
    return crud.update_user_task(db, task, task_data)

@app.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(db: Session = Depends(get_db), task: Task = Depends(get_owned_task)):
    crud.delete_user_task(db, task)
    return None
