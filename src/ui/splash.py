"""
REREAL - Spitit: Splash screen.
Shown on first run or when launch_on_startup is true.
"""

import customtkinter as ctk
from src.ui.theme import (
    BG_BASE, ACCENT, ACCENT_DIM, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, SPLASH_WIDTH, SPLASH_HEIGHT, CORNER_RADIUS_SM,
    BG_SURFACE, BG_ELEVATED, GLASS_BORDER, BORDER_WIDTH,
)
from src.ui.components import AccentButton, GhostButton
from src.updater import CURRENT_VERSION


class SplashScreen:
    """
    Splash screen shown on app launch.
    Size: 460×320, centered.
    
    Shows logo, tagline, and two action buttons.
    """

    def __init__(self, root, config: dict, fonts: dict, on_settings=None, on_start=None):
        self._root = root
        self._config = config
        self._fonts = fonts
        self._on_settings = on_settings
        self._on_start = on_start
        self._win = None

    def show(self):
        """Display the splash screen."""
        self._win = ctk.CTkToplevel(self._root)
        self._win.title("REREAL · Spitit")
        self._win.geometry(
            f"{SPLASH_WIDTH}x{SPLASH_HEIGHT}+"
            f"{(self._root.winfo_screenwidth() - SPLASH_WIDTH) // 2}+"
            f"{(self._root.winfo_screenheight() - SPLASH_HEIGHT) // 2}"
        )
        self._win.configure(fg_color=BG_BASE)
        self._win.resizable(False, False)

        # Try to set icon
        try:
            from src.config import get_asset_path
            ico_path = get_asset_path("icon.ico")
            if ico_path.exists():
                self._win.iconbitmap(str(ico_path))
        except Exception:
            pass

        # Content
        content = ctk.CTkFrame(self._win, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=32, pady=24)

        # Logo placeholder (yellow circle with bars)
        logo_frame = ctk.CTkFrame(content, fg_color="transparent")
        logo_frame.pack(pady=(16, 8))

        logo_canvas = ctk.CTkCanvas(logo_frame, width=64, height=64, bg=BG_BASE, highlightthickness=0)
        logo_canvas.pack()
        self._draw_logo(logo_canvas)

        # Title
        title = ctk.CTkLabel(
            content,
            text="REREAL · Spitit",
            text_color=ACCENT,
            font=self._fonts["xl"],
        )
        title.pack(pady=(8, 2))

        # Version
        version = ctk.CTkLabel(
            content,
            text=f"v{CURRENT_VERSION}",
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
        )
        version.pack()

        # Tagline
        tagline = ctk.CTkLabel(
            content,
            text="Speak. Release. Done.",
            text_color=TEXT_SECONDARY,
            font=self._fonts["md"],
        )
        tagline.pack(pady=(12, 24))

        # Buttons row
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(pady=(0, 16))

        GhostButton(
            btn_frame,
            text="Open Settings",
            font=self._fonts["md"],
            width=160,
            command=self._open_settings,
        ).pack(side="left", padx=(0, 12))

        AccentButton(
            btn_frame,
            text="Start in background",
            font=self._fonts["md_b"],
            width=180,
            command=self._start_background,
        ).pack(side="left")

        # Don't show on startup checkbox
        self._dont_show_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(
            content,
            text="Don't show this on startup",
            variable=self._dont_show_var,
            text_color=TEXT_MUTED,
            font=self._fonts["xs"],
            fg_color=ACCENT,
            hover_color=ACCENT,
            checkmark_color=BG_BASE,
            border_color=TEXT_MUTED,
        )
        checkbox.pack(pady=(0, 8))

        # Handle close
        self._win.protocol("WM_DELETE_WINDOW", self._start_background)
        self._win.focus_force()

    def _draw_logo(self, canvas):
        """Draw a simple logo on the canvas."""
        size = 64
        margin = 4
        # Yellow rounded rect
        canvas.create_oval(margin, margin, size - margin, size - margin, fill=ACCENT, outline="")

        # Dark bars
        cx = size // 2
        cy = size // 2
        heights = [0.25, 0.45, 0.7, 0.45, 0.25]
        bar_w = 4
        gap = 3
        total = 5 * bar_w + 4 * gap
        sx = cx - total // 2

        for i, h_pct in enumerate(heights):
            h = max(4, int(30 * h_pct))
            x1 = sx + i * (bar_w + gap)
            x2 = x1 + bar_w
            y1 = cy - h // 2
            y2 = cy + h // 2
            canvas.create_rectangle(x1, y1, x2, y2, fill=BG_BASE, outline="")

    def _open_settings(self):
        """Open settings and close splash."""
        self._save_preference()
        if self._win:
            self._win.destroy()
            self._win = None
        if self._on_settings:
            self._on_settings()

    def _start_background(self):
        """Dismiss splash to tray."""
        self._save_preference()
        if self._win:
            self._win.destroy()
            self._win = None
        if self._on_start:
            self._on_start()

    def _save_preference(self):
        """Save the 'don't show' preference."""
        if self._dont_show_var.get():
            self._config["first_run"] = False
            from src.config import save_config
            save_config(self._config)

    def close(self):
        if self._win:
            self._win.destroy()
            self._win = None
