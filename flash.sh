#!/usr/bin/env bash
# Flash OpenCR firmware via USB.
# Run from the project root: ./flash.sh
# Requires arduino-cli. Run setup.sh first if not installed.
set -e

BOARD="OpenCR:OpenCR:opencr"
PORT="${1:-/dev/ttyACM0}"   # override port: ./flash.sh /dev/ttyACM1
OPENCR_INDEX="https://raw.githubusercontent.com/ROBOTIS-GIT/OpenCR/master/arduino/opencr_arduino/opencr/package_opencr_index.json"
SKETCH="opencr"

echo "==> Compiling $SKETCH for $BOARD"
arduino-cli compile \
    --fqbn "$BOARD" \
    --additional-urls "$OPENCR_INDEX" \
    "$SKETCH"

echo "==> Uploading to $PORT"
arduino-cli upload \
    --fqbn "$BOARD" \
    --port "$PORT" \
    --additional-urls "$OPENCR_INDEX" \
    "$SKETCH"

echo "Done. Monitor with:"
echo "  arduino-cli monitor --port $PORT --config baudrate=115200"
