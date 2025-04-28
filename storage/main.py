import asyncio
import aio_pika
import asyncpg
import json

RABBITMQ_URL = "amqp://localhost/"
PROCESSED_EXCHANGE = "processed"
STORAGE_QUEUE = "storage_requests"
RESPONSE_EXCHANGE = "storage_done"
RESPONSE_QUEUE = "notifier_responses"

POSTGRES_DSN = "postgresql://postgres:postgres@localhost:5432/cloudhf"

async def save_to_db(pool, text, image_base64, human_count):
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO detections (text, image_base64, human_count)
            VALUES ($1, $2, $3)
        ''', text, image_base64, human_count)

async def main():

    # db_pool = await asyncpg.create_pool(dsn=POSTGRES_DSN)
    # print("Connected to PostgreSQL!")

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    processed_exchange = await channel.declare_exchange(PROCESSED_EXCHANGE, aio_pika.ExchangeType.DIRECT)
    response_exchange = await channel.declare_exchange(RESPONSE_EXCHANGE, aio_pika.ExchangeType.DIRECT)

    queue = await channel.declare_queue(STORAGE_QUEUE, durable=True)
    await queue.bind(processed_exchange, routing_key=STORAGE_QUEUE)

    print("Waiting for messages...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                try:
                    data = json.loads(message.body)

                    text = data.get('text', '')
                    image_base64 = data.get('image', '')
                    human_count = data.get('human_count', 0)

                    # # Save into DB
                    # await save_to_db(db_pool, text, image_base64, human_count)
                    # print(f"Saved record to DB: {text}, {human_count} humans")

                    await response_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(data).encode()
                        ),
                        routing_key=RESPONSE_QUEUE
                    )
                    print(f"Sent response back to Notifier for sid: {data.get('sid')}")

                except Exception as e:
                    print(f"Failed to process message: {e}")

if __name__ == "__main__":
    asyncio.run(main())
