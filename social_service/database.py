import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

# Сначала проверяем переменную окружения от Docker, если пусто — берем из config
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# Создаем движок, который теперь точно увидит хост social_db
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_social_db():
    """Фабрика сессий для эндпоинтов лайков."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
