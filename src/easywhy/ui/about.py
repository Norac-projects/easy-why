from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .. import APP_NAME, __version__
from ..platform_info import pretty_name


class AboutTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        text = QLabel(f"""
<h2>{APP_NAME} <span style="font-size:12px; color:#888;">v{__version__}</span></h2>
<p><b>A Norac Projects tool.</b></p>
<p>Every system monitor can show you a wall of numbers. {APP_NAME} exists because
none of them answer the actual question: <i>why is my computer hot, slow or loud
right now?</i> This app watches your machine in the background, figures out the
root cause, tells you in plain English, and hands you the fix.</p>
<p>It knows the usual suspects — browser tab bloat, a stuck backup, a runaway
indexer, thermal throttling, swap thrash, unexpected network traffic, dried-out
thermal paste, and the Raspberry Pi's favourite party trick, undervoltage from a
cheap cable.</p>
<p>Runs on Windows, Linux and Raspberry Pi (currently: {pretty_name()}).
Nothing leaves your machine — no telemetry, no network calls, no accounts.</p>
<p>Every action the app can take is behind an explicit confirmation and is
reversible wherever the operating system allows it.</p>
<p>Contact us:</p>
<p>Telegram : @NoracProjects</p>
<p>Email : Norac-Projects@Proton.me
<p style="color:#888;">MIT licensed. Built with Python and PySide6.</p>
""")
        text.setWordWrap(True)
        text.setTextFormat(Qt.RichText)
        text.setAlignment(Qt.AlignTop)
        layout.addWidget(text)
