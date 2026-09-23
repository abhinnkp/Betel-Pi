from app.vad.base import VADProcessor
from app.config.config import Config
import logging

try:
    import webrtcvad
except ImportError:
    webrtcvad = None

logger = logging.getLogger(__name__)

class WebRTCVADProcessor(VADProcessor):
    """
    Production VAD implementation using webrtcvad-wheels.
    Performs rigid validation of incoming PCM frames to ensure they meet WebRTC requirements.
    """
    def __init__(self, config: Config):
        if webrtcvad is None:
            raise RuntimeError("webrtcvad-wheels is not installed. Cannot instantiate WebRTCVADProcessor.")

        vad_cfg = config.raw["vad"]
        audio_cfg = config.raw["audio"]

        self.sample_rate = audio_cfg["sample_rate"]
        self.channels = audio_cfg["channels"]
        self.sample_width = audio_cfg["sample_width"]
        self.format = audio_cfg["format"]
        self.frame_duration_ms = vad_cfg["frame_duration_ms"]

        self.expected_bytes = config.expected_frame_bytes

        if self.format != "S16_LE" or self.channels != 1 or self.sample_width != 2:
            raise ValueError(f"WebRTCVAD strictly requires mono S16_LE 16-bit PCM. Provided: format={self.format}, channels={self.channels}, width={self.sample_width}")

        if self.sample_rate not in (8000, 16000, 32000, 48000):
            raise ValueError(f"WebRTCVAD requires sample rates of 8000, 16000, 32000, or 48000. Provided: {self.sample_rate}")

        self.vad = webrtcvad.Vad(vad_cfg["mode"])

    def process_frame(self, frame: bytes) -> bool:
        if len(frame) != self.expected_bytes:
            raise ValueError(f"VAD expected {self.expected_bytes} bytes, received {len(frame)} bytes.")

        return self.vad.is_speech(frame, self.sample_rate)

    def reset(self):
        pass # WebRTC VAD has no internal state to reset between calls
