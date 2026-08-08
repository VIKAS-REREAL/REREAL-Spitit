"""
REREAL - Spitit: Settings window.
Modern 2-pane sidebar layout (~720×640) with 5 regrouped navigation tabs,
live microphone RMS level meter, and safe history clear confirmation.
"""

import threading
import webbrowser
import numpy as np
import customtkinter as ctk
from PIL import Image

from src.config import get_asset_path, set_window_icon
from src.ui.theme import (
    BG_BASE, BG_SURFACE, BG_ELEVATED, GLASS_BG, GLASS_BORDER,
    ACCENT, ACCENT_HOVER, ACCENT_DIM, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, TEXT_ON_ACCENT, CORNER_RADIUS, CORNER_RADIUS_SM,
    BORDER_WIDTH, SETTINGS_WIDTH, SETTINGS_HEIGHT,
    STATE_DONE, STATE_ERROR,
)
from src.ui.components import (
    GlassFrame, AccentButton, GhostButton, SectionHeader,
    ToggleSwitch, RadioCard, HotkeyButton, StatusBadge,
    SidebarNavButton,
)
from src.transcriber import LANGUAGES
from src.hotkey import format_combo, validate_combo, HotkeyRecorder
from src.updater import check_for_update, CURRENT_VERSION


class SettingsWindow:
    """
    Main settings window for REREAL - Spitit.
    Size: 720×640, 2-pane sidebar tabbed layout.
    """

    def __init__(self, root, config: dict, fonts: dict, on_save=None, on_close=None):
        self._root = root
        self._config = config
        self._fonts = fonts
        self._on_save = on_save
        self._on_close = on_close
        self._win = None
        self._hotkey_recorder = HotkeyRecorder()
        self._vars = {}

        self._nav_buttons = {}
        self._current_tab = "general"
        self._is_dirty = False
        
        # Mic meter stream state
        self._mic_stream = None
        self._mic_meter_running = False
        self._mic_level_bar = None
        self._mic_level_lbl = None
        self._test_mic_btn = None
        self._api_status = None
        self._api_entry = None
        self._update_status = None
        self._thresh_label = None

    def _widget_valid(self, attr_name: str) -> bool:
        """Return True if self.<attr_name> exists, is not None, and is a valid widget."""
        w = getattr(self, attr_name, None)
        if w is None:
            return False
        try:
            return bool(w.winfo_exists())
        except Exception:
            return False


    def show(self, highlight_api_key: bool = False):
        """Open the settings window."""
        if self._win and self._win.winfo_exists():
            self._win.focus_force()
            return

        self._win = ctk.CTkToplevel(self._root)
        self._win.title("REREAL · Spitit — Settings")
        self._win.geometry(f"{SETTINGS_WIDTH}x{SETTINGS_HEIGHT}")
        self._win.minsize(700, 520)
        self._win.configure(fg_color=BG_BASE)
        self._win.resizable(True, True)


        # Set window icon
        set_window_icon(self._win)

        # Initialize variables from config
        self._init_vars()

        # Handle window close
        self._win.protocol("WM_DELETE_WINDOW", self.close)

        # ── Main 2-Pane Split Container ──
        self._main_container = ctk.CTkFrame(self._win, fg_color=BG_BASE, corner_radius=0)
        self._main_container.pack(fill="both", expand=True)

        # ── Left Sidebar (180px fixed width) ──
        self._sidebar_frame = ctk.CTkFrame(
            self._main_container,
            fg_color=BG_SURFACE,
            width=190,
            corner_radius=0,
            border_color=GLASS_BORDER,
            border_width=BORDER_WIDTH,
        )
        self._sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        self._sidebar_frame.pack_propagate(False)

        # ── Right Content Pane ──
        self._content_pane = ctk.CTkScrollableFrame(
            self._main_container,
            fg_color=BG_BASE,
            scrollbar_button_color=BG_ELEVATED,
            scrollbar_button_hover_color=ACCENT,
        )
        self._content_pane.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        # Build Sidebar & Footer
        self._build_sidebar()
        self._build_footer()

        # Initial Tab Switch
        initial_tab = "general" if not highlight_api_key else "general"
        self._switch_tab(initial_tab)

        if highlight_api_key:
            self._win.after(200, lambda: self._focus_api_key_entry())

        self._win.focus_force()

    def _init_vars(self):
        """Create tkinter variables from config and attach dirty state listeners."""
        cfg = self._config
        self._vars = {
            "api_key": ctk.StringVar(value=cfg.get("api_key", "")),
            "mode": ctk.StringVar(value=cfg.get("mode", "hold")),
            "hold_hotkey": ctk.StringVar(value=cfg.get("hold_hotkey", "alt+left shift")),
            "toggle_hotkey": ctk.StringVar(value=cfg.get("toggle_hotkey", "alt+left shift+space")),
            "language": ctk.StringVar(value=self._get_language_display(cfg.get("language", "en"))),
            "mic_device": ctk.StringVar(value="System Default"),
            "output_paste": ctk.BooleanVar(value=cfg.get("output_paste", True)),
            "output_clipboard": ctk.BooleanVar(value=cfg.get("output_clipboard", True)),
            "output_notification": ctk.BooleanVar(value=cfg.get("output_notification", True)),
            "output_sound": ctk.BooleanVar(value=cfg.get("output_sound", True)),
            "history_enabled": ctk.BooleanVar(value=cfg.get("history_enabled", True)),
            "silence_threshold": ctk.DoubleVar(value=cfg.get("silence_threshold", 0.01)),
            "launch_on_startup": ctk.BooleanVar(value=cfg.get("launch_on_startup", False)),
        }
        self._is_dirty = False
        for var in self._vars.values():
            var.trace_add("write", lambda *_: self._mark_dirty())

    def _mark_dirty(self):
        """Mark dirty state and update footer hint."""
        self._is_dirty = True
        if hasattr(self, "_dirty_dot") and self._dirty_dot:
            self._dirty_dot.configure(text="● Unsaved changes", text_color=ACCENT)

    def _get_language_display(self, code: str) -> str:
        """Convert language code to display name."""
        from src.transcriber import LANGUAGE_NAMES
        return LANGUAGE_NAMES.get(code, "English")

    def _get_language_code(self, display: str) -> str:
        """Convert display name to language code."""
        return LANGUAGES.get(display, "en")

    # ── Sidebar Construction ────────────────────────────────────────────────

    def _build_sidebar(self):
        """Build the left sidebar navigation items."""
        # Top Logo Header
        header = ctk.CTkFrame(self._sidebar_frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(16, 20))

        try:
            png_path = get_asset_path("icon.png")
            if png_path.exists():
                pil_img = Image.open(png_path).convert("RGBA")
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(36, 36))
                logo_lbl = ctk.CTkLabel(header, image=ctk_img, text="")
                logo_lbl.pack(side="left", padx=(4, 8))
        except Exception:
            pass

        titles_frame = ctk.CTkFrame(header, fg_color="transparent")
        titles_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            titles_frame,
            text="Spitit",
            text_color=ACCENT,
            font=self._fonts["lg"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            titles_frame,
            text=f"v{CURRENT_VERSION}",
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
            anchor="w",
        ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(self._sidebar_frame, fg_color=GLASS_BORDER, height=1).pack(fill="x", padx=12, pady=(0, 12))

        # Nav items (5 regrouped sections)
        nav_items = [
            ("general", "General", "🔑"),
            ("dictation", "Dictation", "🎙️"),
            ("microphone", "Microphone", "🎤"),
            ("output", "Output", "📋"),
            ("history", "History", "📜"),
        ]

        self._nav_buttons = {}
        for key, label, icon in nav_items:
            btn = SidebarNavButton(
                self._sidebar_frame,
                title=label,
                icon=icon,
                fonts=self._fonts,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(fill="x", padx=8, pady=3)
            self._nav_buttons[key] = btn

    def _switch_tab(self, tab_key: str):
        """Switch active content tab in the right pane."""
        # Stop mic meter if navigating away from microphone tab
        if self._current_tab == "microphone" and tab_key != "microphone":
            self._stop_mic_meter()

        self._current_tab = tab_key

        # Highlight sidebar buttons
        for k, btn in self._nav_buttons.items():
            btn.set_active(k == tab_key)

        # Clear right content pane
        for child in self._content_pane.winfo_children():
            child.destroy()

        # Mount selected tab builder
        if tab_key == "general":
            self._build_tab_general(self._content_pane)
        elif tab_key == "dictation":
            self._build_tab_dictation(self._content_pane)
        elif tab_key == "microphone":
            self._build_tab_microphone(self._content_pane)
        elif tab_key == "output":
            self._build_tab_output(self._content_pane)
        elif tab_key == "history":
            self._build_tab_history(self._content_pane)

    # ── Tab 1: General (API Key + Startup + About) ──────────────────────────

    def _build_tab_general(self, parent):
        """General Settings: Groq API Key + Launch on startup + About & Updates."""
        # API Key Section
        self._build_api_key_section(parent)

        # Startup Section
        startup_frame = GlassFrame(parent)
        startup_frame.pack(fill="x", pady=(0, 12))

        SectionHeader(startup_frame, "App Lifecycle", "⚡", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        ToggleSwitch(
            startup_frame,
            label="Launch on Windows startup",
            description="Start REREAL - Spitit automatically when Windows boots",
            variable=self._vars["launch_on_startup"],
            fonts=self._fonts,
        ).pack(fill="x", padx=16, pady=(0, 12))

        # About & Updates Section
        self._build_about_section(parent)

    def _build_api_key_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "Groq API Key", "🔑", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        entry_frame = ctk.CTkFrame(section, fg_color="transparent")
        entry_frame.pack(fill="x", padx=16, pady=(0, 4))

        self._api_entry = ctk.CTkEntry(
            entry_frame,
            textvariable=self._vars["api_key"],
            show="•",
            placeholder_text="gsk_...",
            fg_color=BG_SURFACE,
            border_color=GLASS_BORDER,
            text_color=TEXT_PRIMARY,
            font=self._fonts["mono"],
            height=38,
        )
        self._api_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._show_key = False
        self._eye_btn = ctk.CTkButton(
            entry_frame,
            text="👁",
            width=38,
            height=38,
            fg_color=BG_SURFACE,
            hover_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY,
            corner_radius=CORNER_RADIUS_SM,
            command=self._toggle_key_visibility,
        )
        self._eye_btn.pack(side="left", padx=(0, 4))

        self._test_btn = ctk.CTkButton(
            entry_frame,
            text="Test",
            width=60,
            height=38,
            fg_color=BG_SURFACE,
            hover_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY,
            corner_radius=CORNER_RADIUS_SM,
            command=self._test_api_key,
        )
        self._test_btn.pack(side="left")

        self._api_status = ctk.CTkLabel(
            section,
            text="",
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
            anchor="w",
        )
        self._api_status.pack(fill="x", padx=16, pady=(0, 4))

        link = ctk.CTkLabel(
            section,
            text="Get your free key at console.groq.com",
            text_color=ACCENT,
            font=self._fonts["xs"],
            cursor="hand2",
        )
        link.pack(padx=16, pady=(0, 12), anchor="w")
        link.bind("<Button-1>", lambda e: webbrowser.open("https://console.groq.com"))

    def _focus_api_key_entry(self):
        if hasattr(self, "_api_entry") and self._api_entry.winfo_exists():
            self._api_entry.focus_set()

    def _toggle_key_visibility(self):
        self._show_key = not self._show_key
        self._api_entry.configure(show="" if self._show_key else "•")
        self._eye_btn.configure(text="🔒" if self._show_key else "👁")

    def _test_api_key(self):
        key = self._vars["api_key"].get().strip()
        if not key:
            self._api_status.configure(text="⚠ Please enter an API key first.", text_color=STATE_ERROR)
            return

        if not key.startswith("gsk_"):
            self._api_status.configure(text="⚠ Key should start with 'gsk_'", text_color=STATE_ERROR)
            return

        self._api_status.configure(text="Testing connection...", text_color=TEXT_SECONDARY)
        self._test_btn.configure(state="disabled")

        def _do_test():
            from src.transcriber import test_connection
            success, msg = test_connection(key)
            if self._root:
                self._root.after(0, lambda: self._show_test_result(success, msg))

        threading.Thread(target=_do_test, daemon=True).start()

    def _show_test_result(self, success: bool, msg: str):
        color = STATE_DONE if success else STATE_ERROR
        icon = "✓" if success else "✗"
        if self._widget_valid("_api_status"):
            self._api_status.configure(text=f"{icon} {msg}", text_color=color)
        if self._widget_valid("_test_btn"):
            self._test_btn.configure(state="normal")


    def _build_about_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "About & Updates", "ℹ️", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        badge_frame = ctk.CTkFrame(section, fg_color="transparent")
        badge_frame.pack(fill="x", padx=16, pady=(0, 8))

        StatusBadge(
            badge_frame,
            text=f"v{CURRENT_VERSION}",
            color=ACCENT,
            fonts=self._fonts,
        ).pack(side="left")

        self._update_status = ctk.CTkLabel(
            badge_frame,
            text="",
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
        )
        self._update_status.pack(side="left", padx=(12, 0))

        check_btn = ctk.CTkButton(
            section,
            text="Check for Updates",
            fg_color=BG_SURFACE,
            hover_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY,
            font=self._fonts["sm"],
            corner_radius=CORNER_RADIUS_SM,
            height=32,
            command=self._check_updates,
        )
        check_btn.pack(padx=16, pady=(0, 8), anchor="w")

        links_frame = ctk.CTkFrame(section, fg_color="transparent")
        links_frame.pack(fill="x", padx=16, pady=(0, 12))

        for text, url in [
            ("GitHub", "https://github.com/VIKAS-REREAL/REREAL-Spitit"),
            ("Groq Console", "https://console.groq.com"),
            ("Website", "https://vikas-rereal.github.io/REREAL-Spitit/"),
        ]:
            link = ctk.CTkLabel(
                links_frame,
                text=text,
                text_color=ACCENT,
                font=self._fonts["xs"],
                cursor="hand2",
            )
            link.pack(side="left", padx=(0, 16))
            link.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))

    def _check_updates(self):
        self._update_status.configure(text="Checking...", text_color=TEXT_SECONDARY)

        def _do_check():
            result = check_for_update()
            if self._root:
                self._root.after(0, lambda: self._show_update_result(result))

        threading.Thread(target=_do_check, daemon=True).start()

    def _show_update_result(self, result: dict):
        if not self._widget_valid("_update_status"):
            return
        if result["available"]:
            self._update_status.configure(
                text=f"New version v{result['version']} found! Starting auto-update...",
                text_color=ACCENT,
            )
            threading.Thread(target=self._download_and_install_update, args=(result,), daemon=True).start()
        else:
            self._update_status.configure(
                text="✓ You're on the latest version",
                text_color=STATE_DONE,
            )


    def _download_and_install_update(self, result: dict):
        import urllib.request
        import sys
        import os
        import subprocess
        import time
        from pathlib import Path

        try:
            exe_dir = Path(sys.executable).parent
            is_installed = (exe_dir / "unins000.exe").exists() or "Program Files" in str(exe_dir)
            is_frozen = getattr(sys, "frozen", False)
            
            if is_installed and is_frozen:
                download_url = result["setup_url"]
                filename = f"REREAL-Spitit-Setup-{result['version']}.exe"
            else:
                download_url = result["portable_url"]
                filename = "REREAL-Spitit-New.exe"

            if not download_url:
                download_url = result["setup_url"] or result["portable_url"]

            from src.config import get_config_dir
            download_dir = get_config_dir()
            dest_path = download_dir / filename

            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": "REREAL-Spitit-Updater"}
            )
            
            with urllib.request.urlopen(req) as response:
                total_size = int(response.info().get('Content-Length', 0))
                downloaded = 0
                block_size = 1024 * 64
                
                with open(dest_path, "wb") as f:
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            if self._root:
                                self._root.after(0, lambda p=percent: self._update_status.configure(
                                    text=f"Downloading update: {p}%...", text_color=ACCENT
                                ))
                            
            if self._root:
                self._root.after(0, lambda: self._update_status.configure(
                    text="Installing update...", text_color=STATE_DONE
                ))
            time.sleep(1)

            if is_installed and is_frozen:
                subprocess.Popen([str(dest_path)])
            else:
                current_exe = Path(sys.executable)
                bat_path = download_dir / "update_spitit.bat"
                target_exe = current_exe if is_frozen else exe_dir / "REREAL-Spitit.exe"
                
                bat_content = f"""@echo off
timeout /t 2 /nobreak > nul
move /y "{dest_path}" "{target_exe}"
start "" "{target_exe}"
del "%~f0"
"""
                with open(bat_path, "w", encoding="ascii") as f:
                    f.write(bat_content)
                
                subprocess.Popen([str(bat_path)], shell=True)

            if self._root:
                self._root.after(0, lambda: os._exit(0))

        except Exception as e:
            print(f"[Updater] Error during update download/install: {e}")

    # ── Tab 2: Dictation (Mode + Hotkeys + Language) ────────────────────────

    def _build_tab_dictation(self, parent):
        """Dictation Settings: Activation Mode + Custom Hotkeys + Language."""
        mode_section = GlassFrame(parent)
        mode_section.pack(fill="x", pady=(0, 12))

        SectionHeader(mode_section, "Activation Mode", "🎙️", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        mode_var = self._vars["mode"]
        RadioCard(
            mode_section,
            title="Hold to Talk",
            subtitle="Hold hotkey to record, release to transcribe",
            variable=mode_var,
            value="hold",
            fonts=self._fonts,
        ).pack(fill="x", padx=16, pady=(0, 6))

        RadioCard(
            mode_section,
            title="Toggle to Talk",
            subtitle="Press hotkey to start/stop recording",
            variable=mode_var,
            value="toggle",
            fonts=self._fonts,
        ).pack(fill="x", padx=16, pady=(0, 12))

        hk_section = GlassFrame(parent)
        hk_section.pack(fill="x", pady=(0, 12))

        SectionHeader(hk_section, "Custom Hotkeys", "⌨️", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        hold_frame = ctk.CTkFrame(hk_section, fg_color="transparent")
        hold_frame.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            hold_frame,
            text="Hold Hotkey:",
            text_color=TEXT_SECONDARY,
            font=self._fonts["sm"],
        ).pack(side="left", padx=(0, 8))

        self._hold_hk_btn = HotkeyButton(
            hold_frame,
            combo_text=format_combo(self._vars["hold_hotkey"].get()),
            fonts=self._fonts,
            command=lambda: self._record_hotkey("hold"),
        )
        self._hold_hk_btn.pack(side="right", fill="x", expand=True)

        toggle_frame = ctk.CTkFrame(hk_section, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=16, pady=(0, 6))

        ctk.CTkLabel(
            toggle_frame,
            text="Toggle Hotkey:",
            text_color=TEXT_SECONDARY,
            font=self._fonts["sm"],
        ).pack(side="left", padx=(0, 8))

        self._toggle_hk_btn = HotkeyButton(
            toggle_frame,
            combo_text=format_combo(self._vars["toggle_hotkey"].get()),
            fonts=self._fonts,
            command=lambda: self._record_hotkey("toggle"),
        )
        self._toggle_hk_btn.pack(side="right", fill="x", expand=True)

        self._hotkey_status = ctk.CTkLabel(
            hk_section,
            text="",
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
            anchor="w",
        )
        self._hotkey_status.pack(fill="x", padx=16, pady=(0, 12))

        lang_section = GlassFrame(parent)
        lang_section.pack(fill="x", pady=(0, 12))

        SectionHeader(lang_section, "Language", "🌐", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        lang_names = list(LANGUAGES.keys())
        self._lang_menu = ctk.CTkOptionMenu(
            lang_section,
            variable=self._vars["language"],
            values=lang_names,
            fg_color=BG_SURFACE,
            button_color=BG_ELEVATED,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_SURFACE,
            dropdown_hover_color=BG_ELEVATED,
            text_color=TEXT_PRIMARY,
            font=self._fonts["md"],
            dropdown_font=self._fonts["sm"],
            corner_radius=CORNER_RADIUS_SM,
            height=38,
        )
        self._lang_menu.pack(fill="x", padx=16, pady=(0, 12))

    def _record_hotkey(self, target: str):
        btn = self._hold_hk_btn if target == "hold" else self._toggle_hk_btn
        var_key = "hold_hotkey" if target == "hold" else "toggle_hotkey"
        btn.set_recording(True)

        def on_complete(combo):
            if self._root:
                self._root.after(0, lambda: self._hotkey_recorded(combo, target, btn, var_key))

        def on_update(display):
            if self._root:
                self._root.after(0, lambda: btn.configure(text=display))

        self._hotkey_recorder.start(on_complete=on_complete, on_update=on_update)

    def _hotkey_recorded(self, combo, target, btn, var_key):
        if combo is None:
            btn.set_combo(format_combo(self._vars[var_key].get()))
            self._hotkey_status.configure(text="Cancelled.", text_color=TEXT_MUTED)
            return

        valid, msg = validate_combo(combo)
        if not valid:
            btn.set_combo(format_combo(self._vars[var_key].get()))
            self._hotkey_status.configure(text=f"✗ {msg}", text_color=STATE_ERROR)
            return

        other_key = "toggle_hotkey" if target == "hold" else "hold_hotkey"
        if combo == self._vars[other_key].get():
            btn.set_combo(format_combo(self._vars[var_key].get()))
            self._hotkey_status.configure(
                text="✗ Hold and Toggle hotkeys must be different.",
                text_color=STATE_ERROR,
            )
            return

        self._vars[var_key].set(combo)
        btn.set_combo(format_combo(combo))

        status_text = f"✓ Set to {format_combo(combo)}"
        if msg:
            status_text += f"  ({msg})"
        self._hotkey_status.configure(text=status_text, text_color=STATE_DONE)

    # ── Tab 3: Microphone (Device + Silence Slider + Live RMS Meter) ───────

    def _build_tab_microphone(self, parent):
        """Microphone Settings: Picker + Silence Slider + Live RMS Audio Level Meter."""
        mic_section = GlassFrame(parent)
        mic_section.pack(fill="x", pady=(0, 12))

        header_row = ctk.CTkFrame(mic_section, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(12, 8))

        SectionHeader(header_row, "Microphone Input", "🎤", fonts=self._fonts).pack(side="left")

        refresh_btn = ctk.CTkButton(
            header_row,
            text="↻ Refresh",
            width=80,
            height=28,
            fg_color=BG_SURFACE,
            hover_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
            corner_radius=CORNER_RADIUS_SM,
            command=self._refresh_mics,
        )
        refresh_btn.pack(side="right")

        self._mic_devices = []
        self._mic_menu = ctk.CTkOptionMenu(
            mic_section,
            variable=self._vars["mic_device"],
            values=["System Default"],
            fg_color=BG_SURFACE,
            button_color=BG_ELEVATED,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=BG_SURFACE,
            dropdown_hover_color=BG_ELEVATED,
            text_color=TEXT_PRIMARY,
            font=self._fonts["sm"],
            dropdown_font=self._fonts["xs"],
            corner_radius=CORNER_RADIUS_SM,
            height=38,
        )
        self._mic_menu.pack(fill="x", padx=16, pady=(0, 12))

        self._refresh_mics()

        thresh_section = GlassFrame(parent)
        thresh_section.pack(fill="x", pady=(0, 12))

        SectionHeader(thresh_section, "Silence Filtering", "🎚️", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        thresh_frame = ctk.CTkFrame(thresh_section, fg_color="transparent")
        thresh_frame.pack(fill="x", padx=16, pady=(0, 12))

        thresh_val = self._vars["silence_threshold"]
        self._thresh_label = ctk.CTkLabel(
            thresh_frame,
            text=f"Ignore silence below volume: {thresh_val.get():.3f}",
            text_color=TEXT_SECONDARY,
            font=self._fonts["sm"],
            anchor="w",
        )
        self._thresh_label.pack(fill="x")

        slider = ctk.CTkSlider(
            thresh_frame,
            from_=0.001,
            to=0.05,
            variable=thresh_val,
            progress_color=ACCENT,
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            fg_color=BG_SURFACE,
            command=self._on_threshold_change,
        )
        slider.pack(fill="x", pady=(4, 0))

        meter_section = GlassFrame(parent)
        meter_section.pack(fill="x", pady=(0, 12))

        meter_header = ctk.CTkFrame(meter_section, fg_color="transparent")
        meter_header.pack(fill="x", padx=16, pady=(12, 8))

        SectionHeader(meter_header, "Live Mic Meter", "📊", fonts=self._fonts).pack(side="left")

        self._test_mic_btn = ctk.CTkButton(
            meter_header,
            text="Start Test",
            width=90,
            height=28,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            font=self._fonts["xs"],
            corner_radius=CORNER_RADIUS_SM,
            command=self._toggle_mic_meter,
        )
        self._test_mic_btn.pack(side="right")

        meter_box = ctk.CTkFrame(meter_section, fg_color="transparent")
        meter_box.pack(fill="x", padx=16, pady=(0, 12))

        self._mic_level_lbl = ctk.CTkLabel(
            meter_box,
            text="Click 'Start Test' to check microphone input level",
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
            anchor="w",
        )
        self._mic_level_lbl.pack(fill="x", pady=(0, 4))

        self._mic_level_bar = ctk.CTkProgressBar(
            meter_box,
            height=10,
            corner_radius=5,
            progress_color=ACCENT,
            fg_color=BG_SURFACE,
        )
        self._mic_level_bar.pack(fill="x")
        self._mic_level_bar.set(0.0)

    def _on_threshold_change(self, value):
        if self._widget_valid("_thresh_label"):
            self._thresh_label.configure(text=f"Ignore silence below volume: {value:.3f}")


    def _refresh_mics(self):
        try:
            from src.recorder import Recorder
            devices = Recorder.list_devices()
            self._mic_devices = devices
            names = ["System Default"] + [
                f"{d['name']} ({d['sample_rate']}Hz)" for d in devices
            ]
            self._mic_menu.configure(values=names)

            current_idx = self._config.get("mic_device_index")
            if current_idx is not None:
                for d in devices:
                    if d["index"] == current_idx:
                        self._vars["mic_device"].set(
                            f"{d['name']} ({d['sample_rate']}Hz)"
                        )
                        break
        except Exception:
            self._mic_menu.configure(values=["System Default (no devices found)"])

    def _toggle_mic_meter(self):
        if self._mic_meter_running:
            self._stop_mic_meter()
        else:
            self._start_mic_meter()

    def _start_mic_meter(self):
        import sounddevice as sd
        if self._mic_meter_running:
            return

        self._mic_meter_running = True
        if hasattr(self, "_test_mic_btn") and self._test_mic_btn.winfo_exists():
            self._test_mic_btn.configure(text="Stop Test", fg_color=STATE_ERROR, hover_color="#d32f2f", text_color="#ffffff")

        device_idx = None
        mic_name = self._vars["mic_device"].get()
        if not (mic_name == "System Default" or mic_name.startswith("System Default")):
            for d in getattr(self, "_mic_devices", []):
                if f"{d['name']} ({d['sample_rate']}Hz)" == mic_name:
                    device_idx = d["index"]
                    break

        def callback(indata, frames, time_info, status):
            if not self._mic_meter_running:
                return
            rms = float(np.sqrt(np.mean(indata ** 2)))
            level = min(rms * 15.0, 1.0)
            if self._root:
                self._root.after(0, lambda l=level, r=rms: self._update_meter_ui(l, r))

        try:
            self._mic_stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype="float32",
                blocksize=1024,
                device=device_idx,
                callback=callback,
            )
            self._mic_stream.start()
            if self._widget_valid("_mic_level_lbl"):
                self._mic_level_lbl.configure(text="Listening... Speak into your microphone", text_color=ACCENT)
        except Exception as e:
            self._stop_mic_meter()
            if self._widget_valid("_mic_level_lbl"):
                self._mic_level_lbl.configure(text=f"⚠ Mic test error: {e}", text_color=STATE_ERROR)

    def _update_meter_ui(self, level: float, rms: float):
        if not self._mic_meter_running:
            return
        if self._widget_valid("_mic_level_bar"):
            self._mic_level_bar.set(level)
            thresh = self._vars["silence_threshold"].get()
            color = STATE_DONE if rms >= thresh else ACCENT
            self._mic_level_bar.configure(progress_color=color)

    def _stop_mic_meter(self):
        self._mic_meter_running = False
        if self._mic_stream:
            try:
                self._mic_stream.stop()
                self._mic_stream.close()
            except Exception:
                pass
            self._mic_stream = None

        if self._widget_valid("_test_mic_btn"):
            try:
                self._test_mic_btn.configure(text="Start Test", fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color=TEXT_ON_ACCENT)
            except Exception:
                pass
        if self._widget_valid("_mic_level_lbl"):
            try:
                self._mic_level_lbl.configure(text="Click 'Start Test' to check microphone input level", text_color=TEXT_MUTED)
            except Exception:
                pass
        if self._widget_valid("_mic_level_bar"):
            try:
                self._mic_level_bar.set(0.0)
            except Exception:
                pass


    # ── Tab 4: Output (4 Toggles) ───────────────────────────────────────────

    def _build_tab_output(self, parent):
        """Output Settings: 4 Toggles."""
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "Output Options", "📋", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        toggles = [
            ("Auto-paste", "Types into active text field automatically", self._vars["output_paste"]),
            ("Copy to clipboard", "Always copies transcription to clipboard", self._vars["output_clipboard"]),
            ("Desktop notification", "Shows Windows toast notification", self._vars["output_notification"]),
            ("Sound feedback", "Plays subtle done sound after transcription", self._vars["output_sound"]),
        ]

        for label, desc, var in toggles:
            ToggleSwitch(
                section, label=label, description=desc, variable=var, fonts=self._fonts
            ).pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkFrame(section, fg_color="transparent", height=4).pack()

    # ── Tab 5: History (History List + Safe Clear All Popover) ─────────────

    def _build_tab_history(self, parent):
        """History Settings: History List with safe Clear All confirmation popover."""
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        header_row = ctk.CTkFrame(section, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(12, 8))

        SectionHeader(header_row, "Transcription History", "📜", fonts=self._fonts).pack(side="left")

        ctrl_frame = ctk.CTkFrame(header_row, fg_color="transparent")
        ctrl_frame.pack(side="right")

        ctk.CTkSwitch(
            ctrl_frame,
            text="",
            variable=self._vars["history_enabled"],
            onvalue=True,
            offvalue=False,
            progress_color=ACCENT,
            button_color=TEXT_PRIMARY,
            width=40,
        ).pack(side="left", padx=(0, 8))

        clear_btn = ctk.CTkButton(
            ctrl_frame,
            text="Clear All",
            width=70,
            height=26,
            fg_color=BG_SURFACE,
            hover_color=STATE_ERROR,
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
            corner_radius=CORNER_RADIUS_SM,
            command=self._confirm_clear_history,
        )
        clear_btn.pack(side="left")

        self._history_frame = ctk.CTkFrame(section, fg_color="transparent")
        self._history_frame.pack(fill="x", padx=16, pady=(0, 12))
        self._render_history()

    def _render_history(self):
        if not hasattr(self, "_history_frame") or not self._history_frame.winfo_exists():
            return

        for child in self._history_frame.winfo_children():
            child.destroy()

        history = self._config.get("history", [])
        if not history:
            ctk.CTkLabel(
                self._history_frame,
                text="No transcriptions yet.",
                text_color=TEXT_MUTED,
                font=self._fonts["xs"],
            ).pack(pady=8)
            return

        for i, entry in enumerate(history[:20]):
            self._build_history_row(self._history_frame, entry, i)

    def _build_history_row(self, parent, entry: dict, index: int):
        row = ctk.CTkFrame(
            parent,
            fg_color=BG_SURFACE if index % 2 == 0 else "transparent",
            corner_radius=CORNER_RADIUS_SM,
            height=36,
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        ts = entry.get("ts", "")[:16].replace("T", " ")
        ctk.CTkLabel(
            row,
            text=ts,
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
            width=110,
        ).pack(side="left", padx=(8, 4))

        text = entry.get("text", "")
        truncated = text[:40] + ("…" if len(text) > 40 else "")
        text_label = ctk.CTkLabel(
            row,
            text=truncated,
            text_color=TEXT_PRIMARY,
            font=self._fonts["xs"],
            anchor="w",
        )
        text_label.pack(side="left", fill="x", expand=True, padx=4)

        text_label.bind("<Button-1>", lambda e, t=text: self._show_full_text(t))
        text_label.configure(cursor="hand2")

        words = entry.get("words", 0)
        ctk.CTkLabel(
            row,
            text=f"{words}w",
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
            width=30,
        ).pack(side="left", padx=4)

        copy_btn = ctk.CTkButton(
            row,
            text="📋",
            width=30,
            height=24,
            fg_color="transparent",
            hover_color=BG_ELEVATED,
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
            command=lambda t=text: self._copy_history_text(t),
        )
        copy_btn.pack(side="right", padx=4)

    def _show_full_text(self, text: str):
        popup = ctk.CTkToplevel(self._win)
        popup.title("Full Transcription")
        popup.geometry("400x250")
        popup.configure(fg_color=BG_BASE)
        popup.resizable(True, True)
        set_window_icon(popup)

        textbox = ctk.CTkTextbox(
            popup,
            fg_color=BG_SURFACE,
            text_color=TEXT_PRIMARY,
            font=self._fonts["md"],
            wrap="word",
            corner_radius=CORNER_RADIUS_SM,
        )
        textbox.pack(fill="both", expand=True, padx=12, pady=12)
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")

        popup.focus_force()

    def _copy_history_text(self, text: str):
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            pass

    def _confirm_clear_history(self):
        """Show confirmation popover modal before wiping history."""
        popover = ctk.CTkToplevel(self._win)
        popover.title("Confirm Clear History")
        popover.geometry("340x160")
        popover.configure(fg_color=BG_BASE)
        popover.resizable(False, False)
        set_window_icon(popover)

        msg = ctk.CTkLabel(
            popover,
            text="Are you sure you want to clear all history?\nThis action cannot be undone.",
            text_color=TEXT_PRIMARY,
            font=self._fonts["sm"],
            justify="center",
        )
        msg.pack(pady=(20, 16), padx=16)

        btn_frame = ctk.CTkFrame(popover, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        cancel_btn = GhostButton(
            btn_frame,
            text="Cancel",
            font=self._fonts["sm"],
            width=120,
            command=popover.destroy,
        )
        cancel_btn.pack(side="left", padx=(0, 8), expand=True)

        confirm_btn = AccentButton(
            btn_frame,
            text="Clear All",
            fg_color=STATE_ERROR,
            hover_color="#d32f2f",
            text_color="#ffffff",
            font=self._fonts["sm"],
            width=120,
            command=lambda: (self._clear_history(), popover.destroy()),
        )
        confirm_btn.pack(side="right", expand=True)

        popover.focus_force()

    def _clear_history(self):
        self._config["history"] = []
        self._render_history()

    # ── Footer ──────────────────────────────────────────────────────────────

    def _build_footer(self):
        """Build persistent bottom save footer with dirty indicator."""
        footer = ctk.CTkFrame(self._win, fg_color=BG_SURFACE, height=58, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        hint_frame = ctk.CTkFrame(footer, fg_color="transparent")
        hint_frame.pack(side="left", padx=16)

        self._dirty_dot = ctk.CTkLabel(
            hint_frame,
            text="Changes are applied on save",
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
        )
        self._dirty_dot.pack(side="left")

        save_btn = AccentButton(
            footer,
            text="SAVE SETTINGS",
            font=self._fonts["md_b"],
            height=38,
            width=150,
            command=self._save,
        )
        save_btn.pack(side="right", padx=16, pady=10)

    def _save(self):
        """Save all settings to config."""
        cfg = self._config

        cfg["api_key"] = self._vars["api_key"].get().strip()
        cfg["mode"] = self._vars["mode"].get()
        cfg["hold_hotkey"] = self._vars["hold_hotkey"].get()
        cfg["toggle_hotkey"] = self._vars["toggle_hotkey"].get()
        cfg["language"] = self._get_language_code(self._vars["language"].get())
        cfg["output_paste"] = self._vars["output_paste"].get()
        cfg["output_clipboard"] = self._vars["output_clipboard"].get()
        cfg["output_notification"] = self._vars["output_notification"].get()
        cfg["output_sound"] = self._vars["output_sound"].get()
        cfg["history_enabled"] = self._vars["history_enabled"].get()
        cfg["silence_threshold"] = round(self._vars["silence_threshold"].get(), 4)
        cfg["first_run"] = False

        mic_name = self._vars["mic_device"].get()
        if mic_name == "System Default" or mic_name.startswith("System Default"):
            cfg["mic_device_index"] = None
        else:
            for d in getattr(self, "_mic_devices", []):
                display = f"{d['name']} ({d['sample_rate']}Hz)"
                if display == mic_name:
                    cfg["mic_device_index"] = d["index"]
                    break

        new_startup = self._vars["launch_on_startup"].get()
        if new_startup != cfg.get("launch_on_startup", False):
            from src.config import set_launch_on_startup
            set_launch_on_startup(new_startup)
        cfg["launch_on_startup"] = new_startup

        from src.config import save_config
        save_config(cfg)

        self._stop_mic_meter()

        if self._on_save:
            self._on_save(cfg)

        if self._win:
            self._win.destroy()
            self._win = None

    def close(self):
        """Close the settings window and stop active streams."""
        self._stop_mic_meter()
        if hasattr(self, "_hotkey_recorder") and self._hotkey_recorder and self._hotkey_recorder.is_recording:
            self._hotkey_recorder.cancel()

        win = self._win
        self._win = None

        if win and win.winfo_exists():
            try:
                win.destroy()
            except Exception:
                pass

        if hasattr(self, "_on_close") and self._on_close:
            try:
                self._on_close()
            except Exception:
                pass

