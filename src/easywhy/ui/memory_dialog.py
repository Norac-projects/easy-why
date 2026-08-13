from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QHeaderView, QLabel,
                               QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from ..actions import ActionError, clear_caches, kill_process
from ..platform_info import detect


def _mb(n): return n / (1024 * 1024)


class MemoryDialog(QDialog):
    """Shows what's actually worth closing, ranked by footprint."""

    def __init__(self, snapshot, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ease memory pressure")
        self.resize(520, 380)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(
            f"{snapshot.mem_percent:.0f}% of RAM in use, "
            f"{_mb(snapshot.mem_available):.0f} MB still available. "
            "These are the biggest memory users right now:"))

        procs = sorted(snapshot.top_procs, key=lambda p: p.memory, reverse=True)[:8]
        self.table = QTableWidget(len(procs), 3)
        self.table.setHorizontalHeaderLabels(("Process", "PID", "Memory MB"))
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for row, p in enumerate(procs):
            for col, text in enumerate((p.name, str(p.pid), f"{_mb(p.memory):.0f}")):
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, p.pid)
                self.table.setItem(row, col, item)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        close_proc = QPushButton("Close selected app")
        close_proc.clicked.connect(self._close_selected)
        buttons.addWidget(close_proc)
        if detect() != "windows":
            drop = QPushButton("Clear disk caches (root)")
            drop.clicked.connect(self._drop_caches)
            buttons.addWidget(drop)
        buttons.addStretch(1)
        done = QPushButton("Done")
        done.clicked.connect(self.accept)
        buttons.addWidget(done)
        layout.addLayout(buttons)

    def _close_selected(self):
        items = self.table.selectedItems()
        if not items:
            return
        pid = items[0].data(Qt.UserRole)
        name = self.table.item(self.table.currentRow(), 0).text()
        answer = QMessageBox.question(self, "Close app",
                                      f"Close {name} (pid {pid})? Unsaved work will be lost.")
        if answer != QMessageBox.Yes:
            return
        try:
            kill_process(pid)
            self.table.removeRow(self.table.currentRow())
        except ActionError as e:
            QMessageBox.warning(self, "Couldn't close it", str(e))

    def _drop_caches(self):
        answer = QMessageBox.question(
            self, "Clear caches",
            "Flush the kernel's file cache to disk and drop it?\n\n"
            "Safe, but things will read from disk slightly slower for a minute while the cache rebuilds.")
        if answer != QMessageBox.Yes:
            return
        try:
            clear_caches()
            QMessageBox.information(self, "Done", "Caches cleared.")
        except ActionError as e:
            QMessageBox.warning(self, "Couldn't clear caches", str(e))
