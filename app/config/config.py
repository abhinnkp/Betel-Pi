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
        except yaml.YAMLError as e:
            raise ConfigError(f"Malformed YAML in config file {filepath}: {e}")
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {filepath}")
        except Exception as e:
            raise ConfigError(f"Failed to load config from {filepath}: {e}")

    def _validate(self):
        # Audio Section
        audio = self._config.get("audio")
        if not isinstance(audio, dict): raise ConfigError("Audio section missing or invalid type.")
        if not isinstance(audio.get("device"), str): raise ConfigError("audio.device must be a string.")

        sample_rate = audio.get("sample_rate")
        if not isinstance(sample_rate, int) or sample_rate not in (8000, 16000, 32000, 48000):
            raise ConfigError("audio.sample_rate must be an integer (8000, 16000, 32000, or 48000).")

        if audio.get("channels") != 1: raise ConfigError("audio.channels must be an integer exactly 1 (mono).")
        if audio.get("sample_width") != 2: raise ConfigError("audio.sample_width must be an integer exactly 2 (16-bit).")
        if not isinstance(audio.get("format"), str) or not audio.get("format"): raise ConfigError("audio.format must be a valid configured string.")

        # Recording Section
        recording = self._config.get("recording")
        if not isinstance(recording, dict): raise ConfigError("Recording section missing or invalid type.")

        output_path = recording.get("output_path")
        if not isinstance(output_path, str) or not output_path.strip():
            raise ConfigError("recording.output_path must be a non-empty string.")

        max_dur = recording.get("max_duration_sec")
        min_dur = recording.get("min_duration_sec")
        if not isinstance(max_dur, (int, float)) or max_dur <= 0: raise ConfigError("recording.max_duration_sec must be numeric > 0.")
        if not isinstance(min_dur, (int, float)) or min_dur <= 0: raise ConfigError("recording.min_duration_sec must be numeric > 0.")
        if min_dur > max_dur: raise ConfigError("recording.min_duration_sec must not exceed max_duration_sec.")

        # VAD Section
        vad = self._config.get("vad")
        if not isinstance(vad, dict): raise ConfigError("VAD section missing or invalid type.")
        if not isinstance(vad.get("enabled"), bool): raise ConfigError("vad.enabled must be a boolean.")
        if vad.get("mode") not in (0, 1, 2, 3): raise ConfigError("vad.mode must be an integer 0, 1, 2, or 3.")
        if vad.get("frame_duration_ms") not in (10, 20, 30): raise ConfigError("vad.frame_duration_ms must be 10, 20, or 30.")

        speech_start = vad.get("speech_start_frames")
        if not isinstance(speech_start, int) or speech_start <= 0: raise ConfigError("vad.speech_start_frames must be a positive integer.")
        silence_frames = vad.get("silence_frames")
        if not isinstance(silence_frames, int) or silence_frames <= 0: raise ConfigError("vad.silence_frames must be a positive integer.")

        pre_roll = vad.get("pre_roll_ms")
        if not isinstance(pre_roll, (int, float)) or pre_roll < 0: raise ConfigError("vad.pre_roll_ms must be non-negative.")
        post_roll = vad.get("post_roll_ms")
        if not isinstance(post_roll, (int, float)) or post_roll < 0: raise ConfigError("vad.post_roll_ms must be non-negative.")

        # Storage Section
        storage = self._config.get("storage")
        if not isinstance(storage, dict): raise ConfigError("Storage section missing or invalid type.")
        min_free = storage.get("minimum_free_mb")
        if not isinstance(min_free, int) or min_free <= 0: raise ConfigError("storage.minimum_free_mb must be a positive integer.")

        max_usage = storage.get("maximum_usage_percent")
        if not isinstance(max_usage, (int, float)) or not (0 < max_usage <= 100):
            raise ConfigError("storage.maximum_usage_percent must be between 1 and 100.")

        smb = storage.get("smb", {})
        if not isinstance(smb, dict): raise ConfigError("storage.smb must be a dict.")
        if not isinstance(smb.get("enabled"), bool): raise ConfigError("storage.smb.enabled must be a boolean.")

        if smb.get("enabled"):
            server = smb.get("server")
            share = smb.get("share")
            mount_path = smb.get("mount_path")
            if not isinstance(server, str) or not server.strip(): raise ConfigError("storage.smb.server must be a non-empty string when enabled.")
            if not isinstance(share, str) or not share.strip(): raise ConfigError("storage.smb.share must be a non-empty string when enabled.")
            if not isinstance(mount_path, str) or not mount_path.startswith("/"): raise ConfigError("storage.smb.mount_path must be a non-empty absolute path when enabled.")

        # Time Section
        time_cfg = self._config.get("time")
        if not isinstance(time_cfg, dict): raise ConfigError("Time section missing or invalid type.")
        ntp = time_cfg.get("ntp", {})
        if not isinstance(ntp, dict): raise ConfigError("time.ntp must be a dict.")
        if not isinstance(ntp.get("enabled"), bool): raise ConfigError("time.ntp.enabled must be a boolean.")

        if ntp.get("enabled"):
            server = ntp.get("server")
            if not isinstance(server, str) or not server.strip():
                raise ConfigError("time.ntp.server must be a valid hostname/IP when enabled.")

        # Logging Section
        logging = self._config.get("logging")
        if not isinstance(logging, dict): raise ConfigError("Logging section missing or invalid type.")

        level = logging.get("level")
        if not isinstance(level, str) or level.upper() not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ConfigError("logging.level must be a valid logging level string.")

        log_file = logging.get("file")
        if not isinstance(log_file, str) or not log_file.strip():
            raise ConfigError("logging.file must be a non-empty string/path.")

    @property
    def raw(self) -> Dict[str, Any]:
        return self._config
