import serial
import time


class SerialComm:
    def __init__(self, port="/dev/ttyACM0", baud=115200, timeout=1.0):
        self.ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(0.5)  # let OpenCR reset after connection

    def send_move(self, fl: int, fr: int, bl: int, br: int) -> str:
        cmd = f"MOVE {fl} {fr} {bl} {br}\n"
        self.ser.write(cmd.encode())
        return self.ser.readline().decode().strip()

    def stop(self) -> str:
        return self.send_move(0, 0, 0, 0)

    def close(self):
        self.stop()
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
