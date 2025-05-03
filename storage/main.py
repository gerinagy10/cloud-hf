import asyncio
import os
import aio_pika
import asyncpg
import json

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

RABBITMQ_URL = os.environ.get('RABBITMQ_CONNECTION') #"amqp://localhost/"
PROCESSED_EXCHANGE = "processed"
STORAGE_QUEUE = "storage_requests"
RESPONSE_EXCHANGE = "storage_done"
RESPONSE_QUEUE = "notifier_responses"

POSTGRES_DSN = os.environ.get('POSTGRE_CONNECTION') #"postgresql://postgres:postgres@localhost:5432/cloudhf"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_pool = None

class Detection(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int
    text: str
    image_base64: str
    human_count: int
    created_at: datetime


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(dsn=POSTGRES_DSN)
    asyncio.create_task(consume_messages())
    print("Storage service started!")


@app.get("/detections", response_model=List[Detection])
async def get_detections():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, text, image_base64, human_count, created_at FROM detections ORDER BY created_at DESC"
        )
        return [dict(row) for row in rows]



async def save_to_db(pool, text, image_base64, human_count):
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO detections (text, image_base64, human_count)
            VALUES ($1, $2, $3)
        ''', text, image_base64, human_count)


async def consume_messages():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    processed_exchange = await channel.declare_exchange(PROCESSED_EXCHANGE, aio_pika.ExchangeType.DIRECT)
    response_exchange = await channel.declare_exchange(RESPONSE_EXCHANGE, aio_pika.ExchangeType.DIRECT)

    queue = await channel.declare_queue(STORAGE_QUEUE, durable=True)
    await queue.bind(processed_exchange, routing_key=STORAGE_QUEUE)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                try:
                    data = json.loads(message.body)

                    text = data.get("text", "")
                    image_base64 = data.get("image", "")
                    human_count = data.get("human_count", 0)

                    await save_to_db(db_pool, text, image_base64, human_count)
                    print(f"Saved record to DB: {text}, {human_count} humans")

                    await response_exchange.publish(
                        aio_pika.Message(body=json.dumps(data).encode()),
                        routing_key=RESPONSE_QUEUE
                    )
                    print(f"Sent response back to Notifier for sid: {data.get('sid')}")

                except Exception as e:
                    print(f"Failed to process message: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
