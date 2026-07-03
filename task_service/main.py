import httpx
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
    lifespan=lifespan  
)

Base.metadata.create_all(bind=engine)

JWT_SECRET = "super_secret_key_123"
JWT_ALGORITHM = "HS256"
AUTH_SERVICE_URL = "http://auth_service:8000/internal/users"

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
    user_exists = await verify_user_exists(user_id)
    if not user_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in auth system"
        )
    return crud.create_user_task(db, task_data, user_id)


@app.get("/", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return crud.get_user_tasks(db, user_id)


@app.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_data: TaskUpdate, 
    db: Session = Depends(get_db), 
    task: Task = Depends(get_owned_task)  # Чистый перехват контроля прав
):
    return crud.update_user_task(db, task, task_data)


@app.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    db: Session = Depends(get_db), 
    task: Task = Depends(get_owned_task)  # Чистый перехват контроля прав
):
    crud.delete_user_task(db, task)
    return None
