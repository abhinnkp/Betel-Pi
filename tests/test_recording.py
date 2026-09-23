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

    engine.handle_vad_event(start_event)
    assert engine.state == RecordingState.RECORDING
    assert engine._frames_written == 3 # pre1, pre2, trig
    assert engine._writer is not None

    # Process speech frames
    f_speech = b'\x04'*640
    res = engine.process_frame(f_speech)
    assert res is None
    assert engine._frames_written == 4

    # Handle SPEECH_END
    end_event = VADEvent(type=VADEventType.SPEECH_END)
    engine.handle_vad_event(end_event)
    assert engine.state == RecordingState.POST_ROLL

    # Post roll is 60ms = 3 frames.
    f_post1, f_post2 = b'\x05'*640, b'\x06'*640
    assert engine.process_frame(f_post1) is None
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
        expected_data = f_pre1 + f_pre2 + f_trig + f_speech + f_post1 + f_post2 + f_post3
        assert data == expected_data

def test_post_roll_interruption(tmp_path):
    cfg = get_base_cfg(tmp_path)
    engine = RecordingEngine(cfg)

    start_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x01'*640)
    engine.handle_vad_event(start_event)
    assert engine.state == RecordingState.RECORDING

    engine.handle_vad_event(VADEvent(type=VADEventType.SPEECH_END))
    assert engine.state == RecordingState.POST_ROLL

    # Process 1 post-roll frame
    engine.process_frame(b'\x02'*640)
    assert engine._post_roll_counter == 1

    # Speech resumes! (A new SPEECH_START comes in during POST_ROLL)
    resume_event = VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x03'*640)
    engine.handle_vad_event(resume_event)

    # Should flip back to RECORDING without creating a new file
    assert engine.state == RecordingState.RECORDING
    assert engine._post_roll_counter == 0
    # The previous 2 frames + 1 triggering frame = 3
    assert engine._frames_written == 3

    # Then eventually ends naturally...
    engine.handle_vad_event(VADEvent(type=VADEventType.SPEECH_END))
    assert engine.state == RecordingState.POST_ROLL

    res = None
    for i in range(3): # Configured post-roll is 3 frames
        res = engine.process_frame(b'\x04'*640)

    assert res is not None
    assert engine.state == RecordingState.IDLE

def test_maximum_duration_enforcement(tmp_path):
    cfg = get_base_cfg(tmp_path) # Max duration is 1 sec = 50 frames
    engine = RecordingEngine(cfg)

    engine.handle_vad_event(VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x00'*640))

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

    engine.handle_vad_event(VADEvent(type=VADEventType.SPEECH_START, triggering_frame=b'\x00'*640))
    engine.process_frame(b'\x00'*640)

    assert engine.state == RecordingState.RECORDING
    res = engine.force_shutdown()
    assert res is not None
    assert res.bytes_written == 2 * 640
    assert engine.state == RecordingState.IDLE
