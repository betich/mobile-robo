#!/usr/bin/env python3
"""
Web controller — serves camera stream and accepts drive commands.
Access at http://<rpi-ip>:8080
"""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import camera
from serial_comm import SerialComm

# ---------------------------------------------------------------------------
# Mecanum kinematics
#
# Motor layout (/ = rollers at +45°, \ = rollers at −45°):
#   FL [/]  FR [\]
#   BL [\]  BR [/]
#
# For body velocity (vx = forward, vy = strafe-left, ω = rotate-CCW):
#   v_FL =  vx − vy − ω
#   v_FR =  vx + vy + ω
#   v_BL =  vx + vy − ω
#   v_BR =  vx − vy + ω
#
# Key → (vx, vy, ω):
#   F / W / ↑  →  (+1,  0,  0)   all wheels +
#   B / S / ↓  →  (−1,  0,  0)   all wheels −
#   L / A / ←  →  ( 0,  0, +1)   FL−, FR+, BL−, BR+  (rotate CCW)
#   R / D / →  →  ( 0,  0, −1)   FL+, FR−, BL+, BR−  (rotate CW)
# ---------------------------------------------------------------------------

SPEED = 150  # PWM magnitude, 0–255

CMD_VECTORS: dict[str, tuple[float, float, float]] = {
    "F":    ( 1,  0,  0),
    "B":    (-1,  0,  0),
    "L":    ( 0,  0,  1),
    "R":    ( 0,  0, -1),
    "STOP": ( 0,  0,  0),
}


def mecanum(vx: float, vy: float, omega: float, speed: int = SPEED) -> tuple[int, int, int, int]:
    fl = vx - vy - omega
    fr = vx + vy + omega
    bl = vx + vy - omega
    br = vx - vy + omega
    scale = speed / max(abs(fl), abs(fr), abs(bl), abs(br), 1)
    return int(fl * scale), int(fr * scale), int(bl * scale), int(br * scale)


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

SERIAL_PORT = "/dev/opencr"
BAUD = 115200
PORT = 8080

robot: SerialComm | None = None
serial_lock = asyncio.Lock()
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global robot
    camera.start()
    try:
        robot = SerialComm(SERIAL_PORT, BAUD)
    except Exception as e:
        print(f"WARNING: serial not available ({e}), drive commands disabled")
        robot = None
    yield
    camera.stop()
    if robot:
        robot.close()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

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
    try:
        while True:
            cmd = (await websocket.receive_text()).strip().upper()
            if cmd not in CMD_VECTORS:
                continue
            vx, vy, omega = CMD_VECTORS[cmd]
            fl, fr, bl, br = mecanum(vx, vy, omega)
            if robot:
                async with serial_lock:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, robot.send_move, fl, fr, bl, br)
    except WebSocketDisconnect:
        if robot:
            async with serial_lock:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, robot.stop)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
