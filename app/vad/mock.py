from app.vad.base import VADProcessor
from app.config.config import Config

class MockVADProcessor(VADProcessor):
    """
    Deterministic mock VAD processor for offline tests.
    Yields speech or silence based on a predefined sequence.
    """
    def __init__(self, config: Config, sequence: list[bool] = None):
        self.config = config
        self.expected_bytes = config.expected_frame_bytes
        self.sequence = sequence or []
        self.index = 0

    def process_frame(self, frame: bytes) -> bool:
        if len(frame) != self.expected_bytes:
            raise ValueError(f"MockVAD expected {self.expected_bytes} bytes, received {len(frame)} bytes.")

        if self.index < len(self.sequence):
            result = self.sequence[self.index]
            self.index += 1
            return result

        return False # Default to silence if sequence runs out

    def reset(self):
        self.index = 0
