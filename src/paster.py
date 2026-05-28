"""
REREAL - Spitit: Output handler.
Clipboard copy, auto-paste, Windows toast notification, done sound.
"""

import threading
from pathlib import Path


def paste_text(text: str, cfg: dict) -> None:
    """
    Handle all output actions for transcribed text.
    
    1. Copy to clipboard (always, as fallback)
    2. Auto-paste via Ctrl+V (if enabled)
    3. Desktop notification (if enabled)
    4. Sound feedback (if enabled)
    """
    import pyperclip
    import time

    # 1. Clipboard — always copy
    if cfg.get("output_clipboard", True):
        try:
            pyperclip.copy(text)
        except Exception as e:
            print(f"[Paster] Clipboard failed: {e}")

    # 2. Auto-paste
    if cfg.get("output_paste", True):
        try:
            time.sleep(0.05)  # Small delay for clipboard to settle
            import keyboard
            keyboard.press_and_release("ctrl+v")
        except Exception as e:
            print(f"[Paster] Auto-paste failed: {e}")

    # 3. Notification
    if cfg.get("output_notification", True):
        truncated = text[:80] + ("…" if len(text) > 80 else "")
        _show_toast(truncated)

    # 4. Sound
    if cfg.get("output_sound", True):
        _play_done_sound()


def _show_toast(message: str) -> None:
    """Show a Windows toast notification (non-blocking)."""
    def _notify():
        try:
            from plyer import notification
            notification.notify(
                title="Spitit — Transcribed",
                message=message,
                app_name="REREAL - Spitit",
                timeout=3,
            )
        except Exception as e:
            print(f"[Paster] Notification failed: {e}")

    threading.Thread(target=_notify, daemon=True).start()


def _play_done_sound() -> None:
    """Play the done chime sound (non-blocking)."""
    def _play():
        try:
            import sounddevice as sd
            import scipy.io.wavfile as wav

            sound_path = _get_sound_path()
            if not sound_path.exists():
                return

            sr, data = wav.read(str(sound_path))
            sd.play(data, sr, blocking=False)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def _get_sound_path() -> Path:
    """Get the path to the done.wav sound file."""
    from src.config import get_asset_path
    return get_asset_path("sound/done.wav")
