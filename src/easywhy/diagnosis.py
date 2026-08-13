from dataclasses import dataclass

OK, WARN, BAD = "ok", "warn", "bad"
_ORDER = {BAD: 0, WARN: 1, OK: 2}

BROWSERS = {"chrome", "chromium", "chromium-browser", "msedge", "firefox",
            "firefox-esr", "brave", "opera", "vivaldi", "librewolf"}
INDEXERS = {"searchindexer", "msmpeng", "tracker-miner-fs", "tracker-miner-fs-3",
            "baloo_file", "baloo_file_extractor", "updatedb", "mlocate", "plocate",
            "tiworker", "compattelrunner"}
BACKUPS = {"rsync", "timeshift", "restic", "borg", "duplicati", "dropbox",
           "onedrive", "googledrivesync", "syncthing", "deja-dup"}


@dataclass(slots=True)
class Verdict:
    severity: str
    title: str
    detail: str
    fix: str
    pid: int | None = None


def _mb(n): return n / (1024 * 1024)
def _gb(n): return n / (1024 ** 3)


def _base_name(name: str) -> str:
    return name.lower().removesuffix(".exe")


def _proc_averages(snaps):
    from .monitor import _is_pseudo
    acc = {}
    for snap in snaps:
        for p in snap.top_procs:
            if _is_pseudo(p.pid, p.name):
                continue
            entry = acc.setdefault(p.pid, {"name": p.name, "cpu": [], "mem": 0, "io": 0.0})
            entry["cpu"].append(p.cpu)
            entry["mem"] = p.memory
            entry["io"] = p.io_read + p.io_write
    return {
        pid: {"name": e["name"], "cpu": sum(e["cpu"]) / len(e["cpu"]),
              "mem": e["mem"], "io": e["io"]}
        for pid, e in acc.items()
    }


def analyze(history) -> list[Verdict]:
    if not history:
        return [Verdict(OK, "Warming up", "Collecting the first samples...", "Give it a few seconds.")]

    snaps = list(history)
    recent = snaps[-8:]
    latest = snaps[-1]
    procs = _proc_averages(recent)
    verdicts = []

    def avg(attr):
        return sum(getattr(s, attr) for s in recent) / len(recent)

    # Raspberry Pi power problems come first, they explain everything else
    if latest.pi_flags.get("undervoltage_now"):
        verdicts.append(Verdict(BAD, "Your Pi is undervolted right now",
            "The board is reporting an active undervoltage condition, which forces it to slow down and can corrupt the SD card.",
            "This is a power supply problem, not a software one. Use the official PSU (5V/3A for Pi 4, 5V/5A for Pi 5) and a short, thick USB cable."))
    elif latest.pi_flags.get("undervoltage_past"):
        verdicts.append(Verdict(WARN, "Undervoltage happened since boot",
            "The Pi dipped below safe voltage at some point since it was powered on.",
            "Your power supply or cable is borderline. Swap the cable first, then the PSU if it happens again."))

    # Thermal throttling
    if latest.throttle["active"] and latest.throttle["reason"] == "thermal":
        top = recent_top(procs)
        who = f" {top['name']} is the main load ({top['cpu']:.0f}% CPU)." if top else ""
        verdicts.append(Verdict(BAD,
            f"CPU is thermally throttling at {latest.hottest:.0f}°C",
            f"The processor hit its temperature limit and cut its own clock speed "
            f"({latest.freq_current:.0f} of {latest.freq_max:.0f} MHz).{who}",
            "Reduce the load or turn on Throttle-safe mode in the toolbar to cap the clock cleanly instead of letting it bounce. "
            "If this keeps happening, clean the dust out and check airflow.",
            pid=top["pid"] if top else None))
    elif latest.throttle["active"] and latest.throttle["reason"] == "power":
        verdicts.append(Verdict(WARN, "CPU is power limited",
            f"The CPU is running at {latest.freq_current:.0f} MHz under load, below its {latest.freq_max:.0f} MHz maximum, without being too hot.",
            "Check the power plan (Windows), the charger on a laptop, or the power supply on a Pi."))

    # Runaway single process — only worth flagging when the machine is actually
    # busy. A process pinning one core on a 16-core box that's otherwise idle is
    # not why anything feels slow.
    ncores = latest.ncores or max(len(latest.per_core), 1)
    hog = max(procs.items(), key=lambda kv: kv[1]["cpu"], default=None)
    system_busy = avg("cpu_total") >= 40
    if hog and system_busy:
        pid, info = hog
        machine_share = info["cpu"] / ncores  # % of the whole CPU, not one core
        base = _base_name(info["name"])
        if machine_share >= 20 and base not in BROWSERS:
            if base in INDEXERS:
                verdicts.append(Verdict(WARN, f"{info['name']} is indexing/scanning hard",
                    f"A background indexer is using {machine_share:.0f}% of your total CPU. These normally calm down on their own.",
                    "If it has been going a long time, lower its priority from the offender panel so it stops fighting your apps, or pause the service.",
                    pid=pid))
            elif base in BACKUPS:
                verdicts.append(Verdict(WARN, f"{info['name']} looks like a backup/sync run",
                    f"{info['name']} is using {machine_share:.0f}% of your CPU and {_mb(info['io']):.0f} MB/s of disk.",
                    "Let it finish if you can. If it has been stuck for hours at the same point, kill it and restart it.",
                    pid=pid))
            else:
                verdicts.append(Verdict(BAD, f"{info['name']} is eating your CPU",
                    f"{info['name']} (pid {pid}) is using about {machine_share:.0f}% of your total CPU "
                    f"({info['cpu']:.0f}% of a single core) — that's the main load right now.",
                    "If you're not actively using it, kill it from the offender panel. If you need it, lower its priority so the rest of the system stays responsive.",
                    pid=pid))

    # Browser bloat, counted across all its helper processes
    browser_load = {}
    for pid, info in procs.items():
        base = _base_name(info["name"])
        if base in BROWSERS:
            entry = browser_load.setdefault(base, {"cpu": 0.0, "count": 0, "pid": pid})
            entry["cpu"] += info["cpu"]
            entry["count"] += 1
            if info["cpu"] > procs.get(entry["pid"], {"cpu": 0})["cpu"]:
                entry["pid"] = pid
    for base, agg in browser_load.items():
        if agg["cpu"] >= 120 or (agg["count"] >= 8 and agg["cpu"] >= 70):
            verdicts.append(Verdict(WARN if agg["cpu"] < 200 else BAD,
                f"{base.capitalize()} is using {agg['cpu']:.0f}% CPU across {agg['count']} processes",
                "That usually means too many open tabs, a heavy web app, or a runaway extension.",
                "Close tabs you're not using, or open the browser's own task manager (Shift+Esc in Chrome) to find the one tab or extension responsible.",
                pid=agg["pid"]))

    # Swap thrash — the classic "it's not the CPU, it's the disk" case
    avail_ratio = latest.mem_available / latest.mem_total if latest.mem_total else 1
    if latest.swap_percent > 50 and avail_ratio < 0.12 and avg("swap_io_rate") > 512 * 1024:
        verdicts.append(Verdict(BAD, "Your system is swapping hard",
            f"RAM is nearly full ({latest.mem_percent:.0f}%) and the OS is shuffling "
            f"{_mb(latest.swap_io_rate):.1f} MB/s to swap. This makes everything feel frozen even though the CPU is fine.",
            "Close the biggest memory users (Ease memory in the toolbar shows them ranked). More RAM is the real long-term fix."))
    elif avail_ratio < 0.08:
        verdicts.append(Verdict(WARN, "Memory is running out",
            f"Only {_gb(latest.mem_available):.1f} GB of {_gb(latest.mem_total):.1f} GB is still available.",
            "Close something big before it starts swapping — hit Ease memory in the toolbar to see what's worth closing."))

    # Disk bound
    if avg("iowait") > 20:
        top_io = max(procs.items(), key=lambda kv: kv[1]["io"], default=None)
        who = f" Biggest disk user: {top_io[1]['name']} at {_mb(top_io[1]['io']):.0f} MB/s." if top_io and top_io[1]["io"] > 1024 * 1024 else ""
        verdicts.append(Verdict(WARN, "The CPU is mostly waiting on the disk",
            f"{avg('iowait'):.0f}% of CPU time is spent waiting for I/O. The machine isn't compute-bound, the disk is the bottleneck.{who}",
            "Check if a backup, update or indexing job is running. On an SD card or old HDD this is normal under heavy writes — an SSD fixes it for good.",
            pid=top_io[0] if top_io else None))

    # Thermal paste degradation signature: hot while doing nothing, over a longer window
    if len(snaps) >= 30:
        window = snaps[-30:]
        hot_idle = [s for s in window if s.hottest >= 78 and s.cpu_total < 15]
        if len(hot_idle) > len(window) * 0.8:
            verdicts.append(Verdict(WARN, "Running hot while idle",
                f"The CPU sits around {sum(s.hottest for s in window)/len(window):.0f}°C at under 15% load. "
                "Healthy cooling shouldn't look like this.",
                "This is the classic signature of dried-out thermal paste, a dust-clogged heatsink, or a fan that isn't spinning up. "
                "Generate a report and take it to whoever does your hardware."))

    # Fan noise correlation
    if len(snaps) >= 10 and latest.fans:
        older = snaps[-10:-3]
        for label, rpm in latest.fans.items():
            past = [s.fans.get(label, 0) for s in older if s.fans.get(label)]
            if past and rpm > 1.3 * (sum(past) / len(past)) and rpm > 1500:
                top = recent_top(procs)
                cause = f"{top['name']} spiking to {top['cpu']:.0f}% CPU" if top else "a load spike"
                verdicts.append(Verdict(WARN, f"Fan \"{label}\" just spun up to {rpm} RPM",
                    f"The noise you're hearing lines up with {cause} pushing the temperature to {latest.hottest:.0f}°C.",
                    "Deal with that process and the fan will settle back down within a minute or two.",
                    pid=top["pid"] if top else None))
                break

    # Network — only flag sustained heavy download, and name the likely app.
    recv_avg = avg("net_recv_rate")
    sent_avg = avg("net_sent_rate")
    if recv_avg > 8 * 1024 * 1024:  # ~8 MB/s (~64 Mbit) sustained down
        culprit = _net_culprit(latest)
        who = f" {culprit} has the most open connections and is the likely source." if culprit else ""
        verdicts.append(Verdict(WARN, f"Something is pulling {_mb(recv_avg):.0f} MB/s down",
            f"Sustained heavy download traffic — a big update, a cloud sync, streaming, or a torrent.{who}",
            "Open the Network tab to see which app holds the most connections. Pause the download if you didn't start it on purpose.",
            pid=None))
    elif sent_avg > 4 * 1024 * 1024:  # heavy upload is more unusual
        culprit = _net_culprit(latest)
        who = f" {culprit} is the likely source." if culprit else ""
        verdicts.append(Verdict(WARN, f"Something is uploading {_mb(sent_avg):.0f} MB/s",
            f"Heavy sustained upload — usually a backup or cloud sync pushing files.{who}",
            "Check the Network tab. If you didn't kick off a backup, worth knowing what's sending this much.",
            pid=None))

    # Battery drain
    if latest.battery and not latest.battery[1] and 0 < latest.battery[2] < 45 * 60:
        verdicts.append(Verdict(WARN, "Battery is draining fast",
            f"About {latest.battery[2] // 60} minutes left at the current draw ({latest.battery[0]:.0f}% remaining).",
            "Heavy CPU load drains laptops fast — closing the top offender buys you real minutes."))

    if not verdicts:
        parts = [f"CPU {latest.cpu_total:.0f}%", f"RAM {latest.mem_percent:.0f}%"]
        if latest.hottest:
            parts.insert(1, f"{latest.hottest:.0f}°C")
        verdicts.append(Verdict(OK, "All clear", ", ".join(parts) + " — nothing looks wrong.",
                                "Nothing to fix right now."))

    verdicts.sort(key=lambda v: _ORDER[v.severity])
    return verdicts


def _net_culprit(snapshot) -> str | None:
    from .network import top_connection_holder
    return top_connection_holder()


def recent_top(procs: dict) -> dict | None:
    if not procs:
        return None
    pid, info = max(procs.items(), key=lambda kv: kv[1]["cpu"])
    if info["cpu"] < 25:
        return None
    return {"pid": pid, **info}
