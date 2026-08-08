"""
REREAL - Spitit: Configuration manager.
Handles loading, saving, defaults, and migration of config.json
stored in %LOCALAPPDATA%\\REREAL_Spitit\\.
"""

import json
import os
import copy
from pathlib import Path
from datetime import datetime

APP_NAME = "REREAL_Spitit"
CONFIG_FILENAME = "config.json"
VERSION = "2.0.1"
MAX_HISTORY = 50

DEFAULTS = {
    "api_key": "",
    "hold_hotkey": "alt+left shift",
    "toggle_hotkey": "alt+left shift+space",
    "mode": "hold",
    "language": "en",
    "launch_on_startup": False,
    "pill_position": None,
    "mic_device_index": None,
    "silence_threshold": 0.01,
    "output_paste": True,
    "output_clipboard": True,
    "output_notification": True,
    "output_sound": True,
    "history_enabled": True,
    "history": [],
    "first_run": True,
    "version": VERSION,
}


def get_config_dir() -> Path:
    """Return the config directory path, creating it if needed."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        # Fallback for non-Windows or missing env var
        local_app_data = Path.home() / "AppData" / "Local"
    config_dir = Path(local_app_data) / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Return the full path to config.json."""
    return get_config_dir() / CONFIG_FILENAME


def load_config() -> dict:
    """
    Load config from disk. If missing or corrupted, return defaults.
    Performs migration to add any new keys from DEFAULTS.
    """
    config_path = get_config_path()
    config = copy.deepcopy(DEFAULTS)

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Merge: saved values override defaults, but new keys are added
            for key, value in saved.items():
                if key in config:
                    config[key] = value
        except (json.JSONDecodeError, OSError, KeyError):
            # Corrupted config — use defaults
            pass

    # Migrate: ensure version is current
    config["version"] = VERSION

    # Validate history
    if not isinstance(config.get("history"), list):
        config["history"] = []

    return config


def save_config(config: dict) -> None:
    """Save config to disk as formatted JSON."""
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"[Config] Failed to save config: {e}")


def add_history_entry(config: dict, text: str, language: str) -> None:
    """Add a transcription to history, rotating oldest if at max."""
    if not config.get("history_enabled", True):
        return

    entry = {
        "text": text,
        "language": language,
        "words": len(text.split()),
        "ts": datetime.now().isoformat(timespec="seconds"),
    }

    history = config.get("history", [])
    history.insert(0, entry)

    # Rotate: keep only MAX_HISTORY entries
    if len(history) > MAX_HISTORY:
        history = history[:MAX_HISTORY]

    config["history"] = history
    save_config(config)


def get_asset_path(filename: str) -> Path:
    """
    Return the correct path to a bundled asset, handling both
    development mode and PyInstaller frozen mode.
    """
    import sys
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as compiled exe
        base = Path(sys._MEIPASS)
    else:
        # Running in development
        base = Path(__file__).parent.parent

    return base / "assets" / filename


def set_launch_on_startup(enabled: bool) -> None:
    """Add or remove the app from Windows startup via registry."""
    try:
        import winreg
        import sys

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        value_name = "REREALSpitit"

        if getattr(sys, "frozen", False):
            exe_path = sys.executable
        else:
            exe_path = f'"{sys.executable}" "{Path(__file__).parent / "main.py"}"'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        )

        if enabled:
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, value_name)
            except FileNotFoundError:
                pass

        winreg.CloseKey(key)
    except Exception as e:
        print(f"[Config] Failed to set startup: {e}")


def setup_app_user_model_id(app_id: str = "REREAL.Spitit.VoiceFlow.2.0") -> None:
    """
    Set Windows Application User Model ID (AppUserModelID).
    Ensures Windows Taskbar and Task Manager group the process under
    its custom icon instead of generic Python / executable icon.
    """
    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception as e:
            print(f"[Config] Failed to set AppUserModelID: {e}")


def apply_win32_icon(window, ico_path_str: str) -> None:
    """Force Win32 WM_SETICON message directly to the window HWND for titlebar and taskbar."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010

        window.update_idletasks()
        raw_hwnd = window.winfo_id()
        hwnd = user32.GetParent(raw_hwnd) or raw_hwnd

        # Load 16x16 icon for titlebar
        hicon_small = user32.LoadImageW(
            0, ico_path_str, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
        )
        # Load 48x48 icon for taskbar / Alt-Tab
        hicon_big = user32.LoadImageW(
            0, ico_path_str, IMAGE_ICON, 48, 48, LR_LOADFROMFILE
        )

        if hicon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
        if hicon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
    except Exception:
        pass


def set_window_icon(window) -> None:
    """
    Apply the app icon to a Tkinter / CustomTkinter window.
    Overrides CustomTkinter's default blue icon by marking _iconbitmap_method_called
    and applying iconbitmap + Win32 WM_SETICON immediately and after CTk's timer.
    """
    try:
        import sys
        import tkinter as tk

        ico_path = get_asset_path("icon.ico")
        png_path = get_asset_path("icon.png")

        # Mark CTk flag so CTk doesn't overwrite with CustomTkinter_icon_Windows.ico
        setattr(window, "_iconbitmap_method_called", True)

        # 1. Tkinter iconphoto (global default for all windows)
        if png_path.exists():
            try:
                icon_img = tk.PhotoImage(file=str(png_path))
                window.iconphoto(True, icon_img)
                window._icon_photo_ref = icon_img
            except Exception:
                pass

        # 2. Tkinter iconbitmap + Win32 WM_SETICON
        if sys.platform == "win32" and ico_path.exists():
            ico_str = str(ico_path)
            try:
                window.iconbitmap(ico_str)
            except Exception:
                try:
                    window.wm_iconbitmap(ico_str)
                except Exception:
                    pass

            # Inject Win32 WM_SETICON immediately and at 100ms, 250ms, 400ms
            apply_win32_icon(window, ico_str)

            def _apply_override(p=ico_str):
                try:
                    setattr(window, "_iconbitmap_method_called", True)
                    window.iconbitmap(p)
                    apply_win32_icon(window, p)
                except Exception:
                    pass

            for delay in (100, 250, 400):
                try:
                    window.after(delay, _apply_override)
                except Exception:
                    pass
    except Exception as e:
        print(f"[Config] Failed to set window icon: {e}")




