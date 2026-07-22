import asyncio
import json
import aio_pika

async def process_message(message: aio_pika.IncomingMessage):
    """Функция обработки каждого входящего сообщения."""
    async with message.process():
        try:
            # Декодируем байты в JSON-словарь
            payload = json.loads(message.body.decode())
            print(f"\n[ВОРКЕР] 🔔 Поймал новое событие из RabbitMQ!")
            print(f"[ВОРКЕР] Тип события: {payload.get('event')}")
            print(f"[ВОРКЕР] Кто подписался (Follower ID): {payload.get('follower_id')}")
            print(f"[ВОРКЕР] На кого (Following ID): {payload.get('following_id')}\n")
            
        except Exception as e:
            print(f"[ВОРКЕР] ❌ Ошибка при разборе сообщения: {e}")

async def main():
    # Подключаемся к RabbitMQ (Docker-хост 'rabbitmq')
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    
    # Открываем канал связи
    channel = await connection.channel()
    
    # Устанавливаем лимит: обрабатывать строго по 1 сообщению за раз
    await channel.set_qos(prefetch_count=1)
    
    # Подключаемся к нашей долговечной очереди
    queue = await channel.declare_queue("subscription_events", durable=True)
    
    print("[*] Фоновый Воркер Подписок запущен. Ожидание новых сообщений...")
    
    # Начинаем бесконечное прослушивание очереди
    await queue.consume(process_message)
    
    # Держим процесс запущенным
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Воркер остановлен пользователем.")
