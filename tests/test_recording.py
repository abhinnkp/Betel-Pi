import pytest
import os
import wave
from app.config.config import Config
from app.vad.base import VADEvent, VADEventType
from app.recording.engine import RecordingEngine, RecordingState

def get_base_cfg(tmp_path) -> Config:
    return Config({
        "audio": {
            "device": "hw:0,0",
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "format": "S16_LE",
            "frame_duration_ms": 20 # => 640 bytes/frame
        },
        # Short durations for fast deterministic testing
        "recording": {"output_path": str(tmp_path), "max_duration_sec": 1, "min_duration_sec": 0.1},
        "vad": {"enabled": True, "mode": 2, "frame_duration_ms": 20, "speech_start_frames": 3, "silence_frames": 5, "pre_roll_ms": 100, "post_roll_ms": 60},
        "storage": {"minimum_free_mb": 100, "maximum_usage_percent": 90, "smb": {"enabled": False}},
        "time": {"ntp": {"enabled": False}},
        "logging": {"level": "DEBUG", "file": "/var/log"}
    })

def test_engine_state_transitions(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    assert engine.state == RecordingState.IDLE

    # Send SPEECH_START with explicit frames to verify ordering without duplication
    f_pre1, f_pre2 = b'\x01'*640, b'\x02'*640
    f_trig = b'\x03'*640

    start_event = VADEvent(
        type=VADEventType.SPEECH_START,
        triggering_frame=f_trig,
        pre_roll_frames=[f_pre1, f_pre2]
    )

    engine.process_frame(f_trig, start_event)
    assert engine.state == RecordingState.RECORDING
    assert engine._frames_written == 3 # pre1, pre2, trig
    assert engine._writer is not None

    # Process speech frames
    f_speech = b'\x04'*640
    res = engine.process_frame(f_speech)
    assert res is None
    assert engine._frames_written == 4

    # Handle SPEECH_END
    # The frame processing SPEECH_END counts as the first post-roll frame (frame 5 overall)
    end_event = VADEvent(type=VADEventType.SPEECH_END)
    engine.process_frame(b'\x05'*640, end_event)
    assert engine.state == RecordingState.POST_ROLL
    assert engine._post_roll_counter == 1

    # Post roll is 60ms = 3 frames. So we need 2 more.
    f_post2 = b'\x06'*640
    assert engine.process_frame(f_post2) is None
    assert engine.state == RecordingState.POST_ROLL

    # Third post-roll frame completes the limit
    f_post3 = b'\x07'*640
    res = engine.process_frame(f_post3)

    assert res is not None
    assert res.bytes_written == 7 * 640
    assert os.path.exists(res.filepath)
    assert engine.state == RecordingState.IDLE
    assert engine._writer is None

    # Validate output file chronologically
    with wave.open(res.filepath, 'rb') as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16000
        assert wav.getnframes() == 7 * 320 # 320 samples per frame
        data = wav.readframes(wav.getnframes())

        # Verify strict exact ordering. No duplication of f_trig.
        expected_data = f_pre1 + f_pre2 + f_trig + f_speech + b'\x05'*640 + f_post2 + f_post3
        assert data == expected_data

def test_post_roll_interruption_no_duplicates(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    # 1. Initial Speech
    f_trig1 = b'\x01'*640
    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=f_trig1)
    engine.process_frame(f_trig1, start_event)
    assert engine.state == RecordingState.RECORDING
    assert engine._frames_written == 1

    # 2. Ends
    engine.process_frame(b'\x02'*640, VADEvent(type=VADEventType.SPEECH_END))
    assert engine.state == RecordingState.POST_ROLL

    # 3. Post roll ticks 1 frame
    engine.process_frame(b'\x03'*640)
    assert engine._frames_written == 3  # (trig1, b02, b03)

    # 4. Speech resumes BEFORE post-roll completes
    # We pass the same triggering frame to the processor as happens in the real pipeline
    f_trig2 = b'\x04'*640
    resume_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=f_trig2)
    engine.process_frame(f_trig2, resume_event)

    assert engine.state == RecordingState.RECORDING
    assert engine._post_roll_counter == 0
    # Crucially, _frames_written must be exactly 4 (trig1, 02, 03, trig2). It must NOT be 5 (duplicate trig2).
    assert engine._frames_written == 4

    # 5. Ends naturally
    # processing SPEECH_END counts as post_roll_counter = 1
    engine.process_frame(b'\x05'*640, VADEvent(type=VADEventType.SPEECH_END))
    assert engine._post_roll_counter == 1
    res = None

    # We must exceed minimum duration limits so post-roll can naturally finalize.
    # Current config min is 0.1s (5 frames). We have 5 frames. Post roll requires 60ms (3 frames).
    # Since we are already at 5 frames when SPEECH_END occurred, exactly 3 post-roll frames are needed.
    res = engine.process_frame(b'\x06'*640) # PR 2
    assert res is None
    res = engine.process_frame(b'\x07'*640) # PR 3 (Completes)
    assert res is not None
    assert engine.state == RecordingState.IDLE

def test_minimum_duration_delays_finalization(tmp_path):
    cfg = get_base_cfg(tmp_path)
    # Config sets min_duration = 0.1s (5 frames). Post roll = 60ms (3 frames).
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)
    engine.process_frame(b'\x01'*640, start_event) # Frame 1

    # Immediate end
    engine.process_frame(b'\x02'*640, VADEvent(type=VADEventType.SPEECH_END)) # Frame 2 (Post roll starts)

    # Process the exact 3 post-roll frames
    engine.process_frame(b'\x03'*640) # Frame 3
    engine.process_frame(b'\x04'*640) # Frame 4
    res = engine.process_frame(b'\x05'*640) # Frame 5 (Post roll technically complete, but min dur 5 frames is hit EXACTLY here)

    assert res is not None
    assert res.bytes_written == 5 * 640

def test_maximum_duration_caps_minimum_duration(tmp_path):
    # Configure an edge case where max duration < min duration (though validated against in Config, we check the engine logic prioritizes Max)
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)
    engine.max_frames = 2 # Force max frames lower than min
    engine.min_frames = 10

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)
    engine.process_frame(b'\x01'*640, start_event)

    # Max duration hit on 2nd frame. It must terminate immediately despite min_frames.
    res = engine.process_frame(b'\x02'*640)
    assert res is not None
    assert engine.state == RecordingState.IDLE
    assert res.bytes_written == 2 * 640

def test_preroll_fits_exactly_max_duration(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)
    engine.max_frames = 3 # 3 frames absolute max

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640, pre_roll_frames=[b'\x02'*640, b'\x03'*640])

    # Pre-roll (2 frames) + Trigger (1 frame) = 3 frames.
    # The moment we process this, max duration should immediately fire finalization, returning a valid result instantly.
    res = engine.process_frame(b'\x01'*640, start_event)
    assert res is not None
    assert engine.state == RecordingState.IDLE
    assert res.bytes_written == 3 * 640

def test_preroll_larger_than_max_duration(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)
    engine.max_frames = 2 # absolute max is 2 frames (1 pre-roll + 1 trigger)

    # Send 3 pre-roll frames
    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640, pre_roll_frames=[b'\x02'*640, b'\x03'*640, b'\x04'*640])

    res = engine.process_frame(b'\x01'*640, start_event)
    assert res is not None
    assert engine.state == RecordingState.IDLE
    assert res.bytes_written == 2 * 640

def test_maximum_duration_enforcement(tmp_path):
    cfg = get_base_cfg(tmp_path) # Max duration is 1 sec = 50 frames
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x00'*640)
    engine.process_frame(b'\x00'*640, start_event)

    res = None
    for i in range(48): # We have 1 triggering frame, so adding 48 gives 49 total
        res = engine.process_frame(b'\x00'*640)
        assert res is None

    # The 50th frame should forcibly trigger finalization, overriding any VAD state
    res = engine.process_frame(b'\x00'*640)
    assert res is not None
    assert res.bytes_written == 50 * 640
    assert engine.state == RecordingState.IDLE

def test_force_shutdown_clean(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x00'*640)
    engine.process_frame(b'\x00'*640, start_event)
    engine.process_frame(b'\x00'*640)

    assert engine.state == RecordingState.RECORDING
    res = engine.force_shutdown()
    assert res is not None
    assert res.bytes_written == 2 * 640
    assert engine.state == RecordingState.IDLE

from unittest.mock import patch

def test_writer_open_failure(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)

    with patch("app.recording.wav_writer.WavWriter.open", side_effect=RuntimeError("simulated open failure")):
        res = engine.process_frame(b'\x01'*640, start_event)

    assert engine.state == RecordingState.ERROR
    assert engine._writer is None
    assert res is None

def test_writer_initial_write_failure(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)

    # Mocking write_frames to fail immediately when writing the triggering frame.
    with patch("app.recording.wav_writer.WavWriter.write_frames", side_effect=RuntimeError("simulated initial write failure")):
        res = engine.process_frame(b'\x01'*640, start_event)

    assert engine.state == RecordingState.ERROR
    assert engine._writer is None
    assert res is None

def test_writer_normal_write_failure(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)
    engine.process_frame(b'\x01'*640, start_event)
    assert engine.state == RecordingState.RECORDING

    # Simulate a mid-stream write failure
    with patch("app.recording.wav_writer.WavWriter.write_frames", side_effect=RuntimeError("simulated normal write failure")):
        res = engine.process_frame(b'\x02'*640)

    assert engine.state == RecordingState.ERROR
    assert engine._writer is None
    assert res is None

def test_writer_close_failure(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)
    engine.process_frame(b'\x01'*640, start_event)

    # Mock close() to fail during a graceful shutdown
    with patch("app.recording.wav_writer.WavWriter.close", side_effect=RuntimeError("simulated close failure")):
        res = engine.force_shutdown()

    assert engine.state == RecordingState.ERROR
    assert engine._writer is None
    assert res is None

def test_writer_cleanup_failure_preserves_original_error(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)
    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)

    # The writer.write_frames calls close() internally when catching an exception.
    # We mock both to fail. The engine should catch the primary write exception cleanly without crashing.
    with patch("app.recording.wav_writer.WavWriter.write_frames", side_effect=RuntimeError("primary write failure")):
        with patch("app.recording.wav_writer.WavWriter.close", side_effect=RuntimeError("secondary cleanup close failure")):
            res = engine.process_frame(b'\x01'*640, start_event)

    assert engine.state == RecordingState.ERROR
    assert engine._writer is None
    assert res is None
