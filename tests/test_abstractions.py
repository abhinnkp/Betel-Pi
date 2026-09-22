from app.system.platform import PlatformInfo
from app.vad.base import VADProcessor
from app.audio.device import AudioDevice, AudioDeviceError, enumerate_devices
from app.audio.mock_device import MockAudioDevice
from app.audio.stats import calculate_rms, calculate_peak
from app.config.config import Config
import pytest
import struct

def test_platform_info():
    assert isinstance(PlatformInfo.get_os(), str)
    assert isinstance(PlatformInfo.get_architecture(), str)
    assert isinstance(PlatformInfo.is_root(), bool)

class MockVADProcessor(VADProcessor):
    def __init__(self, mode: int):
        self.mode = mode
        self.state = 0

    def process_frame(self, frame: bytes) -> bool:
        return len(frame) > 10

    def reset(self):
        self.state = 0

def test_mock_vad_processor():
    vad = MockVADProcessor(mode=2)
    assert vad.process_frame(b'\x00' * 5) is False
    assert vad.process_frame(b'\x00' * 20) is True

    vad.reset()
    assert vad.state == 0

def test_mock_audio_device():
    # Construct a minimal config dict to satisfy MockAudioDevice
    cfg = Config({
        "audio": {
            "device": "hw:0,0",
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "format": "S16_LE",
            "frame_duration_ms": 20
        },
        "recording": {"output_path": "/mnt", "max_duration_sec": 300, "min_duration_sec": 1},
        "vad": {"enabled": True, "mode": 3, "frame_duration_ms": 20, "speech_start_frames": 5, "silence_frames": 30, "pre_roll_ms": 500, "post_roll_ms": 500},
        "storage": {"minimum_free_mb": 1000, "maximum_usage_percent": 90, "smb": {"enabled": False}},
        "time": {"ntp": {"enabled": False}},
        "logging": {"level": "DEBUG", "file": "/var/log"}
    })

    dev = MockAudioDevice(cfg)
    assert not dev.is_open()
    dev.open()
    assert dev.is_open()

    # Check deterministic frame size
    frame = dev.read_frame()
    assert len(frame) == 640 # 16000 * 0.02 * 1 * 2 = 640 bytes

    dev.close()
    assert not dev.is_open()

    with pytest.raises(AudioDeviceError):
        dev.read_frame()

def test_audio_stats():
    # 16-bit PCM test
    # Create 4 samples: 10, -10, 20, -20
    data = struct.pack("<4h", 10, -10, 20, -20)
    rms = calculate_rms(data, 2)
    peak = calculate_peak(data, 2)

    assert peak == 20
    # RMS = sqrt((100+100+400+400)/4) = sqrt(250) = ~15.81
    assert 15.8 < rms < 15.9

    # 8-bit PCM test
    data_8 = struct.pack("4b", 10, -10, 20, -20)
    assert calculate_peak(data_8, 1) == 20
    assert 15.8 < calculate_rms(data_8, 1) < 15.9

def test_enumerate_devices():
    devices = enumerate_devices()
    assert isinstance(devices, list)
    # Could be empty offline, but should return cleanly
