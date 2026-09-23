# Milestone 4: Recording Engine

## Overview
Betel Pi Milestone 4 implements the recording lifecycle engine. It acts as the direct consumer of `VADEvent` hooks generated in M3. The engine dictates when and how raw PCM frames streaming continuously from ALSA are written locally to `.wav` files on the device.

## Lifecycle Constraints
The `RecordingEngine` manages states strictly mapped to speech intervals, enforcing absolute chronological ordering without duplicating or manipulating signal structures:
1. **SPEECH_START:**
   - Initialized `WavWriter`.
   - Flushes explicit `pre_roll_frames` into the file header.
   - Appends the discrete `triggering_frame`.
   - Progresses state to `RECORDING`.
2. **RECORDING:**
   - Continuously writes ALSA streaming `PCM` chunks iteratively via `.writeframes()`.
   - Streams sequentially avoiding unbounded RAM accumulation.
3. **SPEECH_END:**
   - Instead of abruptly truncating the file, the engine trips into `POST_ROLL` extending the writer lifecycle deterministically by `vad.post_roll_ms`.
   - If speech resumes inside this window, the state flawlessly drops back to `RECORDING` ensuring no fragmented recordings.
4. **MAX DURATION:**
   - Capped deterministically by frame iterations matching `recording.max_duration_sec`. Overrides `POST_ROLL` or extended speech strictly terminating the stream and resetting the engine cleanly.

## Audio Formatting
The engine employs standard-library python `wave` writes natively locking formats to:
- Frequency: `16000Hz` (configurable)
- Channels: `1` (mono, strict)
- Width: `2` (16-bit, strict S16_LE)
- Header structures generated organically.

## Safety & Boundaries
- M4 generates files rigidly named via UTC/local machine timestamp `betel_YYYYMMDD_HHMMSS_micros.wav`.
- The `min_duration_sec` logs a warning identifying short-triggers without implicitly modifying file content to permit deterministic diagnostics.
- M4 explicitly does not address Windows SMB uploads, manifest handling, or service networking synchronization. It purely handles local offline caching directly to `/mnt/recordings` or the configured alias.
