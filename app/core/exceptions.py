from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Внутренняя ошибка сервера"

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)

class UserAlreadyExistsException(BaseAPIException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Пользователь с таким именем уже существует"

class InvalidCredentialsException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Неверное имя пользователя или пароль"

class TokenExpiredException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Срок действия токена истек"

class TodoNotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Задача не найдена"

class TodoAccessDeniedException(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "У вас нет прав на редактирование или удаление этой задачи"
