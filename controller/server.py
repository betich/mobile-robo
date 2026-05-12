#!/usr/bin/env python3
"""
Web controller — serves camera stream and accepts drive commands.
Access at http://<rpi-ip>:8080
"""

import asyncio
import threading
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import camera
from serial_comm import SerialComm
from gamepad import GamepadController


class CommanderMutex:
    """Thread-safe mutex: first active input source holds control until all its inputs go idle."""

    def __init__(self):
        self._lock   = threading.Lock()
        self._holder: str | None = None

    def try_claim(self, who: str) -> bool:
        with self._lock:
            if self._holder is None or self._holder == who:
                self._holder = who
                return True
            return False

    def release(self, who: str) -> None:
        with self._lock:
            if self._holder == who:
                self._holder = None

    @property
    def holder(self) -> str | None:
        with self._lock:
            return self._holder


BAUD = 115200
PORT = 8080

robot:        SerialComm | None = None
serial_lock   = threading.Lock()
commander     = CommanderMutex()
STATIC_DIR    = Path(__file__).parent / "static"


def _serial_send(fn, *args):
    with serial_lock:
        fn(*args)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global robot
    camera.start()
    try:
        robot = SerialComm()
        print(f"Serial: {robot.port}")
    except Exception as e:
        print(f"WARNING: serial not available ({e}), drive commands disabled")
        robot = None

    gamepad = GamepadController(robot, serial_lock, commander) if robot else None
    if gamepad:
        gamepad.start()

    yield

    camera.stop()
    if gamepad:
        gamepad.stop()
    if robot:
        robot.close()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text()


async def _mjpeg_frames():
    boundary = b"--frame"
    loop = asyncio.get_event_loop()
    while True:
        frame = await loop.run_in_executor(None, camera.get_frame)
        yield (
            boundary + b"\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame + b"\r\n"
        )
        await asyncio.sleep(1 / 30)


@app.get("/stream")
async def stream():
    return StreamingResponse(
        _mjpeg_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.websocket("/ws")
async def ws_drive(websocket: WebSocket):
    await websocket.accept()
    loop      = asyncio.get_event_loop()
    web_drive = (0.0, 0.0)
    web_servo = (0.0, 0.0)

    def web_active() -> bool:
        return web_drive != (0.0, 0.0) or web_servo != (0.0, 0.0)

    async def do_send(fn, *args):
        if robot:
            await loop.run_in_executor(None, _serial_send, fn, *args)

    try:
        while True:
            parts = (await websocket.receive_text()).strip().split()
            if not parts:
                continue
            kind = parts[0].upper()

            if kind == "DRIVE" and len(parts) == 3:
                u, v      = float(parts[1]), float(parts[2])
                web_drive = (u, v)
                active    = web_active()
                can_send  = commander.try_claim("web") if active else commander.holder == "web"
                if can_send:
                    await do_send(robot.send_drive, u, v)
                if not active:
                    commander.release("web")

            elif kind == "SERVO" and len(parts) == 3:
                x, y      = float(parts[1]), float(parts[2])
                web_servo = (x, y)
                active    = web_active()
                can_send  = commander.try_claim("web") if active else commander.holder == "web"
                if can_send:
                    await do_send(robot.send_servo, x, y)
                if not active:
                    commander.release("web")

    except WebSocketDisconnect:
        commander.release("web")
        if robot:
            await loop.run_in_executor(None, _serial_send, robot.stop)
            await loop.run_in_executor(None, _serial_send, robot.send_servo, 0.0, 0.0)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
