from app.system.platform import PlatformInfo
from app.vad.base import VADProcessor
from app.audio.device import AudioDevice, enumerate_devices
import pytest

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

class MockAudioDevice(AudioDevice):
    def __init__(self):
        super().__init__("mock", 16000, 1, 2)
        self.is_open = False

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def read_frame(self, num_frames: int) -> bytes:
        if not self.is_open:
            raise RuntimeError("Device closed")
        return b'\x00' * num_frames

def test_mock_audio_device():
    dev = MockAudioDevice()
    assert not dev.is_open
    dev.open()
    assert dev.is_open
    assert len(dev.read_frame(10)) == 10
    dev.close()
    assert not dev.is_open

    with pytest.raises(RuntimeError):
        dev.read_frame(10)

def test_enumerate_devices_unimplemented():
    with pytest.raises(NotImplementedError):
        enumerate_devices()
