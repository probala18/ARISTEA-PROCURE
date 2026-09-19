"""
Pydantic Schemas for Module 10: Speech AI Service.
Defines data structures for STT transcription, TTS synthesis, and Voice Query operations.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SpeechLanguage(str, Enum):
    """Supported languages for Speech AI."""
    EN = "en"
    HI = "hi"
    TA = "ta"
    UNKNOWN = "unknown"


class TranscriptionResult(BaseModel):
    """Result of Speech-to-Text transcription."""
    transcript: str = Field(..., description="Transcribed text from the audio input.")
    language: str = Field(..., description="Detected or specified ISO language code (en, hi, ta).")
    confidence: float = Field(..., description="Confidence score of speech recognition (0.0 to 1.0).")
    repetition_needed: bool = Field(
        False, 
        description="True if confidence is low (<0.60) or audio is unclear, requiring the user to repeat."
    )
    repetition_prompt: Optional[str] = Field(
        None, 
        description="Repetition guidance message if repetition_needed is True."
    )
    duration_seconds: Optional[float] = Field(None, description="Audio duration in seconds.")
    provider: str = Field(..., description="Name of the STT provider used.")
    is_mock: bool = Field(False, description="True if a benchmark matcher or mock provider was used.")


class SynthesisRequest(BaseModel):
    """Request payload for Text-to-Speech synthesis."""
    text: str = Field(..., min_length=1, description="Text to synthesize into spoken audio.")
    language: str = Field("en", description="Target ISO language code (en, hi, ta).")
    voice: Optional[str] = Field(None, description="Optional voice name or profile.")


class SynthesisResult(BaseModel):
    """Result of Text-to-Speech synthesis."""
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio content.")
    audio_bytes: Optional[bytes] = Field(None, description="Raw audio bytes (internal use).", exclude=True)
    mime_type: str = Field("audio/wav", description="MIME type of the generated audio.")
    duration_seconds: Optional[float] = Field(None, description="Synthesized audio duration in seconds.")
    provider: str = Field(..., description="Name of the TTS provider used.")
    is_mock: bool = Field(False, description="True if a mock/benchmark TTS generator was used.")
    error: Optional[str] = Field(None, description="Error message if synthesis failed.")


class VoiceQueryResponse(BaseModel):
    """End-to-end voice query response combining transcription, recommendation, and audio summary."""
    transcription: TranscriptionResult = Field(..., description="STT transcription details.")
    recommendation: Optional[Any] = Field(
        None, 
        description="Module 6 RecommendationResponse if transcription was confident and clear."
    )
    spoken_summary: Optional[str] = Field(
        None, 
        description="Concise spoken summary text produced for the user."
    )
    audio_base64: Optional[str] = Field(
        None, 
        description="Synthesized audio base64 for the spoken summary."
    )
    tts_status: str = Field("success", description="Status of TTS synthesis: success, skipped, or failed.")
    tts_error: Optional[str] = Field(None, description="TTS error message if TTS synthesis failed.")
