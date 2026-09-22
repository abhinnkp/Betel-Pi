import pytest
from app.config.config import Config, ConfigError

def test_valid_config():
    valid_data = {
        "audio": {
            "device": "hw:0,0",
            "sample_rate": 16000,
            "channels": 1,
            "sample_width": 2
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
            "silence_frames": 30
        },
        "storage": {
            "minimum_free_mb": 1000,
            "maximum_usage_percent": 90
        },
        "logging": {
            "level": "DEBUG"
        }
    }
    config = Config(valid_data)
    assert config.raw["audio"]["sample_rate"] == 16000
    assert config.raw["vad"]["mode"] == 3

def test_invalid_audio_sample_rate():
    data = {
        "audio": {"device": "hw:0,0", "sample_rate": 44100, "channels": 1, "sample_width": 2},
        "recording": {"output_path": "/mnt", "max_duration_sec": 10, "min_duration_sec": 1},
        "vad": {"mode": 2, "frame_duration_ms": 20, "speech_start_frames": 1, "silence_frames": 10},
        "storage": {"minimum_free_mb": 100, "maximum_usage_percent": 90},
        "logging": {"level": "INFO"}
    }
    with pytest.raises(ConfigError, match="audio.sample_rate must be"):
        Config(data)

def test_invalid_vad_mode():
    data = {
        "audio": {"device": "hw:0,0", "sample_rate": 16000, "channels": 1, "sample_width": 2},
        "recording": {"output_path": "/mnt", "max_duration_sec": 10, "min_duration_sec": 1},
        "vad": {"mode": 5, "frame_duration_ms": 20, "speech_start_frames": 1, "silence_frames": 10},
        "storage": {"minimum_free_mb": 100, "maximum_usage_percent": 90},
        "logging": {"level": "INFO"}
    }
    with pytest.raises(ConfigError, match="vad.mode must be"):
        Config(data)
