import threading
import time
import logging

log = logging.getLogger(__name__)

DEADZONE  = 0.15
MAX_DRIVE = 0.3    # m/s
MAX_SERVO = 45.0   # deg/s
POLL_HZ   = 20


class GamepadController:
    def __init__(self, robot, serial_lock, commander):
        self._robot     = robot
        self._lock      = serial_lock
        self._commander = commander
        self._running   = False
        self._thread    = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True, name="gamepad")
        self._thread.start()

    def stop(self):
        self._running = False

    @staticmethod
    def _dz(v: float) -> float:
        return 0.0 if abs(v) < DEADZONE else v

    def _send(self, fn, *args):
        with self._lock:
            fn(*args)

    def _loop(self):
        try:
            import pygame
        except ImportError:
            log.warning("pygame not installed — gamepad disabled")
            return

        pygame.init()
        pygame.joystick.init()

        js         = None
        last_drive = None
        last_servo = None

        while self._running:
            # Auto-connect
            if js is None:
                pygame.joystick.quit()
                pygame.joystick.init()
                if pygame.joystick.get_count() == 0:
                    time.sleep(1.0)
                    continue
                js = pygame.joystick.Joystick(0)
                js.init()
                log.info("Gamepad connected: %s", js.get_name())
                last_drive = last_servo = None

            try:
                for _ in pygame.event.get():
                    pass

                # Left stick → drive  (axis1: up=−, axis0: right=+)
                u  = self._dz(-js.get_axis(1)) * MAX_DRIVE
                v  = self._dz( js.get_axis(0)) * MAX_DRIVE
                # Right stick → servo (axis4: up=−, axis3: right=+)
                sx = self._dz( js.get_axis(3)) * MAX_SERVO
                sy = self._dz(-js.get_axis(4)) * MAX_SERVO

                is_active = bool(u or v or sx or sy)

                if is_active:
                    if self._commander.try_claim("gamepad"):
                        drive = (round(u, 2), round(v, 2))
                        servo = (round(sx, 2), round(sy, 2))
                        if drive != last_drive:
                            self._send(self._robot.send_drive, *drive)
                            last_drive = drive
                        if servo != last_servo:
                            self._send(self._robot.send_servo, *servo)
                            last_servo = servo
                else:
                    if self._commander.holder == "gamepad":
                        self._send(self._robot.stop)
                        self._send(self._robot.send_servo, 0.0, 0.0)
                        self._commander.release("gamepad")
                        last_drive = last_servo = None

            except Exception as e:
                log.warning("Gamepad error: %s — reconnecting", e)
                js = None
                time.sleep(1.0)

            time.sleep(1.0 / POLL_HZ)
