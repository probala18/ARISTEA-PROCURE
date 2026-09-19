"""
Module 10: Speech AI Package.
Exports provider abstractions, schemas, and SpeechService.
"""
from backend.app.services.speech.schemas import (
    SpeechLanguage,
    TranscriptionResult,
    SynthesisRequest,
    SynthesisResult,
    VoiceQueryResponse,
)
from backend.app.services.speech.stt_provider import (
    BaseSTTProvider,
    FasterWhisperSTTProvider,
    BenchmarkWavSTTProvider,
    get_stt_provider,
)
from backend.app.services.speech.tts_provider import (
    BaseTTSProvider,
    GTTSProvider,
    Pyttsx3TTSProvider,
    MockTTSProvider,
    get_tts_provider,
)
from backend.app.services.speech.speech_service import SpeechService

__all__ = [
    "SpeechLanguage",
    "TranscriptionResult",
    "SynthesisRequest",
    "SynthesisResult",
    "VoiceQueryResponse",
    "BaseSTTProvider",
    "FasterWhisperSTTProvider",
    "BenchmarkWavSTTProvider",
    "get_stt_provider",
    "BaseTTSProvider",
    "GTTSProvider",
    "Pyttsx3TTSProvider",
    "MockTTSProvider",
    "get_tts_provider",
    "SpeechService",
]
