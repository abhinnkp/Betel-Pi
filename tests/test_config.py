import pytest
from app.config.config import Config, ConfigError
import copy

def get_base_data():
    return {
        "audio": {
            "device": "hw:0,0",
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2,
            "format": "S16_LE"
        },
        "recording": {
            "output_path": "/mnt/recordings",
            "max_duration_sec": 300,
            "min_duration_sec": 1
        },
        "vad": {
            "enabled": True,
            "mode": 3,
            "frame_duration_ms": 20,
            "speech_start_frames": 5,
            "silence_frames": 30,
            "pre_roll_ms": 500,
            "post_roll_ms": 500
        },
        "storage": {
            "minimum_free_mb": 1000,
            "maximum_usage_percent": 90,
            "smb": {
                "enabled": True,
                "server": "10.0.0.1",
                "share": "RTLS",
                "mount_path": "/mnt/recordings"
            }
        },
        "time": {
            "ntp": {
                "enabled": True,
                "server": "10.0.0.2"
            }
        },
        "logging": {
            "level": "DEBUG",
            "file": "/var/log/betel.log"
        }
    }

def test_valid_config():
    valid_data = get_base_data()
    config = Config(valid_data)
    assert config.raw["audio"]["sample_rate"] == 16000
    assert config.raw["vad"]["mode"] == 3

def test_missing_sections():
    data = get_base_data()
    del data["audio"]
    with pytest.raises(ConfigError, match="Audio section missing"):
        Config(data)

    data = get_base_data()
    del data["recording"]
    with pytest.raises(ConfigError, match="Recording section missing"):
        Config(data)

def test_invalid_audio_types():
    data = get_base_data()
    data["audio"]["device"] = 123
    with pytest.raises(ConfigError, match="audio.device must be a string"):
        Config(data)

def test_invalid_audio_sample_rate():
    data = get_base_data()
    data["audio"]["sample_rate"] = 44100
    with pytest.raises(ConfigError, match="audio.sample_rate must be an integer \\(8000"):
        Config(data)

def test_invalid_durations():
    data = get_base_data()
    data["recording"]["min_duration_sec"] = -1
    with pytest.raises(ConfigError, match="must be numeric > 0"):
        Config(data)

def test_min_exceeds_max():
    data = get_base_data()
    data["recording"]["min_duration_sec"] = 500
    data["recording"]["max_duration_sec"] = 300
    with pytest.raises(ConfigError, match="must not exceed max_duration_sec"):
        Config(data)

def test_invalid_vad_values():
    data = get_base_data()
    data["vad"]["mode"] = 5
    with pytest.raises(ConfigError, match="vad.mode must be"):
        Config(data)

    data = get_base_data()
    data["vad"]["frame_duration_ms"] = 15
    with pytest.raises(ConfigError, match="frame_duration_ms must be"):
        Config(data)

def test_invalid_pre_post_roll():
    data = get_base_data()
    data["vad"]["pre_roll_ms"] = -50
    with pytest.raises(ConfigError, match="pre_roll_ms must be non-negative"):
        Config(data)

def test_invalid_storage_thresholds():
    data = get_base_data()
    data["storage"]["maximum_usage_percent"] = 150
    with pytest.raises(ConfigError, match="maximum_usage_percent must be between"):
        Config(data)

def test_invalid_smb_config():
    data = get_base_data()
    data["storage"]["smb"]["server"] = "  "
    with pytest.raises(ConfigError, match="server must be a non-empty string"):
        Config(data)

def test_invalid_ntp_config():
    data = get_base_data()
    data["time"]["ntp"]["server"] = ""
    with pytest.raises(ConfigError, match="ntp.server must be a valid hostname/IP"):
        Config(data)

def test_invalid_logging_config():
    data = get_base_data()
    data["logging"]["level"] = "FOO"
    with pytest.raises(ConfigError, match="logging.level must be a valid"):
        Config(data)

def test_config_file_loading_missing(tmp_path):
    with pytest.raises(ConfigError, match="Configuration file not found"):
        Config.from_file(str(tmp_path / "does_not_exist.yaml"))

def test_config_malformed_yaml(tmp_path):
    file_path = tmp_path / "bad.yaml"
    file_path.write_text("invalid: [yaml: {")
    with pytest.raises(ConfigError, match="Malformed YAML"):
        Config.from_file(str(file_path))
