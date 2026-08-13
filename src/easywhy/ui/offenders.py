from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ..actions import ActionError, kill_process, renice_process
from .theme import SEVERITY


def _mb(n): return n / (1024 * 1024)


class OffenderPanel(QWidget):
    """Top processes ranked so the culprit is obvious. Stays visible in the dock
    no matter which tab is open."""

    COLS = ("Process", "PID", "CPU %", "Mem MB", "Disk MB/s")

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(self.COLS)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        buttons = QHBoxLayout()
        self.kill_btn = QPushButton("Kill")
        self.renice_btn = QPushButton("Lower priority")
        buttons.addWidget(self.kill_btn)
        buttons.addWidget(self.renice_btn)
        layout.addLayout(buttons)

        self.kill_btn.clicked.connect(self._kill_selected)
        self.renice_btn.clicked.connect(self._renice_selected)

    def update_snapshot(self, snap):
        selected = self._selected_pid()
        procs = snap.top_procs[:10]
        self.table.setRowCount(len(procs))
        for row, p in enumerate(procs):
            cells = (p.name, str(p.pid), f"{p.cpu:.0f}", f"{_mb(p.memory):.0f}",
                     f"{_mb(p.io_read + p.io_write):.1f}")
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col == 2 and p.cpu >= 90:
                    item.setForeground(QColor(SEVERITY["bad"]))
                elif col == 2 and p.cpu >= 50:
                    item.setForeground(QColor(SEVERITY["warn"]))
                item.setData(Qt.UserRole, p.pid)
                self.table.setItem(row, col, item)
            if p.pid == selected:
                self.table.selectRow(row)

    def _selected_pid(self) -> int | None:
        items = self.table.selectedItems()
        return items[0].data(Qt.UserRole) if items else None

    def _selected(self):
        pid = self._selected_pid()
        if pid is None:
            QMessageBox.information(self, "Easy Why", "Select a process in the list first.")
            return None, None
        return pid, self.table.item(self.table.currentRow(), 0).text()

    def _kill_selected(self):
        pid, name = self._selected()
        if pid is None:
            return
        answer = QMessageBox.question(
            self, "Kill process",
            f"Kill {name} (pid {pid})?\n\nUnsaved work in that app will be lost.")
        if answer != QMessageBox.Yes:
            return
        try:
            kill_process(pid)
        except ActionError as e:
            QMessageBox.warning(self, "Couldn't kill it", str(e))

    def _renice_selected(self):
        pid, name = self._selected()
        if pid is None:
            return
        answer = QMessageBox.question(
            self, "Lower priority",
            f"Drop {name} (pid {pid}) to low priority?\n\n"
            "It keeps running but stops competing with your foreground apps. Harmless and reversible by restarting the app.")
        if answer != QMessageBox.Yes:
            return
        try:
            renice_process(pid)
        except ActionError as e:
            QMessageBox.warning(self, "Couldn't change priority", str(e))
