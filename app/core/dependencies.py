# Файл: app/api/deps.py
from typing import Generator
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Импортируем настройки из твоего файла security
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.database import SessionLocal 
from app.models import User # Твоя SQLAlchemy модель пользователя

# Указывает FastAPI, откуда брать токен в запросах (заголовок Authorization: Bearer <токен>)
# URL указывает на будущий эндпоинт логина, чтобы работала кнопка Authorize в Swagger (/docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db() -> Generator:
    """Зависимость для создания и закрытия сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """
    Зависимость для проверки JWT-токена.
    Извлекает пользователя из базы данных. Если токен невалиден — кидает 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Декодируем токен, используя твои константы из security.py
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") # В "sub" обычно передают id или email пользователя
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    # Ищем пользователя в БД по ID
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Зависимость для проверки роли.
    Вызывается ТОЛЬКО после успешной проверки токена. Если не админ — кидает 403.
    """
    # Убедись, что в твоей модели User в app/models.py есть поле is_admin (Boolean)
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user
