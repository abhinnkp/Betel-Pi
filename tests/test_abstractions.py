from app.system.platform import PlatformInfo
from app.vad.base import VADProcessor

def test_platform_info():
    assert isinstance(PlatformInfo.get_os(), str)
    assert isinstance(PlatformInfo.get_architecture(), str)
    assert isinstance(PlatformInfo.is_root(), bool)

class MockVADProcessor(VADProcessor):
    def __init__(self, mode: int):
        self.mode = mode
        self.state = 0

    def process_frame(self, frame: bytes) -> bool:
        # Mock logic: return True if frame has some arbitrary length
        return len(frame) > 10

    def reset(self):
        self.state = 0

def test_mock_vad_processor():
    vad = MockVADProcessor(mode=2)
    assert vad.process_frame(b'\x00' * 5) is False
    assert vad.process_frame(b'\x00' * 20) is True

    vad.reset()
    assert vad.state == 0
