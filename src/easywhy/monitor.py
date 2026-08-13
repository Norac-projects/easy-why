import threading
import time
from collections import deque
from dataclasses import dataclass, field

import psutil

from .sensors import get_backend

# Windows' "System Idle Process" (pid 0) reports idle time as CPU, and pid 4
# "System" is the kernel — neither is a real culprit and neither is killable.
IGNORED_PIDS = {0}
IGNORED_NAMES = {"system idle process", "system", "kernel_task"}


def _is_pseudo(pid: int, name: str) -> bool:
    return pid in IGNORED_PIDS or (name or "").lower() in IGNORED_NAMES


@dataclass(slots=True)
class ProcSample:
    pid: int
    name: str
    cpu: float          # percent of a single core, can exceed 100 on multicore
    memory: int         # rss bytes
    io_read: float      # bytes/s
    io_write: float     # bytes/s


@dataclass(slots=True)
class Snapshot:
    ts: float
    cpu_total: float
    per_core: list[float]
    iowait: float
    freq_current: float
    freq_max: float
    temps: dict[str, float]
    hottest: float
    fans: dict[str, int]
    mem_total: int
    mem_available: int
    mem_cached: int
    mem_percent: float
    swap_total: int
    swap_used: int
    swap_percent: float
    swap_io_rate: float      # bytes/s in+out
    disk_read_rate: float
    disk_write_rate: float
    net_recv_rate: float     # bytes/s down
    net_sent_rate: float     # bytes/s up
    battery: tuple | None    # (percent, plugged, secs_left)
    throttle: dict
    pi_flags: dict
    ncores: int
    top_procs: list[ProcSample] = field(default_factory=list)


class Monitor:
    """Samples the system every couple of seconds on a background thread and
    keeps a rolling window so you can scrub back and see what spiked."""

    def __init__(self, interval: float = 2.0, history_minutes: int = 30):
        self.interval = interval
        self.backend = get_backend()
        self.history: deque[Snapshot] = deque(maxlen=int(history_minutes * 60 / interval))
        self._listeners = []
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="easywhy-monitor")
        self._proc_io: dict[int, tuple] = {}
        self._last_disk = None
        self._last_swap = None
        self._last_net = None
        self._last_ts = None
        self._ncores = psutil.cpu_count(logical=True) or 1

    def subscribe(self, callback):
        self._listeners.append(callback)

    def start(self):
        psutil.cpu_percent(percpu=True)
        psutil.cpu_times_percent()
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._wake.set()

    def refresh_now(self):
        """Force an immediate sample from the background thread."""
        self._wake.set()

    def _run(self):
        while not self._stop.is_set():
            self._wake.wait(self.interval)
            self._wake.clear()
            if self._stop.is_set():
                break
            try:
                snap = self._sample()
            except Exception:
                continue
            self.history.append(snap)
            for callback in self._listeners:
                callback(snap)

    def _sample(self) -> Snapshot:
        now = time.time()
        dt = (now - self._last_ts) if self._last_ts else self.interval
        dt = max(dt, 0.05)
        self._last_ts = now

        per_core = psutil.cpu_percent(percpu=True)
        cpu_total = sum(per_core) / len(per_core) if per_core else 0.0
        iowait = getattr(psutil.cpu_times_percent(), "iowait", 0.0)

        freq = psutil.cpu_freq()
        freq_current = freq.current if freq else 0.0
        freq_max = freq.max if freq and freq.max else freq_current

        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        swap_now = swap.sin + swap.sout
        swap_io = 0.0
        if self._last_swap is not None:
            swap_io = max(0.0, swap_now - self._last_swap) / dt
        self._last_swap = swap_now

        disk_read = disk_write = 0.0
        disk = psutil.disk_io_counters()
        if disk:
            if self._last_disk:
                disk_read = max(0.0, disk.read_bytes - self._last_disk[0]) / dt
                disk_write = max(0.0, disk.write_bytes - self._last_disk[1]) / dt
            self._last_disk = (disk.read_bytes, disk.write_bytes)

        net_recv = net_sent = 0.0
        net = psutil.net_io_counters()
        if net:
            if self._last_net:
                net_recv = max(0.0, net.bytes_recv - self._last_net[0]) / dt
                net_sent = max(0.0, net.bytes_sent - self._last_net[1]) / dt
            self._last_net = (net.bytes_recv, net.bytes_sent)

        battery = None
        try:
            b = psutil.sensors_battery()
            if b:
                battery = (b.percent, b.power_plugged, b.secsleft)
        except Exception:
            pass

        temps = self.backend.temps()
        hottest = max(temps.values(), default=0.0)
        fans = self.backend.fans()
        throttle = self.backend.throttle_state(freq_current, freq_max, hottest, cpu_total)
        pi_flags = self.backend.extras().get("pi", {})

        return Snapshot(
            ts=now, cpu_total=cpu_total, per_core=per_core, iowait=iowait,
            freq_current=freq_current, freq_max=freq_max,
            temps=temps, hottest=hottest, fans=fans,
            mem_total=mem.total, mem_available=mem.available,
            mem_cached=getattr(mem, "cached", 0), mem_percent=mem.percent,
            swap_total=swap.total, swap_used=swap.used, swap_percent=swap.percent,
            swap_io_rate=swap_io,
            disk_read_rate=disk_read, disk_write_rate=disk_write,
            net_recv_rate=net_recv, net_sent_rate=net_sent,
            battery=battery, throttle=throttle, pi_flags=pi_flags,
            ncores=self._ncores,
            top_procs=self._sample_procs(now),
        )

    def _sample_procs(self, now: float) -> list[ProcSample]:
        out = []
        seen = set()
        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                pid = proc.info["pid"]
                name = proc.info["name"] or "?"
                if _is_pseudo(pid, name):
                    continue
                cpu = proc.cpu_percent(None)
                mem_info = proc.info["memory_info"]
                rss = mem_info.rss if mem_info else 0
                read_rate = write_rate = 0.0
                try:
                    io = proc.io_counters()
                    last = self._proc_io.get(pid)
                    if last:
                        span = now - last[2]
                        if span > 0:
                            read_rate = max(0.0, io.read_bytes - last[0]) / span
                            write_rate = max(0.0, io.write_bytes - last[1]) / span
                    self._proc_io[pid] = (io.read_bytes, io.write_bytes, now)
                except (psutil.AccessDenied, AttributeError, OSError):
                    pass
                seen.add(pid)
                out.append(ProcSample(pid, name, cpu, rss, read_rate, write_rate))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        self._proc_io = {pid: v for pid, v in self._proc_io.items() if pid in seen}
        out.sort(key=lambda p: (p.cpu, p.memory), reverse=True)
        return out[:15]
