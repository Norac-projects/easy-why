from PySide6.QtWidgets import (QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .. import network
from .theme import SERIES
from .widgets import Sparkline


def _rate(bps: float) -> str:
    if bps >= 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.0f} KB/s"
    return f"{bps:.0f} B/s"


class NetworkTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        rates = QHBoxLayout()
        self.down_label = QLabel("↓ —")
        self.up_label = QLabel("↑ —")
        for lbl in (self.down_label, self.up_label):
            lbl.setStyleSheet("font-size: 20px; font-weight: 700;")
        rates.addWidget(self.down_label)
        rates.addSpacing(24)
        rates.addWidget(self.up_label)
        rates.addStretch(1)
        layout.addLayout(rates)

        trend = QGroupBox("Throughput, last few minutes")
        grid = QHBoxLayout(trend)
        down_col = QVBoxLayout()
        down_col.addWidget(QLabel("Download"))
        self.s_down = Sparkline(SERIES["cpu"], y_max=None)
        down_col.addWidget(self.s_down)
        up_col = QVBoxLayout()
        up_col.addWidget(QLabel("Upload"))
        self.s_up = Sparkline(SERIES["disk"], y_max=None)
        up_col.addWidget(self.s_up)
        grid.addLayout(down_col)
        grid.addLayout(up_col)
        layout.addWidget(trend)

        conns = QGroupBox("Who's connected right now")
        conns_layout = QVBoxLayout(conns)
        note = QLabel("Ranked by active external connections — the app with the most open "
                      "sockets is the likeliest source of traffic. Run elevated for the full picture.")
        note.setWordWrap(True)
        conns_layout.addWidget(note)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(("Process", "Connections", "Talking to"))
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        conns_layout.addWidget(self.table)
        layout.addWidget(conns, 1)

    def update_snapshot(self, snap):
        self.down_label.setText("↓ " + _rate(snap.net_recv_rate))
        self.up_label.setText("↑ " + _rate(snap.net_sent_rate))
        self.s_down.add(snap.net_recv_rate / 1024)
        self.s_up.add(snap.net_sent_rate / 1024)

    def refresh_connections(self):
        procs = network.per_process()[:12]
        self.table.setRowCount(len(procs))
        for row, p in enumerate(procs):
            remotes = ", ".join(p.remotes) + ("…" if len(p.remotes) >= 6 else "")
            for col, text in enumerate((p.name, str(p.connections), remotes)):
                self.table.setItem(row, col, QTableWidgetItem(text))
        if not procs:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("No external connections (or need elevation to read them)."))
