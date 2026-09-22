# Betel Pi Architecture (Milestone 1)

## Overview
Betel Pi is a lightweight, strictly audio-only recording application designed for unattended operation on a Raspberry Pi 3A+. It handles voice activity detection (VAD), reliable USB microphone recording, storage monitoring, and graceful failure recovery, all while maintaining low CPU utilization.

The architecture strictly separates the **Python Application Responsibility** from the **Linux/OS Responsibility**.

---

## 1. System Boundaries

### Python Application Responsibilities
- **ALSA Audio Capture:** Reading frames efficiently via ALSA.
- **VAD Processing:** Applying VAD to fixed-size audio frames (via `webrtcvad`).
- **Recording Lifecycle:** Pre-roll, start recording, continue on speech, enforce max duration, handle silence post-roll, and clean shutdown.
- **Storage Monitoring:** Monitoring free space and usage percentage of the mounted recording path to block recordings if thresholds are exceeded.
- **Configuration Management:** Reading `config.yaml` to dictate behavior.
- **CLI and Diagnostics:** Providing basic commands (`status`, `audio-devices`, etc.).

### Linux / OS Responsibilities
- **CIFS/SMB Mount:** The SMB connection to the Windows Intranet Server is entirely managed by the OS using `/etc/fstab` and `cifs-utils`. The Python app **never** mounts or unmounts SMB shares; it only writes to the `/mnt/recordings` directory.
- **NTP Synchronization:** Network Time Protocol is handled by the host OS (e.g., `systemd-timesyncd` or `chrony`). The Python app merely reads the system clock and reports NTP settings purely for diagnostics.
- **Systemd:** Process management, auto-restarting, non-root user execution (`User=betelpi`), and establishing file system and network dependencies.

---

## 2. Component Abstractions

### Configuration Architecture
- `app.config` parses the YAML file. All parameters are validated rigorously on startup (ensuring valid sample rates, positive durations, valid VAD modes, etc.).
- The configuration acts as the single source of truth for all modules.

### ALSA / Audio Capture
- **USB Microphone Abstraction:** `app.audio.device` establishes a strict hierarchy for audio capture:
  ```
  AudioDevice (Interface)
      |
      +-- ALSAAudioDevice (Production)
      |
      +-- MockAudioDevice (Testing)
  ```
- The production implementation **must** use ALSA for USB microphones. Frameworks like PortAudio, sounddevice, or PyAudio are explicitly prohibited.
- Capture logic will prefer blocking ALSA reads to avoid busy-looping and CPU-intensive sleep/poll mechanisms.

### VAD Abstraction
- Defined in `app.vad.base` as an interface `VADProcessor`.
- Planned concrete implementation: `WebRTCVADProcessor` wrapping `webrtcvad-wheels`. This prevents the core application from tightly coupling to the specific VAD library, allowing mock implementations for testing.

### Recording Controller
- The core orchestrator in `app.recording.controller`.
- **Flow:** `AudioStream -> VADProcessor -> RecordingController -> WavWriter`.
- Enforces speech start frames, silence frames, pre-roll, and maximum duration natively. It ensures WAV files are strictly mono, PCM, and 16-bit.

### Storage Abstraction
- Handled by `app.storage.monitor`.
- Operates under the assumption of the SMB boundary:
  ```
  Betel Pi Application -> /mnt/recordings -> Linux CIFS/SMB -> Windows Server
  ```
- No fallback to local storage is permitted if the SMB mount disappears. It immediately enters a `STORAGE_BLOCKED` state.

---

## 3. CPU Optimization Strategy
CPU efficiency is critical for the Raspberry Pi 3A+.
- **Blocking I/O:** Reading from ALSA uses blocking calls.
- **Fixed Size Frames:** Audio is processed in chunks native to the VAD (e.g., 20ms at 16kHz).
- **Minimal Copies:** Audio buffers are passed by reference or memoryview where possible. No unnecessary format resampling.
- **Bounded Memory:** Pre-roll buffer is implemented as a fixed-size ring buffer (e.g., `collections.deque` with `maxlen`).
- **No Per-Frame Logging:** Logging is kept sparse and restricted to state transitions (e.g., `IDLE -> RECORDING`).

---

## 4. WebRTC VAD Compatibility (Debian 13 Trixie / Pi 3A+)
Investigation into `webrtcvad` 2.0.10:
- **Trixie Installability:** Yes (via PyPI/source).
- **Python Version:** Compatible with Python 3.11+.
- **ARMv7 (32-bit):** Compatible.
- **AArch64 (64-bit):** Compatible.
- **Pre-built Wheels:** None exist for ARM Linux.
- **Source Compilation:** Required (`gcc`, `g++`, `python3-dev`).
- **Limitations:** Compiling on a Pi 3A+ is slow and resource-heavy. Therefore, the installer architecture relies on preparing a **MASTER** SD card on one device and cloning the image for fleet deployment.

---

## 5. Installer Architecture
The `scripts/install.sh` handles setup for the **MASTER Raspberry Pi**.
- Detects OS, architecture, and Python version.
- Installs APT dependencies (`python3-dev`, `build-essential`, `python3-pip`, `libasound2-dev`).
- Installs Python dependencies (compiling `webrtcvad`).
- Creates the non-root `betelpi` user and assigns the `audio` group.
- Installs the application to standard Linux paths (e.g., `/opt/betel-pi`), copies `config.yaml` to `/etc/betel-pi/`, and registers the `systemd` service.
- **Note:** It does *not* set up the full fleet. The result is meant to be imaged.

---

## 6. Testing Strategy
- Core logic is tested using dependency injection and mocks (Mock VAD, Mock OS Platform).
- Unit tests run completely offline on any development PC without needing a physical Pi, ALSA, SMB, or NTP.

---

## 7. Explicit Exclusions
- **No Camera / Video / V4L2 / OpenCV:** The system is exclusively audio-only.
- **No Heavy ML Models:** No Whisper, cloud API, or neural networks are used. VAD relies on WebRTC's Gaussian Mixture Model.
