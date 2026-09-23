from enum import Enum, auto
import os
import time
import logging
from typing import Optional, List
from datetime import datetime

from app.config.config import Config
from app.vad.base import VADEvent, VADEventType
from app.recording.wav_writer import WavWriter

logger = logging.getLogger(__name__)

class RecordingState(Enum):
    IDLE = auto()
    RECORDING = auto()
    POST_ROLL = auto()
    ERROR = auto()

class RecordingResult:
    def __init__(self, filepath: str, start_time: float, end_time: float, bytes_written: int):
        self.filepath = filepath
        self.start_time = start_time
        self.end_time = end_time
        self.bytes_written = bytes_written
        self.duration_sec = end_time - start_time

class RecordingEngine:
    """
    Orchestrates the local audio file lifecycle based on VAD events.
    Enforces maximum duration, post-roll extension, and deterministic frame ordering.
    """
    def __init__(self, config: Config):
        self.config = config
        rec_cfg = config.raw["recording"]
        vad_cfg = config.raw["vad"]
        audio_cfg = config.raw["audio"]

        self.output_path = rec_cfg["output_path"]

        # Max duration in frames
        self.max_duration_sec = rec_cfg["max_duration_sec"]
        self.min_duration_sec = rec_cfg["min_duration_sec"]
        self.max_frames = int(self.max_duration_sec * audio_cfg["sample_rate"] / config.frames_per_buffer)
        self.min_frames = int(self.min_duration_sec * audio_cfg["sample_rate"] / config.frames_per_buffer)

        # Post-roll in frames
        frame_dur_ms = audio_cfg["frame_duration_ms"]
        self.post_roll_frames_target = int(vad_cfg["post_roll_ms"] // frame_dur_ms)

        self.sample_rate = audio_cfg["sample_rate"]
        self.channels = audio_cfg["channels"]
        self.sample_width = audio_cfg["sample_width"]
        self.bytes_per_frame = config.expected_frame_bytes

        self.state = RecordingState.IDLE
        self._writer: Optional[WavWriter] = None

        # Counters
        self._frames_written = 0
        self._post_roll_counter = 0
        self._start_time = 0.0
        self._current_filepath = ""

    def _generate_filename(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return os.path.join(self.output_path, f"betel_{timestamp}.wav")

    def handle_vad_event(self, event: VADEvent):
        """Handle top-level state transitions dictated by VAD events."""
        if event.type == VADEventType.SPEECH_START:
            if self.state in (RecordingState.IDLE, RecordingState.ERROR):
                self._start_recording(event)
            elif self.state == RecordingState.POST_ROLL:
                # Post-roll interrupted. Resume recording natively.
                logger.info("Speech resumed during post-roll. Cancelling finalization.")
                self.state = RecordingState.RECORDING
                self._post_roll_counter = 0

                # IMPORTANT: If VAD fires SPEECH_START again while we are in POST_ROLL,
                # we are technically already recording the frames leading up to it.
                # To prevent duplicate frames, we only append the triggering frame.
                # The pre_roll_frames were already captured as normal frames during POST_ROLL.
                if event.triggering_frame:
                    self._write_frame(event.triggering_frame)

        elif event.type == VADEventType.SPEECH_END:
            if self.state == RecordingState.RECORDING:
                logger.info("Speech ended. Entering POST_ROLL.")
                self.state = RecordingState.POST_ROLL
                self._post_roll_counter = 0

    def process_frame(self, frame: bytes) -> Optional[RecordingResult]:
        """
        Process incoming streaming audio frames.
        Returns a RecordingResult if a recording naturally finalizes during this frame loop.
        """
        if self.state == RecordingState.IDLE or self.state == RecordingState.ERROR:
            return None

        # Write the incoming frame immediately
        self._write_frame(frame)

        # Enforce Maximum Duration bounds rigidly
        if self._frames_written >= self.max_frames:
            logger.warning(f"Maximum recording duration ({self.max_duration_sec}s) reached. Forcing finalization.")
            return self._finalize_recording()

        if self.state == RecordingState.POST_ROLL:
            self._post_roll_counter += 1
            if self._post_roll_counter >= self.post_roll_frames_target:
                return self._finalize_recording()

        return None

    def _start_recording(self, event: VADEvent):
        """Initializes the WAV writer and injects pre-roll chronologically."""
        if not os.path.exists(self.output_path):
            try:
                os.makedirs(self.output_path, exist_ok=True)
            except Exception as e:
                logger.error(f"Cannot create output path {self.output_path}: {e}")
                self.state = RecordingState.ERROR
                return

        self._current_filepath = self._generate_filename()
        self._writer = WavWriter(self._current_filepath, self.sample_rate, self.channels, self.sample_width)

        try:
            self._writer.open()
            self._start_time = time.time()
            self._frames_written = 0
            self.state = RecordingState.RECORDING

            # Preserve M3 Contract: Write pre-roll chronologically
            if event.pre_roll_frames:
                self._writer.write_frames(event.pre_roll_frames)
                self._frames_written += len(event.pre_roll_frames)

            # Write Triggering frame exactly once
            if event.triggering_frame:
                self._writer.write_frames([event.triggering_frame])
                self._frames_written += 1

        except Exception as e:
            logger.error(f"Failed to start recording sequence: {e}")
            self.state = RecordingState.ERROR

    def _write_frame(self, frame: bytes):
        if self._writer and self.state in (RecordingState.RECORDING, RecordingState.POST_ROLL):
            try:
                self._writer.write_frames([frame])
                self._frames_written += 1
            except Exception as e:
                logger.error(f"Write failure during recording: {e}")
                self.state = RecordingState.ERROR
                self._writer.close()

    def _finalize_recording(self) -> Optional[RecordingResult]:
        """Safely closes the WAV writer and transitions back to IDLE. Returns metadata."""
        if not self._writer:
            self.state = RecordingState.IDLE
            return None

        # Check minimum duration behavior
        if self._frames_written < self.min_frames:
            # Policy: We finalize what we have, but log heavily. The file remains on disk.
            logger.warning(f"Recording finalized early. Captured {self._frames_written} frames. Below min limit of {self.min_frames}.")

        bytes_written = self._frames_written * self.bytes_per_frame

        try:
            self._writer.close()
        except Exception as e:
            logger.error(f"Error while finalizing: {e}")
            self.state = RecordingState.ERROR
            return None

        result = RecordingResult(
            filepath=self._current_filepath,
            start_time=self._start_time,
            end_time=time.time(),
            bytes_written=bytes_written
        )

        logger.info(f"Recording finalized: {result.filepath} ({bytes_written} bytes)")

        self._writer = None
        self._frames_written = 0
        self._post_roll_counter = 0
        self.state = RecordingState.IDLE
        return result

    def force_shutdown(self) -> Optional[RecordingResult]:
        """Cleanly forces finalization during unexpected application stops."""
        if self.state in (RecordingState.RECORDING, RecordingState.POST_ROLL):
            logger.info("Forcing shutdown. Finalizing active recording safely.")
            return self._finalize_recording()
        return None
