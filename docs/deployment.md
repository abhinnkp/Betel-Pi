# Deployment Strategy

Betel Pi uses a "Master Image" deployment strategy due to the resource constraints of compiling dependencies (like `webrtcvad`) directly on a Raspberry Pi 3A+.

## Process
1. **Prepare Master Pi:** Install Debian Trixie on a Raspberry Pi 3A+.
2. **Run Installer:** Execute `sudo ./scripts/install.sh`. This script will:
   - Install OS level requirements (gcc, g++, python3-dev, libasound2-dev, etc.)
   - Install the VAD dependency (`webrtcvad-wheels==2.0.14`).
     - **AArch64 (64-bit):** Pre-built CPython 3.13 wheel available.
     - **ARMv7/armhf (32-bit):** No published CPython Linux ARMv7 wheel exists; source compilation is required. *ARMv7 source-build path identified; physical Pi verification remains a deployment prerequisite.*
   - Setup the `betelpi` user and `systemd` service
   - Copy `config/config.yaml` to the production location `/etc/betel-pi/config.yaml`
3. **Configure OS Integrations:**
   - Configure `/etc/fstab` for the CIFS/SMB share (`/mnt/recordings`).
   - Configure the OS NTP service (`systemd-timesyncd` or `chrony`) pointing to the local intranet server.
4. **Clone Image:** Clone the SD card to use across the fleet.

Betel Pi never auto-updates itself or connects to the public internet during normal operation.
