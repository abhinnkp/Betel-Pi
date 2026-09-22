from abc import ABC, abstractmethod

class VADProcessor(ABC):
    @abstractmethod
    def process_frame(self, frame: bytes) -> bool:
        """
        Processes a fixed-size audio frame and returns True if speech is detected.
        """
        pass

    @abstractmethod
    def reset(self):
        """
        Resets any internal VAD state.
        """
        pass
