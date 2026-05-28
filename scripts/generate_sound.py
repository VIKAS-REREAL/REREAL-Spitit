"""
REREAL - Spitit: Done sound generator.
Creates a subtle 2-tone chime (C5 + E5) as done.wav.
"""

import os
from pathlib import Path


def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


def generate_sound():
    """Generate the done chime WAV file."""
    import numpy as np
    from scipy.io.wavfile import write

    sr = 44100
    duration = 0.18  # seconds
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float64)

    # Two-tone chime: C5 then E5
    freq1, freq2 = 523.25, 659.25
    tone = (
        np.sin(2 * np.pi * freq1 * t) * np.exp(-t * 18) * 0.4 +
        np.sin(2 * np.pi * freq2 * t) * np.exp(-t * 22) * 0.3
    )

    # Normalize and convert to int16
    tone = np.clip(tone, -1.0, 1.0)
    tone_int16 = (tone * 32767).astype(np.int16)

    # Save
    root = get_project_root()
    sound_dir = root / "assets" / "sound"
    sound_dir.mkdir(parents=True, exist_ok=True)

    output_path = sound_dir / "done.wav"
    write(str(output_path), sr, tone_int16)
    print(f"[OK] Saved: {output_path}")


if __name__ == "__main__":
    generate_sound()
