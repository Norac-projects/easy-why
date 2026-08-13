from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from .. import startup


class StartupTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        hint = QLabel("Programs that launch at login and keep adding background load. "
                      "Disabling is reversible — toggle it back any time.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(("Name", "Command", "Status"))
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        self.toggle_btn = QPushButton("Enable / disable selected")
        self.refresh_btn = QPushButton("Refresh")
        buttons.addWidget(self.toggle_btn)
        buttons.addWidget(self.refresh_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.toggle_btn.clicked.connect(self._toggle)
        self.refresh_btn.clicked.connect(self.reload)
        self._items = []

    def showEvent(self, event):
        super().showEvent(event)
        self.reload()

    def reload(self):
        self._items = startup.list_items()
        self.table.setRowCount(len(self._items))
        for row, item in enumerate(self._items):
            for col, text in enumerate((item.name, item.command,
                                        "enabled" if item.enabled else "disabled")):
                cell = QTableWidgetItem(text)
                cell.setData(Qt.UserRole, row)
                self.table.setItem(row, col, cell)
        if not self._items:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("No user startup items found."))

    def _toggle(self):
        selected = self.table.selectedItems()
        if not selected or not self._items:
            return
        item = self._items[selected[0].data(Qt.UserRole)]
        verb = "Disable" if item.enabled else "Enable"
        answer = QMessageBox.question(self, f"{verb} startup item",
                                      f"{verb} \"{item.name}\" at login?")
        if answer != QMessageBox.Yes:
            return
        try:
            startup.toggle(item)
        except OSError as e:
            QMessageBox.warning(self, "Couldn't change it", str(e))
        self.reload()
