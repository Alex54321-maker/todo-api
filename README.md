# 🚀 FastAPI Social & TODO Backend API

Современный бэкенд для двух приложений (соцсеть и менеджер задач) с полной авторизацией и контейнеризацией.

## 🛠 Стек технологий
* **Framework:** FastAPI, Pydantic v2
* **Database & ORM:** PostgreSQL, SQLModel (SQLAlchemy)
* **Security:** JWT Auth, Passlib (Bcrypt), OAuth2
* **DevOps:** Docker, Docker Compose

## ⚡ Фичи проекта
* Регистрация и JWT-авторизация пользователей с жесткой валидацией паролей.
* **TODO CRUD:** Приватные задачи с привязкой к пользователю.
* **Social API:** Создание постов, Toggle-логика лайков, комментарии под публикациями.
* Автоматическая генерация документации через Swagger UI.
* Полная изоляция приложения и БД через Docker.

## 🚀 Как запустить локально (через Docker)
1. Склонируйте репозиторий.
2. Запустите команду в терминале:
```bash
docker compose up --build
```
3. Откройте Swagger UI по адресу: `http://127.0.0`
