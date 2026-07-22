import json
import asyncio
import aio_pika
import logging
import crud 
from sqlalchemy.orm import Session
from database import engine

# 1. Настраиваем логирование для Project IDX терминала
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("task_worker")

# НАДО ВОТ ТАК:
RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

def process_user_deletion_sync(user_id: int):
    """Синхронная обертка для выполнения CRUD-операции в контексте сессии."""
    with Session(bind=engine) as db:
        try:
            deleted_count = crud.delete_all_user_tasks(db, user_id)
            logger.info(f"Успешно вычищено {deleted_count} задач для user_id={user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка базы данных при удалении задач юзера {user_id}: {e}")
            raise e  # Пробрасываем выше, чтобы сработало исключение в асинхронном контексте

async def process_message(message: aio_pika.IncomingMessage):
    """Обработчик входящих сообщений из RabbitMQ."""
    # requeue=True вернет сообщение в очередь ТОЛЬКО если упадет исключение
    async with message.process(requeue=True): 
        try:
            payload = json.loads(message.body.decode())
            
            # Валидация JSON: если структура битая, requeue не поможет. Ловим KeyError/TypeError отдельно
            if not isinstance(payload, dict):
                logger.warning(f"Неверный формат payload (ожидался dict): {payload}")
                return  # Выходим без raise, сообщение подтвердится (ack) и удалится
                
            user_id = payload.get("user_id")
            
            if user_id:
                logger.info(f"Получено событие удаления пользователя: user_id={user_id}")
                await asyncio.to_thread(process_user_deletion_sync, user_id)
            else:
                logger.warning(f"В сообщении отсутствует user_id: {payload}")
                
        except json.JSONDecodeError as je:
            logger.error(f"Ошибка парсинга JSON, сообщение повреждено: {je}")
            # Не бросаем исключение дальше, чтобы битый JSON не зациклил очередь
            
        except Exception as e:
            logger.error(f"Критическая ошибка обработки сообщения: {e}")
            # Даем системе передышку на 2 секунды перед тем, как контекстный менеджер 
            # вернет сообщение обратно в RabbitMQ (защита от CPU-spamming при падении БД)
            await asyncio.sleep(2)
            raise e

async def wait_for_rabbitmq(host="rabbitmq", port=5672, timeout=30):
    """Ждет, пока порт RabbitMQ реально начнет принимать входящие соединения."""
    logger.info(f"Ожидание доступности сети брокера {host}:{port}...")
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            logger.info("Сетевой порт RabbitMQ открыт и готов к работе!")
            return True
        except (OSError, asyncio.TimeoutError):
            await asyncio.sleep(2)
    logger.critical("Брокер RabbitMQ не ответил по таймауту!")
    return False

async def start_worker():
    """Запуск бесконечного цикла прослушивания очереди с предварительным ожиданием брокера."""
    # ИСПРАВЛЯЕМ ТУТ: меняем "localhost" на "rabbitmq"
    if not await wait_for_rabbitmq(host="rabbitmq"):
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
            
            logger.info("Воркер RabbitMQ успешно запущен и слушает очередь...")
            await queue.consume(process_message)
            
            await asyncio.Future()
        except Exception as e:
            logger.error(f"Сбой в цикле прослушивания, реконнект через 5 сек... Ошибка: {e}")
            await asyncio.sleep(5)
if __name__ == "__main__":
    try:
        asyncio.run(start_worker())
    except KeyboardInterrupt:
        print("[WORKER] Воркер остановлен вручную.")
