# Milestone 3: VAD / Speech Detection

## Overview
Betel Pi Milestone 3 implements a lightweight speech detection layer on top of the established ALSA PCM framework. It specifically leverages the `webrtcvad-wheels` library which is heavily optimized for ARM processors and evaluates deterministic audio chunks, rather than heavily-processing raw audio signals using ML inference.

## VAD Architecture
The speech activity lifecycle sits purely below the recording lifecycle:
1. `ALSAAudioDevice` captures configured chunk (e.g. 640 bytes).
2. `VADStateMachine` processes the frame through a `VADProcessor` wrapper interface.
3. The raw VAD boolean is "debounced" to prevent sudden noise bursts from activating records:
   - `speech_start_frames` enforces consecutive noise matches to trigger `SPEECH_START`.
   - `silence_frames` enforces consecutive silence matches to trigger `SPEECH_END`.

## Pre-Roll and Post-Roll
- **Pre-Roll:** The `VADStateMachine` retains a bounded memory queue (`collections.deque`) representing the exact configured `pre_roll_ms`. When `SPEECH_START` triggers, the event bundles these preceding frames with the signal so they aren't lost to latency. Memory allocations are strict and deterministic to protect the Raspberry Pi 3A+.
- **Post-Roll:** Configurable via `post_roll_ms`, however its actual file-writing behavior is **deferred to Milestone 4**.

## Validation and CPU Impact
- WebRTC VAD imposes strict input constraints. The `WebRTCVADProcessor` asserts that all frames fed to it correspond strictly to `16000Hz`, `mono`, `16-bit` (`S16_LE`), avoiding implicit and expensive resampling logic entirely.
- Disabled VAD logic passes over CPU calculations cleanly, keeping the StateMachine forever in `SILENCE`.
