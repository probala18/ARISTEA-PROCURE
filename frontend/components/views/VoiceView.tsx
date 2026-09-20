'use client';

import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { submitVoiceQuery, synthesizeSpeech, VoiceQueryResponse } from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { CandidateCard } from '@/components/ui/CandidateCard';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface VoiceViewProps {
  onExploreStandard?: (standardId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

export const VoiceView: React.FC<VoiceViewProps> = ({ onExploreStandard, onToast }) => {
  const [language, setLanguage] = useState('en');
  const [selectedAudio, setSelectedAudio] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const [voiceResult, setVoiceResult] = useState<VoiceQueryResponse | null>(null);
  const [playbackAudioUrl, setPlaybackAudioUrl] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioInputRef = useRef<HTMLInputElement>(null);

  // Start live microphone recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const file = new File([audioBlob], 'voice_query.wav', { type: 'audio/wav' });
        setSelectedAudio(file);
        setAudioUrl(URL.createObjectURL(audioBlob));
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
      onToast('Listening... Speak your procurement requirement.', 'info');
    } catch (err: any) {
      onToast('Microphone access denied or unsupported in this browser.', 'error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Create a synthetic sample query audio for instant testing without mic
  const handleCreateSampleAudio = async () => {
    setIsProcessing(true);
    try {
      const sampleText =
        language === 'hi'
          ? 'औद्योगिक पंप के लिए मोटर मानक'
          : language === 'ta'
          ? 'தொழில்துறை பம்பு மோட்டார் தரநிலைகள்'
          : 'High efficiency three phase induction motor for industrial water pumping';

      const synth = await synthesizeSpeech(sampleText, language);
      if (synth.audio_base64) {
        const binary = atob(synth.audio_base64);
        const array = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) array[i] = binary.charCodeAt(i);
        const blob = new Blob([array], { type: synth.mime_type || 'audio/wav' });
        const file = new File([blob], 'sample_query.wav', { type: synth.mime_type || 'audio/wav' });
        setSelectedAudio(file);
        setAudioUrl(URL.createObjectURL(blob));
        onToast('Generated synthetic sample voice query.', 'success');
      }
    } catch (err: any) {
      onToast(err.message || 'Sample audio creation failed.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleProcessVoice = async () => {
    if (!selectedAudio) {
      onToast('Please record audio or upload an audio file first.', 'error');
      return;
    }

    setIsProcessing(true);
    setVoiceResult(null);
    setPlaybackAudioUrl(null);

    try {
      const res = await submitVoiceQuery(selectedAudio, language, true);
      setVoiceResult(res);

      if (res.synthesized_audio?.audio_base64) {
        const binary = atob(res.synthesized_audio.audio_base64);
        const array = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) array[i] = binary.charCodeAt(i);
        const blob = new Blob([array], { type: res.synthesized_audio.mime_type || 'audio/wav' });
        setPlaybackAudioUrl(URL.createObjectURL(blob));
      }

      onToast(`Speech transcribed: "${res.transcription.transcript || res.transcription.transcription}"`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Voice query processing failed.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Voice Procurement Assistant"
        subtitle="End-to-End Multilingual Speech AI supporting English, Hindi, and Tamil with calibrated confidence scoring."
        badge="Multilingual Speech AI"
      >
        {/* Language Selector */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
            Spoken Language:
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {[
              { code: 'en', label: 'English' },
              { code: 'hi', label: 'हिंदी (Hindi)' },
              { code: 'ta', label: 'தமிழ் (Tamil)' },
            ].map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => setLanguage(lang.code)}
                style={{
                  padding: '7px 16px',
                  borderRadius: 'var(--radius-full)',
                  border: language === lang.code ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                  background: language === lang.code ? 'var(--accent-primary-subtle)' : '#f8fafc',
                  color: language === lang.code ? 'var(--accent-primary-dark)' : 'var(--text-secondary)',
                  fontSize: '0.85rem',
                  fontWeight: language === lang.code ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        {/* Audio Input Controls */}
        <div
          style={{
            background: '#f8fafc',
            borderRadius: 'var(--radius-lg)',
            padding: '28px 24px',
            border: '1px solid var(--border-subtle)',
            marginBottom: '22px',
            textAlign: 'center',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap', marginBottom: '18px' }}>
            {/* Live Record Toggle */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={isRecording ? 'btn-accent' : 'btn-primary'}
              style={{ minWidth: '170px' }}
            >
              {isRecording ? '⏹ Stop Recording' : '🎙️ Record Voice'}
            </button>

            {/* File Upload input */}
            <input
              ref={audioInputRef}
              type="file"
              accept="audio/*"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  setSelectedAudio(e.target.files[0]);
                  setAudioUrl(URL.createObjectURL(e.target.files[0]));
                }
              }}
            />
            <button
              type="button"
              onClick={() => audioInputRef.current?.click()}
              className="btn-secondary"
            >
              📁 Choose Audio File
            </button>

            {/* Instant Sample Generator */}
            <button
              type="button"
              onClick={handleCreateSampleAudio}
              className="btn-secondary"
            >
              ⚡ Load Synthetic Audio
            </button>
          </div>

          {/* Audio Preview */}
          {audioUrl && (
            <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                Input Audio: {selectedAudio?.name || 'Recording'}
              </span>
              <audio controls src={audioUrl} style={{ width: '100%', maxWidth: '400px', height: '36px' }} />
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={handleProcessVoice}
            disabled={!selectedAudio || isProcessing}
            className="btn-primary"
            style={{ minWidth: '210px' }}
          >
            {isProcessing ? 'Processing Speech...' : 'Analyze Voice Query 🚀'}
          </button>
        </div>
      </Panel>

      {/* Processing Skeletons */}
      {isProcessing && (
        <Panel title="Transcribing Speech & Calibrating Confidence...">
          <LoadingSkeleton height="80px" />
          <LoadingSkeleton height="100px" />
        </Panel>
      )}

      {/* Voice Results */}
      {!isProcessing && voiceResult && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
          {/* Transcription Card */}
          <div
            className="glass-panel"
            style={{
              padding: '22px 26px',
              marginBottom: '20px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
              borderLeft: '4px solid var(--accent-primary)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary-dark)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                TRANSCRIPTION (Confidence: {Math.round(voiceResult.transcription.confidence * 100)}%)
              </span>
              <span className="badge badge-indigo">
                Language: {voiceResult.transcription.language || voiceResult.transcription.detected_language || language}
              </span>
            </div>

            <p style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.5 }}>
              "{voiceResult.transcription.transcript || voiceResult.transcription.transcription}"
            </p>

            {voiceResult.transcription.repetition_needed && (
              <div
                style={{
                  marginTop: '12px',
                  padding: '10px 14px',
                  background: 'rgba(220, 38, 38, 0.06)',
                  border: '1px solid rgba(220, 38, 38, 0.22)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.82rem',
                  color: 'var(--status-danger)',
                }}
              >
                ⚠️ Audio confidence is low ({Math.round(voiceResult.transcription.confidence * 100)}%). Repetition advised.
              </div>
            )}
          </div>

          {/* Spoken Response & Synthesized Audio Player */}
          {voiceResult.spoken_summary && (
            <div
              className="glass-panel"
              style={{
                padding: '22px 26px',
                marginBottom: '20px',
                background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, #f8fafc 100%)',
                border: '1px solid rgba(79, 70, 229, 0.2)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                <span style={{ fontSize: '1.25rem' }}>🔊</span>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-primary-dark)' }}>
                  Spoken Response Summary
                </h4>
              </div>

              <p style={{ fontSize: '0.96rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.55 }}>
                {voiceResult.spoken_summary}
              </p>

              {playbackAudioUrl && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <audio controls autoPlay src={playbackAudioUrl} style={{ width: '100%', maxWidth: '420px', height: '36px' }} />
                </div>
              )}
            </div>
          )}

          {/* Recommended Standards from Voice Query */}
          {voiceResult.recommendation?.recommendations && (
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '22px 0 16px', color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
                Mapped Standards ({voiceResult.recommendation.recommendations.length})
              </h3>
              {voiceResult.recommendation.recommendations.map((cand, idx) => (
                <CandidateCard
                  key={cand.standard_id || idx}
                  candidate={cand}
                  rank={idx + 1}
                  onExplore={onExploreStandard}
                />
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};
