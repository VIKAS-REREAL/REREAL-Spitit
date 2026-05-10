"""CustomTkinter: floating status pill and settings window."""

from __future__ import annotations

import math
import tkinter as tk
from typing import Any, Callable, Literal

import customtkinter as ctk
from PIL import Image

from tray import ensure_icon_png

State = Literal["hidden", "recording", "transcribing", "done", "error"]

BG = "#1e1e1e"
ACCENT = "#FFD505"
TEXT_LIGHT = "#ffffff"
TEXT_DARK = "#000000"
DONE_GREEN = "#3ddc84"
ERROR_RED = "#ff6b6b"
WAVE_ON_YELLOW = "#1a1a1a"
# Windows: pixels with this exact color become transparent (true rounded silhouette).
_CHROMA_KEY = "#010203"
HOVER_YELLOW = "#c9ab00"

FONT_FAMILY = "Segoe UI"

# Tiny wave-only chip (no chrome, no labels)
PILL_W = 76
PILL_H = 22
PILL_R = min(11, PILL_H // 2)


def _canvas_round_rect_fill(
    c: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    r: float,
    fill: str,
) -> None:
    r = int(min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    if r <= 0:
        c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=fill, width=1)
        return
    kw = {"fill": fill, "outline": fill, "width": 1}
    c.create_rectangle(x1 + r, y1, x2 - r, y2, **kw)
    c.create_rectangle(x1, y1 + r, x2, y2 - r, **kw)
    c.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, **kw)
    c.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, **kw)
    c.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, **kw)
    c.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, **kw)


def apply_titlebar_icon(window: tk.Misc, master: ctk.CTk) -> None:
    """Set OS title bar / taskbar icon from masterâ€™s shared PhotoImage or assets PNG."""
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
    """Minimal floating chip: animated wave only (native tk, no heavy frame)."""

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
            self.attributes("-alpha", 0.93)
        except Exception:
            pass
        self._chroma = _CHROMA_KEY
        self.configure(bg=self._chroma)
        try:
            self.wm_attributes("-transparentcolor", self._chroma)
        except Exception:
            self.configure(bg=BG)
            self._chroma = BG
        self.resizable(False, False)
        self._state: State = "hidden"
        self._wave_phase = 0.0
        self._wave_color = WAVE_ON_YELLOW
        self._fill_color = ACCENT
        self._wave_active = False
        self._drag_dx = 0
        self._drag_dy = 0
        self._dragging = False

        self._hide_job = None
        self._wave_job = None

        self._canvas = tk.Canvas(
            self,
            width=PILL_W,
            height=PILL_H,
            highlightthickness=0,
            bd=0,
            bg=self._chroma,
            relief="flat",
        )
        self._canvas.pack(padx=0, pady=0)

        self._canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_motion)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)
        self.configure(cursor="hand2")

        self.withdraw()

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

    def _geometry_size(self) -> tuple[int, int]:
        return PILL_W, PILL_H

    def _place_bottom_right(self) -> None:
        w, h = self._geometry_size()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        margin = 20
        x = sw - w - margin
        y = sh - h - margin - 44
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _place_pill(self) -> None:
        w, h = self._geometry_size()
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

    def _apply_theme(self, canvas_bg: str, wave_color: str) -> None:
        self._fill_color = canvas_bg
        self._wave_color = wave_color
        if self._chroma == _CHROMA_KEY:
            self.configure(bg=self._chroma)
            self._canvas.configure(bg=self._chroma)
        else:
            self.configure(bg=canvas_bg)
            self._canvas.configure(bg=canvas_bg)

    def _draw_rounded_background(self, cw: int, ch: int) -> None:
        r = min(PILL_R, cw // 2, ch // 2)
        _canvas_round_rect_fill(self._canvas, 0, 0, cw, ch, r, self._fill_color)

    def _draw_wave_frame(self) -> None:
        cw = self._canvas.winfo_width() or PILL_W
        ch = self._canvas.winfo_height() or PILL_H
        self._canvas.delete("all")
        self._draw_rounded_background(cw, ch)
        inset = max(4, int(PILL_R * 0.55))
        mid = ch / 2.0
        amp = ch * 0.22
        ph = self._wave_phase
        n = 42
        flat: list[float] = []
        for i in range(n + 1):
            t = i / n
            x = inset + t * (cw - 2 * inset)
            y = mid + amp * (
                0.62 * math.sin(ph * 1.1 + t * math.pi * 3.0)
                + 0.35 * math.sin(-ph * 0.9 + t * math.pi * 5.2 + 0.8)
            )
            flat.extend([x, y])
        if len(flat) >= 4:
            self._canvas.create_line(
                *flat,
                fill=self._wave_color,
                width=1,
                smooth=True,
                splinesteps=12,
            )

    def _wave_tick(self) -> None:
        if not self._wave_active or self._state not in ("recording", "transcribing"):
            return
        self._wave_phase += 0.18
        self._draw_wave_frame()
        self._wave_job = self.after(52, self._wave_tick)

    def _start_wave(self) -> None:
        self._wave_active = True
        self._wave_phase = 0.0
        if self._wave_job is not None:
            try:
                self.after_cancel(self._wave_job)
            except Exception:
                pass
            self._wave_job = None
        self._wave_tick()

    def _stop_wave(self) -> None:
        self._wave_active = False
        if self._wave_job is not None:
            try:
                self.after_cancel(self._wave_job)
            except Exception:
                pass
            self._wave_job = None
        self._canvas.delete("all")

    def _cancel_timers(self) -> None:
        if self._hide_job is not None:
            try:
                self.after_cancel(self._hide_job)
            except Exception:
                pass
        self._hide_job = None
        self._stop_wave()

    def show_hidden(self) -> None:
        self._cancel_timers()
        self._state = "hidden"
        self.withdraw()

    def show_recording(self) -> None:
        self._cancel_timers()
        self._state = "recording"
        self._apply_theme(ACCENT, WAVE_ON_YELLOW)
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._start_wave()

    def show_transcribing(self) -> None:
        self._cancel_timers()
        self._state = "transcribing"
        self._apply_theme(BG, ACCENT)
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._start_wave()

    def show_done(self) -> None:
        self._cancel_timers()
        self._state = "done"
        self._apply_theme(BG, DONE_GREEN)
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._draw_static_wave(DONE_GREEN)
        self._hide_job = self.after(900, self.show_hidden)

    def _draw_static_wave(self, color: str) -> None:
        cw = self._canvas.winfo_width() or PILL_W
        ch = self._canvas.winfo_height() or PILL_H
        self._canvas.delete("all")
        self._draw_rounded_background(cw, ch)
        inset = max(4, int(PILL_R * 0.55))
        mid = ch / 2.0
        amp = ch * 0.14
        n = 32
        flat: list[float] = []
        for i in range(n + 1):
            t = i / n
            x = inset + t * (cw - 2 * inset)
            y = mid + amp * math.sin(t * math.pi * 2.2)
            flat.extend([x, y])
        if len(flat) >= 4:
            self._canvas.create_line(
                *flat,
                fill=color,
                width=1,
                smooth=True,
                splinesteps=10,
            )

    def show_error(self, message: str) -> None:
        del message
        self._cancel_timers()
        self._state = "error"
        self._apply_theme(BG, ERROR_RED)
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._draw_static_wave(ERROR_RED)
        self._hide_job = self.after(2800, self.show_hidden)

    def show_mode_notice(self, mode_label: str) -> None:
        del mode_label
        self._cancel_timers()
        self._state = "done"
        self._apply_theme(BG, ACCENT)
        self.deiconify()
        self._place_pill()
        self.update_idletasks()
        self._draw_static_wave(ACCENT)
        self._hide_job = self.after(800, self.show_hidden)


class SettingsWindow(ctk.CTkToplevel):
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
        self.title("REREAL Â· Spitit â€” Settings")
        self.configure(fg_color=BG)
        self.minsize(400, 480)
        self.geometry("540x620")
        self.resizable(True, True)
        self.attributes("-topmost", False)
        try:
            self.transient(master)
        except Exception:
            pass

        apply_titlebar_icon(self, master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        header.grid_columnconfigure(1, weight=1)

        pil = Image.open(ensure_icon_png()).convert("RGBA")
        pil_sm = pil.resize((44, 44), Image.Resampling.LANCZOS)
        self._logo = ctk.CTkImage(light_image=pil_sm, dark_image=pil_sm, size=(44, 44))

        ctk.CTkLabel(header, image=self._logo, text="").grid(row=0, column=0, padx=(0, 14))
        title_block = ctk.CTkFrame(header, fg_color="transparent")
        title_block.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            title_block,
            text="REREAL Â· Spitit",
            font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_block,
            text="Voice to text â€” settings",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#a0a0a0",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

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
        pad = {"padx": 0, "pady": (0, 14)}

        ctk.CTkLabel(
            body,
            text="Groq API key",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(4, 6))
        self._api = ctk.CTkEntry(
            body,
            height=44,
            fg_color="#2a2a2a",
            text_color=TEXT_LIGHT,
            border_color=ACCENT,
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            placeholder_text="Paste your Groq API key",
            show="*",
        )
        self._api.bind("<FocusIn>", lambda _e: self._api.configure(border_width=2))
        self._api.bind("<FocusOut>", lambda _e: self._api.configure(border_width=1))
        self._api.grid(row=1, column=0, sticky="ew", **pad)
        self._api.configure(cursor="xterm")

        ctk.CTkLabel(
            body,
            text="Activation mode",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", pady=(8, 6))
        self._mode_var = ctk.StringVar(value="hold")
        mode_wrap = ctk.CTkFrame(body, fg_color="transparent")
        mode_wrap.grid(row=3, column=0, sticky="ew", **pad)
        mode_wrap.grid_columnconfigure(0, weight=1)
        rb_kw = {
            "font": ctk.CTkFont(family=FONT_FAMILY, size=13),
            "text_color": TEXT_LIGHT,
            "fg_color": ACCENT,
            "hover_color": HOVER_YELLOW,
            "radiobutton_width": 20,
            "radiobutton_height": 20,
            "cursor": "hand2",
        }
        ctk.CTkRadioButton(
            mode_wrap,
            text="Hold to talk â€” hold Alt + Left Shift",
            variable=self._mode_var,
            value="hold",
            **rb_kw,
        ).pack(anchor="w", pady=6)
        ctk.CTkRadioButton(
            mode_wrap,
            text="Toggle to talk â€” Alt + Left Shift + Space",
            variable=self._mode_var,
            value="toggle",
            **rb_kw,
        ).pack(anchor="w", pady=6)

        ctk.CTkLabel(
            body,
            text="Language (Whisper)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).grid(row=4, column=0, sticky="ew", pady=(8, 6))
        langs = [
            "en",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "nl",
            "pl",
            "ru",
            "ja",
            "ko",
            "zh",
            "auto",
        ]
        self._lang = ctk.CTkOptionMenu(
            body,
            values=langs,
            height=40,
            corner_radius=8,
            fg_color="#2a2a2a",
            button_color=ACCENT,
            button_hover_color=HOVER_YELLOW,
            dropdown_fg_color="#2a2a2a",
            dropdown_hover_color="#3d3d3d",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_LIGHT,
            dynamic_resizing=True,
        )
        self._lang.grid(row=5, column=0, sticky="ew", **pad)
        self._lang.configure(cursor="hand2")

        self._startup = ctk.CTkCheckBox(
            body,
            text="Launch on Windows startup",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=TEXT_LIGHT,
            fg_color=ACCENT,
            hover_color=HOVER_YELLOW,
            checkmark_color=TEXT_DARK,
            cursor="hand2",
        )
        self._startup.grid(row=6, column=0, sticky="w", pady=(12, 8))

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
            text="Save settings",
            height=46,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=HOVER_YELLOW,
            text_color=TEXT_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            command=self._save_clicked,
            cursor="hand2",
        )
        self._save_btn.grid(row=1, column=0, sticky="ew")

        self._load_fields()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        self._save_hint.configure(text="Saved â€” settings stored to config.json")
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


class SplashWindow(ctk.CTkToplevel):
    """One-shot startup panel: centered, close hides to tray; process and hotkeys keep running."""

    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self._master = master
        self.title("REREAL Â· Spitit")
        self.configure(fg_color=BG)
        self.resizable(False, False)
        apply_titlebar_icon(self, master)

        w, h = 440, 300
        self._win_w = w
        self._win_h = h
        self.geometry(f"{w}x{h}")
        self.minsize(w, h)
        self.maxsize(w, h)

        self.protocol("WM_DELETE_WINDOW", self.dismiss)
        self.bind("<Escape>", lambda _e: self.dismiss())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 8))
        header.grid_columnconfigure(0, weight=1)

        pil = Image.open(ensure_icon_png()).convert("RGBA")
        pil_sm = pil.resize((48, 48), Image.Resampling.LANCZOS)
        self._logo = ctk.CTkImage(light_image=pil_sm, dark_image=pil_sm, size=(48, 48))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew")
        title_row.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(title_row, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(left, image=self._logo, text="").pack(side="left", padx=(0, 12))
        titles = ctk.CTkFrame(left, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(
            titles,
            text="REREAL Â· Spitit",
            font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
            text_color=TEXT_LIGHT,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            titles,
            text="Voice to text is ready",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color="#a0a0a0",
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        close_btn = ctk.CTkButton(
            title_row,
            text="Ã—",
            width=40,
            height=36,
            corner_radius=8,
            fg_color="#2a2a2a",
            hover_color="#3d3d3d",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=22),
            command=self.dismiss,
            cursor="hand2",
        )
        close_btn.grid(row=0, column=1, sticky="e", padx=(8, 0))

        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(4, 12))
        ctk.CTkLabel(
            body,
            text=(
                "The app stays in the system tray. Use the title bar âœ•, the button above, "
                "or Esc to hide this window.\n\n"
                "Hold Alt + Left Shift to dictate (or toggle mode in Settings). "
                "Open Settings from the tray icon anytime."
            ),
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color="#c8c8c8",
            anchor="w",
            justify="left",
            wraplength=380,
        ).pack(anchor="w", fill="x")

        footer = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))
        footer_btns = ctk.CTkFrame(footer, fg_color="transparent")
        footer_btns.pack(fill="x")
        footer_btns.grid_columnconfigure(0, weight=1)
        footer_btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            footer_btns,
            text="Open Settings",
            height=44,
            corner_radius=10,
            fg_color="#2a2a2a",
            hover_color="#3d3d3d",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            command=self._open_settings,
            cursor="hand2",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(
            footer_btns,
            text="Continue in background",
            height=44,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=HOVER_YELLOW,
            text_color=TEXT_DARK,
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
            command=self.dismiss,
            cursor="hand2",
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.withdraw()

    def _center(self) -> None:
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = self._win_w, self._win_h
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _open_settings(self) -> None:
        self._master.after(0, self._master._settings.open_front)  # type: ignore

    def dismiss(self) -> None:
        """Hide splash only; tray + hotkeys remain active."""
        self.withdraw()

    def show_centered(self) -> None:
        apply_titlebar_icon(self, self._master)
        self._center()
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after_idle(lambda: self.attributes("-topmost", False))
        self.focus_force()


def apply_ctk_theme() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    ctk.set_widget_scaling(1.0)

