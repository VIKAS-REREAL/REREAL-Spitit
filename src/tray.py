"""
REREAL - Spitit: System tray icon and menu.
Uses pystray for the system tray integration.
"""

import threading
from pathlib import Path


class TrayManager:
    """
    Manages the system tray icon and context menu.
    
    Menu:
        Open Settings
        Toggle Mode (Hold ↔ Toggle)
        ─────────────────
        Copy last: [first 30 chars...]
        ─────────────────
        Check for Updates
        ─────────────────
        Quit
    """

    def __init__(
        self,
        on_open_settings=None,
        on_toggle_mode=None,
        on_check_updates=None,
        on_copy_last=None,
        on_quit=None,
        config=None,
    ):
        self._on_open_settings = on_open_settings
        self._on_toggle_mode = on_toggle_mode
        self._on_check_updates = on_check_updates
        self._on_copy_last = on_copy_last
        self._on_quit = on_quit
        self._config = config or {}
        self._icon = None
        self._thread = None
        self._last_text = ""

    def start(self):
        """Start the tray icon in a background thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def update_last_text(self, text: str):
        """Update the 'copy last' text in the tray menu."""
        self._last_text = text
        if self._icon:
            self._icon.update_menu()

    def _run(self):
        """Set up and run the tray icon."""
        import pystray
        from pystray import MenuItem, Menu
        from PIL import Image

        image = self._load_icon()

        def get_menu():
            mode = self._config.get("mode", "hold")
            mode_label = f"Switch to {'Toggle' if mode == 'hold' else 'Hold'} mode"

            items = [
                MenuItem("Open Settings", self._action_settings),
                MenuItem(mode_label, self._action_toggle_mode),
                Menu.SEPARATOR,
            ]

            # Copy last
            if self._last_text:
                truncated = self._last_text[:30]
                if len(self._last_text) > 30:
                    truncated += "…"
                items.append(
                    MenuItem(f"Copy last: {truncated}", self._action_copy_last)
                )
                items.append(Menu.SEPARATOR)

            items.extend([
                MenuItem("Check for Updates", self._action_check_updates),
                Menu.SEPARATOR,
                MenuItem("Quit", self._action_quit),
            ])

            return items

        self._icon = pystray.Icon(
            name="REREAL-Spitit",
            icon=image,
            title="REREAL - Spitit",
            menu=Menu(lambda: get_menu()),
        )

        self._icon.run()

    def _load_icon(self):
        """Load the tray icon image."""
        from PIL import Image, ImageDraw

        # Try to load from assets
        try:
            from src.config import get_asset_path
            icon_path = get_asset_path("icon.png")
            if icon_path.exists():
                return Image.open(icon_path).resize((64, 64))
        except Exception:
            pass

        # Fallback: generate programmatically
        return self._generate_icon()

    def _generate_icon(self):
        """Generate a simple tray icon programmatically."""
        from PIL import Image, ImageDraw

        size = 64
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Yellow rounded square background
        margin = 4
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=10,
            fill="#FFD505",
        )

        # 5 dark bars
        inner_left = 14
        inner_right = size - 14
        inner_width = inner_right - inner_left
        bar_heights_pct = [0.38, 0.60, 1.0, 0.60, 0.38]
        bar_w = max(3, inner_width // 9)
        gap = max(2, inner_width // 12)
        total_w = 5 * bar_w + 4 * gap
        start_x = (size - total_w) // 2
        max_h = int(size * 0.5)
        center_y = size // 2

        bar_color = "#111113"
        for i in range(5):
            h = max(3, int(max_h * bar_heights_pct[i]))
            x1 = start_x + i * (bar_w + gap)
            x2 = x1 + bar_w
            y1 = center_y - h // 2
            y2 = center_y + h // 2
            draw.rounded_rectangle([x1, y1, x2, y2], radius=bar_w // 2, fill=bar_color)

        return img

    def _action_settings(self, icon=None, item=None):
        if self._on_open_settings:
            self._on_open_settings()

    def _action_toggle_mode(self, icon=None, item=None):
        if self._on_toggle_mode:
            self._on_toggle_mode()

    def _action_check_updates(self, icon=None, item=None):
        if self._on_check_updates:
            self._on_check_updates()

    def _action_copy_last(self, icon=None, item=None):
        if self._on_copy_last:
            self._on_copy_last()

    def _action_quit(self, icon=None, item=None):
        if self._on_quit:
            self._on_quit()
