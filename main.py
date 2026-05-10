"""
Spitit — Voice-to-text for Windows.

Hotkey → Microphone → Groq Whisper → Paste into active window.

Usage:
    python -m spitit          # Run from source
    python main.py            # Alternative entry point

This module wires together the subsystems (config, hotkeys, recorder,
transcriber, paster, tray icon, and UI windows) and runs the main loop.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

# No sys.path insertion needed since modules are in the root directory.

import customtkinter as ctk

import config as cfg_mod
from config import DEFAULTS
from hotkey import HotkeyController
from tray import create_tray_icon, ensure_icon_png
from ui import SettingsWindow, SplashWindow, StatusPill, apply_ctk_theme

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STARTUP_REG_NAME = "REREALSpitit"
STARTUP_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

logger = logging.getLogger("spitit")


# ---------------------------------------------------------------------------
# Launch-on-startup helpers
# ---------------------------------------------------------------------------
def _startup_command() -> str:
    """Compute the command string to re-launch this app on boot."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    main_py = Path(__file__).resolve()
    return f'"{sys.executable}" "{main_py}"'


def apply_launch_on_startup(enable: bool) -> None:
    """Register or remove the Windows Run-key entry for auto-start."""
    import winreg  # platform-specific; imported lazily

    cmd = _startup_command()
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        STARTUP_KEY_PATH,
        0,
        winreg.KEY_READ | winreg.KEY_SET_VALUE,
    ) as key:
        if enable:
            winreg.SetValueEx(key, STARTUP_REG_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, STARTUP_REG_NAME)
            except FileNotFoundError:
                pass


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class VoiceFlowApp:
    """Top-level orchestrator for the Spitit voice-to-text application.

    Wires together:
      - config persistence
      - system-tray icon + context menu
      - global hotkey listener (hold / toggle)
      - microphone → WAV recording
      - Groq Whisper transcription
      - clipboard-based auto-paste
      - CustomTkinter UI (status pill + settings window)
    """

    def __init__(self) -> None:
        apply_ctk_theme()
        self._config = cfg_mod.load_config()
        apply_launch_on_startup(bool(self._config.get("launch_on_startup")))

        self._root = ctk.CTk()
        self._root.title("REREAL · Spitit")
        self._root.withdraw()  # hidden main window; tray is the entry point
        self._root.protocol("WM_DELETE_WINDOW", self._ignore_close)

        ensure_icon_png()
        self._set_window_icon(self._root)

        self._pill = StatusPill(
            self._root,
            get_pill_position=lambda: self._config.get("pill_position"),
            save_pill_position=self._save_pill_position,
        )
        self._settings = SettingsWindow(
            self._root,
            get_config=self._get_config_snapshot,
            on_save=self._on_settings_saved,
        )
        self._settings.withdraw()

        self._splash = SplashWindow(self._root)

        # Recording state
        self._stop_event: "threading.Event | None" = None
        self._rec_thread: "threading.Thread | None" = None
        self._wav_path: "Path | None" = None
        self._busy = False
        self._lock = threading.Lock()

        # Hotkey controller
        self._hotkeys = HotkeyController(
            mode_getter=lambda: cfg_mod.get_mode(self._config),
            on_start=self._on_hotkey_start,
            on_stop=self._on_hotkey_stop,
        )

        # System tray (runs in its own daemon thread)
        self._tray_icon = create_tray_icon(
            on_open_settings=self._open_settings,
            on_toggle_mode=self._tray_toggle_mode,
            on_quit=self._quit,
        )
        self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()
        time.sleep(0.15)  # brief pause so tray icon initializes

        self._hotkeys.start()
        self._root.after(100, self._splash.show_centered)

    # -- private helpers ---------------------------------------------------

    def _ignore_close(self) -> None:
        """Ignore WM_DELETE_WINDOW — keeps the app in the tray."""
        pass

    def _set_window_icon(self, widget: ctk.CTk) -> None:
        try:
            from PIL import Image, ImageTk

            pil = Image.open(ensure_icon_png()).convert("RGBA")
            icon_img = ImageTk.PhotoImage(pil.resize((64, 64), Image.Resampling.LANCZOS))
            widget._spitit_icon = icon_img  # type: ignore
            widget.iconphoto(True, icon_img)  # type: ignore
        except Exception:
            pass

    def _get_config_snapshot(self) -> dict:
        return dict(self._config)

    def _save_pill_position(self, x: int, y: int) -> None:
        self._config["pill_position"] = [x, y]
        cfg_mod.save_config(self._config)

    def _on_settings_saved(self, new_cfg: dict) -> None:
        self._config.update(new_cfg)
        cfg_mod.save_config(self._config)
        apply_launch_on_startup(bool(self._config.get("launch_on_startup")))

    def _open_settings(self) -> None:
        self._root.after(0, self._settings.open_front)

    def _tray_toggle_mode(self) -> None:
        cur = cfg_mod.get_mode(self._config)
        nxt = "toggle" if cur == "hold" else "hold"
        self._config["mode"] = nxt
        cfg_mod.save_config(self._config)
        label = "Toggle to talk" if nxt == "toggle" else "Hold to talk"
        self._root.after(0, lambda: self._pill.show_mode_notice(label))

    def _quit(self) -> None:
        self._hotkeys.stop()
        try:
            self._tray_icon.stop()
        except Exception:
            pass
        self._root.after(0, self._root.quit)

    # -- recording pipeline ------------------------------------------------

    def _on_hotkey_start(self) -> None:
        """Called by HotkeyController when the user starts holding/toggling."""
        with self._lock:
            if self._busy:
                return
            if self._rec_thread is not None and self._rec_thread.is_alive():
                return
            self._busy = True
            self._stop_event = threading.Event()
            fd, tmp = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            self._wav_path = Path(tmp)
            path = self._wav_path
            ev = self._stop_event

            def run_rec() -> None:
                import recorder

                recorder.record_to_wav(path, ev)

            self._rec_thread = threading.Thread(target=run_rec, daemon=True)
            self._rec_thread.start()
        self._root.after(0, self._pill.show_recording)

    def _on_hotkey_stop(self) -> None:
        """Called when the user releases the hold keys or toggles again."""
        threading.Thread(target=self._finish_recording_pipeline, daemon=True).start()

    def _finish_recording_pipeline(self) -> None:
        """Stop recording, transcribe, and paste the result."""
        stop_ev = self._stop_event
        rec_th = self._rec_thread
        wav = self._wav_path

        try:
            if stop_ev is not None:
                stop_ev.set()
            if rec_th is not None:
                rec_th.join(timeout=90)
        except Exception:
            pass

        self._rec_thread = None
        self._stop_event = None

        ok_file = wav is not None and wav.is_file() and wav.stat().st_size > 64

        def cleanup_wav() -> None:
            try:
                if wav is not None and wav.is_file():
                    wav.unlink(missing_ok=True)
            except OSError:
                pass

        if not ok_file:
            cleanup_wav()
            self._root.after(
                0,
                lambda: self._pill.show_error("Microphone error or recording too short."),
            )
            with self._lock:
                self._busy = False
            return

        self._root.after(0, self._pill.show_transcribing)

        cfg = dict(self._config)
        api_key = str(cfg.get("api_key", ""))
        language = str(cfg.get("language", "en"))

        try:
            import transcriber

            text = transcriber.transcribe_audio(wav, api_key, language)
        except Exception as e:
            cleanup_wav()
            self._root.after(0, lambda: self._pill.show_error(str(e)))
            with self._lock:
                self._busy = False
            return

        cleanup_wav()

        if not text:
            self._root.after(0, lambda: self._pill.show_error("No speech detected."))
            with self._lock:
                self._busy = False
            return

        try:
            import paster

            paster.paste_text(text)
        except Exception as e:
            self._root.after(0, lambda: self._pill.show_error(f"Paste failed: {e}"))
            with self._lock:
                self._busy = False
            return

        self._root.after(0, self._pill.show_done)
        with self._lock:
            self._busy = False

    # -- entry point -------------------------------------------------------

    def run(self) -> None:
        self._root.mainloop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    VoiceFlowApp().run()


if __name__ == "__main__":
    main()
