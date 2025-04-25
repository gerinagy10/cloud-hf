import asyncio
import socketio
import uvicorn

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    max_http_buffer_size=10000000
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

@sio.event
async def connect(sid, environ):
    print("Client connected:", sid)

@sio.event
async def process_data(sid, data):
    print("Event received from:", sid)
    # simulate 5s processing…
    await asyncio.sleep(5)
    await sio.emit("data_processed", data, to=sid)
    print("Event sent to:", sid)

@sio.event
def disconnect(sid):
    print("Client disconnected:", sid)

if __name__ == "__main__":
    uvicorn.run(app_with_cors, host="127.0.0.1", port=8000)
