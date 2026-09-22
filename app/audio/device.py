from typing import List, Dict, Any

class AudioDevice(object):
    def __init__(self, device_id: str, sample_rate: int, channels: int, sample_width: int):
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width

    def open(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def read_frame(self, num_frames: int) -> bytes:
        raise NotImplementedError

def enumerate_devices() -> List[Dict[str, Any]]:
    """Returns a list of available ALSA capture devices."""
    raise NotImplementedError
