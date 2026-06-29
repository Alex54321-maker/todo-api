from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic автоматически ищет эти переменные в окружении (env)
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Настройки для Pydantic v2
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Создаем глобальный объект настроек для импорта в другие файлы
settings = Settings()
