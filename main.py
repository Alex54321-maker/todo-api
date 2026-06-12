import sys  # <--- ДОЛЖНО БЫТЬ ТУТ
import os   # <--- ДОЛЖНО БЫТЬ ТУТ


# Автоматически добавляем корневую папку проекта в пути Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.router import api_router
from app.middlewares.logging import ProcessTimeMiddleware
from app.core.database import init_db
from fastapi.concurrency import run_in_threadpool 

from sqlalchemy import text
from app.core.database import engine

def drop_old_tables():
    # Полностью синхронная функция очистки таблиц
    with engine.connect() as connection:
        with connection.begin():
            connection.execute(text("DROP TABLE IF EXISTS todo CASCADE;"))
            connection.execute(text("DROP TABLE IF EXISTS \"user\" CASCADE;")) # кавычки для безопасности имени user
            print("=== СТАРЫЕ ТАБЛИЦЫ УСПЕШНО СТЕРТЫ ДЛЯ ОБНОВЛЕНИЯ ===")

async def lifespan(app: FastAPI):
    # 1. Безопасно запускаем синхронную очистку в потоке
    # await run_in_threadpool(drop_old_tables)
    
    # 2. Безопасно запускаем синхронное создание новых таблиц в потоке
    await run_in_threadpool(init_db)
    yield


# 2. Инициализируем FastAPI без отступов (в самом начале строки)
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# 3. Подключаем Middleware
app.add_middleware(ProcessTimeMiddleware)

# 4. Базовый домашний эндпоинт
@app.get("/", tags=["System"])
def home():
    # Внутри функции ровно 4 пробела
    return {"message": "Cloud server is running! Go to /api/v1/docs"}

# 5. Подключаем единый роутер
app.include_router(api_router, prefix=settings.API_V1_STR)

# 6. Блок для локального запуска
if __name__ == "__main__":
    import uvicorn
    # Внутри блока if ровно 4 пробела
    uvicorn.run("main:app", host="0.0.0.0", port=55350, reload=True)
