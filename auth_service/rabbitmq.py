import json
import aio_pika

RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

async def publish_user_deleted_event(user_id: int):
    """Отправляет событие об удалении пользователя в RabbitMQ."""
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                "user_events", 
                type=aio_pika.ExchangeType.FANOUT, 
                durable=True
            )
            message_body = json.dumps({"user_id": user_id}).encode()
            await exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=""
            )
            print(f"[RABBITMQ] Успешно отправлено событие удаления для user_id={user_id}")
    except Exception as e:
        print(f"[RABBITMQ ERROR] Не удалось отправить событие: {e}")
