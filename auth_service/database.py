from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

# 1. Создаем движок (Engine) для работы с PostgreSQL
# Передаем адрес базы из нашего объекта настроек settings
engine = create_engine(settings.DATABASE_URL)

# 2. Создаем фабрику сессий (SessionLocal)
# Каждая сессия — это отдельное подключение для выполнения SQL-запросов
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Базовый класс для моделей
# От него будут наследоваться наши таблицы (например, модель User)
Base = declarative_base()

# 4. Генератор сессий базы данных (Dependency)
# Будет автоматически открывать подключение при запросе и закрывать его после финиша
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

