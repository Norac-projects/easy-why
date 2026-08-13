import sys

from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .ui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Norac Projects")
    window = MainWindow()
    window.show()
    return app.exec()
