import platform
from functools import cache


@cache
def detect() -> str:
    """Returns 'windows', 'pi' or 'linux'."""
    system = platform.system()
    if system == "Windows":
        return "windows"
    if system == "Linux" and _is_raspberry_pi():
        return "pi"
    return "linux"


def _is_raspberry_pi() -> bool:
    try:
        with open("/proc/device-tree/model", "rb") as f:
            return b"raspberry pi" in f.read().lower()
    except OSError:
        pass
    try:
        with open("/proc/cpuinfo") as f:
            return "raspberry pi" in f.read().lower()
    except OSError:
        return False


@cache
def pretty_name() -> str:
    return {"windows": "Windows", "pi": "Raspberry Pi", "linux": "Linux"}[detect()]
