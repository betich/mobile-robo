#!/usr/bin/env bash
# Run from the project root on your LOCAL machine (Mac), not on the RPi.
# Temporarily connect OpenCR USB to this machine, flash, then reconnect to RPi.
#
# Usage:
#   ./flash.sh                   # auto-detect USB port
#   ./flash.sh /dev/cu.usbmodemXXX  # specify port
set -e

BOARD="OpenCR:OpenCR:opencr"
OPENCR_INDEX="https://raw.githubusercontent.com/ROBOTIS-GIT/OpenCR/master/arduino/opencr_release/package_opencr_index.json"
SKETCH="opencr"

# --- Detect port ---
if [ -n "$1" ]; then
    PORT="$1"
else
    PORT=$(ls /dev/cu.usbmodem* /dev/ttyACM* 2>/dev/null | head -1)
    if [ -z "$PORT" ]; then
        echo "ERROR: No OpenCR USB device found."
        echo "  Connect OpenCR to this machine and retry, or specify port:"
        echo "  ./flash.sh /dev/cu.usbmodemXXXXX"
        exit 1
    fi
    echo "==> Auto-detected port: $PORT"
fi

# --- Install arduino-cli if missing ---
if ! command -v arduino-cli &>/dev/null; then
    echo "==> Installing arduino-cli"
    brew install arduino-cli
fi

# --- Configure OpenCR board manager URL (idempotent) ---
if ! arduino-cli config dump 2>/dev/null | grep -q "opencr_release"; then
    echo "==> Adding OpenCR board manager URL"
    arduino-cli config add board_manager.additional_urls "$OPENCR_INDEX"
fi

# --- Install OpenCR core if missing ---
if ! arduino-cli core list 2>/dev/null | grep -q "OpenCR:OpenCR"; then
    echo "==> Installing OpenCR arduino core (first time, may take a while)"
    arduino-cli core update-index
    arduino-cli core install OpenCR:OpenCR
fi

echo "==> Compiling $SKETCH"
arduino-cli compile --fqbn "$BOARD" "$SKETCH"

echo "==> Uploading to $PORT"
arduino-cli upload --fqbn "$BOARD" --port "$PORT" "$SKETCH"

echo ""
echo "Done! Reconnect OpenCR to the RPi (/dev/ttyACM0)."
