"""
FastAPI Router for Speech AI API (Module 10).
Implements Section 68 Voice API specifications:
- POST /api/speech/transcribe
- POST /api/speech/synthesize
- POST /api/speech/voice-query
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import validate_upload
from backend.app.services.speech import (
    SpeechService,
    TranscriptionResult,
    SynthesisRequest,
    SynthesisResult,
    VoiceQueryResponse,
)

router = APIRouter(prefix="/speech", tags=["Speech AI API"])
speech_router = router


def get_speech_service() -> SpeechService:
    """Dependency provider for SpeechService."""
    return SpeechService()


@router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe (WAV/MP3/PCM)"),
    language_hint: Optional[str] = Query(None, description="Optional ISO language hint ('en', 'hi', 'ta')"),
    service: SpeechService = Depends(get_speech_service),
):
    """
    Transcribes audio into text with language detection and confidence scoring.
    Flags repetition_needed if confidence is low (<0.60) or audio is unclear.
    """
    audio_data = await file.read()
    try:
        validate_upload(
            file.filename or "audio.wav",
            audio_data,
            {"wav", "mp3", "pcm"},
            settings.MAX_AUDIO_BYTES,
            file.content_type,
            {"audio/wav", "audio/x-wav", "audio/mpeg", "application/octet-stream"},
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid audio upload."
        )

    try:
        result = service.transcribe(audio_data, language_hint=language_hint)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Speech transcription failed.")


@router.post("/synthesize", response_model=SynthesisResult)
def synthesize_speech(
    request: SynthesisRequest,
    service: SpeechService = Depends(get_speech_service),
):
    """
    Synthesizes input text into spoken audio payload (WAV or MP3 base64).
    Supports English ('en'), Hindi ('hi'), and Tamil ('ta').
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text to synthesize cannot be empty.")

    try:
        result = service.synthesize(request.text, language=request.language)
        return result
    except Exception:
        raise HTTPException(status_code=500, detail="Speech synthesis failed.")


@router.post("/voice-query", response_model=VoiceQueryResponse)
async def voice_query(
    file: UploadFile = File(..., description="Audio query file (WAV/MP3)"),
    language_hint: Optional[str] = Query(None, description="Optional ISO language hint ('en', 'hi', 'ta')"),
    synthesize_audio: bool = Query(True, description="Whether to synthesize spoken response audio"),
    db: Session = Depends(get_db),
    service: SpeechService = Depends(get_speech_service),
):
    """
    End-to-End Voice Query:
    1. Transcribes spoken query with confidence evaluation.
    2. Passes transcript to the exact same shared RecommendationEngine.
    3. Produces structured recommendation and concise spoken response summary.
    4. Synthesizes spoken audio (TTS failure will never block text recommendation).
    """
    audio_data = await file.read()
    try:
        validate_upload(
            file.filename or "audio.wav",
            audio_data,
            {"wav", "mp3", "pcm"},
            settings.MAX_AUDIO_BYTES,
            file.content_type,
            {"audio/wav", "audio/x-wav", "audio/mpeg", "application/octet-stream"},
        )
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid audio upload."
        )

    try:
        result = service.voice_query(
            audio_data=audio_data,
            db_session=db,
            language_hint=language_hint,
            synthesize_audio=synthesize_audio,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Voice query execution failed.")
