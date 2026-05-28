"""
REREAL - Spitit: Reusable CTk widgets.
GlassFrame, AccentButton, GhostButton, SectionHeader, etc.
"""

import customtkinter as ctk
from src.ui.theme import (
    GLASS_BG, GLASS_BORDER, BORDER_WIDTH, CORNER_RADIUS, CORNER_RADIUS_SM,
    ACCENT, ACCENT_HOVER, TEXT_ON_ACCENT, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, BG_SURFACE, BG_ELEVATED, BG_BASE, ACCENT_DIM,
)


class GlassFrame(ctk.CTkFrame):
    """Glassmorphism-style frame with subtle border and rounded corners."""

    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": GLASS_BG,
            "border_color": GLASS_BORDER,
            "border_width": BORDER_WIDTH,
            "corner_radius": CORNER_RADIUS,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class AccentButton(ctk.CTkButton):
    """Primary yellow action button."""

    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": ACCENT,
            "hover_color": ACCENT_HOVER,
            "text_color": TEXT_ON_ACCENT,
            "corner_radius": CORNER_RADIUS_SM,
            "height": 40,
            "font": None,  # set by caller with theme fonts
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class GhostButton(ctk.CTkButton):
    """Transparent/outline style button."""

    def __init__(self, master, **kwargs):
        defaults = {
            "fg_color": "transparent",
            "hover_color": BG_ELEVATED,
            "text_color": TEXT_PRIMARY,
            "border_color": GLASS_BORDER,
            "border_width": BORDER_WIDTH,
            "corner_radius": CORNER_RADIUS_SM,
            "height": 40,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)


class SectionHeader(ctk.CTkFrame):
    """Section header with icon and title for settings panels."""

    def __init__(self, master, title: str, icon: str = "", fonts=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        label_text = f"{icon}  {title}" if icon else title
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            text_color=TEXT_PRIMARY,
            font=fonts["lg"] if fonts else None,
            anchor="w",
        )
        self.label.pack(side="left", padx=(4, 0))


class ToggleSwitch(ctk.CTkFrame):
    """Toggle switch with label and description text."""

    def __init__(
        self,
        master,
        label: str,
        description: str = "",
        variable: ctk.BooleanVar = None,
        fonts=None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.title_label = ctk.CTkLabel(
            text_frame,
            text=label,
            text_color=TEXT_PRIMARY,
            font=fonts["md_b"] if fonts else None,
            anchor="w",
        )
        self.title_label.pack(anchor="w")

        if description:
            self.desc_label = ctk.CTkLabel(
                text_frame,
                text=description,
                text_color=TEXT_SECONDARY,
                font=fonts["xs"] if fonts else None,
                anchor="w",
            )
            self.desc_label.pack(anchor="w")

        self.switch = ctk.CTkSwitch(
            self,
            text="",
            variable=variable,
            onvalue=True,
            offvalue=False,
            progress_color=ACCENT,
            button_color=TEXT_PRIMARY,
            button_hover_color=ACCENT_HOVER,
            width=44,
        )
        self.switch.pack(side="right", pady=4)


class RadioCard(ctk.CTkFrame):
    """
    Selectable radio-style card with yellow left border when active.
    """

    def __init__(
        self,
        master,
        title: str,
        subtitle: str = "",
        variable: ctk.StringVar = None,
        value: str = "",
        fonts=None,
        command=None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=GLASS_BG,
            border_color=GLASS_BORDER,
            border_width=BORDER_WIDTH,
            corner_radius=CORNER_RADIUS_SM,
            **kwargs,
        )
        self._variable = variable
        self._value = value
        self._command = command

        self.radio = ctk.CTkRadioButton(
            self,
            text="",
            variable=variable,
            value=value,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            border_color=TEXT_MUTED,
            command=self._on_select,
            width=20,
        )
        self.radio.pack(side="left", padx=(12, 8), pady=12)

        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, pady=12, padx=(0, 12))

        self.title_label = ctk.CTkLabel(
            text_frame,
            text=title,
            text_color=TEXT_PRIMARY,
            font=fonts["md_b"] if fonts else None,
            anchor="w",
        )
        self.title_label.pack(anchor="w")

        if subtitle:
            self.subtitle_label = ctk.CTkLabel(
                text_frame,
                text=subtitle,
                text_color=TEXT_SECONDARY,
                font=fonts["xs"] if fonts else None,
                anchor="w",
            )
            self.subtitle_label.pack(anchor="w")

        # Make entire card clickable
        self.bind("<Button-1>", lambda e: self._click())
        self.title_label.bind("<Button-1>", lambda e: self._click())
        if subtitle:
            self.subtitle_label.bind("<Button-1>", lambda e: self._click())
        text_frame.bind("<Button-1>", lambda e: self._click())

        # Track variable changes for styling
        if variable:
            variable.trace_add("write", lambda *_: self._update_style())

    def _click(self):
        if self._variable:
            self._variable.set(self._value)
        if self._command:
            self._command()

    def _on_select(self):
        self._update_style()
        if self._command:
            self._command()

    def _update_style(self):
        if self._variable and self._variable.get() == self._value:
            self.configure(border_color=ACCENT, fg_color="#3a3721")
        else:
            self.configure(border_color=GLASS_BORDER, fg_color=GLASS_BG)


class HotkeyButton(ctk.CTkButton):
    """
    Styled button for displaying and recording hotkey combos.
    Shows current binding in mono font. Clicks to enter recording mode.
    """

    def __init__(self, master, combo_text: str = "Alt + LShift", fonts=None, **kwargs):
        super().__init__(
            master,
            text=combo_text,
            fg_color=BG_SURFACE,
            hover_color=BG_ELEVATED,
            text_color=TEXT_PRIMARY,
            border_color=GLASS_BORDER,
            border_width=BORDER_WIDTH,
            corner_radius=CORNER_RADIUS_SM,
            font=fonts["mono"] if fonts else None,
            height=38,
            **kwargs,
        )
        self._recording = False

    def set_recording(self, active: bool):
        """Visual feedback for recording state."""
        self._recording = active
        if active:
            self.configure(
                text="Press your combo...",
                border_color=ACCENT,
                fg_color=ACCENT_DIM,
            )
        else:
            self.configure(
                border_color=GLASS_BORDER,
                fg_color=BG_SURFACE,
            )

    def set_combo(self, text: str):
        """Update the displayed key combo."""
        self.configure(text=text)
        self.set_recording(False)


class StatusBadge(ctk.CTkLabel):
    """Small colored badge for version / status display."""

    def __init__(self, master, text: str, color: str = ACCENT, fonts=None, **kwargs):
        # Pre-compute a dark tinted background from the color
        bg_color = StatusBadge._dim_color(color)
        super().__init__(
            master,
            text=f"  {text}  ",
            text_color=color,
            font=fonts["xs"] if fonts else None,
            fg_color=bg_color,
            corner_radius=4,
            **kwargs,
        )

    @staticmethod
    def _dim_color(hex_color: str, factor: float = 0.12) -> str:
        """Create a dimmed version of a hex color (simulating alpha on dark bg)."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) < 6:
            return "#1a1a1e"
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Blend with near-black background
        bg = 0x11
        r = int(bg + (r - bg) * factor)
        g = int(bg + (g - bg) * factor)
        b = int(bg + (b - bg) * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
