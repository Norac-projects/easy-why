from ..platform_info import detect


def get_backend():
    plat = detect()
    if plat == "windows":
        from .windows import WindowsBackend
        return WindowsBackend()
    if plat == "pi":
        from .pi import PiBackend
        return PiBackend()
    from .linux import LinuxBackend
    return LinuxBackend()
