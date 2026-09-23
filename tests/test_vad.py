import pytest
from app.config.config import Config
from app.vad.base import VADState, VADEvent
from app.vad.mock import MockVADProcessor
from app.vad.webrtc import WebRTCVADProcessor
from app.vad.state import VADStateMachine

def get_base_cfg() -> Config:
    return Config({
        "audio": {
            "device": "hw:0,0",
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "format": "S16_LE",
            "frame_duration_ms": 20
        },
        "recording": {"output_path": "/mnt", "max_duration_sec": 300, "min_duration_sec": 1},
        "vad": {"enabled": True, "mode": 3, "frame_duration_ms": 20, "speech_start_frames": 3, "silence_frames": 5, "pre_roll_ms": 100, "post_roll_ms": 100},
        "storage": {"minimum_free_mb": 1000, "maximum_usage_percent": 90, "smb": {"enabled": False}},
        "time": {"ntp": {"enabled": False}},
        "logging": {"level": "DEBUG", "file": "/var/log"}
    })

def test_webrtc_vad_initialization():
    cfg = get_base_cfg()
    vad = WebRTCVADProcessor(cfg)
    assert vad.sample_rate == 16000

    # Check invalid byte length rejection
    with pytest.raises(ValueError, match="VAD expected 640 bytes"):
        vad.process_frame(b'\x00' * 10)

    # Check synthetic 20ms silence frame (640 bytes)
    assert vad.process_frame(b'\x00' * 640) is False

def test_mock_vad_processor():
    cfg = get_base_cfg()
    sequence = [True, False, True]
    vad = MockVADProcessor(cfg, sequence)

    assert vad.process_frame(b'\x00' * 640) is True
    assert vad.process_frame(b'\x00' * 640) is False
    assert vad.process_frame(b'\x00' * 640) is True
    assert vad.process_frame(b'\x00' * 640) is False # Out of bounds falls back to False

    vad.reset()
    assert vad.process_frame(b'\x00' * 640) is True

def test_vad_state_machine_speech_trigger():
    cfg = get_base_cfg()
    # speech_start_frames = 3, silence_frames = 5
    # pre_roll = 100ms / 20ms = 5 frames max len

    # 2 silent frames, 3 speech frames (triggers START), 1 speech, 5 silence (triggers END)
    sequence = [False, False, True, True, True, True, False, False, False, False, False]
    vad = MockVADProcessor(cfg, sequence)
    sm = VADStateMachine(vad, cfg)

    assert sm.state == VADState.SILENCE

    # Frame 0, 1: Silence
    assert sm.process_frame(b'\x00' * 640) is None
    assert sm.process_frame(b'\x00' * 640) is None

    # Frame 2, 3: Speech but no trigger yet
    assert sm.process_frame(b'\x00' * 640) is None
    assert sm.process_frame(b'\x00' * 640) is None

    # Frame 4: 3rd Speech frame -> SPEECH_START
    event = sm.process_frame(b'\x00' * 640)
    assert event is not None
    assert event[0] == VADEvent.SPEECH_START
    assert len(event[1]) == 5 # Frames 0, 1, 2, 3, 4 are appended to buffer right before process checks.
    assert sm.state == VADState.SPEECH

    # Frame 5: Speech continues
    assert sm.process_frame(b'\x00' * 640) is None

    # Frame 6, 7, 8, 9: Silence begins but no trigger
    for _ in range(4):
        assert sm.process_frame(b'\x00' * 640) is None

    # Frame 10: 5th Silence frame -> SPEECH_END
    event = sm.process_frame(b'\x00' * 640)
    assert event is not None
    assert event[0] == VADEvent.SPEECH_END
    assert sm.state == VADState.SILENCE

def test_vad_disabled():
    raw_cfg = get_base_cfg().raw
    raw_cfg["vad"]["enabled"] = False
    cfg = Config(raw_cfg)

    vad = MockVADProcessor(cfg, [True, True, True, True, True])
    sm = VADStateMachine(vad, cfg)

    # Process 5 solid speech frames, but since disabled, returns None and stays SILENCE
    for _ in range(5):
        assert sm.process_frame(b'\x00' * 640) is None

    assert sm.state == VADState.SILENCE

def test_vad_counter_resets():
    cfg = get_base_cfg() # speech_start_frames = 3
    sequence = [True, True, False, True, True, True]
    vad = MockVADProcessor(cfg, sequence)
    sm = VADStateMachine(vad, cfg)

    assert sm.process_frame(b'\x00' * 640) is None # speech 1
    assert sm.process_frame(b'\x00' * 640) is None # speech 2
    assert sm.process_frame(b'\x00' * 640) is None # silence -> resets speech counter
    assert sm.process_frame(b'\x00' * 640) is None # speech 1
    assert sm.process_frame(b'\x00' * 640) is None # speech 2

    event = sm.process_frame(b'\x00' * 640)        # speech 3 -> triggers
    assert event[0] == VADEvent.SPEECH_START
