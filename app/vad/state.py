from collections import deque
from typing import List, Tuple, Optional
from app.vad.base import VADProcessor, VADEvent, VADState
from app.config.config import Config
import logging

logger = logging.getLogger(__name__)

class VADStateMachine:
    """
    Manages the higher-level speech/silence logic using a raw VADProcessor.
    Implements debounce thresholds (speech_start_frames, silence_frames) and a bounded pre-roll buffer.
    """
    def __init__(self, processor: VADProcessor, config: Config):
        self.processor = processor
        self.config = config

        vad_cfg = config.raw["vad"]
        self.enabled = vad_cfg["enabled"]
        self.speech_start_frames = vad_cfg["speech_start_frames"]
        self.silence_frames = vad_cfg["silence_frames"]

        # Calculate pre-roll bounds
        frame_dur_ms = vad_cfg["frame_duration_ms"]
        pre_roll_ms = vad_cfg["pre_roll_ms"]
        self.pre_roll_maxlen = int(pre_roll_ms // frame_dur_ms) if pre_roll_ms > 0 else 0

        self.pre_roll_buffer = deque(maxlen=self.pre_roll_maxlen) if self.pre_roll_maxlen > 0 else None

        self.state = VADState.SILENCE
        self.speech_counter = 0
        self.silence_counter = 0

    def process_frame(self, frame: bytes) -> Optional[Tuple[VADEvent, List[bytes]]]:
        """
        Process a single frame and return a (VADEvent, pre_roll_frames) tuple if a state transition occurs.
        If VAD is disabled, it acts as a pass-through (never triggers speech).
        """
        if not self.enabled:
            return None

        # Maintain bounded pre-roll when in SILENCE
        if self.state == VADState.SILENCE and self.pre_roll_buffer is not None:
            self.pre_roll_buffer.append(frame)

        is_speech = self.processor.process_frame(frame)

        if self.state == VADState.SILENCE:
            if is_speech:
                self.speech_counter += 1
                if self.speech_counter >= self.speech_start_frames:
                    # Transition to SPEECH
                    self.state = VADState.SPEECH
                    self.speech_counter = 0
                    self.silence_counter = 0
                    logger.info("VAD Event: SPEECH_START")

                    # Extract pre-roll frames to return with the event
                    pre_roll_frames = list(self.pre_roll_buffer) if self.pre_roll_buffer else []
                    if self.pre_roll_buffer:
                        self.pre_roll_buffer.clear()

                    return (VADEvent.SPEECH_START, pre_roll_frames)
            else:
                self.speech_counter = 0

        elif self.state == VADState.SPEECH:
            if not is_speech:
                self.silence_counter += 1
                if self.silence_counter >= self.silence_frames:
                    # Transition to SILENCE
                    self.state = VADState.SILENCE
                    self.silence_counter = 0
                    self.speech_counter = 0
                    logger.info("VAD Event: SPEECH_END")
                    return (VADEvent.SPEECH_END, [])
            else:
                self.silence_counter = 0

        return None

    def reset(self):
        """Resets the state machine and pre-roll buffers."""
        self.processor.reset()
        self.state = VADState.SILENCE
        self.speech_counter = 0
        self.silence_counter = 0
        if self.pre_roll_buffer is not None:
            self.pre_roll_buffer.clear()
