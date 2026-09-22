import platform
import os

class PlatformInfo:
    @staticmethod
    def get_os() -> str:
        return platform.system()

    @staticmethod
    def get_architecture() -> str:
        return platform.machine()

    @staticmethod
    def is_root() -> bool:
        return os.geteuid() == 0 if hasattr(os, 'geteuid') else False
