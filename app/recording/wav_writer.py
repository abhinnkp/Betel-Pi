import wave
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class WavWriter:
    """
    Lightweight standard-library streaming WAV writer.
    Writes PCM frames directly to disk without buffering the entire recording in RAM.
    """
    def __init__(self, filepath: str, sample_rate: int, channels: int, sample_width: int):
        self.filepath = filepath
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self._wav: Optional[wave.Wave_write] = None
        self._bytes_written = 0

    def open(self):
        try:
            self._wav = wave.open(self.filepath, 'wb')
            self._wav.setnchannels(self.channels)
            self._wav.setsampwidth(self.sample_width)
            self._wav.setframerate(self.sample_rate)
            logger.info(f"Started recording to {self.filepath}")
        except Exception as e:
            logger.error(f"Failed to initialize WAV file {self.filepath}: {e}")
            self._wav = None
            raise

    def write_frames(self, frames: list[bytes]):
        if not self._wav:
            return

        try:
            data = b''.join(frames)
            self._wav.writeframes(data)
            self._bytes_written += len(data)
        except Exception as e:
            logger.error(f"Failed to write to WAV file {self.filepath}: {e}")
            try:
                self.close()
            except Exception as close_e:
                logger.error(f"Failed to clean up writer during write exception: {close_e}")
            raise e

    def close(self):
        if self._wav:
            try:
                self._wav.close()
                logger.info(f"Finalized WAV file {self.filepath} ({self._bytes_written} bytes)")
            except Exception as e:
                logger.error(f"Error closing WAV file {self.filepath}: {e}")
                raise e
            finally:
                self._wav = None
