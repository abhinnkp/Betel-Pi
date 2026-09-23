# Milestone 2: Audio Capture

## Overview
Betel Pi Milestone 2 implements the production hardware abstraction layer for audio acquisition on the Raspberry Pi 3A+. It uses `pyalsaaudio` to interface directly with the ALSA sound system, specifically designed for low CPU consumption.

## Dependencies
- `pyalsaaudio`: Chosen as the lightest and most reliable ALSA binding. Requires `libasound2-dev` at compile/build time.
- Standard Library `struct` and `math`: Used for calculating RMS and peak levels (preventing reliance on `audioop` which is removed in Python 3.13, or heavyweight libraries like NumPy).

## Abstraction
The `AudioDevice` interface enforces deterministic PCM frame reads based on `config.yaml`.

- `ALSAAudioDevice`: Operates in ALSA's `PCM_NORMAL` blocking mode. This puts the thread to sleep efficiently while the USB microphone fills the buffer, preventing busy-looping and saving CPU cycles on the Pi 3A+.
- `MockAudioDevice`: MockAudioDevice is provided for isolated unit testing and offline development. Production audio-test always uses ALSAAudioDevice and fails if the configured ALSA capture device cannot be initialized.

## ALSA Configuration
The application reads exactly configured fixed size bytes based on:
- Sample Rate (default: 16000Hz)
- Channels (default: 1 / mono)
- Format (default: S16_LE / 16-bit)
- Frame Duration (default: 20ms)

Expected Frame Size: `16000 * 0.02 * 1 * 2 = 640 bytes`.
The ALSA `periodsize` is set natively to the frame buffer length (320 frames).

## Hardware Validation Procedure
1. Confirm OS and dependencies: `uname -a` and `python3 --version`.
2. Find audio devices: `aplay -l`, `arecord -l`, and `arecord -L`.
3. Test using CLI: `betel-pi audio-devices` to list capture capable ALSA nodes.
4. Run capture: `betel-pi audio-test` (captures 50 frames and reports peak, RMS, and underrun/overruns).
5. Watch CPU usage: Open another SSH terminal and run `htop` while running `audio-test`.

*Note: The system implements `AudioOverrunError` detection (ALSA XRUN). Disconnect handling is built to cleanly shut down or report failures without endless polling.*
