#!/usr/bin/env bash
# Flash OpenCR firmware from your local Mac.
# OpenCR stays connected to the RPi — flashing tunnels through SSH.
#
# Usage: ./flash.sh
set -e

BOARD="OpenCR:OpenCR:OpenCR"
SKETCH="opencr"
BUILD_DIR="/tmp/opencr-build"
VIRT_PORT="/tmp/opencr-tty"
BRIDGE_PORT=4444

RPI_USER=kengvaris
RPI_HOST=100.69.19.59
RPI_PASS=014719
OPENCR_PORT=/dev/opencr

OPENCR_LD=~/Library/Arduino15/packages/OpenCR/tools/opencr_tools/1.0.0/macosx/opencr_ld

SSH_BASE=(sshpass -p "$RPI_PASS" ssh -o StrictHostKeyChecking=no)

SSH_CMD() { "${SSH_BASE[@]}" "$RPI_USER@$RPI_HOST" "$@"; }

cleanup() {
    echo "==> Cleaning up"
    kill "$SSH_PID" "$SOCAT_PID" 2>/dev/null || true
    # restart service regardless of how we exit
    SSH_CMD "echo '014719' | sudo -S systemctl start mobile-robo" 2>/dev/null || true
}
trap cleanup EXIT

# --- 1. Compile ---
echo "==> Compiling $SKETCH"
arduino-cli compile --fqbn "$BOARD" --output-dir "$BUILD_DIR" "$SKETCH"
BIN="$BUILD_DIR/opencr.ino.bin"

# --- 2. Stop service so it releases the serial port ---
echo "==> Stopping mobile-robo service"
SSH_CMD "echo '014719' | sudo -S systemctl stop mobile-robo"

# --- 3. Open SSH tunnel: Mac:BRIDGE_PORT → RPi socat → /dev/opencr ---
echo "==> Opening serial tunnel"
"${SSH_BASE[@]}" \
    -L "$BRIDGE_PORT:localhost:$BRIDGE_PORT" \
    "$RPI_USER@$RPI_HOST" \
    "socat TCP-LISTEN:$BRIDGE_PORT,reuseaddr $OPENCR_PORT,b115200,rawer" &
SSH_PID=$!
sleep 2

# --- 4. Create virtual serial port on Mac ---
echo "==> Creating virtual serial port"
rm -f "$VIRT_PORT"
socat pty,link="$VIRT_PORT",rawer tcp:localhost:$BRIDGE_PORT &
SOCAT_PID=$!
sleep 1

REAL_PORT=$(readlink "$VIRT_PORT" 2>/dev/null || echo "")
[ -z "$REAL_PORT" ] && { echo "ERROR: virtual port not created"; exit 1; }
echo "  Port: $REAL_PORT"

# --- 5. Flash ---
echo "==> Flashing"
"$OPENCR_LD" "$REAL_PORT" 115200 "$BIN" 1

echo ""
echo "Done!"
