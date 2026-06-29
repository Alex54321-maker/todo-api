from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    """Схема для регистрации нового пользователя с жесткой валидацией"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=8, max_length=50, description="Пароль")

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not any(char.isupper() for char in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        return v

class UserResponse(BaseModel):
    """Схема ответа: отдаем только безопасные данные, скрывая хэш пароля"""
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Схема, которую клиент получит при успешном входе (Login)"""
    access_token: str
    token_type: str = "bearer"
