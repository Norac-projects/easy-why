from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QApplication, QDockWidget, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QTabWidget, QToolBar, QVBoxLayout,
                               QWidget)

from .. import APP_NAME
from ..actions import ActionError, CpuCap
from ..diagnosis import analyze
from ..elevation import LIMITED_FEATURES, is_elevated, relaunch_hint
from ..monitor import Monitor
from ..platform_info import pretty_name
from ..report import build_report
from .about import AboutTab
from .dashboard import DashboardTab
from .history import HistoryTab
from .memory_dialog import MemoryDialog
from .network_tab import NetworkTab
from .offenders import OffenderPanel
from .startup_tab import StartupTab
from .theme import DARK, LIGHT, SEVERITY
from .widgets import VerdictBanner


class _Bridge(QObject):
    snapshot = Signal(object)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1080, 700)
        self.setMinimumSize(640, 480)

        self.monitor = Monitor()
        self.cpu_cap = CpuCap()
        self._dark = True
        self._latest = None

        self._bridge = _Bridge()
        self._bridge.snapshot.connect(self._on_snapshot, Qt.QueuedConnection)
        self.monitor.subscribe(self._bridge.snapshot.emit)

        self._build_toolbar()
        self._build_central()
        self._build_dock()
        self._build_statusbar()
        self._apply_theme()

        self.monitor.start()

    # --- construction -----------------------------------------------------

    def _build_toolbar(self):
        bar = QToolBar("Actions")
        bar.setMovable(False)
        self.addToolBar(bar)

        refresh_action = QAction("Refresh now", self)
        refresh_action.setToolTip("Take a fresh sample immediately instead of waiting for the next tick.")
        refresh_action.triggered.connect(self._refresh_now)
        bar.addAction(refresh_action)
        bar.addSeparator()

        self.cap_action = QAction("Throttle-safe mode", self, checkable=True)
        self.cap_action.setToolTip("Cap the CPU clock at ~60% so an overheating machine "
                                   "runs steady instead of throttling erratically.")
        self.cap_action.triggered.connect(self._toggle_cap)
        bar.addAction(self.cap_action)

        mem_action = QAction("Ease memory", self)
        mem_action.triggered.connect(self._ease_memory)
        bar.addAction(mem_action)

        report_action = QAction("Generate report", self)
        report_action.triggered.connect(self._save_report)
        bar.addAction(report_action)

        self.theme_action = QAction("Light mode", self)
        self.theme_action.triggered.connect(self._toggle_theme)
        bar.addAction(self.theme_action)

    def _build_central(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.banner = VerdictBanner()
        layout.addWidget(self.banner)

        if not is_elevated():
            layout.addWidget(self._elevation_banner())

        self.tabs = QTabWidget()
        self.dashboard = DashboardTab()
        self.history = HistoryTab(self.monitor)
        self.network = NetworkTab()
        self.startup = StartupTab()
        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.history, "History")
        self.tabs.addTab(self.network, "Network")
        self.tabs.addTab(self.startup, "Startup items")
        self.tabs.addTab(AboutTab(), "About")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs, 1)

        self.setCentralWidget(central)

    def _elevation_banner(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("elevBanner")
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 8, 8)
        label = QLabel(
            "Running without elevation — limited: " + ", ".join(LIMITED_FEATURES) + ". "
            + relaunch_hint())
        label.setWordWrap(True)
        row.addWidget(label, 1)
        hide = QPushButton("Hide")
        hide.clicked.connect(frame.hide)
        row.addWidget(hide, 0, Qt.AlignTop)
        return frame

    def _build_dock(self):
        dock = QDockWidget("Top offenders", self)
        dock.setFeatures(QDockWidget.DockWidgetMovable)
        dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.offenders = OffenderPanel()
        dock.setWidget(self.offenders)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setMinimumWidth(340)

    def _build_statusbar(self):
        elevated = is_elevated()
        color = SEVERITY["ok"] if elevated else SEVERITY["warn"]
        text = "elevated" if elevated else "not elevated"
        self.elev_label = QLabel(f"● {pretty_name()} · {text}")
        self.elev_label.setStyleSheet(f"color: {color}; padding: 0 8px;")
        self.statusBar().addPermanentWidget(self.elev_label)
        self.statusBar().showMessage("Collecting first samples…")

    # --- runtime ----------------------------------------------------------

    def _on_snapshot(self, snap):
        self._latest = snap
        verdicts = analyze(self.monitor.history)
        self.banner.show_verdict(verdicts[0])
        self.dashboard.update_snapshot(snap)
        self.offenders.update_snapshot(snap)
        self.network.update_snapshot(snap)
        current = self.tabs.currentWidget()
        if current is self.history:
            self.history.refresh()
        elif current is self.network:
            self.network.refresh_connections()
        self.statusBar().showMessage(
            f"Sampling every {self.monitor.interval:.0f}s · "
            f"{len(self.monitor.history)} samples in history")

    def _refresh_now(self):
        self.monitor.refresh_now()
        self.statusBar().showMessage("Sampling now…")

    def _on_tab_changed(self, _index):
        if self.tabs.currentWidget() is self.network:
            self.network.refresh_connections()

    def _toggle_cap(self, checked):
        try:
            if checked:
                answer = QMessageBox.question(
                    self, "Throttle-safe mode",
                    "Cap the CPU at roughly 60% of its maximum clock?\n\n"
                    "Use this when the machine is overheating right now — it trades peak speed "
                    "for stable temperatures. Untick to restore full speed.")
                if answer != QMessageBox.Yes:
                    self.cap_action.setChecked(False)
                    return
                self.cpu_cap.enable()
                self.statusBar().showMessage("CPU capped at ~60% — untick Throttle-safe mode to restore.")
            else:
                self.cpu_cap.disable()
                self.statusBar().showMessage("CPU limits restored.")
        except ActionError as e:
            self.cap_action.setChecked(self.cpu_cap.active)
            QMessageBox.warning(self, "Couldn't change CPU limits", str(e))

    def _ease_memory(self):
        if self._latest is None:
            return
        MemoryDialog(self._latest, self).exec()

    def _save_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save diagnostic report",
                                              "easy-why-report.txt", "Text files (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(build_report(self.monitor.history))
            self.statusBar().showMessage(f"Report saved to {path}")
        except OSError as e:
            QMessageBox.warning(self, "Couldn't save report", str(e))

    def _toggle_theme(self):
        self._dark = not self._dark
        self.theme_action.setText("Light mode" if self._dark else "Dark mode")
        self._apply_theme()

    def _apply_theme(self):
        QApplication.instance().setStyleSheet(DARK if self._dark else LIGHT)

    def closeEvent(self, event):
        self.monitor.stop()
        if self.cpu_cap.active:
            try:
                self.cpu_cap.disable()
            except Exception:
                pass
        super().closeEvent(event)
