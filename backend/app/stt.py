from io import BytesIO

from faster_whisper import WhisperModel

# Loaded once at import time — model load takes a few seconds, and doing
# that per-request would make every transcription pay that cost twice over.
_model = WhisperModel("small", device="cpu", compute_type="int8")


def transcribe(audio_bytes: bytes) -> str:
    segments, _ = _model.transcribe(BytesIO(audio_bytes))
    return " ".join(segment.text.strip() for segment in segments)
