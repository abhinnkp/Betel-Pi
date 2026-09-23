import argparse
import sys
import os
from importlib.metadata import version
import time
from app.config.config import Config
from app.audio.device import enumerate_devices, AudioOverrunError, AudioDeviceError
from app.audio.stats import calculate_rms, calculate_peak

def get_config_path(args_path: str = None) -> str:
    """Determine the configuration path prioritizing explicit arg, then production path, then dev path resolved relative to the package."""
    if args_path:
        return args_path

    prod_path = "/etc/betel-pi/config.yaml"
    if os.path.exists(prod_path):
        return prod_path

    # Resolve the dev path relative to this file, avoiding reliance on Current Working Directory (CWD).
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dev_path = os.path.join(package_dir, "config", "config.yaml")
    return dev_path

def print_version():
    try:
        ver = version("betel-pi")
    except Exception:
        ver = "0.1.0 (dev)"
    print(f"Betel Pi v{ver}")

def print_audio_devices():
    print("ALSA Capture Devices")
    print("====================")
    devices = enumerate_devices()
    if not devices:
        print("No capture devices found or ALSA unavailable.")
        return

    for d in devices:
        print(f"- ID: {d['id']} | Name: {d['name']} | Capture Capable: {d['capture_capable']}")

def run_audio_test(config_path: str, frames_to_capture: int = 50):
    print(f"Loading configuration from {config_path}...")
    cfg = Config.from_file(config_path)
    audio_cfg = cfg.raw["audio"]

    print("\nAudio Test Configuration:")
    print(f"Device:        {audio_cfg['device']}")
    print(f"Sample Rate:   {audio_cfg['sample_rate']} Hz")
    print(f"Channels:      {audio_cfg['channels']}")
    print(f"Sample Width:  {audio_cfg['sample_width']} bytes")
    print(f"Frame Dur:     {audio_cfg['frame_duration_ms']} ms")
    print(f"Expected Size: {cfg.expected_frame_bytes} bytes/frame")
    print("----------------------------------------")

    try:
        from app.audio.alsa_device import ALSAAudioDevice
        device = ALSAAudioDevice(cfg)
        device.open()
    except Exception as e:
        print(f"\n[!] Audio Test FAILED: Failed to initialize ALSA device: {e}")
        sys.exit(1)

    try:
        print("\nDevice opened successfully. Capturing...")

        captured_frames = 0
        xrun_count = 0
        total_rms = 0.0
        max_peak = 0

        start_time = time.time()

        while captured_frames < frames_to_capture:
            try:
                frame = device.read_frame()
                captured_frames += 1

                rms = calculate_rms(frame, audio_cfg['sample_width'])
                peak = calculate_peak(frame, audio_cfg['sample_width'])

                total_rms += rms
                if peak > max_peak:
                    max_peak = peak

            except AudioOverrunError:
                xrun_count += 1
            except AudioDeviceError as e:
                print(f"Capture error: {e}")
                break

        duration = time.time() - start_time

        print("\nTest Complete!")
        print(f"Frames Captured: {captured_frames}")
        print(f"Duration:        {duration:.2f} sec")
        print(f"XRUNs:           {xrun_count}")
        if captured_frames > 0:
            print(f"Avg RMS Level:   {total_rms / captured_frames:.2f}")
            print(f"Peak Level:      {max_peak}")

    finally:
        device.close()

def run_vad_test(config_path: str, use_mock: bool):
    print(f"Loading configuration from {config_path}...")
    cfg = Config.from_file(config_path)
    vad_cfg = cfg.raw["vad"]
    audio_cfg = cfg.raw["audio"]

    print("\nVAD Test Configuration:")
    print(f"VAD Enabled:    {vad_cfg['enabled']}")
    print(f"Mode:           {vad_cfg['mode']}")
    print(f"Sample Rate:    {audio_cfg['sample_rate']} Hz")
    print(f"Frame Dur:      {vad_cfg['frame_duration_ms']} ms")
    print(f"Speech Start:   {vad_cfg['speech_start_frames']} frames")
    print(f"Silence End:    {vad_cfg['silence_frames']} frames")
    print(f"Pre-roll:       {vad_cfg['pre_roll_ms']} ms")
    print(f"Audio Source:   {'Mock' if use_mock else 'ALSA Hardware'}")
    print("----------------------------------------")

    if not vad_cfg["enabled"]:
        print("VAD is disabled in configuration. Exiting.")
        return

    from app.vad.webrtc import WebRTCVADProcessor
    from app.vad.state import VADStateMachine

    try:
        vad_processor = WebRTCVADProcessor(cfg)
        state_machine = VADStateMachine(vad_processor, cfg)
    except Exception as e:
        print(f"[!] Failed to initialize WebRTC VAD: {e}")
        sys.exit(1)

    if use_mock:
        from app.audio.mock_device import MockAudioDevice
        device = MockAudioDevice(cfg)
    else:
        from app.audio.alsa_device import ALSAAudioDevice
        try:
            device = ALSAAudioDevice(cfg)
        except Exception as e:
            print(f"[!] VAD Test FAILED: Failed to initialize ALSA device: {e}")
            sys.exit(1)

    try:
        device.open()
        print("\nDevice opened successfully. Monitoring for VAD events (Press Ctrl+C to stop)...")
        print(f"Current State: {state_machine.state.name}")

        # Capture 100 frames max for the diagnostic test to ensure it terminates
        frames_to_test = 100

        for i in range(frames_to_test):
            try:
                frame = device.read_frame()
                event = state_machine.process_frame(frame)

                if event:
                    event_type, pre_roll = event
                    print(f"[{i:03d}] Event Detected: {event_type.name} | Pre-roll frames returned: {len(pre_roll)}")
                    print(f"      -> New State: {state_machine.state.name}")

            except AudioOverrunError:
                print("[!] XRUN detected.")
            except AudioDeviceError as e:
                print(f"[!] Audio Error: {e}")
                break

        print("\nTest Complete (Reached max diagnostic frames).")

    except KeyboardInterrupt:
        print("\nTest Interrupted by User.")
    finally:
        device.close()

def print_status(config_path: str):
    print("Betel Pi Status")
    print("===============")
    print("Platform: Mock Platform")
    print("OS: Debian GNU/Linux (mocked)")
    print("Architecture: armv7l (mocked)")
    print(f"Config Path: {config_path}")
    print("USB Audio: NOT_CHECKED")
    print("VAD Configuration: Loaded")
    print("Storage Status: NOT_CHECKED")
    print("SMB Mount Status: NOT_CHECKED")
    print("NTP Status: NOT_CHECKED")
    print("Service State: NOT_IMPLEMENTED")

def main():
    parser = argparse.ArgumentParser(description="Betel Pi Audio Recorder CLI")
    parser.add_argument("--config", "-c", help="Path to config.yaml", type=str)
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("version", help="Show application version")
    subparsers.add_parser("status", help="Show system status")
    subparsers.add_parser("audio-devices", help="Enumerate ALSA devices")
    subparsers.add_parser("audio-test", help="Capture a manual test recording")
    vad_parser = subparsers.add_parser("vad-test", help="Run VAD diagnostics")
    vad_parser.add_argument("--mock", action="store_true", help="Use Mock Audio Device instead of ALSA")
    subparsers.add_parser("run", help="Start production recording lifecycle")

    args = parser.parse_args()
    config_path = get_config_path(args.config)

    if args.command == "version":
        print_version()
    elif args.command == "status":
        print_status(config_path)
    elif args.command == "audio-devices":
        print_audio_devices()
    elif args.command == "audio-test":
        run_audio_test(config_path)
    elif args.command == "vad-test":
        run_vad_test(config_path, args.mock)
    elif args.command == "run":
        print("Not implemented yet. Will start production loop in future milestones.")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
