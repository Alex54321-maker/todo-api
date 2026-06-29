# Файл: app/core/security.py
from datetime import datetime, timedelta, timezone
import jwt  # Импортируем именно как jwt, а не pyjwt!
import bcrypt

# Настройки для токена (в будущем их можно вынести в app/core/config.py)
SECRET_KEY = "SUPER_SECRET_RANDOM_STRING_CHANGE_ME"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Хеширует чистый пароль через bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли чистый пароль с хэшем из базы."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict) -> str:
    """Генерирует зашифрованный JWT-токен."""
    to_encode = data.copy()
    # Устанавливаем время жизни токена в формате UTC
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Кодируем данные с помощью нашего секретного ключа
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
