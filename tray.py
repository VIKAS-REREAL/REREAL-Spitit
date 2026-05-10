"""System tray: icon, menu, optional programmatic icon asset."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

ACCENT = "#FFD505"
TOOLTIP = "REREAL - Spitit"


def _dev_assets_dir() -> Path:
    return Path(__file__).resolve().parent / "assets"


def _bundled_icon() -> Path | None:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        p = Path(sys._MEIPASS) / "assets" / "icon.png"
        if p.is_file():
            return p
    return None


def _cache_icon_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "REREAL_Spitit"
    base.mkdir(parents=True, exist_ok=True)
    return base / "icon.png"


def ensure_icon_png() -> Path:
    bundled = _bundled_icon()
    if bundled is not None:
        return bundled

    dev_dir = _dev_assets_dir()
    dev_dir.mkdir(parents=True, exist_ok=True)
    dev_icon = dev_dir / "icon.png"
    if dev_icon.is_file():
        return dev_icon

    img = _draw_tray_icon(256)
    try:
        img.save(dev_icon, format="PNG")
        return dev_icon
    except OSError:
        cache = _cache_icon_path()
        img.save(cache, format="PNG")
        return cache


def _draw_tray_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = int(size * 0.08)
    radius = int(size * 0.18)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=ACCENT,
    )
    bar_color = "#000000"
    inner_top = margin + int(size * 0.12)
    inner_bottom = size - margin - int(size * 0.14)
    inner_h = inner_bottom - inner_top
    cx = size // 2
    w = max(2, int(size * 0.062))
    rel_heights = (0.38, 0.58, 1.0, 0.58, 0.38)
    gaps = int(size * 0.075)
    total_w = w * len(rel_heights) + gaps * (len(rel_heights) - 1)
    x0 = cx - total_w // 2
    for i, rh in enumerate(rel_heights):
        h = max(1, int(inner_h * rh))
        x = x0 + i * (w + gaps)
        y = inner_bottom - h
        top = max(inner_top, y)
        draw.rectangle([x, top, x + w, inner_bottom], fill=bar_color)
    return img


def load_tray_image() -> Image.Image:
    path = ensure_icon_png()
    return Image.open(path).convert("RGBA")


def create_tray_icon(
    on_open_settings: Callable[[], None],
    on_toggle_mode: Callable[[], None],
    on_quit: Callable[[], None],
):
    import pystray
    from pystray import MenuItem as item

    image = load_tray_image()
    menu = pystray.Menu(
        item("Open Settings", lambda: on_open_settings()),
        item("Toggle Mode", lambda: on_toggle_mode()),
        pystray.Menu.SEPARATOR,
        item("Quit", lambda: on_quit()),
    )
    return pystray.Icon("rereal_spitit", image, TOOLTIP, menu)


ICON_PATH = _dev_assets_dir() / "icon.png"
