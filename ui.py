"""CustomTkinter: floating status pill and settings window with a fully customized, premium UI/UX."""

from __future__ import annotations

import math
import tkinter as tk
from typing import Any, Callable, Literal

import customtkinter as ctk
from PIL import Image

from tray import ensure_icon_png

State = Literal["hidden", "recording", "transcribing", "done", "error"]

BG = "#131313"
CARD_BG = "#202020"
ACCENT = "#FFD505"
TEXT_LIGHT = "#ffffff"
TEXT_DARK = "#000000"
DONE_GREEN = "#3ddc84"
ERROR_RED = "#ff6b6b"

_CHROMA_KEY = "#010203"
HOVER_YELLOW = "#c9ab00"
FONT_FAMILY = "Segoe UI"


def apply_titlebar_icon(window: tk.Misc, master: ctk.CTk) -> None:
    """Set OS title bar / taskbar icon from master's shared PhotoImage or assets PNG."""
    try:
        from PIL import Image, ImageTk

        if hasattr(master, "_spitit_icon"):
            window.iconphoto(True, master._spitit_icon)  # type: ignore
            return
        pil = Image.open(ensure_icon_png()).convert("RGBA")
        icon_img = ImageTk.PhotoImage(pil.resize((64, 64), Image.Resampling.LANCZOS))
        window._spitit_win_icon = icon_img  # type: ignore
        window.iconphoto(True, icon_img)  # type: ignore
    except Exception:
        pass


class StatusPill(tk.Toplevel):
    """Floating capsule pill with smooth animated wave visualiser for voice status."""

    _PILL_W = 160
    _PILL_H = 36

    def __init__(
        self,
        master: ctk.CTk,
        get_pill_position: Callable[[], Any],
        save_pill_position: Callable[[int, int], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._get_pill_position = get_pill_position
        self._save_pill_position = save_pill_position
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-toolwindow", True)
        except Exception:
            pass
        try:
            self.attributes("-alpha", 0.95)
        except Exception:
            pass

        self._chroma = _CHROMA_KEY
        self.configure(bg=self._chroma)
        try:
            self.wm_attributes("-transparentcolor", self._chroma)
        except Exception:
            pass

        self.resizable(False, False)
        self._state: State = "hidden"
        self._wave_phase = 0.0
        self._wave_active = False
        self._drag_dx = 0
        self._drag_dy = 0
        self._dragging = False

        self._hide_job = None
        self._wave_job = None

        self._canvas = tk.Canvas(
            self,
            width=self._PILL_W,
            height=self._PILL_H,
            highlightthickness=0,
            bd=0,
            bg=self._chroma,
        )
        self._canvas.pack(padx=0, pady=0)

        self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_motion)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self.configure(cursor="hand2")

        self.withdraw()

    # ── drag ──────────────────────────────────────────────────────
    def _on_drag_start(self, event: tk.Event) -> None:
        self._dragging = True
        self._drag_dx = event.x_root - self.winfo_rootx()
        self._drag_dy = event.y_root - self.winfo_rooty()

    def _on_drag_motion(self, event: tk.Event) -> None:
        if not self._dragging:
            return
        x = event.x_root - self._drag_dx
        y = event.y_root - self._drag_dy
        self.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event: tk.Event) -> None:
        if not self._dragging:
            return
        self._dragging = False
        if self._save_pill_position is not None:
            self._save_pill_position(self.winfo_rootx(), self.winfo_rooty())

    # ── positioning ───────────────────────────────────────────────
    def _place_bottom_right(self) -> None:
        w, h = self._PILL_W, self._PILL_H
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw - w - 20
        y = sh - h - 60
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _place_pill(self) -> None:
        w, h = self._PILL_W, self._PILL_H
        raw = self._get_pill_position()
        if raw is not None and isinstance(raw, (list, tuple)) and len(raw) == 2:
            try:
                x, y = int(raw[0]), int(raw[1])
                sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
                x = max(0, min(x, sw - w))
                y = max(0, min(y, sh - h))
                self.geometry(f"{w}x{h}+{x}+{y}")
                return
            except (TypeError, ValueError):
                pass
        self._place_bottom_right()

    # ── capsule drawing ───────────────────────────────────────────
    @staticmethod
    def _draw_capsule(canvas: tk.Canvas, w: int, h: int, fill: str,
                      outline: str | None = None) -> None:
        r = h // 2
        # left cap
        canvas.create_oval(0, 0, h, h, fill=fill, outline=fill)
        # right cap
        canvas.create_oval(w - h, 0, w, h, fill=fill, outline=fill)
        # centre bar
        canvas.create_rectangle(r, 0, w - r, h, fill=fill, outline=fill)
        # optional border
        if outline:
            canvas.create_oval(1, 1, h - 1, h - 1, outline=outline, width=1, fill="")
            canvas.create_oval(w - h + 1, 1, w - 1, h - 1, outline=outline, width=1, fill="")
            canvas.create_rectangle(r, 1, w - r, h - 1, outline="", fill="")
            canvas.create_line(r, 1, w - r, 1, fill=outline)
            canvas.create_line(r, h - 1, w - r, h - 1, fill=outline)

    # ── redraw helpers ────────────────────────────────────────────
    def _redraw(self) -> None:
        c = self._canvas
        w = c.winfo_width() or self._PILL_W
        h = c.winfo_height() or self._PILL_H
        c.delete("all")

        if self._state == "recording":
            self._draw_capsule(c, w, h, ACCENT)
            self._draw_animated_wave(c, w, h, "#1a1a1a")
        elif self._state == "transcribing":
            self._draw_capsule(c, w, h, "#1e1e1e", outline=ACCENT)
            self._draw_animated_wave(c, w, h, ACCENT)
        elif self._state == "done":
            self._draw_capsule(c, w, h, "#1e1e1e", outline=DONE_GREEN)
            self._draw_done_wave(c, w, h)
        elif self._state == "error":
            self._draw_capsule(c, w, h, "#1e1e1e", outline=ERROR_RED)
            self._draw_error_wave(c, w, h)

    def _draw_animated_wave(self, c: tk.Canvas, w: int, h: int,
                            color: str) -> None:
        n_points = 80
        inset_x = 14
        mid_y = h / 2.0
        amplitude = h * 0.32
        ph = self._wave_phase
        pts: list[float] = []
        for i in range(n_points + 1):
            t = i / n_points
            x = inset_x + t * (w - 2 * inset_x)
            y = mid_y + amplitude * (
                0.6 * math.sin(ph * 1.2 + t * math.pi * 4.0)
                + 0.4 * math.sin(-ph * 0.8 + t * math.pi * 7.0 + 1.2)
            )
            pts.extend([x, y])
        if len(pts) >= 4:
            c.create_line(
                *pts, fill=color, width=2, smooth=True,
                splinesteps=48, capstyle=tk.ROUND,
            )

    def _draw_done_wave(self, c: tk.Canvas, w: int, h: int) -> None:
        n = 80
        inset_x = 14
        mid_y = h / 2.0
        amplitude = h * 0.18
        pts: list[float] = []
        for i in range(n + 1):
            t = i / n
            x = inset_x + t * (w - 2 * inset_x)
            y = mid_y + amplitude * math.sin(t * math.pi * 2.5)
            pts.extend([x, y])
        if len(pts) >= 4:
            c.create_line(
                *pts, fill=DONE_GREEN, width=2, smooth=True,
                splinesteps=32,
            )

    def _draw_error_wave(self, c: tk.Canvas, w: int, h: int) -> None:
        n = 80
        inset_x = 14
        mid_y = h / 2.0
        amplitude = h * 0.28
        pts: list[float] = []
        for i in range(n + 1):
            t = i / n
            x = inset_x + t * (w - 2 * inset_x)
            y = mid_y + amplitude * (
                math.sin(t * math.pi * 6.0 + 1.0) * 0.7
                + math.sin(t * math.pi * 11.0) * 0.3
            )
            pts.extend([x, y])
        if len(pts) >= 4:
            c.create_line(
                *pts, fill=ERROR_RED, width=2, smooth=True,
                splinesteps=32,
            )

    # ── animation loop ────────────────────────────────────────────
    def _wave_tick(self) -> None:
        if not self._wave_active:
            return
        self._wave_phase += 0.15
        self._redraw()
        self._wave_job = self.after(33, self._wave_tick)

    def _cancel_timers(self) -> None:
        if self._wave_job is not None:
            try:
                self.after_cancel(self._wave_job)
            except Exception:
                pass
            self._wave_job = None
        self._wave_active = False
        if self._hide_job is not None:
            try:
                self.after_cancel(self._hide_job)
            except Exception:
                pass
            self._hide_job = None

    # ── public state methods ──────────────────────────────────────
    def show_hidden(self) -> None:
        self._cancel_timers()
        self._state = "hidden"
        self.withdraw()

    def show_recording(self) -> None:
        self._cancel_timers()
        self._state = "recording"
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._wave_active = True
        self._wave_phase = 0.0
        self._wave_tick()

    def show_transcribing(self) -> None:
        self._cancel_timers()
        self._state = "transcribing"
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._wave_active = True
        self._wave_phase = 0.0
        self._wave_tick()

    def show_done(self) -> None:
        self._cancel_timers()
        self._state = "done"
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._redraw()
        self._hide_job = self.after(900, self.show_hidden)

    def show_error(self, message: str) -> None:
        del message
        self._cancel_timers()
        self._state = "error"
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._redraw()
        self._hide_job = self.after(2800, self.show_hidden)

    def show_mode_notice(self, mode_label: str) -> None:
        del mode_label
        self._cancel_timers()
        self._state = "done"
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._redraw()
        self._hide_job = self.after(800, self.show_hidden)


class SettingsWindow(ctk.CTkToplevel):
    """Modern Settings Window with Group Cards, Eye-Visibility API toggles, and customized selectable Activation Mode cards."""

    def __init__(
        self,
        master: ctk.CTk,
        get_config: Callable[[], dict],
        on_save: Callable[[dict], None],
    ) -> None:
        super().__init__(master)
        self._get_config = get_config
        self._on_save = on_save
        self._master = master
        self.title("REREAL · Spitit — Settings")
        self.configure(fg_color=BG)
        self.minsize(440, 520)
        self.geometry("500x640")
        self.resizable(False, False)
        self.attributes("-topmost", False)
        try:
            self.transient(master)
        except Exception:
            pass

        apply_titlebar_icon(self, master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Block
        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(1, weight=1)

        pil = Image.open(ensure_icon_png()).convert("RGBA")
        pil_sm = pil.resize((44, 44), Image.Resampling.LANCZOS)
        self._logo = ctk.CTkImage(light_image=pil_sm, dark_image=pil_sm, size=(44, 44))

        ctk.CTkLabel(header, image=self._logo, text="").grid(row=0, column=0, padx=(0, 14))
        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            title_block,
            text="REREAL · Spitit",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_block,
            text="Voice to text — settings",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#a0a0a0",
            anchor="w",
        ).pack(anchor="w", pady=(1, 0))

        # Main Scrollable Frame containing Settings Cards
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color="#3d3d3d",
            scrollbar_button_hover_color=ACCENT,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 8))

        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.pack(fill="x", expand=True)
        body.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------
        # Card 1: Groq API Key
        # ----------------------------------------------------
        api_card = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=10)
        api_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        api_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            api_card,
            text="Groq API key",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))

        self._api_entry_frame = ctk.CTkFrame(api_card, fg_color="#2b2b2b", corner_radius=8, height=44)
        self._api_entry_frame.pack(fill="x", padx=16, pady=(0, 16))

        self._api = ctk.CTkEntry(
            self._api_entry_frame,
            height=44,
            fg_color="transparent",
            text_color=TEXT_LIGHT,
            border_width=0,
            corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            placeholder_text="Paste your Groq API key",
            show="*",
        )
        self._api.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self._api.configure(cursor="xterm")

        self._eye_visible = False
        self._eye_btn = ctk.CTkButton(
            self._api_entry_frame,
            text="👁",
            width=40,
            height=44,
            fg_color="transparent",
            hover=False,
            text_color="#888888",
            font=ctk.CTkFont(family=FONT_FAMILY, size=18),
            command=self._toggle_api_visibility,
            cursor="hand2",
        )
        self._eye_btn.pack(side="right", padx=(0, 6))

        # ----------------------------------------------------
        # Card 2: Activation Mode (Redesigned Selection Cards)
        # ----------------------------------------------------
        mode_card = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=10)
        mode_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        mode_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            mode_card,
            text="Activation mode",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))

        self._mode_var = ctk.StringVar(value="hold")

        # -- Option A: Hold to Talk Card --
        self._hold_card = ctk.CTkFrame(mode_card, fg_color=CARD_BG, border_color="#3d3d3d", border_width=1, corner_radius=8)
        self._hold_card.pack(fill="x", padx=16, pady=(0, 8))
        self._hold_card.grid_columnconfigure(0, weight=1)

        hold_txt_frame = ctk.CTkFrame(self._hold_card, fg_color="transparent")
        hold_txt_frame.grid(row=0, column=0, sticky="w", padx=14, pady=8)
        ctk.CTkLabel(
            hold_txt_frame,
            text="Hold to talk",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            hold_txt_frame,
            text="Alt + Left Shift",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#888888",
        ).pack(anchor="w", pady=(1, 0))

        self._hold_radio_canvas = tk.Canvas(self._hold_card, width=20, height=20, bg=CARD_BG, bd=0, highlightthickness=0, cursor="hand2")
        self._hold_radio_canvas.grid(row=0, column=1, padx=16, sticky="e")

        # -- Option B: Toggle to Talk Card --
        self._toggle_card = ctk.CTkFrame(mode_card, fg_color=CARD_BG, border_color="#3d3d3d", border_width=1, corner_radius=8)
        self._toggle_card.pack(fill="x", padx=16, pady=(0, 16))
        self._toggle_card.grid_columnconfigure(0, weight=1)

        toggle_txt_frame = ctk.CTkFrame(self._toggle_card, fg_color="transparent")
        toggle_txt_frame.grid(row=0, column=0, sticky="w", padx=14, pady=8)
        ctk.CTkLabel(
            toggle_txt_frame,
            text="Toggle to talk",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            toggle_txt_frame,
            text="Alt + Left Shift + Space",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#888888",
        ).pack(anchor="w", pady=(1, 0))

        self._toggle_radio_canvas = tk.Canvas(self._toggle_card, width=20, height=20, bg=CARD_BG, bd=0, highlightthickness=0, cursor="hand2")
        self._toggle_radio_canvas.grid(row=0, column=1, padx=16, sticky="e")

        # Bind select events
        self._bind_click_recursive(self._hold_card, lambda _e: self._set_mode("hold"))
        self._bind_click_recursive(self._toggle_card, lambda _e: self._set_mode("toggle"))

        # ----------------------------------------------------
        # Card 3: Language Card
        # ----------------------------------------------------
        lang_card = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=10)
        lang_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        lang_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            lang_card,
            text="Language (Whisper)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 6))

        langs = ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja", "ko", "zh", "auto"]
        self._lang = ctk.CTkOptionMenu(
            lang_card,
            values=langs,
            height=40,
            corner_radius=8,
            fg_color="#2b2b2b",
            button_color="#2b2b2b",
            button_hover_color="#3d3d3d",
            dropdown_fg_color="#232323",
            dropdown_hover_color="#3d3d3d",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_LIGHT,
            dynamic_resizing=True,
        )
        self._lang.pack(fill="x", padx=16, pady=(0, 16))
        self._lang.configure(cursor="hand2")

        # ----------------------------------------------------
        # Card 4: Launch on Startup Card
        # ----------------------------------------------------
        startup_card = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=10)
        startup_card.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        startup_card.grid_columnconfigure(0, weight=1)

        self._startup = ctk.CTkCheckBox(
            startup_card,
            text="Launch on Windows startup",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
            fg_color=ACCENT,
            hover_color=HOVER_YELLOW,
            checkmark_color=TEXT_DARK,
            cursor="hand2",
        )
        self._startup.pack(fill="x", padx=16, pady=16)

        # Footer Button
        footer = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(8, 20))
        footer.grid_columnconfigure(0, weight=1)

        self._save_hint = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=DONE_GREEN,
            anchor="w",
        )
        self._save_hint.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._save_btn = ctk.CTkButton(
            footer,
            text="SAVE SETTINGS",
            height=46,
            corner_radius=23,
            fg_color=ACCENT,
            hover_color=HOVER_YELLOW,
            text_color=TEXT_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            command=self._save_clicked,
            cursor="hand2",
        )
        self._save_btn.grid(row=1, column=0, sticky="ew")

        self._load_fields()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _toggle_api_visibility(self) -> None:
        self._eye_visible = not self._eye_visible
        if self._eye_visible:
            self._api.configure(show="")
            self._eye_btn.configure(text_color=ACCENT)
        else:
            self._api.configure(show="*")
            self._eye_btn.configure(text_color="#888888")

    def _bind_click_recursive(self, widget: tk.Misc, callback: Callable[[tk.Event], None]) -> None:
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            self._bind_click_recursive(child, callback)

    def _set_mode(self, mode: Literal["hold", "toggle"]) -> None:
        self._mode_var.set(mode)
        self._update_activation_mode_ui()

    def _update_activation_mode_ui(self) -> None:
        mode = self._mode_var.get()
        # Hold option
        if mode == "hold":
            self._hold_card.configure(fg_color="#2d2815", border_color=ACCENT, border_width=2)
            self._hold_radio_canvas.configure(bg="#2d2815")
            self._draw_radio_circle(self._hold_radio_canvas, selected=True)
        else:
            self._hold_card.configure(fg_color=CARD_BG, border_color="#3d3d3d", border_width=1)
            self._hold_radio_canvas.configure(bg=CARD_BG)
            self._draw_radio_circle(self._hold_radio_canvas, selected=False)

        # Toggle option
        if mode == "toggle":
            self._toggle_card.configure(fg_color="#2d2815", border_color=ACCENT, border_width=2)
            self._toggle_radio_canvas.configure(bg="#2d2815")
            self._draw_radio_circle(self._toggle_radio_canvas, selected=True)
        else:
            self._toggle_card.configure(fg_color=CARD_BG, border_color="#3d3d3d", border_width=1)
            self._toggle_radio_canvas.configure(bg=CARD_BG)
            self._draw_radio_circle(self._toggle_radio_canvas, selected=False)

    def _draw_radio_circle(self, canvas: tk.Canvas, selected: bool) -> None:
        canvas.delete("all")
        bg_col = canvas.cget("bg")
        # Custom elegant circle drawing
        if selected:
            canvas.create_oval(2, 2, 18, 18, outline=ACCENT, width=2)
            canvas.create_oval(6, 6, 14, 14, outline=ACCENT, fill=ACCENT, width=0)
        else:
            canvas.create_oval(2, 2, 18, 18, outline="#555555", width=2)

    def _load_fields(self) -> None:
        cfg = self._get_config()
        self._api.delete(0, "end")
        self._api.insert(0, str(cfg.get("api_key", "")))
        mode = cfg.get("mode", "hold")
        self._mode_var.set("hold" if mode == "hold" else "toggle")
        self._lang.set(str(cfg.get("language", "en")))
        if cfg.get("launch_on_startup"):
            self._startup.select()
        else:
            self._startup.deselect()
        self._update_activation_mode_ui()

    def _save_clicked(self) -> None:
        mode = self._mode_var.get()
        if mode not in ("hold", "toggle"):
            mode = "hold"
        cfg = {
            "api_key": self._api.get().strip(),
            "mode": mode,
            "language": self._lang.get(),
            "launch_on_startup": bool(self._startup.get()),
        }
        self._on_save(cfg)
        self._save_hint.configure(text="Saved — settings stored to config.json")
        self.after(2800, lambda: self._save_hint.configure(text=""))

    def _on_close(self) -> None:
        self.withdraw()

    def open_front(self) -> None:
        self._load_fields()
        self._save_hint.configure(text="")
        self.deiconify()
        self.update_idletasks()
        apply_titlebar_icon(self, self._master)
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(lambda: self.attributes("-topmost", False))
        self.focus_force()


class SplashWindow(tk.Toplevel):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self._master = master
        self.overrideredirect(True)
        self.resizable(False, False)

        self._win_w = 860
        self._win_h = 460
        self.geometry(f"{self._win_w}x{self._win_h}")
        self.bind("<Escape>", lambda _e: self.dismiss())

        self._chroma = "#010203"
        self.configure(bg=self._chroma)
        try:
            self.wm_attributes("-transparentcolor", self._chroma)
        except Exception:
            pass

        from PIL import Image, ImageTk, ImageDraw
        try:
            pil_img = Image.open("assets/Splash_screen.png").resize(
                (self._win_w, self._win_h), Image.Resampling.LANCZOS
            ).convert("RGBA")
            mask = Image.new("L", (self._win_w, self._win_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [(0, 0), (self._win_w, self._win_h)], radius=24, fill=255
            )
            pil_img.putalpha(mask)
            self._bg_photo = ImageTk.PhotoImage(pil_img)
        except Exception:
            self._bg_photo = None

        # Background
        if self._bg_photo:
            bg_lbl = tk.Label(self, image=self._bg_photo, bd=0,
                              highlightthickness=0, bg=self._chroma)
            bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
            bg_lbl.lower()

        # --- Button container frame anchored bottom-right ---
        btn_frame = tk.Frame(self, bg=self._chroma)
        btn_frame.place(relx=1.0, rely=1.0, x=-24, y=-24, anchor="se")

        # Settings button
        self._settings_btn = tk.Label(
            btn_frame,
            text="Settings",
            font=("Segoe UI", 14, "underline"),
            fg="#ffffff",
            bg=self._chroma,
            cursor="hand2",
            padx=8,
            pady=4,
        )
        self._settings_btn.pack(side="left", padx=(0, 12))
        self._settings_btn.bind("<Button-1>", lambda e: (self._open_settings(), self.dismiss()))

        # Run in Background button
        self._run_btn = ctk.CTkButton(
            btn_frame,
            text="Run in Background",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#ffffff",
            fg_color="#1a1a1a",
            hover_color="#333333",
            width=200,
            height=44,
            corner_radius=12,
            bg_color=self._chroma,
            command=self.dismiss,
            cursor="hand2",
        )
        self._run_btn.pack(side="left")

        # Lift buttons above background
        btn_frame.lift()

        self._auto_close_job = None
        self.withdraw()

    def dismiss(self) -> None:
        if hasattr(self, "_auto_close_job") and self._auto_close_job:
            try:
                self.after_cancel(self._auto_close_job)
            except Exception:
                pass
            self._auto_close_job = None
        self.withdraw()

    def _open_settings(self) -> None:
        # Dynamically locate the SettingsWindow child to prevent attribute errors on CTk master
        for child in self._master.winfo_children():
            if child.__class__.__name__ == "SettingsWindow":
                self._master.after(0, child.open_front)
                return
        if hasattr(self._master, "_settings"):
            self._master.after(0, self._master._settings.open_front)

    def show_centered(self) -> None:
        apply_titlebar_icon(self, self._master)
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - self._win_w) // 2)
        y = max(0, (sh - self._win_h) // 2)
        self.geometry(f"{self._win_w}x{self._win_h}+{x}+{y}")
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(lambda: self.attributes("-topmost", False))
        self.focus_force()
        self._auto_close_job = self.after(60000, self.dismiss)


def apply_ctk_theme() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    ctk.set_widget_scaling(1.0)
