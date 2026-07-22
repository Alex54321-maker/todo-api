from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import crud
from models import Base
from database import engine, get_social_db
from crud import toggle_subscription
from pydantic import BaseModel
from typing import List, Dict
from fastapi.responses import FileResponse
import os
import json
import aio_pika

# 🔥 Магия: SQLAlchemy автоматически проверит и создаст таблицы в micro_social_db
Base.metadata.create_all(bind=engine)

# Описание входящего запроса от task_service
class LikesBatchRequest(BaseModel):
    entity_ids: List[int]

# Описание типа ответа
LikesBatchResponse = Dict[str, int]

app = FastAPI(
    title="Micro Social Service",
    description="Сервис лайков и подписок на idx.dev",
    version="1.0.0",
)

# 🎯 ОСТАВИЛИ ТОЛЬКО ОДИН ПРАВИЛЬНЫЙ ВАРИАНТ ФУНКЦИИ:
@app.get("/")
def read_root():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path_to_frontend = os.path.join(current_dir, "index.html")
    
    if os.path.exists(path_to_frontend):
        return FileResponse(path_to_frontend)
    return {"status": f"Файл не найден по пути: {path_to_frontend}"}

# 🎯 ИСПРАВЛЕНО: Добавлены все три варианта путей для точной склейки шлюзом Nginx
@app.post("/toggle", status_code=status.HTTP_200_OK)
@app.post("/toggle/", status_code=status.HTTP_200_OK)
@app.post("//toggle", status_code=status.HTTP_200_OK)
def toggle_like(
    user_id: int, 
    task_id: int, 
    db: Session = Depends(get_social_db)
):
    """Эндпоинт-переключатель лайков."""
    try:
        result = crud.toggle_like(db=db, user_id=user_id, task_id=task_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке лайка: {str(e)}"
        )

# 🎯 ИСПРАВЛЕНО: Добавлены три варианта путей для Nginx + асинхронный деф (async def) для работы RabbitMQ
@app.post("/subscriptions/toggle", status_code=status.HTTP_200_OK)
@app.post("/subscriptions/toggle/", status_code=status.HTTP_200_OK)
@app.post("//subscriptions/toggle", status_code=status.HTTP_200_OK)
async def toggle_subscription(
    follower_id: int, 
    following_id: int, 
    db: Session = Depends(get_social_db)
):
    """Эндпоинт-переключатель подписок с уведомлением в RabbitMQ."""
    try:
        # 1. Сначала железно отрабатываем стандартную логику в базе данных PostgreSQL через crud
        result = crud.toggle_subscription(
            db=db, 
            follower_id=follower_id, 
            following_id=following_id
        )
        
        # 2. Асинхронно отправляем событие в RabbitMQ
        # Мы заворачиваем это в try/except, чтобы если брокер "прилег", подписка в БД всё равно сработала
        try:
            # 'rabbitmq' — это имя сервиса из вашего docker-compose.yml
            connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
            async with connection:
                channel = await connection.channel()
                
                # Создаем или подключаемся к долговечной (durable) очереди событий подписок
                queue = await channel.declare_queue("subscription_events", durable=True)
                
                # Формируем тело события. result.get("status") подскажет "subscribed" или "unsubscribed"
                event_body = {
                    "event": f"user_{result.get('status', 'toggled')}",
                    "follower_id": follower_id,
                    "following_id": following_id
                }
                
                # Публикуем сообщение в очередь
                await channel.default_exchange.publish(
                    aio_pika.Message(body=json.dumps(event_body).encode()),
                    routing_key=queue.name
                )
                print(f" [x] Событие подписки успешно отправлено в RabbitMQ: {event_body}")
                
        except Exception as rabbit_err:
            # Если RabbitMQ выдал ошибку, просто пишем в логи контейнера. Главное — БД уже обновилась!
            print(f" ПРЕДУПРЕЖДЕНИЕ: Не удалось отправить событие в RabbitMQ: {rabbit_err}")

        # Возвращаем стандартный ответ вашего crud.py обратно на фронтенд
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке подписки: {str(e)}"
        )

@app.get("/subscriptions/following")
def read_following(follower_id: int, db: Session = Depends(get_social_db)):
    try:
        following_ids = crud.get_following_list(db, follower_id=follower_id)
        return {
            "follower_id": follower_id,
            "following": following_ids,
            "count": len(following_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении подписок: {str(e)}")

# Этот эндпоинт принимает список ID задач и возвращает словарь с количеством лайков
@app.post("/api/v1/likes/batch", response_model=Dict[int, int])
def get_likes_batch(payload: LikesBatchRequest, db: Session = Depends(get_social_db)):
    # Вызываем нашу новую функцию из crud.py, передавая туда список entity_ids
    likes_map = crud.get_likes_count_batch(db, entity_ids=payload.entity_ids)
    return likes_map
