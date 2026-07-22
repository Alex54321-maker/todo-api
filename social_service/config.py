from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ЗАМЕНЯЕМ localhost НА ИМЕНА КОНТЕЙНЕРОВ ДЛЯ РАБОТЫ В DOCKER
    DATABASE_URL: str = "postgresql://postgres:postgres@micro_postgres_db:5432/micro_social_db"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq_broker:5672/"

    class Config:
        env_file = ".env"

settings = Settings()

