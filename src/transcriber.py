"""
REREAL - Spitit: Groq Whisper transcription client.
Handles all language modes including Hinglish with LLM post-processing.
"""

import io


# Language display names → internal codes
LANGUAGES = {
    "Auto-detect": "auto",
    "English": "en",
    "Hinglish": "hinglish",
    "Hindi": "hi",
    "Hindi + English Mix": "mixed_hi_en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
}

# Reverse mapping
LANGUAGE_NAMES = {v: k for k, v in LANGUAGES.items()}

# Whisper-compatible language codes (subset that Whisper accepts)
WHISPER_LANG_CODES = {
    "en", "hi", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
}

HINGLISH_WHISPER_PROMPT = (
    "The speaker is an Indian person speaking Hinglish — a natural mix of Hindi and English. "
    "Transcribe all Hindi words in Roman/English script (transliteration), NOT Devanagari. "
    "English words should remain in English. "
    "For example: 'yaar kya scene hai' not 'यार क्या सीन है'. "
    "Another example: 'main kal office jaaunga' not 'मैं कल ऑफिस जाऊंगा'. "
    "Write exactly what is spoken, do not translate."
)

HINGLISH_SYSTEM_PROMPT = """You are a Hinglish text normalizer. 
The input is speech-to-text output of someone speaking Hinglish (Hindi words mixed with English, spoken casually).
Your job:
1. If any Hindi words appear in Devanagari script, convert them to Roman transliteration (e.g. 'यार' → 'yaar', 'क्या' → 'kya', 'हो गया' → 'ho gaya')
2. Keep all English words exactly as they are
3. Keep the exact meaning and words — do NOT translate, do NOT rephrase
4. Fix obvious STT errors in context (e.g. "main kal offer jaaunga" → "main kal office jaaunga" if that makes more sense)
5. Output ONLY the cleaned Hinglish text, nothing else

Examples:
Input: "यार kya scene hai aaj"
Output: "yaar kya scene hai aaj"

Input: "I need to submit the report kal tak"  
Output: "I need to submit the report kal tak"

Input: "bhai bahut zyada kaam hai"
Output: "bhai bahut zyada kaam hai"
"""

MIXED_HI_EN_PROMPT = (
    "The speaker switches between Hindi and English. "
    "Transcribe Hindi speech in Devanagari script and English speech in English. "
    "Do not translate — preserve the exact language used for each word."
)

MODEL_WHISPER = "whisper-large-v3-turbo"
MODEL_LLM = "llama-3.1-8b-instant"


def transcribe(wav_bytes: bytes, api_key: str, language: str = "en") -> str:
    """
    Transcribe WAV audio using Groq Whisper API.
    
    Args:
        wav_bytes: Raw WAV file bytes (int16 PCM, 16kHz mono).
        api_key: Groq API key.
        language: Language code from LANGUAGES dict values.
    
    Returns:
        Transcribed text string.
    
    Raises:
        ValueError: If API key is missing or transcription fails.
        RuntimeError: If Groq API call fails.
    """
    if not api_key:
        raise ValueError("Groq API key is not set. Please add your key in Settings.")

    from groq import Groq

    client = Groq(api_key=api_key)

    # Build transcription kwargs
    create_kwargs = {
        "model": MODEL_WHISPER,
        "file": ("recording.wav", io.BytesIO(wav_bytes)),
        "response_format": "text",
    }

    # Language-specific configuration
    if language == "en":
        create_kwargs["language"] = "en"

    elif language == "hi":
        create_kwargs["language"] = "hi"

    elif language == "auto":
        # No language param — Whisper auto-detects
        pass

    elif language == "hinglish":
        # Don't set language — let Whisper detect, but guide with prompt
        create_kwargs["prompt"] = HINGLISH_WHISPER_PROMPT

    elif language == "mixed_hi_en":
        create_kwargs["prompt"] = MIXED_HI_EN_PROMPT

    elif language in WHISPER_LANG_CODES:
        create_kwargs["language"] = language

    # else: unsupported language, let Whisper auto-detect

    try:
        transcription = client.audio.transcriptions.create(**create_kwargs)
    except Exception as e:
        raise RuntimeError(f"Groq API error: {e}") from e

    # The response is a string when response_format="text"
    raw_text = str(transcription).strip()

    if not raw_text:
        raise ValueError("Transcription returned empty text.")

    # Hinglish post-processing: pass through LLM for cleanup
    if language == "hinglish":
        raw_text = _hinglish_cleanup(client, raw_text)

    return raw_text


def _hinglish_cleanup(client, raw_text: str) -> str:
    """
    Post-process Hinglish transcription through Groq LLM to ensure
    Roman script output and fix STT artifacts.
    """
    try:
        completion = client.chat.completions.create(
            model=MODEL_LLM,
            messages=[
                {"role": "system", "content": HINGLISH_SYSTEM_PROMPT},
                {"role": "user", "content": raw_text},
            ],
            temperature=0.05,
            max_tokens=1024,
        )
        cleaned = completion.choices[0].message.content.strip()
        return cleaned if cleaned else raw_text
    except Exception:
        # If LLM cleanup fails, return raw Whisper output
        return raw_text


def test_connection(api_key: str) -> tuple[bool, str]:
    """
    Test API connection by sending a minimal request.
    Returns (success: bool, message: str).
    """
    if not api_key:
        return False, "No API key provided."

    if not api_key.startswith("gsk_"):
        return False, "Invalid API key format (should start with 'gsk_')."

    try:
        from groq import Groq
        import numpy as np

        client = Groq(api_key=api_key)

        # Generate a 1-second silent WAV
        sr = 16000
        silence = np.zeros(sr, dtype=np.int16)
        wav_buffer = io.BytesIO()
        import wave
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(silence.tobytes())
        wav_buffer.seek(0)

        client.audio.transcriptions.create(
            model=MODEL_WHISPER,
            file=("test.wav", wav_buffer),
            response_format="text",
            language="en",
        )
        return True, "Connection successful! API key is valid."
    except Exception as e:
        return False, f"Connection failed: {e}"
