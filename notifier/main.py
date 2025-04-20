# main.py
import asyncio
import socketio
import uvicorn

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# 1) Create your Async Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"   # allow any origin at the Engine‑IO level
)

# 2) Create a FastAPI app (for any REST endpoints you might add)
app = FastAPI()

# 3) Mount the Socket.IO server under FastAPI
#    This exposes both WebSocket and polling endpoints at /socket.io/
socketio_app = socketio.ASGIApp(sio, other_asgi_app=app)

# 4) Wrap the entire ASGI stack in CORS
#    This ensures the HTTP polling endpoints AND the WebSocket handshake
#    all get the right Access‑Control headers.
app_with_cors = CORSMiddleware(
    app=socketio_app,
    allow_origins=["*"],      # or ["http://localhost:5173"] if you want to lock it down
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# 5) Socket.IO event handlers
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
    # **IMPORTANT**: run the wrapped app, not `app` or `socketio_app` directly
    uvicorn.run(app_with_cors, host="127.0.0.1", port=8000)
