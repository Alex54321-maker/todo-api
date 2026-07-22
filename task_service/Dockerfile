FROM python:3.10-slim

# Указываем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей из папки task_service в контейнер
COPY requirements.txt .

# Устанавливаем библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код сервиса
COPY . .

# Запускаем микросервис на порту 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
