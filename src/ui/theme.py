"""
REREAL - Spitit: Theme constants.
All colors, fonts, and design tokens for the glassmorphism dark UI.
"""

# ── Color Palette ──────────────────────────────────────────────────────────

BG_DEEP      = "#0a0a0b"       # deepest background
BG_BASE      = "#111113"       # main window background
BG_SURFACE   = "#1a1a1e"       # card/section background
BG_ELEVATED  = "#222228"       # elevated surface (hover)
GLASS_BG     = "#16161a"       # glassmorphism panel base
GLASS_BORDER = "#2a2a2e"       # subtle white border (pre-computed 8% white on dark bg)
GLASS_BLUR   = "#1e1e24"       # semi-transparent equivalent (used in pill)

ACCENT       = "#FFD505"       # primary yellow — REREAL brand
ACCENT_HOVER = "#e6c000"       # darker yellow on hover
ACCENT_DIM   = "#3d3210"       # 19% opacity yellow on dark bg (glow, highlights)

TEXT_PRIMARY   = "#f0f0f2"
TEXT_SECONDARY = "#9090a0"
TEXT_MUTED     = "#505060"
TEXT_ON_ACCENT = "#0a0a0b"

STATE_RECORDING    = "#FFD505"   # yellow
STATE_TRANSCRIBING = "#4d9eff"   # blue
STATE_DONE         = "#3ddc84"   # green
STATE_ERROR        = "#ff5f5f"   # red

# ── Fonts ──────────────────────────────────────────────────────────────────

FONT_FAMILY = "Segoe UI Variable Display"
FONT_FAMILY_FALLBACK = "Segoe UI"
FONT_MONO   = "Cascadia Code"
FONT_MONO_FALLBACK = "Consolas"


def get_fonts():
    """
    Create and return CTkFont instances. Must be called after CTk root exists.
    Returns a dict of font objects.
    """
    from customtkinter import CTkFont
    import tkinter.font as tkfont

    # Check if preferred font family is available
    available_families = tkfont.families()
    family = FONT_FAMILY if FONT_FAMILY in available_families else FONT_FAMILY_FALLBACK
    mono = FONT_MONO if FONT_MONO in available_families else FONT_MONO_FALLBACK

    return {
        "xl":    CTkFont(family=family, size=22, weight="bold"),
        "lg":    CTkFont(family=family, size=16, weight="bold"),
        "md":    CTkFont(family=family, size=14),
        "md_b":  CTkFont(family=family, size=14, weight="bold"),
        "sm":    CTkFont(family=family, size=12),
        "xs":    CTkFont(family=family, size=11),
        "mono":  CTkFont(family=mono,   size=12),
    }


# ── Dimension Constants ────────────────────────────────────────────────────

CORNER_RADIUS = 12
CORNER_RADIUS_SM = 8
BORDER_WIDTH = 1

# Pill
PILL_WIDTH = 120
PILL_HEIGHT = 34
PILL_ALPHA = 0.94
PILL_TICK_MS = 52  # animation tick in ms

# Settings window
SETTINGS_WIDTH = 520
SETTINGS_HEIGHT = 720

# Splash
SPLASH_WIDTH = 460
SPLASH_HEIGHT = 320

# ── Glassmorphism style kwargs (for easy re-use) ────────────────────────────

GLASS_FRAME_KWARGS = {
    "fg_color": GLASS_BG,
    "border_color": GLASS_BORDER,
    "border_width": BORDER_WIDTH,
    "corner_radius": CORNER_RADIUS,
}
