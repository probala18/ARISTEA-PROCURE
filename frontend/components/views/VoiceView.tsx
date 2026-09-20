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
      onToast('Listening... Speak your procurement query.', 'info');
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
      // Synthesize audio for a standard query
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

      onToast(`Speech transcribed: "${res.transcription.transcription}"`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Voice query processing failed.', 'error');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <Panel
        title="Voice Query & Speech Intelligence"
        subtitle="End-to-End Multilingual Speech AI (Module 10) supporting English, Hindi, and Tamil with confidence calibration."
        badge="Module 10 Speech AI"
      >
        {/* Language Selector */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Language Preference:
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
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
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-full)',
                  border: language === lang.code ? '1px solid var(--accent-teal)' : '1px solid rgba(255, 255, 255, 0.08)',
                  background: language === lang.code ? 'rgba(20, 184, 166, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  color: language === lang.code ? '#ffffff' : 'var(--text-secondary)',
                  fontSize: '0.85rem',
                  fontWeight: language === lang.code ? 600 : 400,
                  cursor: 'pointer',
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
            background: 'rgba(15, 23, 42, 0.6)',
            borderRadius: 'var(--radius-lg)',
            padding: '24px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            marginBottom: '20px',
            textAlign: 'center',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap', marginBottom: '16px' }}>
            {/* Live Record Toggle */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={isRecording ? 'btn-accent' : 'btn-primary'}
              style={{ minWidth: '160px' }}
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
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Input Audio: {selectedAudio?.name || 'Recording'}
              </span>
              <audio controls src={audioUrl} style={{ width: '100%', maxWidth: '380px', height: '36px' }} />
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={handleProcessVoice}
            disabled={!selectedAudio || isProcessing}
            className="btn-primary"
            style={{ minWidth: '200px' }}
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
              padding: '20px 24px',
              marginBottom: '20px',
              borderLeft: '4px solid var(--accent-teal)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-teal)' }}>
                TRANSCRIPTION (Confidence: {Math.round(voiceResult.transcription.confidence * 100)}%)
              </span>
              <span className="badge badge-blue">
                Language: {voiceResult.transcription.detected_language || language}
              </span>
            </div>

            <p style={{ fontSize: '1.1rem', fontWeight: 500, color: '#ffffff', lineHeight: 1.5 }}>
              "{voiceResult.transcription.transcription}"
            </p>

            {voiceResult.transcription.repetition_needed && (
              <div
                style={{
                  marginTop: '10px',
                  padding: '8px 12px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem',
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
                padding: '20px 24px',
                marginBottom: '20px',
                background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(15, 23, 42, 0.8) 100%)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>🔊</span>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-teal)' }}>
                  Spoken Response Summary
                </h4>
              </div>

              <p style={{ fontSize: '0.95rem', color: '#e2e8f0', marginBottom: '14px' }}>
                {voiceResult.spoken_summary}
              </p>

              {playbackAudioUrl && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <audio controls autoPlay src={playbackAudioUrl} style={{ width: '100%', maxWidth: '400px', height: '36px' }} />
                </div>
              )}
            </div>
          )}

          {/* Recommended Standards from Voice Query */}
          {voiceResult.recommendation?.recommendations && (
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '20px 0 14px', color: '#ffffff' }}>
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
