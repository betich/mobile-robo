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

echo "==> Installing arduino-cli (for flashing OpenCR from RPi)"
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR="$HOME/.local/bin" sh

echo "==> Ensuring ~/.local/bin is in PATH"
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc || \
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

echo "==> Installing OpenCR arduino core"
OPENCR_INDEX="https://raw.githubusercontent.com/ROBOTIS-GIT/OpenCR/master/arduino/opencr_arduino/opencr/package_opencr_index.json"
arduino-cli core update-index --additional-urls "$OPENCR_INDEX"
arduino-cli core install OpenCR:OpenCR --additional-urls "$OPENCR_INDEX"

echo "==> Adding udev rules for OpenCR USB access"
# Lets non-root users access /dev/ttyACM0 without sudo
cat <<'EOF' | sudo tee /etc/udev/rules.d/99-opencr.rules > /dev/null
SUBSYSTEM=="tty", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE="0666", SYMLINK+="opencr"
EOF
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
