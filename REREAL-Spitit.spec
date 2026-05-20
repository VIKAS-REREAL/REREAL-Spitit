# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: one-file GUI build with CustomTkinter + pystray assets."""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

for pkg in ("customtkinter", "pystray"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Bundle tray icon PNG (used at runtime by tray.py)
datas.append(("assets/icon.png", "assets"))

hiddenimports += [
    "PIL._tkinter_finder",
    "sounddevice",
    "numpy",
    "scipy",
    "groq",
    "httpx",
    "pydantic",
    "keyboard",
    "pyperclip",
]

a = Analysis(
    ["main.py"],
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
    a.zipfiles,
    a.datas,
    [],
    name="REREAL-Spitit",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="version.txt",
    icon="assets/icon.ico",
)
