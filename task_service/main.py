import httpx
import json
import aio_pika
from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from jwt import decode, PyJWTError

from schemas import TaskCreate, TaskResponse, TaskUpdate
from database import engine, Base, get_db
from models import Task
import asyncio
from contextlib import asynccontextmanager
from worker import start_worker  
import crud  # Подключаем наш CRUD слой

@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(start_worker()) 
    yield
    worker_task.cancel()

app = FastAPI(
    title="Task Microservice", 
    version="1.0.0", 
    root_path="/api/tasks",
    redirect_slashes=False,  # <--- ДОБАВЛЯЕМ ЭТУ СТРОКУ! Запрещаем принудительный редирект на слэш
    lifespan=lifespan  
)

Base.metadata.create_all(bind=engine)

JWT_SECRET = "super_secret_key_123"
JWT_ALGORITHM = "HS256"
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

def get_current_user_id(authorization: str = Header(...)) -> int:
    try:
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
            
        payload = decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token missing user ID")
        return int(user_id)
        
    except (PyJWTError, ValueError):
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# --- ПРОДЮСЕР СОБЫТИЙ (RABBITMQ PRODUCER) ---
async def publish_task_created(task_id: int, user_id: int, title: str):
    try:
        # Подключаемся к брокеру сообщений
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            
            # Объявляем ту же очередь, которую будет слушать воркер
            queue = await channel.declare_queue("task_created_queue", durable=True)
            
            # Формируем тело сообщения
            message_body = {
                "event": "task.created",
                "task_id": task_id,
                "user_id": user_id,
                "title": title
            }
            
            # Отправляем сообщение в очередь
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message_body).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # Чтобы сообщение не пропало при перезапуске RabbitMQ
                ),
                routing_key="task_created_queue",
            )
            print(f"[ПРОДЮСЕР] 🚀 Событие task.created отправлено для задачи {task_id}")
    except Exception as e:
        # Логируем ошибку, но не ломаем создание задачи для пользователя
        print(f"[ПРОДЮСЕР ОШИБКА] ❌ Не удалось отправить событие в RabbitMQ: {e}")


# --- АВТОМАТИЧЕСКАЯ ПРОВЕРКА ПРАВ (404 И 403 FORBIDDEN CONTROL) ---
def get_owned_task(
    task_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> Task:
    task = crud.get_task_by_id(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Task not found"
        )
        
    if task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to access this task"
        )
        
    return task


# --- ЭНДПОИНТЫ ---

@app.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # ВРЕМЕННО ОТКЛЮЧИЛИ ДЛЯ ТЕСТА ОЧЕРЕДИ:
    # user_exists = await verify_user_exists(user_id)
    # if not user_exists:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found in auth system"
    #     )
    
    # 1. Создаем задачу в базе данных сервиса задач
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
def update_task(
    task_data: TaskUpdate, 
    db: Session = Depends(get_db), 
    task: Task = Depends(get_owned_task)
):
    return crud.update_user_task(db, task, task_data)


@app.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    db: Session = Depends(get_db), 
    task: Task = Depends(get_owned_task)
):
    crud.delete_user_task(db, task)
    return None
