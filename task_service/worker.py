import json
import asyncio
import aio_pika
import socket
from sqlalchemy.orm import Session
from database import engine
from models import Task

RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

def delete_user_tasks_sync(user_id: int):
    """Синхронная функция для удаления задач из БД."""
    with Session(bind=engine) as db:
        try:
            deleted_count = db.query(Task).filter(Task.owner_id == user_id).delete()
            db.commit()
            print(f"[WORKER] Успешно удалено {deleted_count} задач для user_id={user_id}")
        except Exception as e:
            db.rollback()
            print(f"[WORKER DATABASE ERROR] Ошибка удаления задач: {e}")

async def process_message(message: aio_pika.IncomingMessage):
    """Обработчик входящих сообщений из RabbitMQ."""
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            user_id = payload.get("user_id")
            if user_id:
                print(f"[WORKER] Получено событие удаления пользователя: user_id={user_id}")
                await asyncio.to_thread(delete_user_tasks_sync, user_id)
        except Exception as e:
            print(f"[WORKER ERROR] Ошибка обработки сообщения: {e}")

async def wait_for_rabbitmq(host="rabbitmq", port=5672, timeout=30):
    """Ждет, пока порт RabbitMQ реально начнет принимать входящие соединения."""
    print(f"[WORKER] Ожидание доступности сети брокера {host}:{port}...")
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            print("[WORKER] Сетевой порт RabbitMQ открыт и готов к работе!")
            return True
        except (OSError, asyncio.TimeoutError):
            await asyncio.sleep(2)
    print("[WORKER CRITICAL] Брокер RabbitMQ не ответил по таймауту!")
    return False

async def start_worker():
    """Запуск бесконечного цикла прослушивания очереди с предварительным ожиданием брокера."""
    if not await wait_for_rabbitmq():
        return

    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            
            exchange = await channel.declare_exchange(
                "user_events", 
                type=aio_pika.ExchangeType.FANOUT, 
                durable=True
            )
            
            queue = await channel.declare_queue("task_service_queue", durable=True)
            await queue.bind(exchange, routing_key="")
            
            print("[WORKER] Воркер RabbitMQ успешно запущен и слушает очередь...")
            await queue.consume(process_message)
            
            await asyncio.Future()
        except Exception as e:
            print(f"[WORKER CRASH] Сбой в цикле прослушивания, реконнект через 5 сек... Ошибка: {e}")
            await asyncio.sleep(5)
