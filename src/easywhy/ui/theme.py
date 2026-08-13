SEVERITY = {"ok": "#2ecc71", "warn": "#f1c40f", "bad": "#e74c3c"}

SERIES = {
    "cpu": "#4fc3f7",
    "temp": "#ff8a65",
    "mem": "#81c784",
    "disk": "#ba68c8",
}


def severity_for(value: float, warn: float, bad: float) -> str:
    if value >= bad:
        return "bad"
    if value >= warn:
        return "warn"
    return "ok"


DARK = """
QWidget { background: #14171c; color: #d7dce2; font-size: 13px; }
QMainWindow, QDialog { background: #14171c; }
QTabWidget::pane { border: 1px solid #262b33; border-radius: 6px; }
QTabBar::tab { background: #1b1f26; padding: 7px 16px; border-top-left-radius: 6px;
               border-top-right-radius: 6px; margin-right: 2px; color: #9aa3ad; }
QTabBar::tab:selected { background: #262b33; color: #e8edf2; }
QGroupBox { border: 1px solid #262b33; border-radius: 8px; margin-top: 14px;
            padding-top: 10px; font-weight: 600; color: #9aa3ad; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QPushButton { background: #262b33; border: 1px solid #333a44; border-radius: 6px;
              padding: 6px 14px; color: #e8edf2; }
QPushButton:hover { background: #2f3540; }
QPushButton:pressed { background: #1b1f26; }
QPushButton:disabled { color: #5c6570; }
QToolBar { background: #1b1f26; border: none; spacing: 6px; padding: 4px; }
QToolButton { background: transparent; border-radius: 6px; padding: 6px 10px; color: #d7dce2; }
QToolButton:hover { background: #262b33; }
QToolButton:checked { background: #34506b; }
QTableWidget { background: #171a20; gridline-color: #262b33; border: none;
               selection-background-color: #34506b; }
QHeaderView::section { background: #1b1f26; border: none; padding: 6px; color: #9aa3ad; }
QStatusBar { background: #1b1f26; color: #9aa3ad; }
QScrollBar:vertical { background: #171a20; width: 10px; }
QScrollBar::handle:vertical { background: #333a44; border-radius: 5px; min-height: 24px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QLabel#verdictTitle { font-size: 17px; font-weight: 700; color: #f2f5f8; }
QLabel#verdictDetail { color: #b8c0c9; }
QLabel#verdictFix { color: #8fd3a8; }
QFrame#banner { border-radius: 8px; background: #1b1f26; }
QFrame#elevBanner { background: #3d3320; border: 1px solid #6b5a2a; border-radius: 8px; }
"""

LIGHT = """
QWidget { background: #f4f6f8; color: #23282e; font-size: 13px; }
QMainWindow, QDialog { background: #f4f6f8; }
QTabWidget::pane { border: 1px solid #d5dae0; border-radius: 6px; }
QTabBar::tab { background: #e6eaee; padding: 7px 16px; border-top-left-radius: 6px;
               border-top-right-radius: 6px; margin-right: 2px; color: #5c6570; }
QTabBar::tab:selected { background: #ffffff; color: #23282e; }
QGroupBox { border: 1px solid #d5dae0; border-radius: 8px; margin-top: 14px;
            padding-top: 10px; font-weight: 600; color: #5c6570; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QPushButton { background: #ffffff; border: 1px solid #c9cfd6; border-radius: 6px;
              padding: 6px 14px; }
QPushButton:hover { background: #eef1f4; }
QToolBar { background: #e6eaee; border: none; spacing: 6px; padding: 4px; }
QToolButton { background: transparent; border-radius: 6px; padding: 6px 10px; }
QToolButton:hover { background: #d5dae0; }
QToolButton:checked { background: #bcd4ea; }
QTableWidget { background: #ffffff; gridline-color: #e0e4e8; border: none;
               selection-background-color: #bcd4ea; }
QHeaderView::section { background: #e6eaee; border: none; padding: 6px; color: #5c6570; }
QStatusBar { background: #e6eaee; color: #5c6570; }
QLabel#verdictTitle { font-size: 17px; font-weight: 700; }
QLabel#verdictDetail { color: #4a525b; }
QLabel#verdictFix { color: #1e7a43; }
QFrame#banner { border-radius: 8px; background: #ffffff; border: 1px solid #d5dae0; }
QFrame#elevBanner { background: #fdf3d7; border: 1px solid #e0c66a; border-radius: 8px; }
"""
