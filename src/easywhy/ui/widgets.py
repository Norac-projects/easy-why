from collections import deque

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .theme import SEVERITY


class Sparkline(QWidget):
    def __init__(self, color: str, maxlen: int = 120, y_max: float | None = 100.0):
        super().__init__()
        self.color = QColor(color)
        self.values: deque[float] = deque(maxlen=maxlen)
        self.y_max = y_max
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def add(self, value: float):
        self.values.append(value)
        self.update()

    def paintEvent(self, _):
        if len(self.values) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        top = self.y_max or max(max(self.values), 1.0)
        top = max(top, 1.0)
        step = w / (self.values.maxlen - 1)
        path = QPainterPath()
        points = []
        for i, v in enumerate(self.values):
            x = w - (len(self.values) - 1 - i) * step
            y = h - min(v / top, 1.0) * (h - 4) - 2
            points.append((x, y))
        path.moveTo(*points[0])
        for x, y in points[1:]:
            path.lineTo(x, y)
        fill = QPainterPath(path)
        fill.lineTo(points[-1][0], h)
        fill.lineTo(points[0][0], h)
        fill.closeSubpath()
        area = QColor(self.color)
        area.setAlpha(45)
        p.fillPath(fill, area)
        p.setPen(QPen(self.color, 1.6))
        p.drawPath(path)


class Gauge(QWidget):
    """240° arc gauge with big value in the middle, colored by thresholds."""

    def __init__(self, label: str, unit: str, warn: float, bad: float, max_value: float = 100.0):
        super().__init__()
        self.label = label
        self.unit = unit
        self.warn, self.bad = warn, bad
        self.max_value = max_value
        self.value: float | None = None
        self.setMinimumSize(130, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_value(self, value: float | None, max_value: float | None = None):
        self.value = value
        if max_value:
            self.max_value = max_value
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height() - 14)
        rect = QRectF((self.width() - side) / 2 + 8, 4, side - 16, side - 16)
        start, span = 210 * 16, -240 * 16

        p.setPen(QPen(QColor(120, 130, 140, 60), 9, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, start, span)

        if self.value is not None and self.max_value:
            frac = min(self.value / self.max_value, 1.0)
            if self.value >= self.bad:
                color = QColor(SEVERITY["bad"])
            elif self.value >= self.warn:
                color = QColor(SEVERITY["warn"])
            else:
                color = QColor(SEVERITY["ok"])
            p.setPen(QPen(color, 9, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, start, int(span * frac))
            text = f"{self.value:.0f}{self.unit}"
        else:
            text = "—"

        f = QFont(self.font())
        f.setPointSize(15)
        f.setBold(True)
        p.setFont(f)
        p.setPen(self.palette().text().color())
        p.drawText(rect, Qt.AlignCenter, text)

        f.setPointSize(9)
        f.setBold(False)
        p.setFont(f)
        p.setPen(QColor(140, 150, 160))
        p.drawText(QRectF(0, rect.bottom() - 2, self.width(), 18), Qt.AlignCenter, self.label)


class CoreBars(QWidget):
    def __init__(self):
        super().__init__()
        self.values: list[float] = []
        self.setMinimumHeight(56)

    def set_values(self, values: list[float]):
        self.values = values
        self.update()

    def paintEvent(self, _):
        if not self.values:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        n = len(self.values)
        gap = 3
        bar_w = max(4.0, (self.width() - gap * (n - 1)) / n)
        h = self.height()
        for i, v in enumerate(self.values):
            x = i * (bar_w + gap)
            frac = min(v / 100.0, 1.0)
            color = SEVERITY["bad"] if v >= 90 else SEVERITY["warn"] if v >= 65 else SEVERITY["ok"]
            p.fillRect(QRectF(x, h - 3, bar_w, 2), QColor(120, 130, 140, 70))
            p.fillRect(QRectF(x, h - frac * (h - 4) - 3, bar_w, frac * (h - 4)), QColor(color))


class VerdictBanner(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("banner")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 12, 0)
        self._bar = QFrame()
        self._bar.setFixedWidth(6)
        row.addWidget(self._bar)
        col = QVBoxLayout()
        col.setContentsMargins(12, 10, 0, 10)
        col.setSpacing(2)
        self._title = QLabel("Warming up…")
        self._title.setObjectName("verdictTitle")
        self._detail = QLabel("")
        self._detail.setObjectName("verdictDetail")
        self._detail.setWordWrap(True)
        self._fix = QLabel("")
        self._fix.setObjectName("verdictFix")
        self._fix.setWordWrap(True)
        for w in (self._title, self._detail, self._fix):
            col.addWidget(w)
        row.addLayout(col, 1)

    def show_verdict(self, verdict):
        self._bar.setStyleSheet(f"background: {SEVERITY[verdict.severity]}; border-radius: 3px;")
        self._title.setText(verdict.title)
        self._detail.setText(verdict.detail)
        self._fix.setText("Fix: " + verdict.fix if verdict.fix else "")
