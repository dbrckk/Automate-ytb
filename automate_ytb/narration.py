"""Optional natural neural TTS for original video narration.

The Kokoro model is loaded only when explicitly selected. Plain imports,
offline previews, and test runs never download a model or contact an API.
"""
from __future__ import annotations

import math
from pathlib import Path
import tempfile
import wave

DEFAULT_VOICES = {"fr": "ff_siwis", "en": "af_heart"}
VOICE_CHOICES = {"fr": frozenset({"ff_siwis"}),
                 "en": frozenset({"af_heart", "af_bella", "am_michael"})}
SAMPLE_RATE_KOKORO = 24000


class SpeechEngine:
    def __init__(self, *, engine: str, language: str, voice: str | None = None):
        if engine not in ("espeak", "kokoro"):
            raise ValueError("Supported speech engines: espeak, kokoro")
        if language not in ("fr", "en"):
            raise ValueError("Speech language must be fr or en")
        self.engine = engine
        self.language = language
        self.voice = None
        self._pipeline = None
        if engine == "kokoro":
            self.voice = voice or DEFAULT_VOICES[language]
            if self.voice not in VOICE_CHOICES[language]:
                raise ValueError("Unsupported voice/language combination")
            try:
                from kokoro import KPipeline
            except ImportError:
                raise RuntimeError(
                    "Kokoro is optional. Install: python -m pip install -e '.[speech]'"
                ) from None
            # Load once per episode, not once per sentence or scene.
            self._pipeline = KPipeline(lang_code="f" if language == "fr" else "a",
                                       repo_id="hexgrad/Kokoro-82M")
        elif voice:
            raise ValueError("Custom voices require Kokoro")

    def audio(self, text: str) -> tuple[bytes, int]:
        if not isinstance(text, str) or not text.strip() or len(text) > 8000:
            raise ValueError("Narration must be 1–8000 characters per scene")
        if self.engine == "espeak":
            from .studio import synthesize_voice
            with tempfile.TemporaryDirectory(prefix="automate-ytb-voice-") as folder:
                wav_path = Path(folder) / "speech.wav"
                if not synthesize_voice(text, wav_path, self.language):
                    raise RuntimeError("eSpeak is unavailable on this runner")
                with wave.open(str(wav_path), "rb") as wav:
                    info = wav.getparams()
                    if info.nchannels != 1 or info.sampwidth != 2 or info.comptype != "NONE":
                        raise RuntimeError("Unsupported eSpeak WAV format")
                    frames = wav.readframes(info.nframes)
                    if not frames:
                        raise RuntimeError("eSpeak returned empty audio")
                    return frames, info.framerate
        # Kokoro returns float samples at 24kHz in the published KPipeline API.
        try:
            import numpy as np
        except ImportError:
            raise RuntimeError("Kokoro requires NumPy; install speech dependencies") from None
        segments = []
        for generated in self._pipeline(text, voice=self.voice, speed=1.0):
            # Kokoro 0.9.4 returns a KPipeline.Result carrying .audio.
            # Older versions also documented (graphemes, phonemes, audio)
            # tuples; accepting both keeps existing user projects readable.
            if hasattr(generated, "audio"):
                sound = generated.audio
            elif isinstance(generated, (tuple, list)) and len(generated) >= 3:
                sound = generated[2]
            else:
                raise RuntimeError("Kokoro returned an unsupported audio segment")
            if hasattr(sound, "detach"):
                sound = sound.detach().cpu().numpy()
            samples = np.asarray(sound, dtype=np.float32).reshape(-1)
            if samples.size == 0:
                continue
            if not np.isfinite(samples).all():
                raise RuntimeError("Kokoro returned non-finite audio samples")
            if samples.size > 24000 * 600:
                raise RuntimeError("Kokoro audio segment is unexpectedly long")
            segments.append(samples)
        if not segments:
            raise RuntimeError("Kokoro did not synthesize any audio")
        # Add a small inter-segment breath. Each scene gets final silent padding
        # from the episode timeline composer; nothing gets cut to fit the video.
        separator = np.zeros(2400, dtype=np.float32)
        together = np.concatenate(
            [piece for i, audio in enumerate(segments)
             for piece in ((separator, audio) if i else (audio,))]
        )
        pcm = (np.clip(together, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
        if not pcm:
            raise RuntimeError("Kokoro output is empty")
        return pcm, SAMPLE_RATE_KOKORO
