from typing import List, Dict, Any

class AudioDeviceError(Exception):
    """Base exception for audio device errors."""
    pass

class AudioOverrunError(AudioDeviceError):
    """Raised when the audio device reports a buffer overrun (XRUN)."""
    pass

class AudioDevice:
    """Base interface for deterministic audio capture."""

    def open(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def is_open(self) -> bool:
        raise NotImplementedError

    def read_frame(self) -> bytes:
        """Read exactly one configured frame of PCM audio."""
        raise NotImplementedError

def enumerate_devices() -> List[Dict[str, Any]]:
    """Returns a list of available ALSA capture devices."""
    try:
        import alsaaudio
        # ALSA exposes available PCM capture devices directly
        pcm_devices = alsaaudio.pcms(alsaaudio.PCM_CAPTURE)

        return [{"id": name, "name": name, "capture_capable": True} for name in pcm_devices]
    except ImportError:
        return []
