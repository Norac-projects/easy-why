import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .theme import SERIES


def _mb(n): return n / (1024 * 1024)


class TimelineChart(QWidget):
    """CPU, temperature, memory and disk overlaid on one timeline. Hover to
    scrub back and see exactly what spiked and when."""

    hovered = Signal(object)  # Snapshot | None

    def __init__(self):
        super().__init__()
        self.snaps = []
        self._hover_idx = None
        self.setMouseTracking(True)
        self.setMinimumHeight(240)

    def set_history(self, snaps):
        self.snaps = snaps
        self.update()

    def mouseMoveEvent(self, event):
        if not self.snaps:
            return
        frac = min(max(event.position().x() / max(self.width(), 1), 0.0), 1.0)
        idx = int(frac * (len(self.snaps) - 1))
        if idx != self._hover_idx:
            self._hover_idx = idx
            self.hovered.emit(self.snaps[idx])
            self.update()

    def leaveEvent(self, _):
        self._hover_idx = None
        self.hovered.emit(None)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        pad_bottom = 18

        p.setPen(QPen(QColor(120, 130, 140, 40), 1))
        for frac in (0.25, 0.5, 0.75):
            y = (h - pad_bottom) * frac
            p.drawLine(0, int(y), w, int(y))

        if len(self.snaps) < 2:
            p.setPen(QColor(140, 150, 160))
            p.drawText(self.rect(), Qt.AlignCenter, "History builds up while the app runs…")
            return

        disk_peak = max((s.disk_read_rate + s.disk_write_rate for s in self.snaps), default=1) or 1
        series = [
            (SERIES["cpu"], lambda s: s.cpu_total / 100),
            (SERIES["temp"], lambda s: s.hottest / 105),
            (SERIES["mem"], lambda s: s.mem_percent / 100),
            (SERIES["disk"], lambda s: (s.disk_read_rate + s.disk_write_rate) / disk_peak),
        ]
        n = len(self.snaps)
        for color, getter in series:
            path = QPainterPath()
            for i, snap in enumerate(self.snaps):
                x = i / (n - 1) * w
                y = (h - pad_bottom) * (1 - min(getter(snap), 1.0))
                path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
            p.setPen(QPen(QColor(color), 1.6))
            p.drawPath(path)

        p.setPen(QColor(140, 150, 160))
        p.drawText(4, h - 4, time.strftime("%H:%M", time.localtime(self.snaps[0].ts)))
        p.drawText(w - 44, h - 4, time.strftime("%H:%M", time.localtime(self.snaps[-1].ts)))

        if self._hover_idx is not None:
            x = self._hover_idx / (n - 1) * w
            p.setPen(QPen(QColor(230, 235, 240, 160), 1, Qt.DashLine))
            p.drawLine(int(x), 0, int(x), h - pad_bottom)


class HistoryTab(QWidget):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        layout = QVBoxLayout(self)

        legend = QHBoxLayout()
        for name, key in (("CPU %", "cpu"), ("Temp", "temp"), ("Memory %", "mem"), ("Disk", "disk")):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {SERIES[key]}; font-size: 15px;")
            legend.addWidget(dot)
            legend.addWidget(QLabel(name))
            legend.addSpacing(12)
        legend.addStretch(1)
        layout.addLayout(legend)

        self.chart = TimelineChart()
        self.chart.hovered.connect(self._show_point)
        layout.addWidget(self.chart, 1)

        self.info = QLabel("Hover over the chart to scrub back in time.")
        self.info.setWordWrap(True)
        layout.addWidget(self.info)

    def refresh(self):
        self.chart.set_history(list(self.monitor.history))

    def _show_point(self, snap):
        if snap is None:
            self.info.setText("Hover over the chart to scrub back in time.")
            return
        when = time.strftime("%H:%M:%S", time.localtime(snap.ts))
        top = ",  ".join(f"{p.name} {p.cpu:.0f}%" for p in snap.top_procs[:3])
        throttle = f"   ⚠ throttling ({snap.throttle['reason']})" if snap.throttle["active"] else ""
        self.info.setText(
            f"{when}  —  CPU {snap.cpu_total:.0f}%,  {snap.hottest:.0f}°C,  "
            f"RAM {snap.mem_percent:.0f}%,  disk {_mb(snap.disk_read_rate + snap.disk_write_rate):.1f} MB/s{throttle}\n"
            f"Top at that moment:  {top or '—'}")
