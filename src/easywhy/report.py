import time

from . import APP_NAME, __version__
from .diagnosis import analyze
from .elevation import is_elevated
from .platform_info import pretty_name


def _mb(n): return n / (1024 * 1024)
def _gb(n): return n / (1024 ** 3)


def build_report(history) -> str:
    snaps = list(history)
    lines = [
        f"{APP_NAME} diagnostic report",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Platform: {pretty_name()}   Elevated: {'yes' if is_elevated() else 'no'}   "
        f"App version: {__version__}",
        "",
    ]
    if not snaps:
        lines.append("No samples collected yet.")
        return "\n".join(lines)

    latest = snaps[-1]
    lines += ["=== Verdicts ==="]
    for v in analyze(history):
        lines += [f"[{v.severity.upper()}] {v.title}", f"  {v.detail}", f"  Fix: {v.fix}", ""]

    lines += [
        "=== Current state ===",
        f"CPU: {latest.cpu_total:.1f}% total, {latest.freq_current:.0f}/{latest.freq_max:.0f} MHz, "
        f"iowait {latest.iowait:.1f}%",
        f"Memory: {latest.mem_percent:.0f}% used, {_gb(latest.mem_available):.1f} GB available "
        f"of {_gb(latest.mem_total):.1f} GB, cache {_gb(latest.mem_cached):.1f} GB",
        f"Swap: {latest.swap_percent:.0f}% used ({_gb(latest.swap_used):.1f} GB)",
        f"Disk: read {_mb(latest.disk_read_rate):.1f} MB/s, write {_mb(latest.disk_write_rate):.1f} MB/s",
        f"Network: down {_mb(latest.net_recv_rate):.2f} MB/s, up {_mb(latest.net_sent_rate):.2f} MB/s",
    ]
    if latest.temps:
        lines.append("Temperatures: " + ", ".join(f"{k} {v:.0f}°C" for k, v in latest.temps.items()))
    if latest.fans:
        lines.append("Fans: " + ", ".join(f"{k} {v} RPM" for k, v in latest.fans.items()))
    if latest.battery:
        pct, plugged, secs = latest.battery
        state = "charging" if plugged else f"discharging, ~{secs // 60} min left" if secs and secs > 0 else "discharging"
        lines.append(f"Battery: {pct:.0f}% ({state})")
    if latest.pi_flags:
        active = [k for k, v in latest.pi_flags.items() if v]
        lines.append("Pi flags: " + (", ".join(active) if active else "none"))

    lines += ["", "=== Top processes right now ==="]
    for p in latest.top_procs[:10]:
        lines.append(f"  {p.name:<28} pid {p.pid:<7} cpu {p.cpu:6.1f}%  "
                     f"mem {_mb(p.memory):8.0f} MB  disk {_mb(p.io_read + p.io_write):6.1f} MB/s")

    span = max(1, len(snaps))
    lines += [
        "",
        f"=== Last {span * 2 // 60} minutes ===",
        f"CPU avg {sum(s.cpu_total for s in snaps) / span:.0f}%, "
        f"peak {max(s.cpu_total for s in snaps):.0f}%",
        f"Temp avg {sum(s.hottest for s in snaps) / span:.0f}°C, "
        f"peak {max(s.hottest for s in snaps):.0f}°C",
        f"Throttling seen: {'yes' if any(s.throttle['active'] for s in snaps) else 'no'}",
    ]
    return "\n".join(lines)
