try:
    import webrtcvad
    print(f"webrtcvad version: {webrtcvad.__version__}")
except ImportError:
    print("webrtcvad not installed")
