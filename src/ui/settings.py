"""
REREAL - Spitit: Settings window.
Full settings UI with all 9 sections as specified.
"""

import threading
import webbrowser
import customtkinter as ctk
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
)
from src.transcriber import LANGUAGES
from src.hotkey import format_combo, validate_combo, HotkeyRecorder
from src.updater import check_for_update, CURRENT_VERSION


class SettingsWindow:
    """
    Main settings window for REREAL - Spitit.
    Size: 520×720, resizable vertically only.
    """

    def __init__(self, root, config: dict, fonts: dict, on_save=None):
        self._root = root
        self._config = config
        self._fonts = fonts
        self._on_save = on_save
        self._win = None
        self._hotkey_recorder = HotkeyRecorder()
        self._vars = {}

    def show(self, highlight_api_key: bool = False):
        """Open the settings window."""
        if self._win and self._win.winfo_exists():
            self._win.focus_force()
            return

        self._win = ctk.CTkToplevel(self._root)
        self._win.title("REREAL · Spitit — Settings")
        self._win.geometry(f"{SETTINGS_WIDTH}x{SETTINGS_HEIGHT}")
        self._win.minsize(SETTINGS_WIDTH, 500)
        self._win.maxsize(SETTINGS_WIDTH, 1200)
        self._win.configure(fg_color=BG_BASE)
        self._win.resizable(False, True)

        # Try to set icon
        try:
            from src.config import get_asset_path
            ico_path = get_asset_path("icon.ico")
            if ico_path.exists():
                self._win.iconbitmap(str(ico_path))
        except Exception:
            pass

        # Initialize variables from config
        self._init_vars()

        # Main scrollable container
        container = ctk.CTkScrollableFrame(
            self._win,
            fg_color=BG_BASE,
            scrollbar_button_color=BG_ELEVATED,
            scrollbar_button_hover_color=ACCENT,
        )
        container.pack(fill="both", expand=True, padx=16, pady=(8, 0))

        # ── Header ──
        self._build_header(container)

        # ── First run banner ──
        if highlight_api_key:
            self._build_first_run_banner(container)

        # ── Section 1: API Key ──
        self._build_api_key_section(container)

        # ── Section 2: Activation Mode ──
        self._build_mode_section(container)

        # ── Section 3: Custom Hotkeys ──
        self._build_hotkeys_section(container)

        # ── Section 4: Language ──
        self._build_language_section(container)

        # ── Section 5: Microphone ──
        self._build_mic_section(container)

        # ── Section 6: Output Options ──
        self._build_output_section(container)

        # ── Section 7: History ──
        self._build_history_section(container)

        # ── Section 8: Appearance ──
        self._build_appearance_section(container)

        # ── Section 9: About / Update ──
        self._build_about_section(container)

        # ── Footer ──
        self._build_footer()

        self._win.focus_force()

    def _init_vars(self):
        """Create tkinter variables from config."""
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

    def _get_language_display(self, code: str) -> str:
        """Convert language code to display name."""
        from src.transcriber import LANGUAGE_NAMES
        return LANGUAGE_NAMES.get(code, "English")

    def _get_language_code(self, display: str) -> str:
        """Convert display name to language code."""
        return LANGUAGES.get(display, "en")

    # ── Header ──────────────────────────────────────────────────────────────

    def _build_header(self, parent):
        """Build the settings header with logo and title."""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(8, 16))

        title = ctk.CTkLabel(
            header,
            text="REREAL · Spitit",
            text_color=ACCENT,
            font=self._fonts["xl"],
        )
        title.pack()

        subtitle = ctk.CTkLabel(
            header,
            text="Settings",
            text_color=TEXT_SECONDARY,
            font=self._fonts["md"],
        )
        subtitle.pack()

    def _build_first_run_banner(self, parent):
        """Show first-run banner prompting API key entry."""
        banner = ctk.CTkFrame(
            parent,
            fg_color=ACCENT_DIM,
            border_color=ACCENT,
            border_width=1,
            corner_radius=CORNER_RADIUS_SM,
        )
        banner.pack(fill="x", pady=(0, 12))

        label = ctk.CTkLabel(
            banner,
            text="⚡  Add your Groq API key to get started →",
            text_color=ACCENT,
            font=self._fonts["md_b"],
        )
        label.pack(padx=16, pady=12)

    # ── Section 1: API Key ──────────────────────────────────────────────────

    def _build_api_key_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "Groq API Key", "🔑", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        # Key entry row
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

        # Eye toggle
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

        # Test button
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

        # Status label
        self._api_status = ctk.CTkLabel(
            section,
            text="",
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
            anchor="w",
        )
        self._api_status.pack(fill="x", padx=16, pady=(0, 4))

        # Helper link
        link = ctk.CTkLabel(
            section,
            text="Get your free key at console.groq.com",
            text_color=ACCENT,
            font=self._fonts["xs"],
            cursor="hand2",
        )
        link.pack(padx=16, pady=(0, 12), anchor="w")
        link.bind("<Button-1>", lambda e: webbrowser.open("https://console.groq.com"))

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
            self._root.after(0, lambda: self._show_test_result(success, msg))

        threading.Thread(target=_do_test, daemon=True).start()

    def _show_test_result(self, success: bool, msg: str):
        color = STATE_DONE if success else STATE_ERROR
        icon = "✓" if success else "✗"
        self._api_status.configure(text=f"{icon} {msg}", text_color=color)
        self._test_btn.configure(state="normal")

    # ── Section 2: Activation Mode ──────────────────────────────────────────

    def _build_mode_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "Activation Mode", "🎙️", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        mode_var = self._vars["mode"]

        RadioCard(
            section,
            title="Hold to Talk",
            subtitle="Hold hotkey to record, release to transcribe",
            variable=mode_var,
            value="hold",
            fonts=self._fonts,
        ).pack(fill="x", padx=16, pady=(0, 6))

        RadioCard(
            section,
            title="Toggle to Talk",
            subtitle="Press hotkey to start/stop recording",
            variable=mode_var,
            value="toggle",
            fonts=self._fonts,
        ).pack(fill="x", padx=16, pady=(0, 12))

    # ── Section 3: Custom Hotkeys ───────────────────────────────────────────

    def _build_hotkeys_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "Custom Hotkeys", "⌨️", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        # Hold hotkey
        hold_frame = ctk.CTkFrame(section, fg_color="transparent")
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

        # Toggle hotkey
        toggle_frame = ctk.CTkFrame(section, fg_color="transparent")
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

        # Validation label
        self._hotkey_status = ctk.CTkLabel(
            section,
            text="",
            text_color=TEXT_SECONDARY,
            font=self._fonts["xs"],
            anchor="w",
        )
        self._hotkey_status.pack(fill="x", padx=16, pady=(0, 12))

    def _record_hotkey(self, target: str):
        """Start recording a hotkey combo."""
        btn = self._hold_hk_btn if target == "hold" else self._toggle_hk_btn
        var_key = "hold_hotkey" if target == "hold" else "toggle_hotkey"
        btn.set_recording(True)

        def on_complete(combo):
            self._root.after(0, lambda: self._hotkey_recorded(combo, target, btn, var_key))

        def on_update(display):
            self._root.after(0, lambda: btn.configure(text=display))

        self._hotkey_recorder.start(on_complete=on_complete, on_update=on_update)

    def _hotkey_recorded(self, combo, target, btn, var_key):
        if combo is None:
            # Cancelled
            btn.set_combo(format_combo(self._vars[var_key].get()))
            self._hotkey_status.configure(text="Cancelled.", text_color=TEXT_MUTED)
            return

        valid, msg = validate_combo(combo)
        if not valid:
            btn.set_combo(format_combo(self._vars[var_key].get()))
            self._hotkey_status.configure(text=f"✗ {msg}", text_color=STATE_ERROR)
            return

        # Check if same as the other hotkey
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
        if msg:  # warning
            status_text += f"  ({msg})"
        self._hotkey_status.configure(text=status_text, text_color=STATE_DONE)

    # ── Section 4: Language ─────────────────────────────────────────────────

    def _build_language_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "Language", "🌐", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        lang_names = list(LANGUAGES.keys())
        self._lang_menu = ctk.CTkOptionMenu(
            section,
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

    # ── Section 5: Microphone ───────────────────────────────────────────────

    def _build_mic_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        header_row = ctk.CTkFrame(section, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(12, 8))

        SectionHeader(header_row, "Microphone", "🎤", fonts=self._fonts).pack(side="left")

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
            section,
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

    def _refresh_mics(self):
        """Refresh the list of available microphone devices."""
        try:
            from src.recorder import Recorder
            devices = Recorder.list_devices()
            self._mic_devices = devices
            names = ["System Default"] + [
                f"{d['name']} ({d['sample_rate']}Hz)" for d in devices
            ]
            self._mic_menu.configure(values=names)

            # Select current device
            current_idx = self._config.get("mic_device_index")
            if current_idx is not None:
                for d in devices:
                    if d["index"] == current_idx:
                        self._vars["mic_device"].set(
                            f"{d['name']} ({d['sample_rate']}Hz)"
                        )
                        break
        except Exception as e:
            self._mic_menu.configure(values=["System Default (no devices found)"])

    # ── Section 6: Output Options ───────────────────────────────────────────

    def _build_output_section(self, parent):
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

        # Bottom spacer
        ctk.CTkFrame(section, fg_color="transparent", height=4).pack()

    # ── Section 7: History ──────────────────────────────────────────────────

    def _build_history_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        header_row = ctk.CTkFrame(section, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(12, 8))

        SectionHeader(header_row, "History", "📜", fonts=self._fonts).pack(side="left")

        # Enable/disable toggle + clear button
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
            command=self._clear_history,
        )
        clear_btn.pack(side="left")

        # History list
        self._history_frame = ctk.CTkFrame(section, fg_color="transparent")
        self._history_frame.pack(fill="x", padx=16, pady=(0, 12))
        self._render_history()

    def _render_history(self):
        """Render the history entries."""
        # Clear existing
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

        for i, entry in enumerate(history[:20]):  # Show max 20 in UI
            self._build_history_row(self._history_frame, entry, i)

    def _build_history_row(self, parent, entry: dict, index: int):
        """Build a single history row."""
        row = ctk.CTkFrame(
            parent,
            fg_color=BG_SURFACE if index % 2 == 0 else "transparent",
            corner_radius=CORNER_RADIUS_SM,
            height=36,
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Timestamp
        ts = entry.get("ts", "")[:16].replace("T", " ")
        ctk.CTkLabel(
            row,
            text=ts,
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
            width=110,
        ).pack(side="left", padx=(8, 4))

        # Text (truncated)
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

        # Click to show full text
        text_label.bind("<Button-1>", lambda e, t=text: self._show_full_text(t))
        text_label.configure(cursor="hand2")

        # Word count
        words = entry.get("words", 0)
        ctk.CTkLabel(
            row,
            text=f"{words}w",
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
            width=30,
        ).pack(side="left", padx=4)

        # Copy button
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
        """Show full transcription text in a popup."""
        popup = ctk.CTkToplevel(self._win)
        popup.title("Full Transcription")
        popup.geometry("400x250")
        popup.configure(fg_color=BG_BASE)
        popup.resizable(True, True)

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
        """Copy history text to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(text)
        except Exception:
            pass

    def _clear_history(self):
        """Clear all history entries."""
        self._config["history"] = []
        self._render_history()

    # ── Section 8: Appearance ───────────────────────────────────────────────

    def _build_appearance_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "Appearance", "🎨", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        # Silence threshold slider
        thresh_frame = ctk.CTkFrame(section, fg_color="transparent")
        thresh_frame.pack(fill="x", padx=16, pady=(0, 8))

        thresh_val = self._vars["silence_threshold"]
        self._thresh_label = ctk.CTkLabel(
            thresh_frame,
            text=f"Ignore silence below: {thresh_val.get():.3f}",
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

        # Launch on startup
        ToggleSwitch(
            section,
            label="Launch on Windows startup",
            description="Start REREAL - Spitit when Windows boots",
            variable=self._vars["launch_on_startup"],
            fonts=self._fonts,
        ).pack(fill="x", padx=16, pady=(0, 12))

    def _on_threshold_change(self, value):
        self._thresh_label.configure(text=f"Ignore silence below: {value:.3f}")

    # ── Section 9: About / Update ───────────────────────────────────────────

    def _build_about_section(self, parent):
        section = GlassFrame(parent)
        section.pack(fill="x", pady=(0, 12))

        SectionHeader(section, "About", "ℹ️", fonts=self._fonts).pack(
            fill="x", padx=16, pady=(12, 8)
        )

        # Version badge
        badge_frame = ctk.CTkFrame(section, fg_color="transparent")
        badge_frame.pack(fill="x", padx=16, pady=(0, 8))

        StatusBadge(
            badge_frame,
            text=f"v{CURRENT_VERSION}",
            color=ACCENT,
            fonts=self._fonts,
        ).pack(side="left")

        # Update checker
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

        # Links
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
            self._root.after(0, lambda: self._show_update_result(result))

        threading.Thread(target=_do_check, daemon=True).start()

    def _show_update_result(self, result: dict):
        if result["available"]:
            self._update_status.configure(
                text=f"Update available: v{result['version']}",
                text_color=ACCENT,
            )
            # Could add download button here
        else:
            self._update_status.configure(
                text="✓ You're on the latest version",
                text_color=STATE_DONE,
            )

    # ── Footer ──────────────────────────────────────────────────────────────

    def _build_footer(self):
        """Build the save button footer."""
        footer = ctk.CTkFrame(self._win, fg_color=BG_BASE, height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        hint = ctk.CTkLabel(
            footer,
            text="Changes are applied on save",
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
        )
        hint.pack(side="left", padx=16)

        save_btn = AccentButton(
            footer,
            text="SAVE SETTINGS",
            font=self._fonts["md_b"],
            height=40,
            width=160,
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

        # Mic device
        mic_name = self._vars["mic_device"].get()
        if mic_name == "System Default" or mic_name.startswith("System Default"):
            cfg["mic_device_index"] = None
        else:
            for d in self._mic_devices:
                display = f"{d['name']} ({d['sample_rate']}Hz)"
                if display == mic_name:
                    cfg["mic_device_index"] = d["index"]
                    break

        # Launch on startup
        new_startup = self._vars["launch_on_startup"].get()
        if new_startup != cfg.get("launch_on_startup", False):
            from src.config import set_launch_on_startup
            set_launch_on_startup(new_startup)
        cfg["launch_on_startup"] = new_startup

        # Save to disk
        from src.config import save_config
        save_config(cfg)

        # Notify parent
        if self._on_save:
            self._on_save(cfg)

        # Close window
        if self._win:
            self._win.destroy()
            self._win = None

    def close(self):
        """Close the settings window."""
        if self._hotkey_recorder.is_recording:
            self._hotkey_recorder.cancel()
        if self._win:
            self._win.destroy()
            self._win = None
