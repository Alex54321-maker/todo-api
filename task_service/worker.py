import json
import asyncio
import aio_pika
# Удаляем прямой импорт Task, импортируем наш crud-слой
import crud 
from sqlalchemy.orm import Session
from database import engine

RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

def process_user_deletion_sync(user_id: int):
    """Синхронная обертка для выполнения CRUD-операции в контексте сессии."""
    with Session(bind=engine) as db:
        try:
            # Вызываем изолированную функцию из crud.py с правильным полем user_id
            deleted_count = crud.delete_all_user_tasks(db, user_id)
            print(f"[WORKER] Успешно вычищено {deleted_count} задач для user_id={user_id}")
        except Exception as e:
            db.rollback()
            print(f"[WORKER DATABASE ERROR] Ошибка при удалении задач юзера {user_id}: {e}")
            raise e # Пробрасываем ошибку выше, чтобы воркер знал о сбое

async def process_message(message: aio_pika.IncomingMessage):
    """Обработчик входящих сообщений из RabbitMQ."""
    # Используем ручное подтверждение/отклонение для безопасности данных
    async with message.process(requeue=True): 
        try:
            payload = json.loads(message.body.decode())
            user_id = payload.get("user_id")
            
            if user_id:
                print(f"[WORKER] Получено событие удаления пользователя: user_id={user_id}")
                # Выполняем синхронный тяжелый запрос к БД в отдельном потоке
                await asyncio.to_thread(process_user_deletion_sync, user_id)
            else:
                print(f"[WORKER WARNING] В сообщении отсутствует user_id: {payload}")
                
        except Exception as e:
            print(f"[WORKER ERROR] Критическая ошибка обработки сообщения: {e}")
            # Благодарю асинхронному контексту message.process(requeue=True), 
            # при вылете исключения сообщение вернется в очередь RabbitMQ и не пропадет.

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
