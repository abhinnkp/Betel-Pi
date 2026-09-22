import struct
import math

def calculate_rms(frame: bytes, sample_width: int) -> float:
    """Calculate the Root Mean Square of a PCM frame using standard libraries."""
    if not frame:
        return 0.0

    # Determine struct format
    if sample_width == 2:
        fmt = f"<{len(frame)//2}h" # Little-endian 16-bit
    elif sample_width == 1:
        fmt = f"{len(frame)}b" # 8-bit signed
    elif sample_width == 4:
        fmt = f"<{len(frame)//4}i" # Little-endian 32-bit
    else:
        return 0.0 # Unsupported calculation offline

    samples = struct.unpack(fmt, frame)
    if not samples:
        return 0.0

    sum_squares = sum(s * s for s in samples)
    return math.sqrt(sum_squares / len(samples))

def calculate_peak(frame: bytes, sample_width: int) -> int:
    """Calculate the absolute peak level of a PCM frame."""
    if not frame:
        return 0

    if sample_width == 2:
        fmt = f"<{len(frame)//2}h"
    elif sample_width == 1:
        fmt = f"{len(frame)}b"
    elif sample_width == 4:
        fmt = f"<{len(frame)//4}i"
    else:
        return 0

    samples = struct.unpack(fmt, frame)
    if not samples:
        return 0

    return max(abs(s) for s in samples)
