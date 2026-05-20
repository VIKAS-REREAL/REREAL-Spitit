"""Microphone capture to WAV using sounddevice (loaded on first use)."""

from __future__ import annotations

import threading
import time
from pathlib import Path


def record_to_wav(
    out_path: Path,
    stop_event: threading.Event,
    sample_rate: int = 16000,
) -> bool:
    """
    Record mono float audio until stop_event is set. Writes 16-bit PCM WAV.
    Returns False if no samples or recording too short / error.
    """
    import numpy as np
    import sounddevice as sd
    from scipy.io import wavfile

    chunks: list = []

    def callback(indata, frames, t, status) -> None:
        if status:
            pass
        chunks.append(indata.copy())

    try:
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            callback=callback,
        )
        stream.start()
        try:
            while not stop_event.is_set():
                time.sleep(0.02)
        finally:
            stream.stop()
            stream.close()
    except Exception:
        return False

    if not chunks:
        return False

    audio = np.concatenate(chunks, axis=0).reshape(-1)
    if audio.size < sample_rate * 0.25:
        return False

    audio_i16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    try:
        wavfile.write(str(out_path), sample_rate, audio_i16)
    except Exception:
        return False
    return True
