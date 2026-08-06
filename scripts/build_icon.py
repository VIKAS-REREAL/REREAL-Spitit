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
    vb_match = re.search(r'viewBox=["\']\s*\S+\s+\S+\s+(\S+)\s+(\S+)', svg_content)
    src_w = float(vb_match.group(1)) if vb_match else 600.0
    src_h = float(vb_match.group(2)) if vb_match else 600.0
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


def generate_icon():
    """Generate the app icon from assets/icon.svg (the authoritative brand icon)."""
    root = get_project_root()
    # SOURCE: assets/icon.svg is the master (richer gradient version)
    svg_path = root / "assets" / "icon.svg"

    if not svg_path.exists():
        print(f"[Error] Source icon not found: {svg_path}")
        sys.exit(1)

    print(f"[*] Rendering from {svg_path}")
    size = 512

    img = _try_cairosvg(svg_path, size)
    if img is None:
        print("[*] cairosvg not available, using PIL rect fallback")
        img = _render_with_pil(svg_path, size)

    assets_dir = root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = root / "docs"

    ico_sizes = [16, 32, 48, 64, 128, 256]

    # Save assets/icon.png and assets/icon.ico
    png_path = assets_dir / "icon.png"
    img.save(str(png_path), "PNG")
    print(f"[OK] Saved: {png_path}")

    ico_path = assets_dir / "icon.ico"
    img.save(str(ico_path), format="ICO", sizes=[(s, s) for s in ico_sizes])
    print(f"[OK] Saved: {ico_path}")

    # Mirror to docs/ for the web page
    img.save(str(docs_dir / "icon.png"), "PNG")
    img.save(str(docs_dir / "icon.ico"), format="ICO", sizes=[(s, s) for s in ico_sizes])
    print(f"[OK] Saved copies to docs/")

    # docs/icon.svg — copy the same SVG so the web page nav shows the richer icon
    import shutil
    shutil.copy(str(svg_path), str(docs_dir / "icon.svg"))
    print(f"[OK] Copied assets/icon.svg → docs/icon.svg")


if __name__ == "__main__":
    generate_icon()
