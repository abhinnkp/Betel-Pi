import subprocess
import sys

def test_cli_version():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Betel Pi v" in result.stdout

def test_cli_status():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "status"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "NOT_CHECKED" in result.stdout
    assert "NOT_IMPLEMENTED" in result.stdout
    assert "Config Path" in result.stdout

def test_cli_audio_devices():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "audio-devices"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "ALSA Capture Devices" in result.stdout

def test_cli_audio_test():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "audio-test"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Audio Test Configuration:" in result.stdout
    assert "Frames Captured: 50" in result.stdout

def test_cli_unknown_command():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "unknown-command"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
