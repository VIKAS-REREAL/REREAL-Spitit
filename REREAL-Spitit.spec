# -*- mode: python ; coding: utf-8 -*-
"""
REREAL - Spitit: PyInstaller spec file.
Builds a single portable .exe with all dependencies bundled.
"""

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for pkg in ("customtkinter", "pystray", "plyer"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

datas += [
    ("assets/icon.png", "assets"),
    ("assets/icon.ico", "assets"),
    ("assets/sound/done.wav", "assets/sound"),
]

hiddenimports += [
    "PIL._tkinter_finder",
    "sounddevice",
    "numpy",
    "scipy",
    "scipy.io",
    "scipy.io.wavfile",
    "groq",
    "httpx",
    "httpx._transports",
    "httpx._transports.default",
    "pydantic",
    "keyboard",
    "pyperclip",
    "plyer",
    "plyer.platforms",
    "plyer.platforms.win",
    "plyer.platforms.win.notification",
    "_sounddevice_data",
]

a = Analysis(
    ["src/main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    a.zipfiles,
    [],
    name="REREAL-Spitit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon="assets/icon.ico",
    version="version.txt",
)
