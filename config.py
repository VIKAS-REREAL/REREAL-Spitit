"""Load and save application configuration."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Literal


def _config_dir() -> Path:
    """Frozen builds store settings under LocalAppData so Program Files installs stay writable."""
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))
        d = base / "REREAL_Spitit"
        d.mkdir(parents=True, exist_ok=True)
        return d
    return Path(__file__).resolve().parent


CONFIG_PATH = _config_dir() / "config.json"


def _migrate_portable_config_if_needed() -> None:
    if not getattr(sys, "frozen", False):
        return
    if CONFIG_PATH.is_file():
        return
    legacy = Path(sys.executable).resolve().parent / "config.json"
    if legacy.is_file():
        try:
            shutil.copy2(legacy, CONFIG_PATH)
        except OSError:
            pass

Mode = Literal["hold", "toggle"]

DEFAULTS: dict[str, Any] = {
    "api_key": "",
    "mode": "hold",
    "language": "en",
    "launch_on_startup": False,
    "pill_position": None,
}


def load_config() -> dict[str, Any]:
    _migrate_portable_config_if_needed()
    if not CONFIG_PATH.is_file():
        save_config(dict(DEFAULTS))
        return dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)
    merged = dict(DEFAULTS)
    for key in DEFAULTS:
        if key in data:
            merged[key] = data[key]
    return merged


def save_config(cfg: dict[str, Any]) -> None:
    out = dict(DEFAULTS)
    for key in DEFAULTS:
        if key in cfg:
            out[key] = cfg[key]
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


def get_mode(cfg: dict[str, Any]) -> Mode:
    m = cfg.get("mode", "hold")
    return m if m in ("hold", "toggle") else "hold"
