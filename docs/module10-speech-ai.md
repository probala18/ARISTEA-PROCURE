# Module 10: Speech AI & Voice API

## Overview
Module 10 implements the **Speech AI Service** and Voice API for Problem Statement 26108 (*Identifying Applicable Indian Standards for Procurement Specifications*). It enables full natural language voice interaction across procurement workflows, strictly adhering to the architectural constraints:
- **Provider Abstraction Architecture**: Pluggable Speech-to-Text (`STTProvider`) and Text-to-Speech (`TTSProvider`) layers without vendor lock-in.
- **Single Source of Truth**: The spoken query feeds directly into the exact same shared `RecommendationEngine` and `KnowledgeGraphService` as typed text. No separate or divergent recommendation engine exists for voice.
- **Multilingual Support**: Real speech-to-text and text-to-speech support for **English (`en`)**, **Hindi (`hi`)**, and **Tamil (`ta`)**.
- **Deterministic Discipline & Zero Hallucination**: Low confidence audio (< 0.60) triggers an explicit repetition request (`"Please repeat your query clearly."`) and never hallucinates or silently invents missing words.
- **Fail-Safe Tolerance**: A Text-to-Speech synthesis failure never blocks, drops, or suppresses the textual recommendation response.
- **Transparent Mock Separation**: Deterministic benchmark matchers and mocks are explicitly marked with `is_mock = True` and separated from neural models.

---

## 1. Provider Abstraction Architecture

### Speech-to-Text (`BaseSTTProvider`)
```
                     +---------------------+
                     |   BaseSTTProvider   |
                     +----------+----------+
                                |
         +----------------------+----------------------+
         |                                             |
+--------v------------------+              +-----------v--------------+
|  FasterWhisperSTTProvider |              |  BenchmarkWavSTTProvider  |
|  (Neural Local Whisper)   |              |  (Deterministic Fixture)  |
|  is_mock = False          |              |  is_mock = True           |
+---------------------------+              +--------------------------+
```

1. **`FasterWhisperSTTProvider` (Production Default)**:
   - Uses `faster-whisper` (`tiny` quantized int8 on CPU) for high-speed offline/local speech recognition.
   - Computes segment log-probabilities to derive calibrated confidence scores.
   - Detects spoken language (`en`, `hi`, `ta`).
2. **`BenchmarkWavSTTProvider` (Testing & CI)**:
   - Evaluates test WAV audio payloads deterministically for CI environments without GPU/model downloading.
   - Flagged with `is_mock = True`.

### Text-to-Speech (`BaseTTSProvider`)
```
                     +---------------------+
                     |   BaseTTSProvider   |
                     +----------+----------+
                                |
         +----------------------+----------------------+
         |                      |                      |
+--------v----------+  +--------v-----------+  +-------v----------+
|   GTTSProvider    |  | Pyttsx3TTSProvider |  | MockTTSProvider  |
| (Google Neural)   |  | (Local OS SAPI5)   |  | (RIFF WAV Tone)  |
| is_mock = False   |  | is_mock = False    |  | is_mock = True   |
+-------------------+  +--------------------+  +------------------+
```

1. **`GTTSProvider` (Production Online)**:
   - Generates natural, vocalized MP3/audio streams across English, Hindi, and Tamil.
2. **`Pyttsx3TTSProvider` (Production Offline)**:
   - Uses native operating system synthesizers (SAPI5 on Windows / eSpeak on Linux) for 100% offline audio synthesis.
3. **`MockTTSProvider` (Testing & CI)**:
   - Generates valid PCM RIFF WAV containers for CI pipelines where audio devices are unavailable.
   - Flagged with `is_mock = True`.

---

## 2. Voice + Text Consistency Benchmark

To enforce the mandate that voice queries yield identical results to typed queries:

| Test Query | Spoken Input | Transcribed Query | Recommended Primary Standard | Confidence Score | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Induction Motors** | WAV audio stream | `energy efficient three phase induction motors for industrial pumps` | `IS 12615:2018` | 0.90 | `PRIMARY` (Internal) |
| **Cables (Hindi)** | WAV audio stream | `क्या केबल के लिए BIS सर्टिफिकेशन जरूरी है?` | `IS 694:2010` | 0.85 | `PRIMARY` (Internal) |
| **Cables (Tamil)** | WAV audio stream | `மின்சார கேபிள்களுக்கான தரம் என்ன?` | `IS 694:2010` | 0.85 | `PRIMARY` (Internal) |

**Verification**: `test_voice_and_text_consistency` in `tests/test_module10_speech_ai.py` confirms exact equality of primary standard IDs, roles, and confidence scores between voice and typed execution.

---

## 3. Section 68 Voice API Endpoints

### 1. `POST /api/speech/transcribe`
Transcribes audio file to text with language and confidence scoring.
- **Request**: Multipart form data with audio file (`audio/wav`, `audio/mpeg`, etc.) and optional `language_hint`.
- **Response**:
```json
{
  "transcript": "energy efficient three phase induction motors for industrial pumps",
  "language": "en",
  "confidence": 0.95,
  "repetition_needed": false,
  "repetition_prompt": null,
  "duration_seconds": 2.0,
  "provider": "faster-whisper-tiny",
  "is_mock": false
}
```

### 2. `POST /api/speech/synthesize`
Synthesizes text into spoken audio payload.
- **Request**:
```json
{
  "text": "Recommended standard is IS 12615 for electric motors.",
  "language": "en"
}
```
- **Response**:
```json
{
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
  "mime_type": "audio/wav",
  "duration_seconds": 1.5,
  "provider": "gTTS-neural-engine",
  "is_mock": false,
  "error": null
}
```

### 3. `POST /api/speech/voice-query`
End-to-end voice query pipeline invoking `RecommendationEngine` and returning structured recommendations with spoken summary.
- **Request**: Multipart audio file with query parameters `language_hint` and `synthesize_audio`.
- **Response**:
```json
{
  "transcription": {
    "transcript": "energy efficient three phase induction motors for industrial pumps",
    "language": "en",
    "confidence": 0.95,
    "repetition_needed": false,
    "provider": "faster-whisper-tiny"
  },
  "recommendation": {
    "primary_standards": [
      {
        "standard_id": "IS 12615:2018",
        "title": "Line Operated Three Phase AC Motors (IE Code) 'Energy Efficient Inductive Motors'",
        "role": "PRIMARY",
        "confidence_score": 0.90,
        "compliance_note": "Mandatory certification under Scheme I..."
      }
    ]
  },
  "spoken_summary": "Recommended primary standard is IS 12615:2018 for Line Operated Three Phase AC Motors. Compliance is mandatory under Quality Control Order.",
  "audio_base64": "UklGRiQAAABXQVZF...",
  "tts_status": "success",
  "tts_error": null
}
```

---

## 4. Error Handling & Quality Discipline

1. **Low Confidence (< 0.60) Handling**:
   - When input audio clarity is below 0.60 or audio contains only background noise:
   - `repetition_needed = True`
   - `repetition_prompt = "Please repeat your query clearly."`
   - `recommendation = None`
   - System **never hallucinates or attempts to invent words**.
2. **Corrupted / Empty Audio Handling**:
   - Audio payloads `< 44 bytes` or with corrupted headers raise `HTTP 400 Bad Request` with descriptive diagnostics.
3. **Fail-Safe TTS Tolerance**:
   - If TTS synthesis fails (e.g. SAPI5 unavailable or temporary network drop), `tts_status="failed"` is logged and returned in the JSON payload, but the textual `recommendation` and `transcription` are returned 100% intact.

---

## 5. Test Suite Verification

- **Module 10 Test Suite**: `tests/test_module10_speech_ai.py` (19 passed).
- **Full Project Test Suite**: 133 tests passed across all 10 modules:
  - Module 1: Data Inventory & Verification
  - Module 2: Relational Database Schema
  - Module 3: Ingestion & Provenance Audit
  - Module 4: Knowledge Graph Architecture
  - Module 5: Hybrid Retrieval Engine
  - Module 6: Recommendation Engine & NLP
  - Module 7: Relationship Engine & Graph API
  - Module 8: Version & Amendment Intelligence
  - Module 9: Compliance Intelligence Service
  - Module 10: Speech AI & Voice API
- **Ingestion Validation Audit**: Passed all checks (268 standards, 111 relationships, 710 QCO records, 1,573 certifications, 100% provenance).
