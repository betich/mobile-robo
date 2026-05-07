from picamera2 import Picamera2
import io

_cam: Picamera2 | None = None


def start(width: int = 640, height: int = 480) -> None:
    global _cam
    _cam = Picamera2()
    config = _cam.create_video_configuration(main={"size": (width, height)})
    _cam.configure(config)
    _cam.start()


def get_frame() -> bytes:
    buf = io.BytesIO()
    _cam.capture_file(buf, format="jpeg")
    return buf.getvalue()


def stop() -> None:
    if _cam:
        _cam.stop()
