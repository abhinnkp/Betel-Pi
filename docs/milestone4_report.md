# Milestone 4 Completion Report

## 1. Files Changed
- `app/recording/engine.py`
- `app/recording/wav_writer.py`
- `app/config/config.py`
- `tests/test_recording.py`
- `docs/milestone4_recording.md`
- `docs/milestone4_report.md`

## 2. Recording Architecture
The architecture centers on the `RecordingEngine` state machine decoupled completely from ALSA APIs. It operates passively, receiving streams of boolean events and frame arrays from the VAD controller, routing them sequentially to the `WavWriter`.

## 3. WAV Implementation
The engine leverages the Python standard library `wave` module. Using deterministic parameters validated continuously throughout previous milestones (`S16_LE`, `mono`, `16000Hz`), it generates valid WAV headers preventing reliance on heavyweight libraries like FFmpeg.

## 4. Recording State Machine
Orchestrates states between `IDLE`, `RECORDING`, `POST_ROLL`, and `ERROR`. It manages the timeout limits internally utilizing strict frame-counting derived organically from chunk dimensions instead of leveraging un-synchronized Python wall-clocks.

## 5. Pre-Roll Handling
Strictly processes the detached `pre_roll_frames` explicitly piped in the `VADEvent` without modifying, extending, or discarding chronological stream layouts.

## 6. Triggering-Frame Handling
Strictly handles the single triggering frame explicitly preventing recording duplication logic against the pre-roll buffers.

## 7. Post-Roll Handling
A counter decremented directly inside the polling loops post `SPEECH_END`. Allows seamless recovery back into `RECORDING` state on VAD interrupt avoiding fragmented short `.wav` files.

## 8. Maximum Duration
Strictly calculated via math `(max_duration_sec * sample_rate / chunk_frames)`. It forces finalization upon breaching the limit unconditionally preventing massive disk bloat.

## 9. Minimum Duration
If speech ends before the configured minimum duration, the engine continues consuming real incoming PCM frames until the minimum duration and required post-roll conditions are satisfied, unless `max_duration_sec` is reached first.

## 10. File Naming
Names deterministicly utilize native `datetime.now()` timestamping appended with microsecond tracking `<path>/betel_YYYYMMDD_HHMMSS_micros.wav` naturally guarding against collision logic.

## 11. Error Handling
All IO errors forcefully trip the engine into the `ERROR` state and invoke hard-stops. It relies gracefully on outer supervisors natively avoiding silent writes or corrupt headers.

## 12. Shutdown Handling
A cleanly invoked `engine.force_shutdown()` enables the service wrapper to invoke `.close()` gracefully against open WAVs on `SIGTERM`.

## 13. Memory Strategy
The implementation uses streaming WAV writes and does not intentionally accumulate the complete recording in RAM. Physical memory behavior remains subject to target-device validation.

## 14. Integration-Test Result
Passed successfully proving exact frame order preservation offline avoiding real ALSA implementations locally via standard deterministic assertions.

## 15. Exact Final Test Count / Result
- Total automated tests: 43
- Result: 43 passed, 0 failed. Tests execute fully offline.

## 16. Package Build Result
Successful via standard `python -m build`. No unexpected heavyweight runtime dependencies were added.

## 17. Known Limitations
None found within the tested software parameters. File rotation logic does not delete older files gracefully inside M4 bounds; they remain indefinitely. However, physical/meeting-room validation has NOT been performed.

The following hardware integrations remain unverified and pending:
- Raspberry Pi 3A+ long-duration recording
- actual USB microphone integration
- sustained filesystem write performance
- SD-card behavior
- CPU usage during complete pipeline
- memory usage on target hardware
- long unattended recording
- real meeting-room audio behavior

## 18. Items Deferred to M5
- System SMB mounting routines
- File storage lifecycle & purging limits
- Multi-device synchronization
- M5 application master loop orchestration
- upload retry
- network monitoring
- end-of-day upload

---

### SOFTWARE VERIFIED
- Recording architecture implemented
- Frame ownership contract verified explicitly avoiding duplicates
- Valid WAV implementations generated natively via standard `wave`
- Pre-roll and sequential chronological boundaries rigidly respected natively
- Triggering-frame correctly isolated and routed once
- Post-roll timeouts respected
- Post-roll correctly interrupted by speech overlaps without bugs
- Maximum duration hard stops enforced
- Minimum duration logic implemented (consuming real frames, no synthetic padding)
- File naming/collision handling safely appending indexes
- Shutdown handling safe against open descriptors
- Error handling forces `ERROR` state and closes files rigidly
- 43 offline automated tests pass
- Build constraints upheld natively

### PHYSICAL / INTEGRATION VALIDATION PENDING
- Physical evaluation of disk read/write bandwidth under extended ALSA loads.
- Real-world validation of timestamp alignments locally.
- Extended continuous ALSA streams running indefinitely on Pi 3A+.
- SD-card and USB mic connectivity issues simulated live.
