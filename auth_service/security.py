from datetime import datetime, timedelta, timezone
from jwt import encode, decode, PyJWTError
from passlib.context import CryptContext
from config import settings

# 1. Настраиваем утилиту для хэширования паролей через bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Функция для создания хэша пароля (для регистрации)
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 3. Функция для проверки пароля (для логина)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 4. Функция для генерации JWT-токена доступа
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    
    # Считаем время протухания токена
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Добавляем время истечения в полезную нагрузку (payload) токена
    to_encode.update({"exp": expire})
    
    # Кодируем данные в строку-токен с помощью нашего секретного ключа
    encoded_jwt = encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt
