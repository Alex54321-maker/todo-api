import asyncio
import json
import aio_pika

async def process_message(message: aio_pika.IncomingMessage):
    """Функция обработки каждого входящего сообщения из всех очередей."""
    async with message.process():
        try:
            # Декодируем байты в JSON-словарь
            payload = json.loads(message.body.decode())
            event_type = payload.get("event")
            
            print(f"\n[ВОРКЕР] 🔔 Поймал новое событие из RabbitMQ!")
            print(f"[ВОРКЕР] Тип события: {event_type}")
            
            # Разводка логики в зависимости от типа события
            if event_type == "subscription.created":
                print(f"[ВОРКЕР] Кто подписался (Follower ID): {payload.get('follower_id')}")
                print(f"[ВОРКЕР] На кого (Following ID): {payload.get('following_id')}\n")
                
            elif event_type == "task.created":
                print(f"[ВОРКЕР] ID созданной задачи: {payload.get('task_id')}")
                print(f"[ВОРКЕР] Создатель задачи (User ID): {payload.get('user_id')}")
                print(f"[ВОРКЕР] Название задачи: '{payload.get('title')}'")
                print(f"[ВОРКЕР] ⚡ СКОРО: Здесь будет автоматическая генерация счетчика лайков в micro_social_db!\n")
            
            else:
                print(f"[ВОРКЕР] ⚠️ Неизвестный тип события: {event_type}\n")
            
        except Exception as e:
            print(f"[ВОРКЕР] ❌ Ошибка при разборе сообщения: {e}")

async def main():
    # Подключаемся к RabbitMQ (Docker-хост 'rabbitmq')
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    
    # Открываем канал связи
    channel = await connection.channel()
    
    # Устанавливаем лимит: обрабатывать строго по 1 сообщению за раз
    await channel.set_qos(prefetch_count=1)
    
    # Объявляем и подключаемся к очереди ПОДПИСОК
    sub_queue = await channel.declare_queue("subscription_events", durable=True)
    await sub_queue.consume(process_message)
    
    # Объявляем и подключаемся к очереди ЗАДАЧ
    task_queue = await channel.declare_queue("task_created_queue", durable=True)
    await task_queue.consume(process_message)
    
    print("[*] Фоновый Воркер Соцсети запущен.")
    print("[*] Ожидание событий (подписки и создание задач)...")
    
    # Держим процесс запущенным
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Воркер остановлен пользователем.")
