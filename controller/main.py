#!/usr/bin/env python3
"""
Controller entry point — runs on the Raspberry Pi.
OpenCR must be connected via USB before running.
"""

import time
from serial_comm import SerialComm


def main():
    with SerialComm() as robot:
        print(f"Connected to OpenCR on {robot.port}")

        # Demo: drive forward briefly, then stop
        print(robot.send_drive(0.3, 0.0))   # forward
        time.sleep(1.0)
        print(robot.stop())

        print("Done")


if __name__ == "__main__":
    main()
