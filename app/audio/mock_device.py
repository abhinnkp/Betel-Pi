from app.audio.device import AudioDevice, AudioDeviceError
from app.config.config import Config

class MockAudioDevice(AudioDevice):
    """A deterministic mock audio device for offline tests."""
    def __init__(self, config: Config):
        self.config = config
        self._is_open = False
        self.expected_bytes = config.expected_frame_bytes

    def open(self):
        self._is_open = True

    def close(self):
        self._is_open = False

    def is_open(self) -> bool:
        return self._is_open

    def read_frame(self) -> bytes:
        if not self._is_open:
            raise AudioDeviceError("Cannot read from a closed device.")
        # Return a zero-filled byte string matching the exact expected length
        return b'\x00' * self.expected_bytes
