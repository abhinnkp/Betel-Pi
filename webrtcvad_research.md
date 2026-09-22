# WebRTC VAD Compatibility on Debian 13 (Trixie) for Raspberry Pi 3A+

## Revision 1: Compatibility with Python 3.13 and WebRTC VAD Packages

The original `webrtcvad` package (version 2.0.10) relies on outdated setup structures (`pkg_resources` which is deprecated/removed in Python 3.12+ environments without `setuptools`). Compiling it natively on Python 3.13 requires manual injection of `setuptools` and build tools. Furthermore, it completely lacks pre-compiled wheels for ARM architectures.

### Investigation of `webrtcvad-wheels`
To address this, we investigated `webrtcvad-wheels` (version 2.0.14) and confirmed the following:

1. **Exact package name:** `webrtcvad-wheels`
2. **Exact package version:** `2.0.14`
3. **Python 3.13 compatibility:** Yes, pre-built wheels exist for Python 3.13 (`cp313-cp313`). It imports correctly without needing `pkg_resources`.
4. **ARMv7 / armhf (32-bit) compatibility:** Pre-built wheels for 32-bit ARM Linux are **NOT** available on PyPI. It must be built from the source distribution (`.tar.gz`).
5. **AArch64 (64-bit) compatibility:** Yes, pre-built wheels (`manylinux2014_aarch64`) are explicitly provided.
6. **Whether wheels exist:** Yes, for AArch64 and x86_64, but not for ARMv7.
7. **Source compilation required:** Required **only** if deploying a 32-bit OS (ARMv7/armhf).
8. **Required build dependencies:** `build-essential` (gcc/g++) and `python3-dev` (if deploying on ARMv7 to compile the C extensions).
9. **Installability via pip:** Yes, it installs perfectly via `pip install webrtcvad-wheels`.
10. **Import functionality:** Confirmed functional (`import webrtcvad`).

## Conclusion & Recommendation
For Debian 13 (Trixie), the recommended package is **`webrtcvad-wheels==2.0.14`**.

**Deployment Strategy:** Because the Raspberry Pi 3A+ supports 64-bit kernels (AArch64), it is highly recommended to install the 64-bit version of Debian Trixie to take advantage of the pre-built `webrtcvad-wheels`. If a 32-bit OS must be used, the `MASTER` Pi image preparation script will need to compile the C extension from source, which takes a few minutes but works.

The project dependency has been updated to `webrtcvad-wheels==2.0.14` and the Python version requirement has been verified for `>=3.11`, fully supporting Python 3.13.
