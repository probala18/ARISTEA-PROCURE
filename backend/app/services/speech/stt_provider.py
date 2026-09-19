"""
Speech-to-Text (STT) Provider Abstraction and Implementations.
Provides:
- BaseSTTProvider (ABC)
- FasterWhisperSTTProvider (Production neural STT using faster-whisper)
- BenchmarkWavSTTProvider (Deterministic benchmark / fixture matcher for CI and offline unit testing)
"""
import io
import math
import os
import wave
from abc import ABC, abstractmethod
from typing import Optional, Dict

from backend.app.services.speech.schemas import TranscriptionResult, SpeechLanguage


class BaseSTTProvider(ABC):
    """Abstract Base Class for Speech-to-Text Providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider implementation."""
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Indicates whether this provider is a benchmark matcher / mock or real neural model."""
        pass

    @abstractmethod
    def transcribe(
        self, 
        audio_data: bytes, 
        language_hint: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcribes raw audio bytes to text with confidence and language detection.
        
        Args:
            audio_data: Raw bytes of the audio file (WAV/MP3/PCM).
            language_hint: Optional language hint ('en', 'hi', 'ta').
            
        Returns:
            TranscriptionResult with transcript, language, confidence, and repetition signals.
        """
        pass


class FasterWhisperSTTProvider(BaseSTTProvider):
    """
    Production Speech-to-Text implementation using the pretrained faster-whisper model.
    Runs locally on CPU with int8 quantization for high-speed inference.
    """

    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    @property
    def provider_name(self) -> str:
        return f"faster-whisper-{self.model_size}"

    @property
    def is_mock(self) -> bool:
        return False

    def _get_model(self):
        """Lazy loads the Whisper model on first use to reduce startup overhead."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
            except Exception as e:
                raise RuntimeError(
                    f"Failed to load faster-whisper model '{self.model_size}': {e}. "
                    "Ensure faster-whisper is installed or use BenchmarkWavSTTProvider for offline testing."
                )
        return self._model

    def transcribe(
        self, 
        audio_data: bytes, 
        language_hint: Optional[str] = None
    ) -> TranscriptionResult:
        if not audio_data or len(audio_data) < 44:
            raise ValueError("Audio data is empty or too short to contain a valid audio stream.")

        model = self._get_model()
        audio_stream = io.BytesIO(audio_data)

        # Transcribe audio stream
        kwargs = {}
        if language_hint and language_hint in ["en", "hi", "ta"]:
            kwargs["language"] = language_hint

        try:
            segments, info = model.transcribe(audio_stream, beam_size=5, **kwargs)
            segment_list = list(segments)
        except Exception as err:
            raise ValueError(f"Failed to decode or transcribe audio stream: {err}")

        text_parts = [seg.text.strip() for seg in segment_list if seg.text.strip()]
        full_text = " ".join(text_parts).strip()

        # Determine language
        detected_lang = info.language if info and info.language else (language_hint or "en")
        if detected_lang not in ["en", "hi", "ta"]:
            detected_lang = "unknown"

        # Calculate average confidence from segment log probabilities
        if segment_list:
            probs = [math.exp(seg.avg_logprob) for seg in segment_list if hasattr(seg, 'avg_logprob')]
            avg_prob = sum(probs) / len(probs) if probs else (info.language_probability if info else 0.85)
            confidence = round(min(1.0, max(0.0, avg_prob)), 3)
        else:
            confidence = 0.0

        # Repetition check (threshold 0.60 or empty transcript)
        repetition_needed = (confidence < 0.60) or (len(full_text) == 0)
        repetition_prompt = "Please repeat your query clearly." if repetition_needed else None

        return TranscriptionResult(
            transcript=full_text,
            language=detected_lang,
            confidence=confidence,
            repetition_needed=repetition_needed,
            repetition_prompt=repetition_prompt,
            duration_seconds=round(info.duration, 2) if info and hasattr(info, 'duration') else None,
            provider=self.provider_name,
            is_mock=False,
        )


class BenchmarkWavSTTProvider(BaseSTTProvider):
    """
    Deterministic benchmark matcher / fixture provider for unit testing, CI pipelines,
    and offline development where neural models cannot be loaded or network is isolated.
    
    NOTE: As required by architectural constraints, this provider is explicitly marked as a mock/benchmark
    and must NOT be presented as a real neural speech recognition engine.
    """

    def __init__(self, custom_fixtures: Optional[Dict[str, Dict]] = None):
        self._fixtures = custom_fixtures or {}

    @property
    def provider_name(self) -> str:
        return "benchmark-wav-fixture-provider"

    @property
    def is_mock(self) -> bool:
        return True

    def register_fixture(self, key: str, transcript: str, language: str, confidence: float, duration: float = 2.0):
        """Registers a known benchmark audio pattern."""
        self._fixtures[key] = {
            "transcript": transcript,
            "language": language,
            "confidence": confidence,
            "duration": duration,
        }

    def transcribe(
        self, 
        audio_data: bytes, 
        language_hint: Optional[str] = None
    ) -> TranscriptionResult:
        if not audio_data or len(audio_data) < 44:
            raise ValueError("Audio data is empty or too short to contain a valid audio stream.")

        # Check for corrupt payload marker or invalid RIFF header in WAV
        if len(audio_data) >= 4 and audio_data[:4] != b"RIFF" and b"corrupt" in audio_data[:50].lower():
            raise ValueError("Corrupt audio stream header detected.")

        # Match registered fixtures by text contained in header or length/hash
        audio_str = str(audio_data[:200])
        matched = None
        for key, fix in self._fixtures.items():
            if key.encode() in audio_data or key in audio_str:
                matched = fix
                break

        if matched:
            confidence = matched["confidence"]
            rep_needed = confidence < 0.60
            return TranscriptionResult(
                transcript=matched["transcript"],
                language=matched["language"],
                confidence=confidence,
                repetition_needed=rep_needed,
                repetition_prompt="Please repeat your query clearly." if rep_needed else None,
                duration_seconds=matched.get("duration", 2.0),
                provider=self.provider_name,
                is_mock=True,
            )

        # Default fallback behavior for arbitrary test WAVs
        # Inspect WAV header parameters to derive basic characteristics
        try:
            with wave.open(io.BytesIO(audio_data), "rb") as wf:
                channels = wf.getnchannels()
                rate = wf.getframerate()
                frames = wf.getnframes()
                duration = round(frames / float(rate), 2) if rate > 0 else 1.0
        except Exception:
            # Not a valid wave file
            if b"corrupt" in audio_data.lower():
                raise ValueError("Corrupt or unsupported audio format.")
            duration = 1.5

        # Check for language hint or test tags
        lang = language_hint if language_hint in ["en", "hi", "ta"] else "en"
        
        # Test tag checks inside audio payload for mock audio generation
        if b"low_confidence" in audio_data:
            return TranscriptionResult(
                transcript="",
                language=lang,
                confidence=0.35,
                repetition_needed=True,
                repetition_prompt="Please repeat your query clearly.",
                duration_seconds=duration,
                provider=self.provider_name,
                is_mock=True,
            )
        elif b"hindi_cable" in audio_data:
            return TranscriptionResult(
                transcript="क्या केबल के लिए BIS सर्टिफिकेशन जरूरी है?",
                language="hi",
                confidence=0.92,
                repetition_needed=False,
                repetition_prompt=None,
                duration_seconds=duration,
                provider=self.provider_name,
                is_mock=True,
            )
        elif b"tamil_cable" in audio_data:
            return TranscriptionResult(
                transcript="மின்சார கேபிள்களுக்கான தரம் என்ன?",
                language="ta",
                confidence=0.91,
                repetition_needed=False,
                repetition_prompt=None,
                duration_seconds=duration,
                provider=self.provider_name,
                is_mock=True,
            )
        elif b"motor_query" in audio_data:
            return TranscriptionResult(
                transcript="energy efficient three phase induction motors for industrial pumps",
                language="en",
                confidence=0.95,
                repetition_needed=False,
                repetition_prompt=None,
                duration_seconds=duration,
                provider=self.provider_name,
                is_mock=True,
            )

        # Generic default transcript for valid WAV test inputs
        return TranscriptionResult(
            transcript="energy efficient induction motors",
            language=lang,
            confidence=0.88,
            repetition_needed=False,
            repetition_prompt=None,
            duration_seconds=duration,
            provider=self.provider_name,
            is_mock=True,
        )


def get_stt_provider(provider_type: Optional[str] = None) -> BaseSTTProvider:
    """
    Factory function for obtaining an STT Provider.
    Defaults to FasterWhisperSTTProvider if available, otherwise BenchmarkWavSTTProvider.
    Can be overridden via SPEECH_STT_PROVIDER environment variable ('faster_whisper' or 'mock').
    """
    selected = provider_type or os.getenv("SPEECH_STT_PROVIDER", "faster_whisper").lower()
    
    if selected in ["faster_whisper", "whisper", "real"]:
        try:
            return FasterWhisperSTTProvider()
        except Exception:
            # Fallback to benchmark provider if model loading is prohibited or failed
            return BenchmarkWavSTTProvider()
    elif selected in ["mock", "benchmark", "fixture"]:
        return BenchmarkWavSTTProvider()
    else:
        return BenchmarkWavSTTProvider()
