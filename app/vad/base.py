from enum import Enum, auto
from typing import Optional, List
from abc import ABC, abstractmethod

class VADEvent(Enum):
    SPEECH_START = auto()
    SPEECH_END = auto()

class VADState(Enum):
    SILENCE = auto()
    SPEECH = auto()

class VADProcessor(ABC):
    @abstractmethod
    def process_frame(self, frame: bytes) -> bool:
        """
        Processes a single configured audio frame and returns True if raw speech is detected.
        Must perform rigid frame validation before processing.
        """
        pass

    @abstractmethod
    def reset(self):
        """Resets any internal VAD state."""
        pass
