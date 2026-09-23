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
    # ALSA isn't present in this offline environment, so it MUST exit non-zero
    # and MUST NOT silently fall back to Mock.
    assert result.returncode != 0
    assert "Audio Test FAILED: Failed to initialize ALSA device" in result.stdout
    assert "MockAudioDevice" not in result.stdout

def test_cli_vad_test_mock():
    # Test that --mock successfully runs the vad diagnostic offline
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "vad-test", "--mock"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "VAD Test Configuration:" in result.stdout
    assert "Test Complete (Reached max diagnostic frames)." in result.stdout

def test_cli_unknown_command():
    result = subprocess.run(
        [sys.executable, "-m", "app.cli", "unknown-command"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
