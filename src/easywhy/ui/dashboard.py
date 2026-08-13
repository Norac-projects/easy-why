from PySide6.QtWidgets import (QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QScrollArea, QVBoxLayout, QWidget)

from .theme import SERIES
from .widgets import CoreBars, Gauge, Sparkline


def _mb(n): return n / (1024 * 1024)
def _gb(n): return n / (1024 ** 3)


class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        outer.addWidget(scroll)
        body = QWidget()
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setSpacing(10)

        gauges = QHBoxLayout()
        self.g_cpu = Gauge("CPU", "%", warn=65, bad=90)
        self.g_temp = Gauge("Hottest sensor", "°C", warn=70, bad=85, max_value=105)
        self.g_mem = Gauge("Memory", "%", warn=75, bad=92)
        self.g_swap = Gauge("Swap", "%", warn=40, bad=75)
        for g in (self.g_cpu, self.g_temp, self.g_mem, self.g_swap):
            gauges.addWidget(g)
        layout.addLayout(gauges)

        cores_box = QGroupBox("Per-core load")
        cores_layout = QVBoxLayout(cores_box)
        self.cores = CoreBars()
        cores_layout.addWidget(self.cores)
        layout.addWidget(cores_box)

        trends = QGroupBox("Last few minutes")
        grid = QGridLayout(trends)
        self.s_cpu = Sparkline(SERIES["cpu"])
        self.s_temp = Sparkline(SERIES["temp"], y_max=105)
        self.s_mem = Sparkline(SERIES["mem"])
        self.s_disk = Sparkline(SERIES["disk"], y_max=None)
        for col, (name, spark) in enumerate([("CPU %", self.s_cpu), ("Temp °C", self.s_temp),
                                             ("Memory %", self.s_mem), ("Disk MB/s", self.s_disk)]):
            grid.addWidget(QLabel(name), 0, col)
            grid.addWidget(spark, 1, col)
        layout.addWidget(trends)

        bottom = QHBoxLayout()
        self.sensors_box = QGroupBox("Sensors")
        self.sensors_label = QLabel("No sensor data yet.")
        self.sensors_label.setWordWrap(True)
        QVBoxLayout(self.sensors_box).addWidget(self.sensors_label)
        bottom.addWidget(self.sensors_box, 1)

        self.details_box = QGroupBox("Details")
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        QVBoxLayout(self.details_box).addWidget(self.details_label)
        bottom.addWidget(self.details_box, 1)
        layout.addLayout(bottom)
        layout.addStretch(1)

    def update_snapshot(self, snap):
        self.g_cpu.set_value(snap.cpu_total)
        self.g_temp.set_value(snap.hottest if snap.temps else None)
        self.g_mem.set_value(snap.mem_percent)
        self.g_swap.set_value(snap.swap_percent if snap.swap_total else None)
        self.cores.set_values(snap.per_core)

        self.s_cpu.add(snap.cpu_total)
        self.s_temp.add(snap.hottest)
        self.s_mem.add(snap.mem_percent)
        self.s_disk.add(_mb(snap.disk_read_rate + snap.disk_write_rate))

        sensor_lines = [f"{name}:  {value:.0f}°C" for name, value in sorted(snap.temps.items())]
        sensor_lines += [f"{name}:  {rpm} RPM" for name, rpm in sorted(snap.fans.items())]
        if snap.pi_flags:
            active = [k.replace("_", " ") for k, v in snap.pi_flags.items() if v]
            sensor_lines.append("Pi status:  " + (", ".join(active) if active else "healthy"))
        self.sensors_label.setText("\n".join(sensor_lines) if sensor_lines
                                   else "No temperature or fan sensors exposed on this system.")

        details = [
            f"Clock:  {snap.freq_current:.0f} / {snap.freq_max:.0f} MHz"
            + ("   ⚠ throttling (" + snap.throttle["reason"] + ")" if snap.throttle["active"] else ""),
            f"I/O wait:  {snap.iowait:.1f}%",
            f"Memory:  {_gb(snap.mem_available):.1f} GB available, {_gb(snap.mem_cached):.1f} GB cache",
            f"Swap I/O:  {_mb(snap.swap_io_rate):.1f} MB/s",
            f"Disk:  ↓ {_mb(snap.disk_read_rate):.1f}  ↑ {_mb(snap.disk_write_rate):.1f} MB/s",
            f"Network:  ↓ {_mb(snap.net_recv_rate):.2f}  ↑ {_mb(snap.net_sent_rate):.2f} MB/s",
        ]
        if snap.battery:
            pct, plugged, secs = snap.battery
            state = "on AC" if plugged else (f"~{secs // 60} min left" if secs and secs > 0 else "on battery")
            details.append(f"Battery:  {pct:.0f}% ({state})")
        self.details_label.setText("\n".join(details))
