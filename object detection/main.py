import asyncio
import os
import aio_pika
import json
import cv2
import numpy as np
import base64

from ultralytics import YOLO

RABBITMQ_URL = os.environ.get('RABBITMQ_CONNECTION') #"amqp://localhost/"
REQUEST_EXCHANGE = "requests"
PROCESSED_EXCHANGE = "processed"
REQUEST_QUEUE = "detection_requests"
STORAGE_QUEUE = "storage_requests"

model = YOLO('yolov8n.pt')

async def detect_humans(base64_image: str):

    image_data = base64.b64decode(base64_image)
    np_arr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Image decoding failed!")

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    results = model.predict(source=rgb_image, imgsz=640, conf=0.5, device='cpu', classes=[0])

    human_count = len(results[0].boxes)

    for box in results[0].boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    _, buffer = cv2.imencode('.jpg', image)
    encoded_image = base64.b64encode(buffer).decode('utf-8')

    return encoded_image, human_count


async def main():

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    request_exchange = await channel.declare_exchange(REQUEST_EXCHANGE, aio_pika.ExchangeType.DIRECT)
    processed_exchange = await channel.declare_exchange(PROCESSED_EXCHANGE, aio_pika.ExchangeType.DIRECT)

    await channel.declare_queue(REQUEST_QUEUE, durable=True)
    queue = await channel.declare_queue(REQUEST_QUEUE, durable=True)
    await queue.bind(request_exchange, routing_key=REQUEST_QUEUE)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body)
                print(f"Received message from client {data['sid']}")

                base64_image = data.get('image')
                if base64_image:
                    processed_image, human_count = await detect_humans(base64_image)
                    data['image'] = processed_image
                    data['human_count'] = human_count

                await processed_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(data).encode()
                    ),
                    routing_key=STORAGE_QUEUE
                )
                print(f"Processed and sent message with {human_count} humans detected.")

if __name__ == "__main__":
    asyncio.run(main())
