from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cloud FastAPI with UV & SQLModel"
    API_V1_STR: str= "/api/v1"
  
    # 💡 ВАЖНО: Используем чистый "postgresql://", убрав асинковское "+asyncpg"
    DATABASE_URL: str = "postgresql://user@/postgres?host=/tmp/postgres"

settings = Settings()
