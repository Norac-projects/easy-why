import os
import sys
from functools import cache


@cache
def is_elevated() -> bool:
    if os.name == "nt":
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.geteuid() == 0


def relaunch_hint() -> str:
    if os.name == "nt":
        return "Close the app and start it again with a right click > \"Run as administrator\"."
    script = os.path.abspath(sys.argv[0])
    return f"Relaunch it with:  sudo {sys.executable} {script}"


LIMITED_FEATURES = (
    "some temperature and fan sensors",
    "killing processes owned by other users",
    "CPU frequency capping (throttle-safe mode)",
    "clearing disk caches",
)
