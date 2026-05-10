"""Utility: convert assets/icon.png → assets/icon.ico (multi-resolution)."""

from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SRC = ASSETS / "icon.png"
DST = ASSETS / "icon.ico"

SIZES = (256, 128, 64, 32, 16)


def main() -> None:
    src_img = Image.open(SRC).convert("RGBA")
    frames = []
    for s in SIZES:
        resized = src_img.resize((s, s), Image.Resampling.LANCZOS)
        # Pillow expects a list of (size, image) tuples for multi-resolution ICO
        frames.append(resized)

    DST.parent.mkdir(parents=True, exist_ok=True)
    # Save as multi-resolution ICO; first frame is used as base
    frames[0].save(DST, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"OK  {DST}  ({', '.join(f'{s}x{s}' for s in SIZES)})")


if __name__ == "__main__":
    main()
