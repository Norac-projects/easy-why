import glob
import os
import subprocess

import psutil

from .platform_info import detect


class ActionError(RuntimeError):
    pass


def kill_process(pid: int):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        try:
            proc.wait(3)
        except psutil.TimeoutExpired:
            proc.kill()
    except psutil.NoSuchProcess:
        pass
    except psutil.AccessDenied:
        raise ActionError("Access denied — that process belongs to another user. Relaunch elevated to kill it.")


def renice_process(pid: int):
    """Drop the process to low priority so it stops fighting the foreground."""
    try:
        proc = psutil.Process(pid)
        if os.name == "nt":
            proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            proc.nice(10)
    except psutil.NoSuchProcess:
        pass
    except psutil.AccessDenied:
        raise ActionError("Access denied — lowering priority for this process needs elevation.")


def clear_caches():
    if detect() == "windows":
        raise ActionError("Cache clearing works on Linux and Raspberry Pi only. "
                          "Windows manages its file cache automatically.")
    if os.geteuid() != 0:
        raise ActionError("Clearing caches needs root. Relaunch with sudo.")
    subprocess.run(["sync"], check=True)
    with open("/proc/sys/vm/drop_caches", "w") as f:
        f.write("3\n")


class CpuCap:
    """Throttle-safe mode: cap the CPU clock so an overheating machine
    stabilizes at a lower speed instead of throttling erratically.
    Fully reversible — disable restores exactly what was there before."""

    def __init__(self):
        self.active = False
        self._saved: dict[str, str] = {}

    def enable(self, percent: int = 60):
        plat = detect()
        if plat == "windows":
            self._windows_set(percent)
        else:
            self._linux_set(percent)
        self.active = True

    def disable(self):
        plat = detect()
        if plat == "windows":
            self._windows_set(100)
        else:
            self._linux_restore()
        self.active = False

    def _linux_set(self, percent: int):
        if os.geteuid() != 0:
            raise ActionError("Capping the CPU frequency needs root. Relaunch with sudo.")
        paths = glob.glob("/sys/devices/system/cpu/cpu*/cpufreq")
        if not paths:
            raise ActionError("This kernel doesn't expose cpufreq controls.")
        for path in paths:
            try:
                with open(os.path.join(path, "cpuinfo_max_freq")) as f:
                    hw_max = int(f.read().strip())
                target = os.path.join(path, "scaling_max_freq")
                if target not in self._saved:
                    with open(target) as f:
                        self._saved[target] = f.read().strip()
                with open(target, "w") as f:
                    f.write(str(hw_max * percent // 100))
            except OSError as e:
                raise ActionError(f"Couldn't write cpufreq limits: {e}")

    def _linux_restore(self):
        for target, value in self._saved.items():
            try:
                with open(target, "w") as f:
                    f.write(value)
            except OSError:
                pass
        self._saved.clear()

    def _windows_set(self, percent: int):
        cmds = [
            ["powercfg", "/setacvalueindex", "scheme_current", "sub_processor",
             "PROCTHROTTLEMAX", str(percent)],
            ["powercfg", "/setdcvalueindex", "scheme_current", "sub_processor",
             "PROCTHROTTLEMAX", str(percent)],
            ["powercfg", "/setactive", "scheme_current"],
        ]
        for cmd in cmds:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise ActionError("powercfg refused the change — run the app as Administrator.")
