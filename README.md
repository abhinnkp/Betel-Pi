# Betel Pi

Betel Pi is a Raspberry Pi-based audio-only recording device designed for high reliability, unattended operation, and minimal CPU utilization.

## Key Features
- **Audio Only:** Captures USB microphone audio using ALSA. (No camera or video components).
- **VAD (Voice Activity Detection):** Utilizes `webrtcvad` for highly efficient speech detection on ARM processors.
- **Configurable Lifecycle:** Pre-roll, post-roll, silence detection, and max duration are all configurable in `config.yaml`.
- **SMB Recording:** Writes directly to an intranet SMB share mounted via Linux CIFS.
- **Offline Capable:** Does not require internet connectivity; relies on local OS NTP.

## Getting Started
Please see the `docs/` folder for architecture details.

### Requirements
- Raspberry Pi 3A+ (ARMv7 or AArch64)
- Debian 13 (Trixie)
- Python 3.11+
