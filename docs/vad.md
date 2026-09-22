# VAD (Voice Activity Detection)

Betel Pi uses `webrtcvad` to identify speech vs silence. This library is written in C++ and uses Gaussian Mixture Models, which is incredibly CPU efficient on low power ARM chips.

## Configuration
The `vad` section in `config.yaml` controls behavior:

- `mode`: WebRTC aggressiveness (0 to 3, where 3 is most aggressive at filtering out non-speech noise).
- `frame_duration_ms`: The size of the audio chunk analyzed (must be 10, 20, or 30 ms).
- `speech_start_frames`: The number of consecutive speech frames required to trigger a recording. This prevents loud, sudden noises from creating phantom recordings.
- `silence_frames`: The number of consecutive silent frames required to stop a recording.
- `pre_roll_ms` & `post_roll_ms`: Retains audio buffers just before and just after the VAD triggers, creating smoother audio clips.

## Abstraction
The application code depends only on a `VADProcessor` interface (`app/vad/base.py`). The planned concrete implementation `WebRTCVADProcessor` will wrap the actual `webrtcvad-wheels` library (deferred to later milestones). This allows tests to pass in a mock VAD processor and prevents tight coupling.
