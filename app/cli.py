import argparse
import sys
from importlib.metadata import version

def print_version():
    try:
        ver = version("betel-pi")
    except Exception:
        ver = "0.1.0 (dev)"
    print(f"Betel Pi v{ver}")

def print_status():
    print("Betel Pi Status")
    print("===============")
    print("Platform: Mock Platform")
    print("OS: Debian GNU/Linux (mocked)")
    print("Architecture: armv7l (mocked)")
    print("USB Audio: Not initialized")
    print("VAD Configuration: Loaded")
    print("Storage Status: OK")
    print("SMB Mount Status: OK")
    print("NTP Status: Synchronized (mocked)")
    print("Service State: Not running")

def main():
    parser = argparse.ArgumentParser(description="Betel Pi Audio Recorder CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("version", help="Show application version")
    subparsers.add_parser("status", help="Show system status")
    subparsers.add_parser("audio-devices", help="Enumerate ALSA devices")
    subparsers.add_parser("audio-test", help="Capture a manual test recording")
    subparsers.add_parser("vad-test", help="Run VAD diagnostics")
    subparsers.add_parser("run", help="Start production recording lifecycle")

    args = parser.parse_args()

    if args.command == "version":
        print_version()
    elif args.command == "status":
        print_status()
    elif args.command == "audio-devices":
        print("Not implemented yet.")
    elif args.command == "audio-test":
        print("Not implemented yet.")
    elif args.command == "vad-test":
        print("Not implemented yet.")
    elif args.command == "run":
        print("Not implemented yet.")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
