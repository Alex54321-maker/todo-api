# Файл: app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlmodel import Session, select
from jose import jwt, JWTError 

from app.core.database import get_db 
# --- ИСПРАВЛЕННЫЕ ИМПОРТЫ ---
from app.models.user import User  # Таблица базы данных из models
from app.schemas.users import UserCreate, UserResponse, Token  # Схемы валидации из schemas
from app.core.security import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM 

# --- ИМПОРТ НАШИХ КАСТОМНЫХ ОШИБОК ---
from app.core.exceptions import (
    UserAlreadyExistsException, 
    InvalidCredentialsException,
    TokenExpiredException  # Если создавали, или используйте InvalidCredentialsException
)

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    statement = select(User).where(User.username == user_data.username)
    existing_user = db.exec(statement).first()
    
    # Заменили HTTPException на чистый класс ошибки
    if existing_user:
        raise UserAlreadyExistsException()
    
    hashed_pwd = hash_password(user_data.password)
    new_user = User(username=user_data.username, hashed_password=hashed_pwd)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    statement = select(User).where(User.username == form_data.username)
    user = db.exec(statement).first()
    
    # Заменили HTTPException на чистый класс ошибки
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Исправьте URL, если у вас роутер подключается по-другому в main.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Зависимость для проверки JWT-токена. 
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise InvalidCredentialsException()
    except JWTError:
        raise InvalidCredentialsException()
        
    statement = select(User).where(User.username == username)
    user = db.exec(statement).first()
    
    if user is None:
        raise InvalidCredentialsException()
        
    return user
