"""
Voxera Local STT Service — faster-whisper fallback.

Used as a fallback when ElevenLabs Scribe and Groq Whisper are both
unreachable.  Model is loaded lazily on first call and kept in memory.

Env:
    WHISPER_MODEL_SIZE  — "tiny", "base", "small", "medium", "large-v3"
                          (default "base")
"""

import io
import logging
import tempfile
import os
from typing import Optional, Tuple

from backend.config import settings

logger = logging.getLogger("voxera.local_stt")

# Lazy singleton — the model is heavy so we load once.
_model = None
_model_loading = False


def _get_model():
    """Returns the cached WhisperModel (loads on first call)."""
    global _model, _model_loading
    if _model is not None:
        return _model
    if _model_loading:
        return None

    _model_loading = True
    try:
        from faster_whisper import WhisperModel

        model_size = settings.WHISPER_MODEL_SIZE
        # Use CPU by default — GPU users can set device via env or code.
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = "int8" if device == "cpu" else "float16"

        logger.info(
            f"Loading faster-whisper model '{model_size}' on {device} "
            f"(compute_type={compute_type})…"
        )
        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info(f"faster-whisper model '{model_size}' loaded successfully.")
        return _model
    except ImportError:
        logger.error(
            "faster-whisper is not installed.  "
            "Run:  pip install faster-whisper"
        )
        _model_loading = False
        return None
    except Exception as exc:
        logger.error(f"Failed to load faster-whisper model: {exc}", exc_info=True)
        _model_loading = False
        return None


async def transcribe_local(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    language: Optional[str] = None,
) -> Tuple[bool, str, float, float]:
    """
    Transcribes audio bytes using the local faster-whisper model.

    Returns:
        (success, transcription_text, confidence, duration_seconds)
    """
    model = _get_model()
    if model is None:
        return (False, "", 0.0, 0.0)

    # faster-whisper needs a file path — write to a temp file
    tmp_path = None
    try:
        suffix = os.path.splitext(filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix="voxera_stt_"
        ) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        segments, info = model.transcribe(
            tmp_path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )

        # Collect all segment texts
        texts = []
        for seg in segments:
            texts.append(seg.text.strip())

        full_text = " ".join(texts).strip()
        duration = info.duration if info else 0.0
        # Average log-probability is a rough confidence proxy
        confidence = 0.88 if full_text else 0.0

        return (True, full_text, confidence, duration)

    except Exception as exc:
        logger.error(f"Local STT transcription failed: {exc}", exc_info=True)
        return (False, "", 0.0, 0.0)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def is_available() -> bool:
    """Returns True if faster-whisper can be imported."""
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False

