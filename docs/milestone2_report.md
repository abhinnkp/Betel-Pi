# Milestone 2 Completion Report

## 1. Files Changed
- `pyproject.toml`
- `app/config/config.py`
- `app/cli.py`
- `app/audio/device.py`
- `app/audio/alsa_device.py`
- `app/audio/mock_device.py`
- `app/audio/stats.py`
- `config/config.yaml`
- `tests/test_abstractions.py`
- `tests/test_cli.py`
- `tests/test_config.py`
- `docs/deployment.md`
- `docs/milestone2_audio.md`
- `README.md`

## 2. ALSA Dependency Selected
The implementation utilizes `pyalsaaudio==0.11.0`.

## 3. Dependency Compatibility Findings
- **Python 3.13:** Compatible. However, `audioop` is removed in 3.13, so audio statistics (RMS and Peak) are computed via Python's standard `struct` and `math` modules.
- **Debian Trixie:** Requires `libasound2-dev` and `gcc` during the master image deployment phase to compile the ALSA C extensions.
- **ARMv7 / AArch64:** ARMv7/AArch64 source-build path identified. Physical Python 3.13 + pyalsaaudio verification remains pending on the target Raspberry Pi hardware.

## 4. Audio Architecture
Audio capture utilizes a strict interface boundary (`AudioDevice`). The production adapter `ALSAAudioDevice` uses `PCM_NORMAL` (blocking reads), explicitly avoiding CPU-heavy Python sleep loops. The tests fall back seamlessly to `MockAudioDevice` allowing isolated offline development.

## 5. Frame Calculation
Frame dimensions are strictly deterministic based on configuration. For a standard config (16000Hz, 1 channel, 2-byte width, 20ms duration), the system automatically calculates `16000 * 0.02 * 1 * 2 = 640 bytes`. `ALSAAudioDevice` natively sets its `periodsize` to match the exact chunk frames required.

## 6. ALSA Configuration
The system strictly parses configuration values to apply `alsaaudio.PCM_FORMAT_S16_LE`, sample rate, and channels. If an XRUN occurs, it throws an `AudioOverrunError`.

## 7. Mock Implementation
`MockAudioDevice` mimics the exact byte sizes of the requested stream using `\x00` fills, allowing the `audio-test` CLI to verify lifecycle logic offline.

## 8. CLI Implementation
Added `betel-pi audio-devices` which queries ALSA PCMs directly, and `betel-pi audio-test` which initiates a deterministic hardware capture to report XRUN counts, duration, Peak, and RMS values.

## 9. Unit Test Count/Result
- **Total Tests:** 24
- **Result:** 24 passed (0 failures). Tests execute fully offline without ALSA hardware or network access.

## 10. Package Build Result
`python -m build` successfully produces `sdist` and `wheel` metadata.

## 11. Hardware Verification Status
*Note: No physical Raspberry Pi 3A+ + USB microphone was available during M2. The following items remain explicitly unverified:*
- **Hardware validation:** NOT PERFORMED
- **CPU measurement:** NOT PERFORMED
- **RAM measurement:** NOT PERFORMED
- **XRUN validation:** NOT PERFORMED
- **USB disconnect test:** NOT PERFORMED

## 12. Verification Breakdown

### SOFTWARE VERIFIED
- ALSA abstraction implemented
- MockAudioDevice implemented
- deterministic PCM frame calculation
- blocking capture architecture defined
- CLI (`audio-devices`, `audio-test`)
- offline statistics (RMS/Peak) via Python `struct`/`math`
- 26 tests fully offline
- Package builds containing pinned dependencies

### HARDWARE VERIFIED
*(None - pending physical testing.)*

## 13. Items Deferred to M3
- **VAD Processing Lifecycle:** Integrating `webrtcvad-wheels` with the captured frames.
- **Recording Logic:** Writing frames to WAV files via the `WavWriter`.
- **Pre-Roll/Post-Roll/Silence orchestration:** Enforcing ring buffers and silence tracking.
- **File Storage lifecycle:** Orchestrating naming and paths.
