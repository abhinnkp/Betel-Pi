import argparse
import sys
import os
from importlib.metadata import version

def get_config_path(args_path: str = None) -> str:
    """Determine the configuration path prioritizing explicit arg, then production path, then dev path."""
    if args_path:
        return args_path

    prod_path = "/etc/betel-pi/config.yaml"
    if os.path.exists(prod_path):
        return prod_path

    dev_path = "config/config.yaml"
    return dev_path

def print_version():
    try:
        ver = version("betel-pi")
    except Exception:
        ver = "0.1.0 (dev)"
    print(f"Betel Pi v{ver}")

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
    subparsers.add_parser("vad-test", help="Run VAD diagnostics")
    subparsers.add_parser("run", help="Start production recording lifecycle")

    args = parser.parse_args()
    config_path = get_config_path(args.config)

    if args.command == "version":
        print_version()
    elif args.command == "status":
        print_status(config_path)
    elif args.command == "audio-devices":
        print("Not implemented yet.")
    elif args.command == "audio-test":
        print("Not implemented yet.")
    elif args.command == "vad-test":
        print("Not implemented yet.")
    elif args.command == "run":
        print("Not implemented yet. Will start production loop in future milestones.")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
