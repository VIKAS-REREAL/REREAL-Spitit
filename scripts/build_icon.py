"""
REREAL - Spitit: Icon generator.
Reads assets/icon.svg (the full-quality brand icon with gradients/filters)
and renders it as a multi-resolution PNG and ICO for the app, installer,
and docs pages.

Preferred renderer: cairosvg (pip install cairosvg)
Fallback renderer: PIL rect-parser (no external deps)
"""

import os
import sys
import re
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def _try_cairosvg(svg_path: Path, size: int):
    """Try rendering SVG with cairosvg. Returns PIL Image or None."""
    try:
        import cairosvg
        from PIL import Image
        import io
        png_bytes = cairosvg.svg2png(
            url=str(svg_path),
            output_width=size,
            output_height=size,
        )
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    except ImportError:
        return None
    except Exception as e:
        print(f"[Warning] cairosvg render failed: {e}")
        return None


def _render_with_pil(svg_path: Path, size: int):
    """Fallback: parse <rect> elements and draw with PIL."""
    from PIL import Image, ImageDraw

    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Detect viewBox width/height for scale
    vb_match = re.search(r'viewBox=["\']\s*([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)', svg_content)
    src_w = float(vb_match.group(3)) if vb_match else 600.0
    src_h = float(vb_match.group(4)) if vb_match else 600.0
    scale = size / max(src_w, src_h)


    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    rect_matches = re.findall(r'<rect\s+([^>]+)/>', svg_content)
    for rect in rect_matches:
        def get_attr(name, default="0"):
            m = re.search(fr'{name}=["\']([^"\']+)', rect)
            return m.group(1) if m else default

        x = float(get_attr("x", "0"))
        y = float(get_attr("y", "0"))
        w = float(get_attr("width", str(src_w)))
        h = float(get_attr("height", str(src_h)))
        rx = float(get_attr("rx", "0"))
        fill = get_attr("fill", "black")

        # Parse gradient references — use first gradient stop color
        if fill.startswith("url("):
            grad_id = re.search(r'url\(#([^)]+)\)', fill)
            if grad_id:
                gid = grad_id.group(1)
                stop = re.search(rf'id="{gid}".*?stop-color=["\']([^"\']+)', svg_content, re.DOTALL)
                fill = stop.group(1) if stop else "#FFD505"
            else:
                fill = "#FFD505"

        draw.rounded_rectangle(
            [x * scale, y * scale, (x + w) * scale, (y + h) * scale],
            radius=rx * scale,
            fill=fill,
        )

    return img


def make_multi_resolution_ico():
    """
    Ensure assets/icon.ico contains all 8 standard Windows resolutions
    (16x16, 24x24, 32x32, 48x48, 64x64, 96x96, 128x128, 256x256)
    in uncompressed BMP format for 100% Inno Setup & PyInstaller compatibility.
    """
    root = get_project_root()
    assets_dir = root / "assets"
    docs_dir = root / "docs"
    png_path = assets_dir / "icon.png"
    ico_path = assets_dir / "icon.ico"

    if not png_path.exists():
        print(f"[Warning] Cannot build multi-res ICO: {png_path} missing")
        return

    try:
        from PIL import Image
        img = Image.open(png_path).convert("RGBA")
        ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (96, 96), (128, 128), (256, 256)]
        img.save(str(ico_path), format="ICO", sizes=ico_sizes, bitmap_format="bmp")
        print(f"[OK] Generated uncompressed multi-res ICO for Inno Setup: {ico_path}")

        # Mirror to docs/
        if docs_dir.exists():
            img.save(str(docs_dir / "icon.ico"), format="ICO", sizes=ico_sizes, bitmap_format="bmp")
    except Exception as e:
        print(f"[Warning] Failed building multi-res ICO: {e}")



def generate_icon(force: bool = False):
    """Generate the app icon from assets/icon.svg if missing or forced. Preserves custom icons."""
    root = get_project_root()
    assets_dir = root / "assets"
    png_path = assets_dir / "icon.png"
    ico_path = assets_dir / "icon.ico"
    svg_path = assets_dir / "icon.svg"

    if "--force" in sys.argv:
        force = True

    # If custom PNG exists, generate 8-frame multi-res ICO from it
    if png_path.exists():
        make_multi_resolution_ico()
        return

    if not force and png_path.exists() and ico_path.exists():
        print(f"[OK] Preserving custom icons: {png_path} and {ico_path}")
        return

    if not svg_path.exists():
        print(f"[Warning] Source icon not found: {svg_path}")
        return

    print(f"[*] Rendering from {svg_path}")
    size = 512

    img = _try_cairosvg(svg_path, size)
    if img is None:
        print("[*] cairosvg not available, using PIL rect fallback")
        img = _render_with_pil(svg_path, size)

    assets_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = root / "docs"

    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (96, 96), (128, 128), (256, 256)]

    # Save assets/icon.png and assets/icon.ico
    img.save(str(png_path), "PNG")
    print(f"[OK] Saved: {png_path}")

    img.save(str(ico_path), format="ICO", sizes=ico_sizes)
    print(f"[OK] Saved: {ico_path}")

    if docs_dir.exists():
        img.save(str(docs_dir / "icon.png"), "PNG")
        img.save(str(docs_dir / "icon.ico"), format="ICO", sizes=ico_sizes)
        print(f"[OK] Saved copies to docs/")


    # docs/icon.svg — copy the same SVG so the web page nav shows the richer icon
    import shutil
    shutil.copy(str(svg_path), str(docs_dir / "icon.svg"))
    print("[OK] Copied assets/icon.svg -> docs/icon.svg")


if __name__ == "__main__":
    generate_icon()
