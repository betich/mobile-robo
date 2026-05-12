import glob
import serial
import time
from pathlib import Path


def _find_port() -> str:
    candidates = ['/dev/opencr'] + sorted(glob.glob('/dev/ttyACM*'))
    for port in candidates:
        if not Path(port).exists():
            continue
        try:
            s = serial.Serial(port, 115200, timeout=0.1)
            s.close()
            return port
        except serial.SerialException:
            continue
    raise RuntimeError(f"OpenCR not found — tried: {candidates or 'no devices'}")


class SerialComm:
    def __init__(self, port: str | None = None, baud=115200, timeout=1.0):
        if port is None:
            port = _find_port()
        self.port = port
        self.ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(0.5)  # let OpenCR reset after connection

    def send_drive(self, u: float, v: float) -> str:
        cmd = f"drive {u} {v}\n"
        self.ser.write(cmd.encode())
        return self.ser.readline().decode().strip()

    def send_servo(self, x_spd: float, y_spd: float) -> str:
        cmd = f"servo {x_spd} {y_spd}\n"
        self.ser.write(cmd.encode())
        return self.ser.readline().decode().strip()

    def stop(self) -> str:
        return self.send_drive(0, 0)

    def close(self):
        self.stop()
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
