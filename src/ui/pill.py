"""
REREAL - Spitit: Floating status pill.
Animated waveform chip that shows recording/transcribing/done/error states.
True transparent edges via chroma key, draggable, always-on-top.
"""

import math
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
from src.ui.theme import (
    PILL_WIDTH, PILL_HEIGHT, PILL_ALPHA, PILL_TICK_MS,
    STATE_RECORDING, STATE_TRANSCRIBING, STATE_DONE, STATE_ERROR,
    BG_BASE, TEXT_SECONDARY, ACCENT_DIM,
)

# Chroma key color (must be a color not used anywhere else in the pill)
CHROMA_KEY = "#010101"

# Waveform bar config
NUM_BARS = 5
BAR_BASE_HEIGHTS = [0.3, 0.6, 1.0, 0.6, 0.3]
BAR_PHASE_OFFSETS = [0.0, 0.4, 0.8, 1.2, 1.6]
BAR_WIDTH_RATIO = 0.06   # fraction of pill width
BAR_GAP_RATIO = 0.04     # fraction of pill width
BAR_MAX_HEIGHT_RATIO = 0.6  # fraction of pill height


class StatusPill:
    """
    Floating pill window that shows app state with animations.
    
    States:
        - hidden: window withdrawn
        - recording: animated waveform bars (yellow)
        - transcribing: spinning arc loader (blue)
        - done: checkmark icon (green), auto-hide after 900ms
        - error: X icon (red), auto-hide after 2800ms
    """

    def __init__(self, root: tk.Tk, config: dict = None):
        self._root = root
        self._config = config or {}
        self._state = "hidden"
        self._tick_id = None
        self._hide_id = None
        self._phase = 0.0
        self._arc_angle = 0.0
        self._word_count = 0
        self._drag_data = {"x": 0, "y": 0}
        self._duration = 0.0
        self._max_duration = 120.0

        # Create the toplevel window
        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.attributes("-alpha", PILL_ALPHA)
        self._win.attributes("-transparentcolor", CHROMA_KEY)
        self._win.configure(bg=CHROMA_KEY)

        # Set as toolwindow to hide from taskbar
        try:
            self._win.attributes("-toolwindow", True)
        except tk.TclError:
            pass

        # Canvas for drawing
        self._canvas = tk.Canvas(
            self._win,
            width=PILL_WIDTH,
            height=PILL_HEIGHT,
            bg=CHROMA_KEY,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack()

        # Word count label (below pill)
        self._word_label = tk.Label(
            self._win,
            text="",
            fg=TEXT_SECONDARY,
            bg=CHROMA_KEY,
            font=("Segoe UI", 9),
        )

        # Position
        self._set_initial_position()

        # Drag bindings
        self._canvas.bind("<Button-1>", self._on_drag_start)
        self._canvas.bind("<B1-Motion>", self._on_drag_motion)
        self._canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        # Start hidden
        self._win.withdraw()

    def _set_initial_position(self):
        """Set the pill position from config or default (bottom-right)."""
        saved_pos = self._config.get("pill_position")
        if saved_pos and isinstance(saved_pos, list) and len(saved_pos) == 2:
            self._win.geometry(f"+{saved_pos[0]}+{saved_pos[1]}")
        else:
            # Bottom-right, 20px from edges
            screen_w = self._root.winfo_screenwidth()
            screen_h = self._root.winfo_screenheight()
            x = screen_w - PILL_WIDTH - 20
            y = screen_h - PILL_HEIGHT - 60  # Above taskbar
            self._win.geometry(f"+{x}+{y}")

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        x = self._win.winfo_x() + (event.x - self._drag_data["x"])
        y = self._win.winfo_y() + (event.y - self._drag_data["y"])
        self._win.geometry(f"+{x}+{y}")

    def _on_drag_end(self, event):
        # Save position to config
        x = self._win.winfo_x()
        y = self._win.winfo_y()
        self._config["pill_position"] = [x, y]

    def set_state(self, state: str, word_count: int = 0, duration: float = 0.0):
        """
        Change the pill state.
        
        Args:
            state: One of 'hidden', 'recording', 'transcribing', 'done', 'error'
            word_count: Number of words (shown in done state)
            duration: Current recording duration in seconds
        """
        # Cancel pending operations
        if self._tick_id:
            self._root.after_cancel(self._tick_id)
            self._tick_id = None
        if self._hide_id:
            self._root.after_cancel(self._hide_id)
            self._hide_id = None

        self._state = state
        self._word_count = word_count
        self._duration = duration

        if state == "hidden":
            self._win.withdraw()
            self._word_label.pack_forget()
            return

        self._win.deiconify()
        self._win.lift()
        self._phase = 0.0
        self._arc_angle = 0.0

        if state == "recording":
            self._tick_animate()
        elif state == "transcribing":
            self._tick_animate()
        elif state == "done":
            self._draw_done()
            # Show word count
            if word_count > 0:
                self._word_label.configure(text=f"{word_count} words")
                self._word_label.pack(pady=(0, 2))
            # Auto-hide after 900ms
            self._hide_id = self._root.after(900, lambda: self.set_state("hidden"))
        elif state == "error":
            self._draw_error()
            self._word_label.pack_forget()
            # Auto-hide after 2800ms
            self._hide_id = self._root.after(2800, lambda: self.set_state("hidden"))

    def update_duration(self, duration: float):
        """Update the recording duration for the progress bar."""
        self._duration = duration

    def _tick_animate(self):
        """Animation tick — dispatches to the correct drawing method."""
        if self._state == "recording":
            self._draw_recording()
        elif self._state == "transcribing":
            self._draw_transcribing()
        else:
            return

        self._phase += 0.15
        self._arc_angle += 8.0
        self._tick_id = self._root.after(PILL_TICK_MS, self._tick_animate)

    def _render_image(self, draw_func):
        """
        Generic rendering method that sets up a 4x supersampled RGBA image,
        calls the draw function, resizes it with LANCZOS downsampling,
        composites it over the CHROMA_KEY background, and updates the canvas.
        """
        w_4x = PILL_WIDTH * 4
        h_4x = PILL_HEIGHT * 4

        # Create 4x RGBA canvas
        img_4x = Image.new("RGBA", (w_4x, h_4x), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img_4x)

        # 1. Draw the base pill shape first (glassmorphic dark background + border)
        # fill is BG_BASE ("#111113"), border is "#2a2a2e"
        draw.rounded_rectangle(
            [0, 0, w_4x - 1, h_4x - 1],
            radius=h_4x // 2,
            fill="#111113",
            outline="#2a2a2e",
            width=4
        )

        # 2. Call the state-specific drawing function
        draw_func(draw, w_4x, h_4x)

        # 3. Resize using LANCZOS for perfect antialiasing
        try:
            LANCZOS = Image.Resampling.LANCZOS
        except AttributeError:
            LANCZOS = Image.LANCZOS

        img = img_4x.resize((PILL_WIDTH, PILL_HEIGHT), LANCZOS)

        # 4. Paste over solid CHROMA_KEY background
        final_img = Image.new("RGB", (PILL_WIDTH, PILL_HEIGHT), CHROMA_KEY)
        final_img.paste(img, (0, 0), img)

        # 5. Convert to Tkinter PhotoImage and update canvas
        self._photo_ref = ImageTk.PhotoImage(final_img)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo_ref)

    def _draw_recording(self):
        """Draw the animated fluid tapered waves for recording state in PIL."""
        def draw_func(draw: ImageDraw.ImageDraw, w_4x: int, h_4x: int):
            cy = h_4x // 2

            # Draw 3 overlapping waves with different colors, speeds, frequencies, and opacities
            # Color palettes: accent yellow, and subtle bright additions
            # Wave 1 (Deep/Back wave)
            points1 = []
            for x in range(0, w_4x + 4, 4):
                envelope = math.sin(math.pi * x / w_4x)
                sine_val = math.sin(self._phase + (x * 0.015))
                y = cy + 24 * envelope * sine_val
                points1.append((x, y))
            draw.line(points1, fill=(255, 213, 5, 60), width=6)

            # Wave 2 (Middle wave)
            points2 = []
            for x in range(0, w_4x + 4, 4):
                envelope = math.sin(math.pi * x / w_4x)
                sine_val = math.sin(-self._phase * 1.3 + (x * 0.025) + 2.0)
                y = cy + 34 * envelope * sine_val
                points2.append((x, y))
            draw.line(points2, fill=(255, 213, 5, 120), width=8)

            # Wave 3 (Front/Main glowing wave)
            points3 = []
            for x in range(0, w_4x + 4, 4):
                envelope = math.sin(math.pi * x / w_4x)
                sine_val = math.sin(self._phase * 0.9 + (x * 0.012) - 1.5)
                y = cy + 40 * envelope * sine_val
                points3.append((x, y))
            draw.line(points3, fill=(255, 255, 255, 200), width=10)

            # Duration progress bar at the bottom
            if self._duration > 0 and self._max_duration > 0:
                progress = min(self._duration / self._max_duration, 1.0)
                bar_y = h_4x - 12
                bar_h = 6
                start_x = h_4x // 2
                end_x = w_4x - (h_4x // 2)

                # Draw subtle dark track
                draw.rounded_rectangle([start_x, bar_y, end_x, bar_y + bar_h], radius=bar_h // 2, fill=(40, 40, 45, 120))

                # Draw yellow glowing progress
                prog_x = start_x + int((end_x - start_x) * progress)
                if prog_x > start_x:
                    draw.rounded_rectangle([start_x, bar_y, prog_x, bar_y + bar_h], radius=bar_h // 2, fill=(255, 213, 5, 220))

        self._render_image(draw_func)

    def _draw_transcribing(self):
        """Draw spinning loader ring for transcribing state in PIL."""
        def draw_func(draw: ImageDraw.ImageDraw, w_4x: int, h_4x: int):
            cx = w_4x // 2
            cy = h_4x // 2
            r = h_4x // 2 - 24  # radius is 44

            # Draw background dim track (ACCENT_DIM yellow)
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                outline=(61, 50, 16, 120),
                width=12
            )

            # Spinning arc (blue)
            start_angle = int(self._arc_angle) % 360
            end_angle = start_angle + 90
            draw.arc(
                [cx - r, cy - r, cx + r, cy + r],
                start=start_angle,
                end=end_angle,
                fill=(77, 158, 255, 255),
                width=12
            )

        self._render_image(draw_func)

    def _draw_done(self):
        """Draw checkmark icon with rounded caps for done state in PIL."""
        def draw_func(draw: ImageDraw.ImageDraw, w_4x: int, h_4x: int):
            cx = w_4x // 2
            cy = h_4x // 2
            s = 20

            # Checkmark points at 4x
            p1 = (cx - s, cy)
            p2 = (cx - s // 3, cy + s * 0.6)
            p3 = (cx + s, cy - s * 0.5)

            # Draw line segments
            draw.line([p1, p2, p3], fill=(61, 220, 132, 255), width=12)

            # Round caps and joint using overlapping circles
            r_cap = 6
            for p in (p1, p2, p3):
                draw.ellipse([p[0] - r_cap, p[1] - r_cap, p[0] + r_cap, p[1] + r_cap], fill=(61, 220, 132, 255))

        self._render_image(draw_func)

    def _draw_error(self):
        """Draw X icon with rounded caps for error state in PIL."""
        def draw_func(draw: ImageDraw.ImageDraw, w_4x: int, h_4x: int):
            cx = w_4x // 2
            cy = h_4x // 2
            s = 18

            # Two crossing lines
            p1_1, p1_2 = (cx - s, cy - s), (cx + s, cy + s)
            p2_1, p2_2 = (cx + s, cy - s), (cx - s, cy + s)

            # Draw lines
            draw.line([p1_1, p1_2], fill=(255, 95, 95, 255), width=12)
            draw.line([p2_1, p2_2], fill=(255, 95, 95, 255), width=12)

            # Round caps using overlapping circles
            r_cap = 6
            for p in (p1_1, p1_2, p2_1, p2_2):
                draw.ellipse([p[0] - r_cap, p[1] - r_cap, p[0] + r_cap, p[1] + r_cap], fill=(255, 95, 95, 255))

        self._render_image(draw_func)

    def destroy(self):
        """Clean up the pill window."""
        if self._tick_id:
            self._root.after_cancel(self._tick_id)
        if self._hide_id:
            self._root.after_cancel(self._hide_id)
        try:
            self._win.destroy()
        except Exception:
            pass
