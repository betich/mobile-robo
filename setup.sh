#!/usr/bin/env bash
# Run this once on the Raspberry Pi after syncing the project:
#   ./setup.sh
set -e

echo "==> Updating package lists"
sudo apt-get update -y

echo "==> Installing system packages"
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git

echo "==> Installing Python dependencies"
pip3 install --break-system-packages -r controller/requirements.txt


echo "==> Adding udev rules for OpenCR USB access"
wget -q https://raw.githubusercontent.com/ROBOTIS-GIT/OpenCR/master/99-opencr-cdc.rules
sudo cp ./99-opencr-cdc.rules /etc/udev/rules.d/
rm ./99-opencr-cdc.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "==> Adding ${USER} to dialout group (serial port access)"
sudo usermod -a -G dialout "$USER"

echo "==> Registering systemd service"
sudo cp ~/mobile-robo/mobile-robo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mobile-robo
sudo systemctl restart mobile-robo

echo ""
echo "Done! Re-login (or run 'newgrp dialout') for group change to take effect."
echo ""
echo "Quick reference:"
echo "  Web UI        : http://$(hostname -I | awk '{print $1}'):8080"
echo "  Service logs  : journalctl -u mobile-robo -f"
echo "  Restart service: sudo systemctl restart mobile-robo"
echo "  Flash OpenCR  : cd ~/mobile-robo && ./flash.sh"
echo "  Serial monitor: arduino-cli monitor --port /dev/ttyACM0 --config baudrate=115200"
