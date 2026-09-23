# Milestone 3 Completion Report

## 1. Files Changed
- `app/vad/base.py`
- `app/vad/webrtc.py`
- `app/vad/mock.py`
- `app/vad/state.py`
- `app/cli.py`
- `tests/test_vad.py`
- `tests/test_cli.py`
- `docs/milestone3_vad.md`
- `docs/milestone3_report.md`

## 2. WebRTC VAD Implementation
The core `VADProcessor` interface was strictly implemented via `WebRTCVADProcessor` tying the production application to `webrtcvad-wheels`.

## 3. Dependency Verification
Confirmed `webrtcvad-wheels==2.0.14` correctly processes standard standard inputs natively without throwing warnings, and rejects malformed types, fully conforming offline without hitting PyPI via the pre-pinned M2 configurations.

## 4. Frame Validation
Implemented strict length-checking byte validations before feeding chunks to `webrtcvad`, asserting properties directly match the expected ALSA chunk configurations.

## 5. State-Machine Behavior
Implemented `VADStateMachine` successfully transitioning between `SILENCE` and `SPEECH`.

## 6. Speech-Start Threshold
Correctly forces consecutive boolean truths from the raw VAD before transitioning cleanly. Counters are properly wiped if non-speech interrupts.

## 7. Silence Threshold
Correctly asserts continued silence tracking before issuing an end event.

## 8. Pre-Roll Semantics
Implemented via a bounded `collections.deque`. Pre-roll contains *only* audio frames immediately preceding the `SPEECH_START`-triggering frame. The triggering frame is delivered separately in the `VADEvent` and must not be duplicated.

## 9. Exact Pre-Roll Rounding Behavior
The pre-roll maximum frame boundary is mathematically derived via exact integer division rounding (`pre_roll_ms // frame_duration_ms`).

## 9. Post-Roll Deferral
Recognized in logic but explicit execution is deferred to Milestone 4.

## 10. Event Model
Abstracted cleanly via a strongly typed `VADEvent` dataclass carrying the `VADEventType`, the `triggering_frame`, and `pre_roll_frames` without duplication.

## 11. VAD Disabled Behavior
Handled natively in the StateMachine where processing yields `None` statically if the YAML states `enabled: False`.

## 12. CLI Diagnostic
Added `betel-pi vad-test` with specific flags indicating Mock or Real device execution paths to diagnose threshold/trigger settings interactively.

## 13. Exact Final Test Count
- Total automated tests: 34
- Result: 34 passed, 0 failed. Tests execute fully offline.

## 14. Package Build Result
Successful via standard `python -m build`. No unexpected heavyweight runtime dependencies were added.

## 15. Known Software Limitations
None found within the tested software parameters.

## 16. Physical Validation Pending
Physical/meeting-room validation has not yet been performed. Known pending validation items on the physical Raspberry Pi 3A+ include:
- ambient meeting-room noise
- speech detection accuracy
- false positives
- false negatives
- microphone placement effects
- background HVAC/fan noise
- multiple speakers
- distant speech

## 17. Meeting-room tuning pending
- Currently defaulting configurations (`mode=2`, `speech_start_frames=3`, `silence_frames=25`) will need iterative adjustments during live physical testing.

## 18. Items Deferred to M4
- Recording files / WAV creation
- Recording segmentation logic
- Storage lifecycle and bounds checking
- Post-roll enforcement logic onto writers
- SMB integrations
- File-naming architectures

---

### SOFTWARE VERIFIED
- WebRTC VAD abstractions implemented
- Dependency constraint validations implemented
- Strict frame validation checks
- VAD state machine implemented
- Speech-start logic and debounce implemented
- Speech-end logic and debounce implemented
- Strict pre-roll semantics verified
- Event model implemented
- VAD disabled behavior
- CLI Diagnostic
- Package build
- 34 Automated Tests Passed

### PHYSICAL VALIDATION PENDING
- Physical meeting-room VAD accuracy, noise evaluations, and multi-speaker tests remain unverified until physical installation.
