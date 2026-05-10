"""Groq Whisper transcription (groq imported on call)."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def transcribe_audio(
    wav_path: Path,
    api_key: str,
    language: str,
    model: str = "whisper-large-v3-turbo",
) -> str:
    from groq import Groq

    if not api_key or not api_key.strip():
        raise ValueError("API key is not set. Open Settings and add your Groq API key.")

    client = Groq(api_key=api_key.strip())
    lang = (language or "").strip().lower()

    create_kwargs: dict = {"file": None, "model": model}
    if lang and lang != "auto":
        create_kwargs["language"] = lang

    try:
        with open(wav_path, "rb") as audio_file:
            create_kwargs["file"] = (wav_path.name, audio_file.read())
            transcription = client.audio.transcriptions.create(**create_kwargs)
    except Exception as e:
        logger.error(f"Groq API transcription failed: {e}", exc_info=True)
        raise RuntimeError(f"Transcription failed: {e}")

    text = getattr(transcription, "text", None) or ""
    return text.strip()
