import yaml
from typing import Dict, Any

class ConfigError(Exception):
    """Raised when there is an error in the configuration validation."""
    pass

class Config:
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
        self._validate()

    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        try:
            with open(filepath, "r") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ConfigError("Config file must contain a YAML dictionary.")
                return cls(data)
        except Exception as e:
            raise ConfigError(f"Failed to load config from {filepath}: {e}")

    def _validate(self):
        # Audio Section
        audio = self._config.get("audio", {})
        if not isinstance(audio, dict): raise ConfigError("Audio section missing or invalid.")
        if "device" not in audio: raise ConfigError("audio.device is required.")
        if audio.get("sample_rate") not in (8000, 16000, 32000, 48000):
            raise ConfigError("audio.sample_rate must be 8000, 16000, 32000, or 48000.")
        if audio.get("channels") != 1: raise ConfigError("audio.channels must be 1 (mono).")
        if audio.get("sample_width") != 2: raise ConfigError("audio.sample_width must be 2 (16-bit).")

        # Recording Section
        recording = self._config.get("recording", {})
        if not isinstance(recording, dict): raise ConfigError("Recording section missing or invalid.")
        if "output_path" not in recording: raise ConfigError("recording.output_path is required.")
        if recording.get("max_duration_sec", -1) <= 0: raise ConfigError("recording.max_duration_sec must be positive.")
        if recording.get("min_duration_sec", -1) <= 0: raise ConfigError("recording.min_duration_sec must be positive.")

        # VAD Section
        vad = self._config.get("vad", {})
        if not isinstance(vad, dict): raise ConfigError("VAD section missing or invalid.")
        if vad.get("mode") not in (0, 1, 2, 3): raise ConfigError("vad.mode must be 0, 1, 2, or 3.")
        if vad.get("frame_duration_ms") not in (10, 20, 30): raise ConfigError("vad.frame_duration_ms must be 10, 20, or 30.")
        if vad.get("speech_start_frames", -1) <= 0: raise ConfigError("vad.speech_start_frames must be positive.")
        if vad.get("silence_frames", -1) <= 0: raise ConfigError("vad.silence_frames must be positive.")

        # Storage Section
        storage = self._config.get("storage", {})
        if not isinstance(storage, dict): raise ConfigError("Storage section missing or invalid.")
        if storage.get("minimum_free_mb", -1) <= 0: raise ConfigError("storage.minimum_free_mb must be positive.")
        if not (0 < storage.get("maximum_usage_percent", -1) <= 100): raise ConfigError("storage.maximum_usage_percent must be between 1 and 100.")
        smb = storage.get("smb", {})
        if smb.get("enabled"):
            if "server" not in smb: raise ConfigError("storage.smb.server is required if SMB is enabled.")
            if "share" not in smb: raise ConfigError("storage.smb.share is required if SMB is enabled.")

        # Time Section
        time_cfg = self._config.get("time", {})
        if not isinstance(time_cfg, dict): raise ConfigError("Time section missing or invalid.")
        ntp = time_cfg.get("ntp", {})
        if ntp.get("enabled") and "server" not in ntp:
            raise ConfigError("time.ntp.server is required if NTP is enabled.")

        # Logging Section
        logging = self._config.get("logging", {})
        if not isinstance(logging, dict): raise ConfigError("Logging section missing or invalid.")
        if "level" not in logging: raise ConfigError("logging.level is required.")

    @property
    def raw(self) -> Dict[str, Any]:
        return self._config
