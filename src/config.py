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
VERSION = "2.0.0"
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
