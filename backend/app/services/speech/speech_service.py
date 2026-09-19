"""
Speech AI Service for PS 26108.
Bridges audio inputs with the unified procurement intelligence engine:
- Speech-to-Text transcription with confidence and repetition detection
- Voice query routing directly into the shared RecommendationEngine
- Spoken audio synthesis (TTS) for recommendations and compliance summaries
- Strict error tolerance (TTS failure never blocks text response)
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.services.recommendation.schemas import (
    RecommendationRequest,
    RecommendationResponse,
)
from backend.app.services.recommendation.recommendation_engine import RecommendationEngine
from backend.app.services.speech.schemas import (
    TranscriptionResult,
    SynthesisResult,
    VoiceQueryResponse,
    SpeechLanguage,
)
from backend.app.services.speech.stt_provider import (
    BaseSTTProvider,
    get_stt_provider,
)
from backend.app.services.speech.tts_provider import (
    BaseTTSProvider,
    get_tts_provider,
)

logger = logging.getLogger(__name__)


class SpeechService:
    """
    Unified Speech AI Service coordinating STT, recommendation processing, and TTS.
    Adheres strictly to the architectural constraints:
    - Same backend recommendation pipeline as typed text.
    - Pluggable provider abstraction.
    - Low confidence repetition request without hallucination.
    - TTS failures never suppress or fail text responses.
    """

    def __init__(
        self,
        stt_provider: Optional[BaseSTTProvider] = None,
        tts_provider: Optional[BaseTTSProvider] = None,
    ):
        self.stt_provider = stt_provider or get_stt_provider()
        self.tts_provider = tts_provider or get_tts_provider()

    def transcribe(
        self, 
        audio_data: bytes, 
        language_hint: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribes audio data to text with confidence and repetition flags."""
        return self.stt_provider.transcribe(audio_data, language_hint=language_hint)

    def synthesize(
        self, 
        text: str, 
        language: str = "en"
    ) -> SynthesisResult:
        """Synthesizes text into spoken audio."""
        return self.tts_provider.synthesize(text, language=language)

    def generate_spoken_summary(
        self, 
        recommendation: RecommendationResponse,
        language: str = "en"
    ) -> str:
        """
        Generates a concise spoken summary suitable for audio vocalization.
        Extracts key recommendation signals: governing standard, title, and mandatory status.
        """
        if recommendation.is_out_of_scope:
            if language == "hi":
                return "यह प्रश्न भारतीय मानक ब्यूरो के खरीद मानकों के दायरे से बाहर है।"
            elif language == "ta":
                return "இந்தக் கேள்வி இந்திய தர நிர்ணய அமைப்பின் கொள்முதல் வரம்பிற்கு அப்பாற்பட்டது."
            return "This query is outside the scope of Indian Standards for procurement."

        if recommendation.is_ambiguous:
            if language == "hi":
                return "एकाधिक मानक लागू हो सकते हैं। कृपया उत्पाद का प्रकार या तकनीकी विवरण स्पष्ट करें।"
            elif language == "ta":
                return "பல தரநிலைகள் பொருந்தக்கூடும். கூடுதல் தொழில்நுட்ப விவரங்களை குறிப்பிடவும்."
            return "Multiple standards may apply. Please provide additional technical specifications."

        if not recommendation.primary_standards:
            if language == "hi":
                return "इस विनिर्देश के लिए कोई प्राथमिक भारतीय मानक नहीं मिला।"
            elif language == "ta":
                return "இந்த விவரக்குறிப்பிற்கு பொருந்தும் முதன்மை இந்திய தரம் எதுவும் கிடைக்கவில்லை."
            return "No primary Indian Standard was identified for this specification."

        top = recommendation.primary_standards[0]
        std_id = top.standard_id or top.is_number
        title = top.title
        is_mandatory = bool(top.compliance_note and "MANDATORY" in top.compliance_note.upper())

        # Build concise spoken sentence
        if language == "hi":
            summary = f"अनुशंसित प्राथमिक मानक {std_id} है, जो {title} के लिए है।"
            if is_mandatory:
                summary += " गुणवत्ता नियंत्रण आदेश के तहत इसका अनुपालन अनिवार्य है।"
        elif language == "ta":
            summary = f"பரிந்துரைக்கப்பட்ட முதன்மை தரம் {std_id}, {title} க்கானது."
            if is_mandatory:
                summary += " தரக் கட்டுப்பாட்டு உத்தரவின் கீழ் இதைப் பின்பற்றுவது கட்டாயமாகும்."
        else:
            summary = f"Recommended primary standard is {std_id} for {title}."
            if is_mandatory:
                summary += " Compliance is mandatory under Quality Control Order."

        return summary

    def voice_query(
        self,
        audio_data: bytes,
        db_session: Session,
        language_hint: Optional[str] = None,
        synthesize_audio: bool = True,
    ) -> VoiceQueryResponse:
        """
        Executes end-to-end voice query:
        1. Transcribes audio input.
        2. Checks confidence (rep-needed -> prompts repetition, skips hallucinated recommendation).
        3. Invokes shared RecommendationEngine (exact same pipeline as typed query).
        4. Synthesizes concise spoken summary if requested.
        """
        # Step 1: Transcribe audio
        transcription = self.transcribe(audio_data, language_hint=language_hint)

        # Step 2: Guard against low confidence / unclear audio
        if transcription.repetition_needed or not transcription.transcript.strip():
            rep_msg = transcription.repetition_prompt or "Please repeat your query clearly."
            return VoiceQueryResponse(
                transcription=transcription,
                recommendation=None,
                spoken_summary=rep_msg,
                audio_base64=None,
                tts_status="skipped",
                tts_error=None,
            )

        # Step 3: Run exact shared RecommendationEngine pipeline
        engine = RecommendationEngine(db_session)
        rec_req = RecommendationRequest(
            query_text=transcription.transcript,
            max_primary=3,
            include_allied=True,
        )
        recommendation = engine.recommend(rec_req)

        # Step 4: Generate concise spoken text summary
        spoken_text = self.generate_spoken_summary(recommendation, language=transcription.language)

        # Step 5: Synthesize spoken summary (Fail-safe: TTS failure NEVER blocks response)
        audio_b64 = None
        tts_status = "skipped"
        tts_err = None

        if synthesize_audio and spoken_text:
            try:
                synth_res = self.synthesize(spoken_text, language=transcription.language)
                if synth_res.error:
                    tts_status = "failed"
                    tts_err = synth_res.error
                    logger.warning(f"TTS synthesis warning: {synth_res.error}")
                else:
                    audio_b64 = synth_res.audio_base64
                    tts_status = "success"
            except Exception as e:
                tts_status = "failed"
                tts_err = str(e)
                logger.error(f"TTS synthesis unexpected failure: {e}", exc_info=True)

        return VoiceQueryResponse(
            transcription=transcription,
            recommendation=recommendation,
            spoken_summary=spoken_text,
            audio_base64=audio_b64,
            tts_status=tts_status,
            tts_error=tts_err,
        )
