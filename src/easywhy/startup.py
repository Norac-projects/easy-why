import os
from dataclasses import dataclass
from pathlib import Path

from .platform_info import detect


@dataclass(slots=True)
class StartupItem:
    name: str
    command: str
    enabled: bool
    ref: str  # file path (Linux) or registry value name (Windows)


def list_items() -> list[StartupItem]:
    if detect() == "windows":
        return _windows_list()
    return _linux_list()


def toggle(item: StartupItem):
    if detect() == "windows":
        _windows_toggle(item)
    else:
        _linux_toggle(item)


# --- Linux / Pi: XDG autostart -------------------------------------------

_AUTOSTART = Path.home() / ".config" / "autostart"


def _linux_list() -> list[StartupItem]:
    items = []
    if not _AUTOSTART.is_dir():
        return items
    for desktop in sorted(_AUTOSTART.glob("*.desktop")):
        name = desktop.stem
        command = ""
        hidden = False
        try:
            for line in desktop.read_text(errors="replace").splitlines():
                if line.startswith("Name="):
                    name = line[5:].strip()
                elif line.startswith("Exec="):
                    command = line[5:].strip()
                elif line.strip().lower() in ("hidden=true", "x-gnome-autostart-enabled=false"):
                    hidden = True
        except OSError:
            continue
        items.append(StartupItem(name, command, not hidden, str(desktop)))
    return items


def _linux_toggle(item: StartupItem):
    path = Path(item.ref)
    lines = [l for l in path.read_text(errors="replace").splitlines()
             if not l.strip().lower().startswith("hidden=")]
    if item.enabled:
        lines.append("Hidden=true")
    path.write_text("\n".join(lines) + "\n")


# --- Windows: HKCU Run key ------------------------------------------------

_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
_DISABLED = r"Software\EasyWhy\DisabledStartup"


def _windows_list() -> list[StartupItem]:
    import winreg
    items = []
    for key_path, enabled in ((_RUN, True), (_DISABLED, False)):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        items.append(StartupItem(name, str(value), enabled, name))
                        i += 1
                    except OSError:
                        break
        except OSError:
            continue
    return items


def _windows_toggle(item: StartupItem):
    import winreg
    src, dst = (_RUN, _DISABLED) if item.enabled else (_DISABLED, _RUN)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, dst) as dst_key:
        winreg.SetValueEx(dst_key, item.name, 0, winreg.REG_SZ, item.command)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, src, 0, winreg.KEY_SET_VALUE) as src_key:
        winreg.DeleteValue(src_key, item.name)
