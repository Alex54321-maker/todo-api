import os
import json
import asyncio
import aio_pika
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

# 1. Настройки подключения
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@social_db:5432/micro_social_db")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

# 2. Инициализация асинхронной SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def auto_like_new_task(task_id: int):
    """
    Воркер перехватывает создание задачи и ставит ей приветственный лайк от Системы (user_id = 0).
    """
    SYSTEM_USER_ID = 0
    
    async with async_session() as session:
        async with session.begin():
            # Защита от дубликатов
            check_query = text("SELECT 1 FROM likes WHERE user_id = :user_id AND post_id = :post_id LIMIT 1;")
            result = await session.execute(check_query, {"user_id": SYSTEM_USER_ID, "post_id": task_id})
            exists = result.scalar()

            if not exists:
                insert_query = text("INSERT INTO likes (user_id, post_id) VALUES (:user_id, :post_id);")
                try:
                    await session.execute(insert_query, {"user_id": SYSTEM_USER_ID, "post_id": task_id})
                    print(f"[ВОРКЕР] ✅ Задача #{task_id} зарегистрирована. Системный лайк успешно поставлен!")
                except Exception as db_err:
                    print(f"[ВОРКЕР] ❌ Ошибка записи в таблицу 'likes': {db_err}")
            else:
                print(f"[ВОРКЕР] ℹ️ Задача #{task_id} уже обрабатывалась воркером ранее.")

async def on_message(message: aio_pika.IncomingMessage):
    """Обработчик сообщений из RabbitMQ"""
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            print(f"[ВОРКЕР] 🔔 Поймал новое событие: {payload}")
            
            event_type = payload.get("event")
            task_id = payload.get("id") or payload.get("task_id")
            
            if event_type == "task.created" and task_id:
                print(f"[ВОРКЕР] 🔄 Интеграция задачи ID: {task_id} в социальную сеть...")
                await auto_like_new_task(int(task_id))
            else:
                print(f"[ВОРКЕР] ℹ️ Событие '{event_type}' пропущено (не требует синхронизации БД).")
                
        except Exception as e:
            print(f"[ВОРКЕР] ❌ Критическая ошибка обработки сообщения: {e}")

async def main():
    """Точка входа воркера"""
    print("[ВОРКЕР] 🚀 Фоновый синхронизатор запущен и готовится к подключению...")
    
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        
        # 🎯 СИНХРОНИЗИРОВАНО: Слушаем именно ту очередь, в которую шлет таск-сервис
        queue = await channel.declare_queue("task_created_queue", durable=True)
        print(f"[ВОРКЕР] 🎧 Канал связи открыт. Слушаю очередь: '{queue.name}'...")
        
        await queue.consume(on_message)
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[ВОРКЕР] 🛑 Процесс остановлен.")
