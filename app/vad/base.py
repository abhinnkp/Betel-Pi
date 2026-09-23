from enum import Enum, auto
from typing import Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

class VADEventType(Enum):
    SPEECH_START = auto()
    SPEECH_END = auto()

@dataclass
class VADEvent:
    type: VADEventType
    triggering_frame: Optional[bytes] = None
    pre_roll_frames: List[bytes] = field(default_factory=list)

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
