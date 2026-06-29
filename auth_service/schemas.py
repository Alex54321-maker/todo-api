from pydantic import BaseModel, EmailStr, Field

# Схема для входных данных при регистрации
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта пользователя")
    password: str = Field(..., min_length=6, description="Пароль (минимум 6 символов)")

# Схема для входных данных при логине
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта для входа")
    password: str = Field(..., description="Пароль")

# Схема для ответа сервера (что отдаем наружу)
class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True  # Чтобы Pydantic умел читать данные из моделей SQLAlchemy

# Схема для выдачи JWT-токена
class Token(BaseModel):
    access_token: str
    token_type: str
