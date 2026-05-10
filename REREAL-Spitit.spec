# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: one-file GUI build with CustomTkinter + pystray assets."""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    "groq",
    "sounddevice",
    "numpy",
    "scipy",
    "keyboard",
    "pyperclip",
    "pystray",
    "PIL",
    "PIL._tkinter_finder",
    "customtkinter",
    "httpx",
    "pydantic",
    "pkg_resources",
    "packaging",
    "pyparsing",
    "setuptools",
]

# Collect everything from core UI and system libs to be safe
for pkg in ("customtkinter", "pystray", "PIL", "pkg_resources", "packaging"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Bundle tray icon PNG
datas.append(("assets/icon.png", "assets"))

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[], # Remove all exclusions to prevent runtime ModuleNotFoundErrors
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
    console=False, # Final build should be windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="version_info.txt",
    icon="assets/icon.ico",
)
