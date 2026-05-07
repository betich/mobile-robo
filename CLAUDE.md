# mobile-robo

Mecanum-wheel robot with a Raspberry Pi controller layer and an OpenCR motor-drive layer.

## Hardware

| Component | Details |
|-----------|---------|
| Raspberry Pi | 100.69.19.59, user: kengvaris |
| OpenCR board | USB-connected to RPi at `/dev/ttyACM0` |
| Wheels | 4× mecanum wheels (FL M1, FR M2, BL M3, BR M4) |

## Layer Separation

```
mobile-robo/
├── opencr/        # OpenCR firmware — C++/Arduino, flashed via PlatformIO
├── controller/    # RPi Python — cameras, logic, peripherals
└── drafts/        # Scratch space — one-off experiments, not production
```

**Rule**: OpenCR only drives motors. RPi only issues commands and handles peripherals. They talk over USB-serial.

## Motor Layout

```
FL (M1)  FR (M2)
BL (M3)  BR (M4)
```

Forward: all `+` | Clockwise rotate: FL+, FR-, BL-, BR+ | Strafe right: FL+, FR-, BL+, BR-

## Serial Protocol

Commands sent from RPi → OpenCR over 115200 baud:

```
MOVE <fl> <fr> <bl> <br>\n   # values -255..255
```

OpenCR replies `OK` or `ERR bad format`.

## Flashing OpenCR

```bash
cd opencr
pio run -t upload          # build + flash
pio device monitor         # open serial monitor (Ctrl+] to exit)
```

Adjust `upload_port` in `opencr/platformio.ini` if OpenCR appears on a different port.

## Square Drive

On boot, OpenCR runs `squareDrive()` autonomously — no RPi needed. Tune these defines in `opencr/src/main.cpp`:

```cpp
#define DRIVE_SPEED  150   // PWM 0-255
#define TURN_SPEED   120
#define DRIVE_MS    1500   // ms per side
#define TURN_MS      700   // ms per 90° turn
```

## Syncing Controller to RPi

```bash
./sync.sh   # rsync controller/ → kengvaris@100.69.19.59:~/mobile-robo/controller/
```

## Running on RPi

```bash
ssh kengvaris@100.69.19.59
cd ~/mobile-robo/controller
python3 main.py
```

Requires `pyserial`: `pip3 install pyserial`

## Adding Peripherals

Add new modules under `controller/` (e.g., `camera.py`, `lidar.py`) and import them in `main.py`. Keep each peripheral in its own file — one concern per module.
