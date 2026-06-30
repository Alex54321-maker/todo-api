from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User
from schemas import UserCreate, UserResponse, UserLogin, Token
from security import get_password_hash, verify_password, create_access_token

app = FastAPI(title="Auth Microservice", version="1.0.0")

# Автоматически создаем таблицы в PostgreSQL при старте микросервиса
Base.metadata.create_all(bind=engine)

# 1. Эндпоинт РЕГИСТРАЦИИ нового пользователя
@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Проверяем, нет ли уже пользователя с таким email
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Хэшируем голый пароль перед отправкой в базу данных
    hashed_pwd = get_password_hash(user_data.password)
    
    # Создаем объект модели SQLAlchemy БЕЗ username
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pwd
    )
    
    db.add(new_user)
    db.commit()          # Жестко сохраняем в базу данных
    db.refresh(new_user) # Обновляем объект, чтобы получить его ID из базы
    return new_user

# 2. Эндпоинт ЛОГИНА (Вход по email и выдача JWT-токена)
@app.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # Ищем пользователя в базе по его email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    # Если юзер не найден или пароль не совпал с хэшем — выдаем 401 ошибку
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Если всё четко — генерируем цифровой пропуск (JWT)
    # Зашиваем внутрь токена ID и email пользователя
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# 3. ВНУТРЕННИЙ ЭНДПОИНТ (Для проверки существования пользователя из task_service)
@app.get("/internal/users/{user_id}")
def check_user_exists(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )
    return {"status": "active", "user_id": user_id}
