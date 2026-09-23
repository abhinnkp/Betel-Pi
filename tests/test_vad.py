import pytest
from app.config.config import Config
from app.vad.base import VADState, VADEventType
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

    sequence = [False, False, True, True, True, True, False, False, False, False, False]
    vad = MockVADProcessor(cfg, sequence)
    sm = VADStateMachine(vad, cfg)

    assert sm.state == VADState.SILENCE

    # Frame 0, 1: Silence
    f0, f1 = b'\x00'*640, b'\x01'*640
    assert sm.process_frame(f0) is None
    assert sm.process_frame(f1) is None

    # Frame 2, 3: Speech but no trigger yet
    f2, f3 = b'\x02'*640, b'\x03'*640
    assert sm.process_frame(f2) is None
    assert sm.process_frame(f3) is None

    # Frame 4: 3rd Speech frame -> SPEECH_START
    f4 = b'\x04'*640
    event = sm.process_frame(f4)
    assert event is not None
    assert event.type == VADEventType.SPEECH_START

    # Verify explicitly that pre-roll ONLY contains the frames immediately before trigger.
    # Because max_len is 5, it should contain f0, f1, f2, f3.
    # Importantly, f4 is the triggering frame and MUST NOT be in pre-roll.
    assert len(event.pre_roll_frames) == 4
    assert event.pre_roll_frames == [f0, f1, f2, f3]
    assert event.triggering_frame == f4

    assert sm.state == VADState.SPEECH

    # Frame 5: Speech continues
    f5 = b'\x05'*640
    assert sm.process_frame(f5) is None

    # Frame 6, 7, 8, 9: Silence begins but no trigger
    for i in range(6, 10):
        assert sm.process_frame(bytes([i])*640) is None

    # Frame 10: 5th Silence frame -> SPEECH_END
    f10 = b'\x0a'*640
    event = sm.process_frame(f10)
    assert event is not None
    assert event.type == VADEventType.SPEECH_END
    assert sm.state == VADState.SILENCE

def test_zero_pre_roll():
    raw_cfg = get_base_cfg().raw
    raw_cfg["vad"]["pre_roll_ms"] = 0
    cfg = Config(raw_cfg)

    sequence = [True, True, True]
    vad = MockVADProcessor(cfg, sequence)
    sm = VADStateMachine(vad, cfg)

    f0, f1, f2 = b'\x00'*640, b'\x01'*640, b'\x02'*640
    assert sm.process_frame(f0) is None
    assert sm.process_frame(f1) is None
    event = sm.process_frame(f2)

    assert event.type == VADEventType.SPEECH_START
    assert event.pre_roll_frames == []
    assert event.triggering_frame == f2

def test_pre_roll_bounds():
    raw_cfg = get_base_cfg().raw
    raw_cfg["vad"]["pre_roll_ms"] = 40 # Exactly 2 frames (40 // 20)
    cfg = Config(raw_cfg)

    # Sequence: 5 silence frames, then 3 speech frames
    sequence = [False, False, False, False, False, True, True, True]
    vad = MockVADProcessor(cfg, sequence)
    sm = VADStateMachine(vad, cfg)

    frames = [bytes([i])*640 for i in range(8)]

    for i in range(5):
        assert sm.process_frame(frames[i]) is None

    assert sm.process_frame(frames[5]) is None
    assert sm.process_frame(frames[6]) is None
    event = sm.process_frame(frames[7])

    assert event.type == VADEventType.SPEECH_START
    assert event.triggering_frame == frames[7]
    # The maxlen was 2, but we had 5 silence frames and 2 speech frames before trigger.
    # Total prior frames: frames[0..6]. The last 2 are frames[5] and frames[6].
    assert event.pre_roll_frames == [frames[5], frames[6]]

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
    assert event.type == VADEventType.SPEECH_START
