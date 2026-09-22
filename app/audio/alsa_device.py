import logging
from app.audio.device import AudioDevice, AudioDeviceError, AudioOverrunError
from app.config.config import Config

try:
    import alsaaudio
except ImportError:
    alsaaudio = None

logger = logging.getLogger(__name__)

class ALSAAudioDevice(AudioDevice):
    """
    Production ALSA implementation for Raspberry Pi 3A+ using pyalsaaudio.
    Leverages blocking reads and strictly avoids polling/sleep loops for low CPU usage.
    """
    def __init__(self, config: Config):
        if alsaaudio is None:
            raise RuntimeError("pyalsaaudio is not installed. Cannot instantiate ALSAAudioDevice.")

        self.config = config
        self._pcm = None

        audio_cfg = self.config.raw["audio"]
        self.device_name = audio_cfg["device"]
        self.sample_rate = audio_cfg["sample_rate"]
        self.channels = audio_cfg["channels"]

        # ALSA period size is exactly the number of frames per buffer the config demands.
        self.period_size = self.config.frames_per_buffer
        self.expected_bytes = self.config.expected_frame_bytes

        if audio_cfg["format"] == "S16_LE":
            self.format = alsaaudio.PCM_FORMAT_S16_LE
        else:
            raise AudioDeviceError(f"Unsupported ALSA format: {audio_cfg['format']}")

    def open(self):
        if self._pcm is not None:
            return

        logger.info(f"Opening ALSA device '{self.device_name}' at {self.sample_rate}Hz, {self.channels} channel(s)")
        try:
            # PCM_NORMAL specifies blocking mode, avoiding busy-loops.
            self._pcm = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, device=self.device_name)
            self._pcm.setchannels(self.channels)
            self._pcm.setrate(self.sample_rate)
            self._pcm.setformat(self.format)
            self._pcm.setperiodsize(self.period_size)
            logger.info("ALSA device successfully opened and configured.")
        except alsaaudio.ALSAAudioError as e:
            self._pcm = None
            raise AudioDeviceError(f"Failed to open/configure ALSA device: {e}")

    def close(self):
        if self._pcm is not None:
            logger.info("Closing ALSA device.")
            self._pcm.close()
            self._pcm = None

    def is_open(self) -> bool:
        return self._pcm is not None

    def read_frame(self) -> bytes:
        if not self._pcm:
            raise AudioDeviceError("Device is not open.")

        # Blocking read
        length, data = self._pcm.read()

        if length < 0:
            # Overrun (XRUN) occurred.
            logger.warning(f"ALSA buffer overrun (XRUN) detected. Code: {length}")
            raise AudioOverrunError("Buffer overrun detected in ALSA capture.")

        if length == 0:
            raise AudioDeviceError("ALSA read returned 0 frames.")

        if len(data) != self.expected_bytes:
            # Handle partial reads (should not occur in normal blocking mode, but be defensive)
            raise AudioDeviceError(f"Unexpected frame length. Expected {self.expected_bytes}, got {len(data)}")

        return data
