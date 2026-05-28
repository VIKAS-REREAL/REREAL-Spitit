"""
REREAL - Spitit: Icon generator.
Creates the app icon as 512×512 PNG and multi-resolution ICO.

Icon design:
- Rounded square background, fill #FFD505 (yellow)
- 5 vertical bars with rounded tops (waveform)
- Heights: [38%, 60%, 100%, 60%, 38%]
- Bar color: #111113
"""

import os
import sys
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def generate_icon():
    """Generate the app icon as PNG and ICO."""
    from PIL import Image, ImageDraw

    size = 512
    inner_pct = 0.70
    corner_pct = 0.22

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background: rounded square
    margin = 0
    corner_radius = int(size * corner_pct)
    draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=corner_radius,
        fill="#FFD505",
    )

    # Inner area
    inner_size = int(size * inner_pct)
    inner_offset = (size - inner_size) // 2

    # Bar configuration
    bar_heights_pct = [0.38, 0.60, 1.0, 0.60, 0.38]
    num_bars = 5
    bar_width_pct = 0.09
    gap_pct = 0.06

    bar_w = int(inner_size * bar_width_pct)
    gap = int(inner_size * gap_pct)
    max_height = inner_size
    bar_color = "#111113"

    total_width = num_bars * bar_w + (num_bars - 1) * gap
    start_x = (size - total_width) // 2

    # Bottom of bars (vertically centered in inner area)
    center_y = size // 2

    for i in range(num_bars):
        h = max(bar_w, int(max_height * bar_heights_pct[i]))
        x1 = start_x + i * (bar_w + gap)
        x2 = x1 + bar_w
        y_bottom = center_y + max_height // 2
        y_top = y_bottom - h

        # Bar with rounded top and bottom
        r = bar_w // 2
        draw.rounded_rectangle(
            [x1, y_top, x2, y_bottom],
            radius=r,
            fill=bar_color,
        )

    # Save PNG
    root = get_project_root()
    assets_dir = root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    png_path = assets_dir / "icon.png"
    img.save(str(png_path), "PNG")
    print(f"[OK] Saved: {png_path}")

    # Generate ICO with multiple resolutions
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_path = assets_dir / "icon.ico"
    img.save(
        str(ico_path),
        format="ICO",
        sizes=[(s, s) for s in ico_sizes],
    )
    print(f"[OK] Saved: {ico_path}")


if __name__ == "__main__":
    generate_icon()
