# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller EasyWhy.spec

import sys

hidden = []
if sys.platform == "win32":
    hidden += ["wmi", "pythoncom", "win32com", "win32com.client"]

a = Analysis(
    ["main.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="EasyWhy",
    console=False,
    upx=True,
    strip=False,
)
