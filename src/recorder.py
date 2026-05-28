"""
REREAL - Spitit: Audio recorder.
Captures microphone audio using sounddevice, stores in-memory as WAV bytes.
"""

import io
import struct
import threading
import time
import wave


class Recorder:
    """
    Records audio from the microphone into an in-memory WAV buffer.
    
    - Sample rate: 16000 Hz, mono, float32 → converted to int16 PCM for Groq.
    - Minimum duration: 0.3s (else discard).
    - Maximum duration: 120s (auto-stop).
    - Chunk size: 1024 frames.
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_SIZE = 1024
    MIN_DURATION = 0.3
    MAX_DURATION = 120.0

    def __init__(self, device_index=None):
        self._device_index = device_index
        self._frames = []
        self._recording = False
        self._start_time = 0.0
        self._stream = None
        self._lock = threading.Lock()
        self._auto_stop_callback = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def duration(self) -> float:
        if not self._recording:
            return 0.0
        return time.time() - self._start_time

    def set_device(self, device_index):
        """Set the recording device index."""
        self._device_index = device_index

    def start(self, on_auto_stop=None):
        """Start recording. on_auto_stop is called if max duration is reached."""
        import sounddevice as sd
        import numpy as np

        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._recording = True
            self._start_time = time.time()
            self._auto_stop_callback = on_auto_stop

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[Recorder] Status: {status}")
            if self._recording:
                self._frames.append(indata.copy())
                # Check max duration
                if time.time() - self._start_time >= self.MAX_DURATION:
                    self._recording = False
                    if self._auto_stop_callback:
                        self._auto_stop_callback()

        try:
            self._stream = sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="float32",
                blocksize=self.CHUNK_SIZE,
                device=self._device_index,
                callback=callback,
            )
            self._stream.start()
        except Exception as e:
            self._recording = False
            raise RuntimeError(f"Failed to start recording: {e}") from e

    def stop(self) -> bytes:
        """
        Stop recording and return WAV bytes (int16 PCM).
        Returns None if recording was too short.
        Raises ValueError if audio is silence.
        """
        import numpy as np

        with self._lock:
            self._recording = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        duration = time.time() - self._start_time

        if duration < self.MIN_DURATION or not self._frames:
            return None

        # Concatenate all frames
        audio_data = np.concatenate(self._frames, axis=0).flatten()

        # Convert float32 [-1, 1] to int16
        audio_int16 = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)

        # Write to in-memory WAV
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)  # int16 = 2 bytes
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.read()

    def cancel(self):
        """Cancel recording without returning data."""
        with self._lock:
            self._recording = False
            self._frames = []

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def check_silence(self, wav_bytes: bytes, threshold: float = 0.01) -> bool:
        """
        Check if WAV audio is below the silence threshold.
        Returns True if the audio is silence (too quiet).
        """
        import numpy as np

        # Read the WAV data back to get raw samples
        wav_buffer = io.BytesIO(wav_bytes)
        with wave.open(wav_buffer, "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0

        rms = float(np.sqrt(np.mean(audio ** 2)))
        return rms < threshold

    @staticmethod
    def list_devices() -> list:
        """List all available input audio devices."""
        import sounddevice as sd

        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append({
                    "index": i,
                    "name": dev["name"],
                    "sample_rate": int(dev["default_samplerate"]),
                    "channels": dev["max_input_channels"],
                })
        return input_devices
