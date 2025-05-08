import asyncio
import os
import aio_pika
import json
import socketio
import uvicorn
import jsonpickle

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

RABBITMQ_URL = os.environ.get('RABBITMQ_CONNECTION') #"amqp://localhost/"
REQUEST_EXCHANGE = "requests"
RESPONSE_EXCHANGE = "storage_done"
REQUEST_QUEUE = "detection_requests"
RESPONSE_QUEUE = "notifier_responses"

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    max_http_buffer_size=100000000
)

app = FastAPI()
socketio_app = socketio.ASGIApp(sio, other_asgi_app=app)

app_with_cors = CORSMiddleware(
    app=socketio_app,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

producer_connection = None
producer_channel = None

connected_clients = set()

@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)
    connected_clients.add(sid)

@sio.event
def disconnect(sid):
    print("Client disconnected:", sid)
    connected_clients.discard(sid)

@sio.event
async def process_data(sid, data):
    print("Event received from:", sid)

    message = {
        "sid": sid,
        "text": data["text"],
        "image": data["image"].split(",", 1)[-1]
    }

    await producer_channel.default_exchange.publish(
        aio_pika.Message(
            body=jsonpickle.encode(message).encode('utf-8')
        ),
        routing_key=REQUEST_QUEUE
    )
    print(f"Message sent to RabbitMQ for sid {sid}")

async def consume_processed_data():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    await channel.declare_exchange(RESPONSE_EXCHANGE, aio_pika.ExchangeType.DIRECT)
    queue = await channel.declare_queue(RESPONSE_QUEUE, durable=True)
    await queue.bind(RESPONSE_EXCHANGE, routing_key=RESPONSE_QUEUE)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body)
                sid = data.get('sid')
                for sid in connected_clients:
                    await sio.emit("data_processed", data, to=sid)
                    print(f"Processed data sent to {sid}")

@app.on_event("startup")
async def startup_event():
    global producer_connection, producer_channel
    producer_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    producer_channel = await producer_connection.channel()

    await producer_channel.declare_exchange(REQUEST_EXCHANGE, aio_pika.ExchangeType.DIRECT)
    await producer_channel.declare_queue(REQUEST_QUEUE, durable=True)

    asyncio.create_task(consume_processed_data())
    print("RabbitMQ producer connected, consumer coroutine started.")

@app.on_event("shutdown")
async def shutdown_event():
    if producer_connection:
        await producer_connection.close()
    print("RabbitMQ connection closed.")

if __name__ == "__main__":
    uvicorn.run(app_with_cors, host="0.0.0.0", port=8000)
