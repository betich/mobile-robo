#!/usr/bin/env python3
"""
Controller entry point — runs on the Raspberry Pi.
OpenCR must be connected via USB before running.
"""

import time
from serial_comm import SerialComm

SERIAL_PORT = "/dev/opencr"
BAUD = 115200


def main():
    with SerialComm(SERIAL_PORT, BAUD) as robot:
        print("Connected to OpenCR")

        # Demo: drive forward briefly, then stop
        print(robot.send_move(150, 150, 150, 150))  # forward
        time.sleep(1.0)
        print(robot.stop())

        print("Done")


if __name__ == "__main__":
    main()
