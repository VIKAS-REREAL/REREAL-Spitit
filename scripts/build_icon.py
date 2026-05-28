"""
REREAL - Spitit: Icon generator.
Parses the custom SVG icon at docs/icon.svg and renders it as a 512×512 PNG and a multi-resolution ICO.
"""

import os
import sys
import re
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def generate_icon():
    """Generate the app icon as PNG and ICO by parsing docs/icon.svg."""
    from PIL import Image, ImageDraw

    root = get_project_root()
    svg_path = root / "docs" / "icon.svg"
    
    if not svg_path.exists():
        print(f"[Error] Custom icon SVG not found at {svg_path}")
        return

    with open(svg_path, "r") as f:
        svg_content = f.read()

    # Find all <rect ... /> elements
    rect_matches = re.findall(r'<rect\s+([^>]+)/>', svg_content)
    
    # Scale from 600x600 down to 512x512
    size = 512
    scale = size / 600.0

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    for rect in rect_matches:
        def get_attr(name, default="0"):
            m = re.search(fr'{name}="([^"]+)"', rect)
            return m.group(1) if m else default

        x = float(get_attr("x", "0"))
        y = float(get_attr("y", "0"))
        w = float(get_attr("width", "600"))
        h = float(get_attr("height", "600"))
        rx = float(get_attr("rx", "0"))
        fill = get_attr("fill", "black")

        x1 = x * scale
        y1 = y * scale
        x2 = (x + w) * scale
        y2 = (y + h) * scale
        r = rx * scale

        draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill)

    # Save to assets/icon.png and assets/icon.ico
    assets_dir = root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    png_path = assets_dir / "icon.png"
    img.save(str(png_path), "PNG")
    print(f"[OK] Saved assets PNG: {png_path}")

    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_path = assets_dir / "icon.ico"
    img.save(
        str(ico_path),
        format="ICO",
        sizes=[(s, s) for s in ico_sizes],
    )
    print(f"[OK] Saved assets ICO: {ico_path}")

    # Copy to assets/icon.svg
    import shutil
    try:
        shutil.copy(str(svg_path), str(assets_dir / "icon.svg"))
        print(f"[OK] Copied custom SVG to: {assets_dir / 'icon.svg'}")
    except Exception as e:
        print(f"[Warning] Failed to copy custom SVG to assets: {e}")

    # Save copies directly to docs/icon.png and docs/icon.ico
    docs_dir = root / "docs"
    img.save(str(docs_dir / "icon.png"), "PNG")
    print(f"[OK] Saved docs PNG: {docs_dir / 'icon.png'}")
    img.save(
        str(docs_dir / "icon.ico"),
        format="ICO",
        sizes=[(s, s) for s in ico_sizes],
    )
    print(f"[OK] Saved docs ICO: {docs_dir / 'icon.ico'}")


if __name__ == "__main__":
    generate_icon()
