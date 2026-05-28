"""
REREAL - Spitit: Main entry point & VoiceFlowApp orchestrator.
Ties together config, hotkey, recorder, transcriber, paster, pill, tray, settings, splash.
All UI on main thread, cross-thread updates via root.after().
"""

import sys
import os
import threading
import time

# Ensure src is importable when running directly
if getattr(sys, "frozen", False):
    # PyInstaller frozen exe
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if _base not in sys.path:
    sys.path.insert(0, _base)


import customtkinter as ctk

from src.config import load_config, save_config, add_history_entry, VERSION
from src.ui.theme import BG_DEEP, get_fonts


class VoiceFlowApp:
    """
    Main application orchestrator.
    Creates the hidden root window and coordinates all subsystems.
    """

    def __init__(self):
        self._config = load_config()
        self._recording = False
        self._recorder = None
        self._hotkey_ctrl = None
        self._pill = None
        self._tray = None
        self._settings_win = None
        self._splash = None
        self._fonts = None
        self._last_text = ""
        self._record_start_time = 0.0
        self._duration_timer_id = None

    def run(self):
        """Start the application."""
        # Set up CTk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Create hidden root window
        self._root = ctk.CTk()
        self._root.withdraw()  # Hide main window
        self._root.title("REREAL - Spitit")

        # Try to set icon on root
        try:
            from src.config import get_asset_path
            ico_path = get_asset_path("icon.ico")
            if ico_path.exists():
                self._root.iconbitmap(str(ico_path))
        except Exception:
            pass

        # Initialize fonts (must be after root exists)
        self._fonts = get_fonts()

        # Initialize subsystems
        self._init_pill()
        self._init_tray()
        self._init_hotkey()

        # Show splash if first run or launch_on_startup
        if self._config.get("first_run", True):
            self._show_splash(highlight_api_key=True)
        elif self._config.get("launch_on_startup", False):
            self._show_splash(highlight_api_key=False)

        # Run the event loop
        self._root.mainloop()

    def _init_pill(self):
        """Initialize the floating status pill."""
        from src.ui.pill import StatusPill
        self._pill = StatusPill(self._root, self._config)

    def _init_tray(self):
        """Initialize the system tray icon."""
        from src.tray import TrayManager
        self._tray = TrayManager(
            on_open_settings=lambda: self._root.after(0, self._open_settings),
            on_toggle_mode=lambda: self._root.after(0, self._toggle_mode),
            on_check_updates=lambda: self._root.after(0, self._check_updates_from_tray),
            on_copy_last=lambda: self._root.after(0, self._copy_last),
            on_quit=lambda: self._root.after(0, self._quit),
            config=self._config,
        )
        self._tray.start()

    def _init_hotkey(self):
        """Initialize the global hotkey controller."""
        from src.hotkey import HotkeyController
        self._hotkey_ctrl = HotkeyController(
            hold_combo=self._config.get("hold_hotkey", "alt+left shift"),
            toggle_combo=self._config.get("toggle_hotkey", "alt+left shift+space"),
            mode=self._config.get("mode", "hold"),
            on_start=lambda: self._root.after(0, self._start_recording),
            on_stop=lambda: self._root.after(0, self._stop_recording),
        )
        try:
            self._hotkey_ctrl.start()
        except Exception as e:
            print(f"[Main] Hotkey init failed: {e}")

    def _show_splash(self, highlight_api_key: bool = False):
        """Show the splash screen."""
        from src.ui.splash import SplashScreen
        self._splash = SplashScreen(
            self._root,
            self._config,
            self._fonts,
            on_settings=lambda: self._open_settings(highlight_api_key=highlight_api_key),
            on_start=lambda: None,  # Just dismiss
        )
        self._splash.show()

    def _open_settings(self, highlight_api_key: bool = False):
        """Open the settings window."""
        from src.ui.settings import SettingsWindow
        if self._settings_win is None:
            self._settings_win = SettingsWindow(
                self._root,
                self._config,
                self._fonts,
                on_save=self._on_settings_saved,
            )
        self._settings_win.show(highlight_api_key=highlight_api_key)

    def _on_settings_saved(self, config: dict):
        """Called when settings are saved."""
        self._config = config
        self._settings_win = None

        # Update hotkey controller
        if self._hotkey_ctrl:
            self._hotkey_ctrl.update_combos(
                hold_combo=config.get("hold_hotkey", "alt+left shift"),
                toggle_combo=config.get("toggle_hotkey", "alt+left shift+space"),
                mode=config.get("mode", "hold"),
            )

    def _toggle_mode(self):
        """Toggle between hold and toggle mode."""
        current = self._config.get("mode", "hold")
        new_mode = "toggle" if current == "hold" else "hold"
        self._config["mode"] = new_mode
        save_config(self._config)

        if self._hotkey_ctrl:
            self._hotkey_ctrl.update_combos(
                hold_combo=self._config.get("hold_hotkey", "alt+left shift"),
                toggle_combo=self._config.get("toggle_hotkey", "alt+left shift+space"),
                mode=new_mode,
            )

    def _check_updates_from_tray(self):
        """Check for updates (triggered from tray)."""
        self._open_settings()

    def _copy_last(self):
        """Copy last transcription to clipboard."""
        if self._last_text:
            try:
                import pyperclip
                pyperclip.copy(self._last_text)
            except Exception:
                pass

    # ── Recording Flow ──────────────────────────────────────────────────────

    def _start_recording(self):
        """Begin audio recording."""
        if self._recording:
            # Double-tap cancel (in hold mode)
            self._cancel_recording()
            return

        # Check API key
        if not self._config.get("api_key"):
            self._pill.set_state("error")
            self._root.after(500, lambda: self._open_settings(highlight_api_key=True))
            return

        try:
            from src.recorder import Recorder
            self._recorder = Recorder(
                device_index=self._config.get("mic_device_index")
            )
            self._recorder.start(on_auto_stop=lambda: self._root.after(0, self._stop_recording))
            self._recording = True
            self._record_start_time = time.time()
            self._pill.set_state("recording")
            self._start_duration_timer()
        except Exception as e:
            print(f"[Main] Recording failed: {e}")
            self._pill.set_state("error")
            self._recording = False

    def _stop_recording(self):
        """Stop recording and begin transcription."""
        if not self._recording or not self._recorder:
            return

        self._recording = False
        self._stop_duration_timer()

        try:
            wav_bytes = self._recorder.stop()
        except Exception as e:
            print(f"[Main] Stop recording failed: {e}")
            self._pill.set_state("error")
            return

        if wav_bytes is None:
            # Too short
            self._pill.set_state("hidden")
            return

        # Check silence
        threshold = self._config.get("silence_threshold", 0.01)
        if self._recorder.check_silence(wav_bytes, threshold):
            self._pill.set_state("error")
            return

        # Transcribe in background
        self._pill.set_state("transcribing")
        threading.Thread(
            target=self._transcribe_thread,
            args=(wav_bytes,),
            daemon=True,
        ).start()

    def _cancel_recording(self):
        """Cancel the current recording without transcribing."""
        if self._recorder:
            self._recorder.cancel()
        self._recording = False
        self._stop_duration_timer()
        self._pill.set_state("hidden")

    def _start_duration_timer(self):
        """Start updating the pill with recording duration."""
        def tick():
            if self._recording:
                duration = time.time() - self._record_start_time
                self._pill.update_duration(duration)
                self._duration_timer_id = self._root.after(200, tick)
        tick()

    def _stop_duration_timer(self):
        """Stop the duration timer."""
        if self._duration_timer_id:
            self._root.after_cancel(self._duration_timer_id)
            self._duration_timer_id = None

    def _transcribe_thread(self, wav_bytes: bytes):
        """Run transcription in a background thread."""
        try:
            from src.transcriber import transcribe
            text = transcribe(
                wav_bytes,
                api_key=self._config.get("api_key", ""),
                language=self._config.get("language", "en"),
            )

            self._root.after(0, lambda: self._on_transcription_done(text))

        except Exception as e:
            print(f"[Main] Transcription failed: {e}")
            self._root.after(0, lambda: self._pill.set_state("error"))

    def _on_transcription_done(self, text: str):
        """Handle successful transcription (on main thread)."""
        word_count = len(text.split())
        self._last_text = text

        # Update tray
        if self._tray:
            self._tray.update_last_text(text)

        # Add to history
        add_history_entry(
            self._config,
            text,
            self._config.get("language", "en"),
        )

        # Show done state with word count
        self._pill.set_state("done", word_count=word_count)

        # Paste/clipboard/notification/sound
        from src.paster import paste_text
        paste_text(text, self._config)

    # ── App Lifecycle ───────────────────────────────────────────────────────

    def _quit(self):
        """Quit the application."""
        # Save pill position
        save_config(self._config)

        # Stop hotkeys
        if self._hotkey_ctrl:
            self._hotkey_ctrl.stop()

        # Stop tray
        if self._tray:
            self._tray.stop()

        # Destroy pill
        if self._pill:
            self._pill.destroy()

        # Quit
        self._root.quit()
        self._root.destroy()


def main():
    """Application entry point."""
    app = VoiceFlowApp()
    app.run()


if __name__ == "__main__":
    main()
