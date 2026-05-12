import glob
import pygame
import serial
import time
from pathlib import Path

# =========================
# SERIAL AUTO-DETECT
# =========================

def find_port() -> str:
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
    raise RuntimeError(f"OpenCR not found — tried: {candidates}")

port = find_port()
print("Serial port:", port)

ser = serial.Serial(port, 115200, timeout=0.1)

# Wait for OpenCR reset
time.sleep(2)

# =========================
# PYGAME SETUP
# =========================

pygame.init()
pygame.joystick.init()

joystick_count = pygame.joystick.get_count()

print("Joystick count:", joystick_count)

if joystick_count <= 1:
    print("Joystick 1 not found")
    exit()

# Xbox controller is js1
js = pygame.joystick.Joystick(1)
js.init()

print("Connected:", js.get_name())

# =========================
# SETTINGS
# =========================

MAX_DRIVE = 0.3
MAX_SERVO = 0.3

DEADZONE = 0.15

UPDATE_DELAY = 0.1

last_drive_cmd = ""
last_servo_cmd = ""

# =========================
# MAIN LOOP
# =========================

while True:

    # Update controller events
    for event in pygame.event.get():
        pass

    # ====================================
    # DRIVE STICK (LEFT STICK)
    # ====================================

    drive_y = -js.get_axis(1)   # forward/back
    drive_x = js.get_axis(0)    # sideways

    # Deadzone
    if abs(drive_x) < DEADZONE:
        drive_x = 0.0

    if abs(drive_y) < DEADZONE:
        drive_y = 0.0

    # Scale
    drive_x *= MAX_DRIVE
    drive_y *= MAX_DRIVE

    # Command
    drive_cmd = f"drive {drive_y:.2f} {drive_x:.2f}"

    # Send only if changed
    if drive_cmd != last_drive_cmd:

        ser.write((drive_cmd + "\n").encode())

        print("Sent:", drive_cmd)

        last_drive_cmd = drive_cmd

    # ====================================
    # SERVO STICK (RIGHT STICK)
    # ====================================

    servo_y = -js.get_axis(4)
    servo_x = js.get_axis(3)

    # Deadzone
    if abs(servo_x) < DEADZONE:
        servo_x = 0.0

    if abs(servo_y) < DEADZONE:
        servo_y = 0.0

    # Scale
    servo_x *= MAX_SERVO
    servo_y *= MAX_SERVO

    # Command
    servo_cmd = f"servo {servo_y:.2f} {servo_x:.2f}"

    # Send only if changed
    if servo_cmd != last_servo_cmd:

        ser.write((servo_cmd + "\n").encode())

        print("Sent:", servo_cmd)

        last_servo_cmd = servo_cmd

    # ====================================
    # OPTIONAL SERIAL RESPONSE
    # ====================================

    if ser.in_waiting > 0:

        data = ser.readline().decode('utf-8').strip()

        if data:
            print("Received:", data)

    # ====================================
    # LOOP DELAY
    # ====================================

    time.sleep(UPDATE_DELAY)
