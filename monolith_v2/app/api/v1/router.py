from fastapi import APIRouter, Depends
from sqlmodel import Session
from sqlalchemy import text
from app.api.v1.endpoints.posts import router as posts_router
# Правильные явные импорты роутеров
from app.api.v1.endpoints.todos import router as todos_router
from app.api.v1.endpoints.workers import router as workers_router
from app.api.v1.endpoints.auth import router as auth_router
from app.core.database import get_db  
# 1. ДОБАВЬ ЭТОТ ИМПОРТ:
from app.api.v1.endpoints.comments import router as comments_router
api_router = APIRouter()

# Подключение роутеров с обновленными именами переменных
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(todos_router, prefix="/todos", tags=["TODO CRUD"])
api_router.include_router(workers_router, tags=["Day 2 Legacy"])
api_router.include_router(posts_router, prefix="/posts", tags=["Posts"])
@api_router.get("/status", tags=["System"])
def get_system_status(db: Session = Depends(get_db)): 
    """
    Проверяет, жива ли база данных PostgreSQL.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected (Error: {str(e)})"

    return {
        "status": "running",
        "database": db_status
    }
# 2. ДОБАВЬ ЭТУ СТРОЧКУ В САМЫЙ КОНЕЦ:
api_router.include_router(comments_router, prefix="/posts", tags=["Comments"])