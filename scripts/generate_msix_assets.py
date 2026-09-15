"""
REREAL - Spitit: Modern Windows 10/11 MSIX Visual Asset Generator.
Generates full set of DPI-scaled, target-sized, and unplated (altform-unplated)
assets from assets/icon.png so the app has clean, borderless icons everywhere:
- Taskbar (unplated, no square box)
- Start Menu & All Apps list (unplated)
- Alt+Tab task switcher
- Settings > Installed Apps
- Windows App Installer dialog
- Microsoft Store listing
"""

import sys
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def generate_msix_assets():
    root = get_project_root()
    icon_path = root / "assets" / "icon.png"
    assets_dir = root / "msix" / "Assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if not icon_path.exists():
        print(f"[Error] Source icon not found: {icon_path}")
        sys.exit(1)

    try:
        from PIL import Image
    except ImportError:
        print("[Error] Pillow is required to generate MSIX assets. Install via: pip install Pillow")
        sys.exit(1)

    base_img = Image.open(icon_path).convert("RGBA")

    # Splash screen background color
    splash_bg = (15, 23, 42, 255)  # Slate dark #0F172A

    # Target sizes for Square44x44Logo (plated, unplated, light-unplated)
    target_sizes = [16, 20, 24, 30, 32, 36, 40, 44, 48, 60, 64, 72, 80, 96, 256]

    # Scales for each asset type
    scales = {
        "scale-100": 1.0,
        "scale-125": 1.25,
        "scale-150": 1.50,
        "scale-200": 2.0,
        "scale-400": 4.0,
    }

    # Helper to generate an image
    def make_asset(out_name: str, target_w: int, target_h: int, padding: float = 0.0, fill_bg=None):
        out_path = assets_dir / out_name
        if fill_bg:
            canvas = Image.new("RGBA", (target_w, target_h), fill_bg)
        else:
            canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))

        usable_w = int(target_w * (1.0 - 2 * padding))
        usable_h = int(target_h * (1.0 - 2 * padding))

        scale = min(usable_w / base_img.width, usable_h / base_img.height)
        scaled_w = max(1, int(base_img.width * scale))
        scaled_h = max(1, int(base_img.height * scale))

        resized_img = base_img.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
        offset_x = (target_w - scaled_w) // 2
        offset_y = (target_h - scaled_h) // 2

        canvas.paste(resized_img, (offset_x, offset_y), resized_img)
        canvas.save(out_path, "PNG")

    print(f"[*] Generating comprehensive MSIX visual assets in {assets_dir}...")

    # 1. Base logos (transparent background, edge-to-edge)
    base_assets = {
        "Square44x44Logo.png": (44, 44, 0.0, None),
        "Square71x71Logo.png": (71, 71, 0.0, None),
        "Square150x150Logo.png": (150, 150, 0.0, None),
        "Wide310x150Logo.png": (310, 150, 0.0, None),
        "Square310x310Logo.png": (310, 310, 0.0, None),
        "StoreLogo.png": (50, 50, 0.0, None),
        "SplashScreen.png": (620, 300, 0.25, splash_bg),
    }
    for name, (w, h, pad, bg) in base_assets.items():
        make_asset(name, w, h, pad, bg)

    # 2. Square44x44Logo target sizes & unplated variants (CRITICAL FOR TASKBAR & APP LIST)
    for sz in target_sizes:
        # Standard plated
        make_asset(f"Square44x44Logo.targetsize-{sz}.png", sz, sz, 0.0, None)
        # Unplated (removes the square backplate in taskbar and search!)
        make_asset(f"Square44x44Logo.targetsize-{sz}_altform-unplated.png", sz, sz, 0.0, None)
        # Light unplated (for light theme taskbar)
        make_asset(f"Square44x44Logo.targetsize-{sz}_altform-lightunplated.png", sz, sz, 0.0, None)

    # 3. DPI Scale variants for all main logos
    scale_definitions = {
        "Square44x44Logo": (44, 44, 0.0, None),
        "Square71x71Logo": (71, 71, 0.0, None),
        "Square150x150Logo": (150, 150, 0.0, None),
        "Wide310x150Logo": (310, 150, 0.0, None),
        "Square310x310Logo": (310, 310, 0.0, None),
        "StoreLogo": (50, 50, 0.0, None),
        "SplashScreen": (620, 300, 0.25, splash_bg),
    }
    for base_name, (w, h, pad, bg) in scale_definitions.items():
        for scale_name, factor in scales.items():
            tw = int(w * factor)
            th = int(h * factor)
            make_asset(f"{base_name}.{scale_name}.png", tw, th, pad, bg)

    total_files = len(list(assets_dir.glob("*.png")))
    print(f"[OK] Generated {total_files} MSIX visual assets with unplated taskbar support.")


if __name__ == "__main__":
    generate_msix_assets()
