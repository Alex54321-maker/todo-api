from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings

# --- ДОБАВЛЯЕМ СЮДА ИМПОРТЫ ВСЕХ МОДЕЛЕЙ ---
from app.models.user import User
from app.models.post import Post, PostLike
from app.models.comment import Comment  # <-- Вот теперь SQLModel видит комментарии!
# -------------------------------------------

# 1. Создаем стандартный синхронный движок для PostgreSQL
engine = create_engine(settings.DATABASE_URL, echo=True)

# 2. Синхронная функция-зависимость для получения сессии в роутах
def get_db():
    with Session(engine) as session:
        yield session

# 3. Синхронное автоматическое создание таблиц при старте приложения
def init_db():
    SQLModel.metadata.create_all(engine)
