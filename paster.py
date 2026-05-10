"""Paste text into the active window via clipboard + Ctrl+V."""

from __future__ import annotations

import time


def paste_text(text: str) -> None:
    import keyboard
    import pyperclip

    pyperclip.copy(text)
    time.sleep(0.03)
    keyboard.press_and_release("ctrl+v")
