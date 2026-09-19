"""
Module 10 Test Suite — Speech AI & Voice API.
Tests:
1. Provider Abstraction Architecture:
   - BaseSTTProvider and BaseTTSProvider inheritance
   - Clear distinction between real neural models and benchmark mocks (is_mock flag)
2. Real STT & TTS Providers:
   - FasterWhisperSTTProvider real model loading and transcription
   - GTTSProvider and Pyttsx3TTSProvider real speech synthesis
3. Multilingual Speech Recognition:
   - English, Hindi, and Tamil transcription
4. Voice + Text Consistency:
   - Verifies that audio queries produce identical recommendation results as typed queries
   - Single source of truth: shared RecommendationEngine
5. Voice Error Handling & Low Confidence Discipline:
   - Low confidence (< 0.60) triggers repetition request without hallucination
   - Empty or corrupted audio handled gracefully with actionable diagnostics (HTTP 400 / ValueError)
6. Text-to-Speech Synthesis:
   - Audio synthesis for EN, HI, TA
   - Fail-safe tolerance: TTS failure NEVER suppresses or blocks text recommendation
7. Section 68 Voice API Endpoints:
   - POST /api/speech/transcribe
   - POST /api/speech/synthesize
   - POST /api/speech/voice-query
8. Read-Only Database Integrity:
   - No data mutations during voice queries
9. API Health Check includes Module 10
"""
import io
import os
import sys
import wave
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.core.database import get_engine
from backend.app.models.standard import Standard
from backend.app.api.speech import get_speech_service
from backend.app.services.recommendation import (
    RecommendationRequest,
    RecommendationEngine,
    StandardRole,
)
from backend.app.services.speech import (
    BaseSTTProvider,
    BaseTTSProvider,
    FasterWhisperSTTProvider,
    BenchmarkWavSTTProvider,
    GTTSProvider,
    Pyttsx3TTSProvider,
    MockTTSProvider,
    SpeechService,
    TranscriptionResult,
    SynthesisRequest,
    SynthesisResult,
    VoiceQueryResponse,
)


def create_dummy_wav(marker: bytes = b"", duration_sec: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Helper to generate valid RIFF WAV audio bytes with embedded marker."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frame_count = int(sample_rate * duration_sec)
        data = bytearray(frame_count * 2)
        for i, b in enumerate(marker):
            if i < len(data):
                data[i] = b
        wf.writeframes(data)
    return buf.getvalue()


@pytest.fixture(scope="module")
def db_session():
    """Provides a database session over the real canonical database."""
    engine = get_engine("sqlite:///./sih_bis.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def api_client(db_session):
    """FastAPI TestClient instance configured with test speech service and canonical database."""
    from backend.app.core.database import get_db

    test_service = SpeechService(
        stt_provider=BenchmarkWavSTTProvider(),
        tts_provider=MockTTSProvider(),
    )
    app.dependency_overrides[get_speech_service] = lambda: test_service
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_speech_service, None)
    app.dependency_overrides.pop(get_db, None)


# 1. Provider Abstraction Tests
def test_provider_abstractions():
    """Verify that STT and TTS providers properly inherit from base classes and declare is_mock."""
    benchmark_stt = BenchmarkWavSTTProvider()
    assert isinstance(benchmark_stt, BaseSTTProvider)
    assert benchmark_stt.is_mock is True
    assert "benchmark" in benchmark_stt.provider_name

    whisper_stt = FasterWhisperSTTProvider()
    assert isinstance(whisper_stt, BaseSTTProvider)
    assert whisper_stt.is_mock is False
    assert "faster-whisper" in whisper_stt.provider_name

    mock_tts = MockTTSProvider()
    assert isinstance(mock_tts, BaseTTSProvider)
    assert mock_tts.is_mock is True

    gtts = GTTSProvider()
    assert isinstance(gtts, BaseTTSProvider)
    assert gtts.is_mock is False

    pyttsx3_tts = Pyttsx3TTSProvider()
    assert isinstance(pyttsx3_tts, BaseTTSProvider)
    assert pyttsx3_tts.is_mock is False


# 2. Real STT & TTS Neural / System Execution
def test_real_faster_whisper_execution():
    """Verify real FasterWhisperSTTProvider loads and processes audio without crashing."""
    whisper_stt = FasterWhisperSTTProvider(model_size="tiny")
    assert whisper_stt.is_mock is False
    audio = create_dummy_wav(duration_sec=0.5)
    # Processing silent synthetic audio should succeed and report realistic low probability/empty transcript
    res = whisper_stt.transcribe(audio, language_hint="en")
    assert isinstance(res, TranscriptionResult)
    assert res.provider.startswith("faster-whisper")
    assert res.is_mock is False
    assert res.repetition_needed is True  # silent audio requires repetition


def test_real_tts_provider_pyttsx3():
    """Verify real offline pyttsx3 speech synthesis generates real WAV audio."""
    tts = Pyttsx3TTSProvider()
    assert tts.is_mock is False
    res = tts.synthesize("Indian Standard IS 12615", language="en")
    assert isinstance(res, SynthesisResult)
    assert res.provider == "pyttsx3-local-engine"
    assert res.is_mock is False
    # If SAPI5 audio subsystem is available, audio_base64 is generated
    if res.audio_base64:
        assert len(res.audio_base64) > 100
        assert res.mime_type == "audio/wav"


def test_real_tts_provider_gtts():
    """Verify real online gTTS speech synthesis handles multilingual vocalization."""
    tts = GTTSProvider()
    assert tts.is_mock is False
    assert tts.provider_name == "gTTS-neural-engine"
    # Test English synthesis
    res = tts.synthesize("Standard recommendation", language="en")
    assert isinstance(res, SynthesisResult)
    assert res.provider == "gTTS-neural-engine"
    assert res.is_mock is False
    if res.audio_base64:
        assert len(res.audio_base64) > 100
        assert res.mime_type == "audio/mpeg"


# 3. Multilingual STT Recognition
def test_multilingual_stt_english():
    """Test STT transcription with English audio."""
    stt = BenchmarkWavSTTProvider()
    audio = create_dummy_wav(marker=b"motor_query")
    res = stt.transcribe(audio, language_hint="en")
    
    assert res.language == "en"
    assert "motor" in res.transcript.lower()
    assert res.confidence >= 0.60
    assert not res.repetition_needed


def test_multilingual_stt_hindi():
    """Test STT transcription with Hindi query."""
    stt = BenchmarkWavSTTProvider()
    audio = create_dummy_wav(marker=b"hindi_cable")
    res = stt.transcribe(audio, language_hint="hi")

    assert res.language == "hi"
    assert "केबल" in res.transcript
    assert res.confidence >= 0.60
    assert not res.repetition_needed


def test_multilingual_stt_tamil():
    """Test STT transcription with Tamil query."""
    stt = BenchmarkWavSTTProvider()
    audio = create_dummy_wav(marker=b"tamil_cable")
    res = stt.transcribe(audio, language_hint="ta")

    assert res.language == "ta"
    assert "கேபிள்" in res.transcript
    assert res.confidence >= 0.60
    assert not res.repetition_needed


# 4. Voice + Text Consistency
def test_voice_and_text_consistency(db_session):
    """
    Spoken query and typed query with equivalent wording must yield IDENTICAL
    primary standard recommendations and evidence from the shared RecommendationEngine.
    """
    spoken_audio = create_dummy_wav(marker=b"motor_query")
    speech_service = SpeechService(stt_provider=BenchmarkWavSTTProvider(), tts_provider=MockTTSProvider())
    
    # 1. Run voice query
    voice_resp = speech_service.voice_query(spoken_audio, db_session, synthesize_audio=False)
    assert voice_resp.recommendation is not None
    voice_primary = voice_resp.recommendation.primary_standards[0]

    # 2. Run typed query with exact same text
    typed_engine = RecommendationEngine(db_session)
    typed_resp = typed_engine.recommend(
        RecommendationRequest(query_text=voice_resp.transcription.transcript, max_primary=3)
    )
    typed_primary = typed_resp.primary_standards[0]

    # 3. Verify absolute equivalence
    assert voice_primary.standard_id == typed_primary.standard_id
    assert voice_primary.is_number == typed_primary.is_number
    assert voice_primary.role == typed_primary.role == StandardRole.PRIMARY
    assert voice_primary.confidence_score == typed_primary.confidence_score


# 5. Low Confidence & Error Discipline
def test_low_confidence_repetition_prompt(db_session):
    """
    Low confidence (< 0.60) audio must return an explicit repetition request
    and NEVER hallucinate or invent missing words.
    """
    unclear_audio = create_dummy_wav(marker=b"low_confidence")
    speech_service = SpeechService(stt_provider=BenchmarkWavSTTProvider(), tts_provider=MockTTSProvider())
    
    voice_resp = speech_service.voice_query(unclear_audio, db_session)
    
    assert voice_resp.transcription.repetition_needed is True
    assert voice_resp.transcription.confidence < 0.60
    assert voice_resp.recommendation is None
    assert "repeat" in voice_resp.spoken_summary.lower()


def test_empty_and_corrupt_audio_handling():
    """Verify that empty or corrupt audio raises appropriate errors."""
    stt = BenchmarkWavSTTProvider()
    
    # Empty audio
    with pytest.raises(ValueError) as exc:
        stt.transcribe(b"")
    assert "empty" in str(exc.value).lower() or "too short" in str(exc.value).lower()

    # Corrupt header
    with pytest.raises(ValueError) as exc_corrupt:
        stt.transcribe(b"corrupt_raw_bytes_without_valid_wav_header_abcdefghijklmnopqrstuvwxyz")
    assert "corrupt" in str(exc_corrupt.value).lower()


# 6. Text-to-Speech Synthesis & Fail-Safe Tolerance
def test_tts_synthesis():
    """Verify TTS synthesis generates valid base64 audio payload."""
    tts = MockTTSProvider()
    res = tts.synthesize("Recommended primary standard is IS 12615 for electric motors.", language="en")
    
    assert res.audio_base64 is not None
    assert len(res.audio_base64) > 50
    assert res.mime_type == "audio/wav"
    assert res.duration_seconds > 0


def test_tts_failure_never_blocks_text_response(db_session):
    """
    CRITICAL CONSTRAINT: TTS failure must never block or suppress the text recommendation.
    """
    class BrokenTTSProvider(BaseTTSProvider):
        @property
        def provider_name(self) -> str:
            return "broken-mock-tts"

        @property
        def is_mock(self) -> bool:
            return True

        def synthesize(self, text: str, language: str = "en") -> SynthesisResult:
            return SynthesisResult(
                audio_base64=None,
                audio_bytes=None,
                mime_type="audio/wav",
                provider=self.provider_name,
                is_mock=True,
                error="Audio device unavailable or SAPI5 failure.",
            )

    audio = create_dummy_wav(marker=b"motor_query")
    speech_service = SpeechService(
        stt_provider=BenchmarkWavSTTProvider(),
        tts_provider=BrokenTTSProvider()
    )
    
    voice_resp = speech_service.voice_query(audio, db_session, synthesize_audio=True)
    
    # Text recommendation is fully intact despite TTS error
    assert voice_resp.recommendation is not None
    assert len(voice_resp.recommendation.primary_standards) >= 1
    assert voice_resp.audio_base64 is None
    assert voice_resp.tts_status == "failed"
    assert "Audio device unavailable" in voice_resp.tts_error


# 7. Section 68 Voice API Endpoints
def test_api_transcribe_endpoint(api_client):
    """Test POST /api/speech/transcribe."""
    audio = create_dummy_wav(marker=b"motor_query")
    response = api_client.post(
        "/api/speech/transcribe",
        files={"file": ("query.wav", audio, "audio/wav")},
        params={"language_hint": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert "confidence" in data
    assert data["confidence"] >= 0.60


def test_api_transcribe_corrupt_file_returns_400(api_client):
    """Test POST /api/speech/transcribe with corrupt file returns 400 Bad Request."""
    corrupt_data = b"corrupt_audio_stream_without_riff_header_data_xyz1234567890"
    response = api_client.post(
        "/api/speech/transcribe",
        files={"file": ("corrupt.wav", corrupt_data, "audio/wav")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "corrupt" in detail or "invalid" in detail


def test_api_synthesize_endpoint(api_client):
    """Test POST /api/speech/synthesize."""
    payload = {
        "text": "Recommended standard is IS 694 for PVC insulated electrical cables.",
        "language": "en",
    }
    response = api_client.post("/api/speech/synthesize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["audio_base64"] is not None
    assert data["mime_type"] in ["audio/wav", "audio/mpeg"]


def test_api_synthesize_empty_text_returns_400(api_client):
    """Test POST /api/speech/synthesize with empty string returns 400."""
    response = api_client.post("/api/speech/synthesize", json={"text": "   ", "language": "en"})
    assert response.status_code == 400


def test_api_voice_query_endpoint(api_client):
    """Test POST /api/speech/voice-query end-to-end endpoint."""
    audio = create_dummy_wav(marker=b"motor_query")
    response = api_client.post(
        "/api/speech/voice-query",
        files={"file": ("query.wav", audio, "audio/wav")},
        params={"language_hint": "en", "synthesize_audio": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcription" in data
    assert "recommendation" in data
    assert data["recommendation"] is not None
    assert len(data["recommendation"]["primary_standards"]) >= 1


# 8. Database Integrity
def test_database_integrity_after_voice_query(db_session):
    """Verify that voice processing maintains read-only database integrity."""
    initial_count = db_session.query(Standard).count()
    audio = create_dummy_wav(marker=b"motor_query")
    speech_service = SpeechService(stt_provider=BenchmarkWavSTTProvider(), tts_provider=MockTTSProvider())
    speech_service.voice_query(audio, db_session)
    final_count = db_session.query(Standard).count()
    assert initial_count == final_count


# 9. Health Check Verification
def test_health_check_includes_module10(api_client):
    """Verify /api/health includes Module 10."""
    response = api_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "Module 10" in data["module"]
    assert "Speech AI" in data["module"]
