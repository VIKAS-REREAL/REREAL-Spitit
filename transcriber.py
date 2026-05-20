"""Groq Whisper transcription (groq imported on call)."""

from __future__ import annotations

from pathlib import Path


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
    
    if lang == "mixed_hi_en":
        create_kwargs["prompt"] = "The speaker is mixing English and Hindi languages. Transcribe English spoken words in English script, and Hindi spoken words in Devanagari script."
    elif lang and lang not in ("auto", "hinglish"):
        create_kwargs["language"] = lang

    with open(wav_path, "rb") as audio_file:
        create_kwargs["file"] = audio_file
        transcription = client.audio.transcriptions.create(**create_kwargs)

    text = getattr(transcription, "text", None) or ""
    text = text.strip()
    
    if text and lang == "hinglish":
        sys_prompt = "You are a transliterator. Convert the following text into Hinglish (Hindi words written in the English/Latin alphabet). Do NOT translate the meaning to English. For example, 'आप कैसे हैं' becomes 'Aap kaise hain'. If there are any English words in the text, leave them exactly as they are. Output NOTHING but the transliterated text."
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        text = completion.choices[0].message.content.strip()

    return text
