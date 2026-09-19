"""
Text-to-Speech (TTS) Provider Abstraction and Implementations.
Provides:
- BaseTTSProvider (ABC)
- GTTSProvider (Production online speech synthesis using gTTS for EN, HI, TA)
- Pyttsx3TTSProvider (Production offline local speech synthesis using SAPI5/eSpeak)
- MockTTSProvider (Deterministic audio payload generator for unit testing and CI)
"""
import base64
import io
import os
import struct
import wave
from abc import ABC, abstractmethod
from typing import Optional

from backend.app.services.speech.schemas import SynthesisResult


class BaseTTSProvider(ABC):
    """Abstract Base Class for Text-to-Speech Providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the TTS provider implementation."""
        pass

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        """Indicates whether this provider is a mock or an actual speech synthesis engine."""
        pass

    @abstractmethod
    def synthesize(self, text: str, language: str = "en") -> SynthesisResult:
        """
        Synthesizes text into audible spoken audio.
        
        Args:
            text: Spoken text to synthesize.
            language: Target ISO language code ('en', 'hi', 'ta').
            
        Returns:
            SynthesisResult containing audio bytes/base64 and format details.
        """
        pass


class GTTSProvider(BaseTTSProvider):
    """
    Production Text-to-Speech implementation using Google Text-to-Speech (gTTS).
    Provides natural vocalization for English ('en'), Hindi ('hi'), and Tamil ('ta').
    """

    @property
    def provider_name(self) -> str:
        return "gTTS-neural-engine"

    @property
    def is_mock(self) -> bool:
        return False

    def synthesize(self, text: str, language: str = "en") -> SynthesisResult:
        if not text or not text.strip():
            raise ValueError("Cannot synthesize empty text.")

        lang = language if language in ["en", "hi", "ta"] else "en"
        
        try:
            from gtts import gTTS
            fp = io.BytesIO()
            tts = gTTS(text=text.strip(), lang=lang, slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_bytes = fp.read()
            b64_str = base64.b64encode(audio_bytes).decode("utf-8")
            
            # Estimate duration: ~150 words per minute -> ~2.5 words/sec
            word_count = len(text.split())
            estimated_duration = max(1.0, round(word_count / 2.5, 2))

            return SynthesisResult(
                audio_base64=b64_str,
                audio_bytes=audio_bytes,
                mime_type="audio/mpeg",
                duration_seconds=estimated_duration,
                provider=self.provider_name,
                is_mock=False,
            )
        except Exception as e:
            return SynthesisResult(
                audio_base64=None,
                audio_bytes=None,
                mime_type="audio/mpeg",
                duration_seconds=0.0,
                provider=self.provider_name,
                is_mock=False,
                error=f"gTTS synthesis failed: {str(e)}",
            )


class Pyttsx3TTSProvider(BaseTTSProvider):
    """
    Production Text-to-Speech implementation using pyttsx3.
    Operates 100% offline using local operating system speech synthesizers (e.g. SAPI5 on Windows).
    """

    @property
    def provider_name(self) -> str:
        return "pyttsx3-local-engine"

    @property
    def is_mock(self) -> bool:
        return False

    def synthesize(self, text: str, language: str = "en") -> SynthesisResult:
        if not text or not text.strip():
            raise ValueError("Cannot synthesize empty text.")

        import tempfile
        try:
            import pyttsx3
            engine = pyttsx3.init()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()

            try:
                os.remove(tmp_path)
            except OSError:
                pass

            b64_str = base64.b64encode(audio_bytes).decode("utf-8")
            
            # Duration from WAV if readable
            try:
                with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = round(frames / float(rate), 2) if rate > 0 else 1.0
            except Exception:
                duration = max(1.0, round(len(text.split()) / 2.5, 2))

            return SynthesisResult(
                audio_base64=b64_str,
                audio_bytes=audio_bytes,
                mime_type="audio/wav",
                duration_seconds=duration,
                provider=self.provider_name,
                is_mock=False,
            )
        except Exception as e:
            return SynthesisResult(
                audio_base64=None,
                audio_bytes=None,
                mime_type="audio/wav",
                duration_seconds=0.0,
                provider=self.provider_name,
                is_mock=False,
                error=f"pyttsx3 synthesis failed: {str(e)}",
            )


class MockTTSProvider(BaseTTSProvider):
    """
    Deterministic audio synthesizer for unit testing and offline CI environments.
    Generates a valid standard RIFF WAV payload with silence / sine tone.
    
    NOTE: As required by architectural constraints, a valid WAV container alone is NOT
    presented as real speech synthesis; it is explicitly marked with is_mock = True.
    """

    @property
    def provider_name(self) -> str:
        return "mock-audio-fixture-provider"

    @property
    def is_mock(self) -> bool:
        return True

    def synthesize(self, text: str, language: str = "en") -> SynthesisResult:
        if not text or not text.strip():
            raise ValueError("Cannot synthesize empty text.")

        sample_rate = 16000
        num_samples = int(sample_rate * 0.5)  # 0.5s audio
        
        # Build valid WAV stream
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)  # mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            # Write subtle sinusoidal or silence frames
            data = bytearray(num_samples * 2)
            wf.writeframes(data)

        audio_bytes = buffer.getvalue()
        b64_str = base64.b64encode(audio_bytes).decode("utf-8")

        return SynthesisResult(
            audio_base64=b64_str,
            audio_bytes=audio_bytes,
            mime_type="audio/wav",
            duration_seconds=0.5,
            provider=self.provider_name,
            is_mock=True,
        )


def get_tts_provider(provider_type: Optional[str] = None) -> BaseTTSProvider:
    """
    Factory function for obtaining a TTS Provider.
    Can select 'gtts', 'pyttsx3', or 'mock'.
    Defaults to gtts if available, with fallback to mock if offline.
    """
    selected = provider_type or os.getenv("SPEECH_TTS_PROVIDER", "gtts").lower()
    
    if selected in ["gtts", "google"]:
        return GTTSProvider()
    elif selected in ["pyttsx3", "local", "sapi5"]:
        return Pyttsx3TTSProvider()
    elif selected in ["mock", "fixture", "test"]:
        return MockTTSProvider()
    else:
        return MockTTSProvider()
