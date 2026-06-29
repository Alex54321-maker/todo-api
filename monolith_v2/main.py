import sys  
import os   
from fastapi import FastAPI
from fastapi.responses import FileResponse  # <-- ДОБАВИЛИ ДЛЯ ФРОНТЕНДА
from fastapi.staticfiles import StaticFiles  # <-- ДОБАВИЛИ ДЛЯ ПАПКИ STATIC
from contextlib import asynccontextmanager
from sqlalchemy import text

# Автоматически добавляем корневую папку проекта в пути Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.api.v1.router import api_router
from app.middlewares.logging import ProcessTimeMiddleware
from app.core.database import init_db, engine
from fastapi.concurrency import run_in_threadpool 
from fastapi.middleware.cors import CORSMiddleware

def drop_old_tables():
    """Полностью синхронная функция очистки таблиц."""
    with engine.connect() as connection:
        with connection.begin():
            connection.execute(text("DROP TABLE IF EXISTS todo CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS \"user\" CASCADE;")) 
            print("=== СТАРЫЕ ТАБЛИЦЫ УСПЕШНО СТЕРТЫ ДЛЯ ОБНОВЛЕНИЯ ===")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Безопасно запускаем синхронное создание новых таблиц в потоке
    await run_in_threadpool(init_db)
    yield

# Инициализируем FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Подключаем Middleware
app.add_middleware(ProcessTimeMiddleware)
# Наш новый мидлвар безопасности CORS (добавляем сразу ниже)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
origins = [origin.strip() for origin in allowed_origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ГЛАВНЫЙ РОУТ СВЯЗИ С ФРОНТЕНДОМ

@app.get("/", tags=["System"])
def home():
    """Абсолютно точный путь к нашей главной странице index.html."""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(current_dir, "static", "index.html")
    return FileResponse(index_path)

# Подключаем единый роутер бэкенда
app.include_router(api_router, prefix=settings.API_V1_STR)

# МОНТИРУЕМ ПАПКУ STATIC (чтобы работали будущие стили, картинки и скрипты)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Блок для локального запуска (если запускать без Докера)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=55350, reload=True)
