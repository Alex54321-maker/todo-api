from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

# 1. Создаем отдельный движок (Engine) для Task-Service
engine = create_engine(settings.DATABASE_URL)

# 2. Создаем фабрику сессий для работы с задачами
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Базовый класс для моделей таблиц Task-Service
Base = declarative_base()

# 4. Наш любимый Middle-генератор сессий с оператором yield
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
