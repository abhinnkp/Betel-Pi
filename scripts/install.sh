#!/bin/bash
set -e

echo "======================================"
echo " Betel Pi Installer (Milestone 1 Stub)"
echo "======================================"
echo " Note: This is a structural skeleton for Milestone 1."
echo " The production installer in later milestones will:"
echo " - verify Debian Trixie, arch, and Python version"
echo " - install OS dependencies and create venv"
echo " - install tested dependencies and Betel Pi"
echo " - create betelpi user and configure audio permissions"
echo " - install config.yaml and systemd service"
echo " - configure OS NTP and prepare SMB/fstab deployment"
echo " - preserve existing configuration and never delete recordings"
echo "======================================"

# Ensure script is run as root
if [ "$(id -u)" != "0" ]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "1. Detecting OS and Architecture..."
OS_NAME=$(grep -E '^(PRETTY_NAME)=' /etc/os-release | cut -d '=' -f 2 | tr -d '"')
ARCH=$(uname -m)
echo "   OS: $OS_NAME"
echo "   Architecture: $ARCH"

# In production this will enforce Debian 13 (Trixie) and Python 3.11+

echo "2. Installing OS Dependencies..."
# apt-get update
# apt-get install -y python3-dev build-essential python3-pip libasound2-dev python3-venv

echo "3. Creating dedicated service user (betelpi)..."
if id "betelpi" &>/dev/null; then
    echo "   User betelpi already exists."
else
    useradd -r -s /bin/false betelpi
    echo "   Created betelpi user."
fi
usermod -a -G audio betelpi

echo "4. Setting up application directories..."
APP_DIR="/opt/betel-pi"
CONFIG_DIR="/etc/betel-pi"
LOG_DIR="/var/log/betel-pi"
# mkdir -p $APP_DIR $CONFIG_DIR $LOG_DIR
# chown betelpi:betelpi $LOG_DIR

echo "5. Installing Python Virtual Environment and Dependencies..."
# python3 -m venv $APP_DIR/venv
# $APP_DIR/venv/bin/pip install build wheel
# $APP_DIR/venv/bin/pip install .

echo "6. Installing Configuration..."
# if [ ! -f $CONFIG_DIR/config.yaml ]; then
#     cp config/config.yaml $CONFIG_DIR/
# fi
# chown -R betelpi:betelpi $CONFIG_DIR

echo "7. Systemd Service Setup..."
# cp systemd/betel-pi.service /etc/systemd/system/
# systemctl daemon-reload
# systemctl enable betel-pi.service

echo "8. NTP and OS Configuration..."
# This is a placeholder where install.sh would read config.yaml's NTP settings
# and configure systemd-timesyncd or chrony. The Python app does not do this.

echo "======================================"
echo " Installation Skeleton Complete."
echo " This is a Milestone 1 structural skeleton."
echo "======================================"
