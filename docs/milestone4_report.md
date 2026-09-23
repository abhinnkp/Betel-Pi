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
Monitored analogously to the max cap. Currently finalizes the file safely but raises a strong internal logging warning, ensuring deterministic evaluation.

## 10. File Naming
Names deterministicly utilize native `datetime.now()` timestamping appended with microsecond tracking `<path>/betel_YYYYMMDD_HHMMSS_micros.wav` naturally guarding against collision logic.

## 11. Error Handling
All IO errors forcefully trip the engine into the `ERROR` state and invoke hard-stops. It relies gracefully on outer supervisors natively avoiding silent writes or corrupt headers.

## 12. Shutdown Handling
A cleanly invoked `engine.force_shutdown()` enables the service wrapper to invoke `.close()` gracefully against open WAVs on `SIGTERM`.

## 13. Memory Strategy
Uses standard-library streaming. PCM fragments are directly piped out to `libIO` continuously, completely circumventing multi-megabyte RAM aggregations across extended meetings. Memory profile remains rigidly flat.

## 14. Integration-Test Result
Passed successfully proving exact frame order preservation offline avoiding real ALSA implementations locally via standard deterministic assertions.

## 15. Exact Final Test Count / Result
- Total automated tests: 38
- Result: 38 passed, 0 failed. Tests execute fully offline.

## 16. Package Build Result
Successful via standard `python -m build`. No unexpected heavyweight runtime dependencies were added.

## 17. Known Software Limitations
None found within the tested software parameters. File rotation logic does not delete older files gracefully inside M4 bounds; they remain indefinitely.

## 18. Items Deferred to M5
- System SMB mounting routines
- File storage lifecycle & purging limits
- Multi-device synchronization
- M5 application master loop orchestration

---

### SOFTWARE VERIFIED
- Valid WAV implementations generated natively.
- Pre-roll and sequential chronological boundaries rigidly respected natively.
- Post-roll timeouts respected and correctly interrupted by speech overlaps.
- Maximum duration hard stops enforced.
- Memory profile strictly flat without frame cache buildup.
- 38 offline automated tests pass.
- Build constraints upheld natively.

### PHYSICAL VALIDATION PENDING
- Physical evaluation of disk read/write bandwidth under extended ALSA loads.
- Real-world validation of timestamp alignments locally.
