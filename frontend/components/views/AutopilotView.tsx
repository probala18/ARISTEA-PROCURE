'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Panel } from '@/components/ui/Panel';
import {
  runAutopilot,
  exportAutopilotDocx,
  AutopilotEvent,
  AutopilotResult,
  AutopilotStepStatus,
  AutopilotCitation,
} from '@/lib/api';

interface AutopilotViewProps {
  onExploreStandard: (stdId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

interface StepState {
  step: string;
  title: string;
  status: AutopilotStepStatus;
  summary: string;
  elapsed_ms?: number | null;
}

const DEFAULT_STEPS: StepState[] = [
  { step: 'understand', title: 'Understanding the need', status: 'pending', summary: '' },
  { step: 'standards', title: 'Discovering applicable standards', status: 'pending', summary: '' },
  { step: 'compliance', title: 'Checking QCO & certification mandates', status: 'pending', summary: '' },
  { step: 'versions', title: 'Verifying standard currency', status: 'pending', summary: '' },
  { step: 'market', title: 'Assessing supplier market depth', status: 'pending', summary: '' },
  { step: 'draft', title: 'Drafting the cited tender', status: 'pending', summary: '' },
  { step: 'redteam', title: 'Red-teaming the draft', status: 'pending', summary: '' },
];

const SAMPLES = [
  { label: '☀️ Solar street lights', need: '500 solar street lights with LED luminaires and batteries for village roads in Odisha, budget 40 lakh' },
  { label: '🔌 Building wiring', need: '20 km PVC insulated copper cables 1100V for government hospital wiring in Tamil Nadu' },
  { label: '🏗️ Bridge cement', need: '2000 bags ordinary portland cement 53 grade for bridge construction in Assam' },
  { label: '⚡ Smart meters', need: '10000 smart prepaid electricity meters for DISCOM rollout in Uttar Pradesh, budget 8 crore' },
];

const VOICE_LANGS = [
  { code: 'en-IN', label: 'English' },
  { code: 'hi-IN', label: 'हिन्दी' },
  { code: 'ta-IN', label: 'தமிழ்' },
  { code: 'te-IN', label: 'తెలుగు' },
  { code: 'bn-IN', label: 'বাংলা' },
  { code: 'mr-IN', label: 'मराठी' },
  { code: 'gu-IN', label: 'ગુજરાતી' },
  { code: 'kn-IN', label: 'ಕನ್ನಡ' },
  { code: 'ml-IN', label: 'മലയാളം' },
];

const STATUS_STYLE: Record<AutopilotStepStatus, { color: string; bg: string; icon: string }> = {
  pending: { color: 'var(--text-dim)', bg: 'var(--bg-secondary)', icon: '○' },
  running: { color: 'var(--accent-primary)', bg: 'var(--accent-primary-subtle)', icon: '◌' },
  done: { color: 'var(--status-success)', bg: 'var(--status-success-bg)', icon: '✓' },
  blocked: { color: 'var(--status-warning)', bg: 'var(--status-warning-bg)', icon: '!' },
  error: { color: 'var(--status-danger)', bg: 'var(--status-danger-bg)', icon: '×' },
};

const SEVERITY_BADGE: Record<string, string> = {
  CRITICAL: 'badge badge-red',
  WARNING: 'badge badge-amber',
  ADVISORY: 'badge badge-cyan',
  INFO: 'badge badge-indigo',
};

const READINESS: Record<AutopilotResult['readiness'], { label: string; color: string; bg: string; note: string }> = {
  READY_FOR_APPROVAL: {
    label: 'Ready for approval',
    color: 'var(--status-success)',
    bg: 'var(--status-success-bg)',
    note: 'No open critical findings. Review and sign off before publication.',
  },
  NEEDS_REVIEW: {
    label: 'Needs officer review',
    color: 'var(--status-warning)',
    bg: 'var(--status-warning-bg)',
    note: 'Some findings or clarifications need a procurement officer’s decision.',
  },
  BLOCKED: {
    label: 'Blocked',
    color: 'var(--status-danger)',
    bg: 'var(--status-danger-bg)',
    note: 'Autopilot could not ground this need in the BIS dataset. Add product type, material or rating.',
  },
};

export const AutopilotView: React.FC<AutopilotViewProps> = ({ onExploreStandard, onToast }) => {
  const [need, setNeed] = useState(SAMPLES[0].need);
  const [voiceLang, setVoiceLang] = useState('en-IN');
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [steps, setSteps] = useState<StepState[]>(DEFAULT_STEPS);
  const [result, setResult] = useState<AutopilotResult | null>(null);
  const [activeCitation, setActiveCitation] = useState<AutopilotCitation | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const recognitionRef = useRef<any>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const w = window as any;
    setVoiceSupported(Boolean(w.SpeechRecognition || w.webkitSpeechRecognition));
    return () => abortRef.current?.abort();
  }, []);

  const toggleVoice = () => {
    const w = window as any;
    const Recognition = w.SpeechRecognition || w.webkitSpeechRecognition;
    if (!Recognition) return;
    if (isListening) {
      recognitionRef.current?.stop();
      return;
    }
    const rec = new Recognition();
    rec.lang = voiceLang;
    rec.interimResults = true;
    rec.continuous = false;
    rec.onresult = (e: any) => {
      const transcript = Array.from(e.results)
        .map((r: any) => r[0].transcript)
        .join(' ');
      setNeed(transcript);
    };
    rec.onend = () => setIsListening(false);
    rec.onerror = () => {
      setIsListening(false);
      onToast('Voice capture failed. Check microphone permission.', 'error');
    };
    recognitionRef.current = rec;
    setIsListening(true);
    rec.start();
  };

  const handleRun = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!need.trim() || isRunning) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsRunning(true);
    setResult(null);
    setActiveCitation(null);
    setSteps(DEFAULT_STEPS.map((s) => ({ ...s })));

    const handleEvent = (ev: AutopilotEvent) => {
      if (ev.type === 'step') {
        setSteps((prev) =>
          prev.map((s) =>
            s.step === ev.step
              ? { ...s, status: ev.status, summary: ev.summary, elapsed_ms: ev.elapsed_ms }
              : s,
          ),
        );
      } else if (ev.type === 'result') {
        setResult(ev.result);
      } else if (ev.type === 'error') {
        onToast(ev.detail, 'error');
      }
    };

    try {
      await runAutopilot(need.trim(), handleEvent, {
        language: voiceLang.split('-')[0],
        signal: controller.signal,
      });
      onToast('Autopilot finished — tender package ready.', 'success');
    } catch (err: any) {
      if (err?.name !== 'AbortError') onToast(err.message || 'Autopilot run failed.', 'error');
    } finally {
      setIsRunning(false);
    }
  };

  const handleExport = async () => {
    if (!result) return;
    setIsExporting(true);
    try {
      const blob = await exportAutopilotDocx(result);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ARISTEA-${result.run_id}.docx`;
      a.click();
      URL.revokeObjectURL(url);
      onToast('Tender exported as Word document.', 'success');
    } catch (err: any) {
      onToast(err.message || 'Export failed.', 'error');
    } finally {
      setIsExporting(false);
    }
  };

  const citationMap = new Map((result?.citations || []).map((c) => [c.key, c]));
  const findings = result?.redteam?.findings || [];
  const mandatoryCount = (result?.standards || []).filter((s) => s.compliance?.requirement_level === 'MANDATORY').length;
  const completed = steps.filter((s) => s.status !== 'pending' && s.status !== 'running').length;

  return (
    <div style={{ maxWidth: '1180px', margin: '0 auto' }}>
      {/* Need input */}
      <Panel
        title="Describe your procurement need"
        subtitle="Type or speak in any of 9 languages. Autopilot runs every ARISTEA module and returns a tender where each clause cites its evidence."
        badge="Autopilot"
      >
        <form onSubmit={handleRun}>
          <div style={{ position: 'relative' }}>
            <textarea
              value={need}
              onChange={(e) => setNeed(e.target.value)}
              rows={3}
              placeholder="e.g. 500 solar street lights for village roads in Odisha, budget 40 lakh"
              style={{
                width: '100%',
                padding: '16px 18px',
                paddingRight: '64px',
                fontSize: '1.02rem',
                lineHeight: 1.55,
                borderRadius: 'var(--radius-md)',
                border: `1.5px solid ${isListening ? 'var(--accent-rose)' : 'var(--border-medium)'}`,
                background: 'var(--bg-input)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
                resize: 'vertical',
                outline: 'none',
              }}
            />
            {voiceSupported && (
              <button
                type="button"
                onClick={toggleVoice}
                aria-label={isListening ? 'Stop listening' : 'Speak your need'}
                title={isListening ? 'Stop listening' : 'Speak your need'}
                style={{
                  position: 'absolute',
                  right: '12px',
                  top: '12px',
                  width: '42px',
                  height: '42px',
                  borderRadius: '50%',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '1.15rem',
                  background: isListening ? 'var(--accent-rose)' : 'var(--accent-primary-subtle)',
                  color: isListening ? '#fff' : 'var(--accent-primary)',
                  boxShadow: isListening ? '0 0 0 6px rgba(225, 29, 72, 0.18)' : 'none',
                  transition: 'all 0.2s ease',
                }}
              >
                {isListening ? '■' : '🎙️'}
              </button>
            )}
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', margin: '12px 0 18px' }}>
            {SAMPLES.map((s) => (
              <button
                key={s.label}
                type="button"
                className="btn-secondary"
                onClick={() => setNeed(s.need)}
                style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              >
                {s.label}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              Voice language{' '}
              <select
                value={voiceLang}
                onChange={(e) => setVoiceLang(e.target.value)}
                style={{
                  marginLeft: '6px',
                  padding: '6px 10px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-medium)',
                  background: 'var(--bg-input)',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                {VOICE_LANGS.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </label>
            <div style={{ flex: 1 }} />
            <button type="submit" className="btn-primary" disabled={isRunning || !need.trim()} style={{ minWidth: '220px' }}>
              {isRunning ? `Running… ${completed}/${steps.length}` : '🚀 Generate tender package'}
            </button>
          </div>
        </form>
      </Panel>

      {/* Live pipeline */}
      {(isRunning || result) && (
        <Panel title="Autopilot pipeline" subtitle="Each step calls a verified ARISTEA module. Nothing is invented; unknowns are stated.">
          <div style={{ display: 'grid', gap: '10px' }}>
            {steps.map((s, i) => {
              const st = STATUS_STYLE[s.status];
              return (
                <motion.div
                  key={s.step}
                  layout
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '36px 1fr auto',
                    alignItems: 'center',
                    gap: '14px',
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    border: `1px solid ${s.status === 'running' ? 'var(--border-hover)' : 'var(--border-subtle)'}`,
                    background: s.status === 'running' ? 'var(--accent-primary-subtle)' : 'var(--bg-card)',
                  }}
                >
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      display: 'grid',
                      placeItems: 'center',
                      fontWeight: 800,
                      color: st.color,
                      background: st.bg,
                    }}
                  >
                    {s.status === 'running' ? (
                      <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
                        ◌
                      </motion.span>
                    ) : s.status === 'pending' ? (
                      i + 1
                    ) : (
                      st.icon
                    )}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.92rem' }}>{s.title}</div>
                    {s.summary && (
                      <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{s.summary}</div>
                    )}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {s.elapsed_ms != null ? `${(s.elapsed_ms / 1000).toFixed(1)}s` : ''}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </Panel>
      )}

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {/* Readiness + metrics */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                flexWrap: 'wrap',
                padding: '18px 22px',
                marginBottom: '20px',
                borderRadius: 'var(--radius-lg)',
                background: READINESS[result.readiness].bg,
                border: `1px solid ${READINESS[result.readiness].color}`,
              }}
            >
              <div style={{ flex: '1 1 280px' }}>
                <div style={{ fontWeight: 800, fontSize: '1.08rem', color: READINESS[result.readiness].color }}>
                  {READINESS[result.readiness].label}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{READINESS[result.readiness].note}</div>
              </div>
              {result.sections.length > 0 && (
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      navigator.clipboard.writeText(result.tender_text);
                      onToast('Tender text copied.', 'info');
                    }}
                  >
                    Copy text
                  </button>
                  <button className="btn-accent" onClick={handleExport} disabled={isExporting}>
                    {isExporting ? 'Exporting…' : '⬇ Download .docx'}
                  </button>
                </div>
              )}
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '12px',
                marginBottom: '24px',
              }}
            >
              {[
                { label: 'Standards applied', value: result.standards.length },
                { label: 'Mandatory (QCO/BIS)', value: mandatoryCount },
                { label: 'Evidence citations', value: result.citations.length },
                { label: 'Auto-fixes applied', value: result.redteam?.auto_fixes ?? 0 },
                {
                  label: 'Audit coverage',
                  value:
                    result.redteam?.coverage_after != null
                      ? `${Math.round(result.redteam.coverage_before ?? 0)}% → ${Math.round(result.redteam.coverage_after)}%`
                      : '—',
                },
              ].map((m) => (
                <div
                  key={m.label}
                  style={{
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    boxShadow: 'var(--shadow-card)',
                  }}
                >
                  <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-primary)' }}>{m.value}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>{m.label}</div>
                </div>
              ))}
            </div>

            {result.clarifications.length > 0 && (
              <Panel title="Clarifications needed" subtitle="Autopilot will not guess these. Add them to the need and re-run.">
                {result.clarifications.map((c) => (
                  <div key={c.component} style={{ marginBottom: '8px', fontSize: '0.9rem' }}>
                    <strong>{c.component}:</strong> {c.missing.join(', ')}
                  </div>
                ))}
              </Panel>
            )}

            {/* Tender document + citation inspector */}
            {result.sections.length > 0 && (
              <div className="autopilot-doc-grid">
                <Panel title="Tender document" subtitle="Click any citation to inspect the source record.">
                  <div style={{ fontFamily: 'var(--font-sans)', color: 'var(--text-primary)' }}>
                    {result.sections.map((sec) => {
                      const num = sec.heading.split('.')[0];
                      return (
                        <div key={sec.id} style={{ marginBottom: '20px' }}>
                          <h4 style={{ fontSize: '0.98rem', fontWeight: 800, marginBottom: '8px' }}>{sec.heading}</h4>
                          {sec.clauses.map((c, i) => (
                            <p
                              key={i}
                              style={{
                                fontSize: '0.9rem',
                                lineHeight: 1.6,
                                margin: '0 0 8px',
                                padding: c.kind !== 'clause' ? '8px 10px' : 0,
                                borderRadius: 'var(--radius-sm)',
                                background:
                                  c.kind === 'autofix'
                                    ? 'var(--status-success-bg)'
                                    : c.kind === 'advisory'
                                    ? 'var(--status-warning-bg)'
                                    : 'transparent',
                              }}
                            >
                              <strong style={{ color: 'var(--text-muted)' }}>
                                {num}.{i + 1}
                              </strong>{' '}
                              {c.kind === 'autofix' && (
                                <span className="badge badge-green" style={{ marginRight: '6px' }}>
                                  Red-team fix
                                </span>
                              )}
                              {c.text}
                              {c.citations.map((k) => (
                                <button
                                  key={k}
                                  onClick={() => setActiveCitation(citationMap.get(k) || null)}
                                  style={{
                                    marginLeft: '4px',
                                    padding: '1px 6px',
                                    fontSize: '0.7rem',
                                    fontWeight: 700,
                                    fontFamily: 'var(--font-mono)',
                                    borderRadius: 'var(--radius-full)',
                                    border: '1px solid var(--accent-primary-glow)',
                                    background:
                                      activeCitation?.key === k ? 'var(--accent-primary)' : 'var(--accent-primary-subtle)',
                                    color: activeCitation?.key === k ? '#fff' : 'var(--accent-primary-dark)',
                                    cursor: 'pointer',
                                    verticalAlign: 'middle',
                                  }}
                                >
                                  {k}
                                </button>
                              ))}
                            </p>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                </Panel>

                <div className="autopilot-inspector">
                  <Panel title="Evidence inspector" subtitle={`${result.citations.length} grounded records`}>
                    {activeCitation ? (
                      <div>
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px' }}>
                          <span className="badge badge-indigo">{activeCitation.key}</span>
                          <span className="badge badge-cyan">{activeCitation.source_type.replace(/_/g, ' ')}</span>
                        </div>
                        <div style={{ fontWeight: 700, marginBottom: '6px', fontSize: '0.9rem' }}>{activeCitation.label}</div>
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                          {activeCitation.details}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                          Source: <code>{activeCitation.source_dataset}</code>
                        </div>
                        {activeCitation.provenance && (
                          <pre
                            style={{
                              fontSize: '0.7rem',
                              maxHeight: '220px',
                              overflow: 'auto',
                              padding: '10px',
                              borderRadius: 'var(--radius-sm)',
                              background: 'var(--bg-secondary)',
                              whiteSpace: 'pre-wrap',
                              wordBreak: 'break-word',
                            }}
                          >
                            {JSON.stringify(activeCitation.provenance, null, 2)}
                          </pre>
                        )}
                        {activeCitation.source_type === 'STANDARD_RECORD' && (
                          <button
                            className="btn-secondary"
                            style={{ marginTop: '10px', fontSize: '0.8rem' }}
                            onClick={() => onExploreStandard(activeCitation.label)}
                          >
                            Open in Standards Directory →
                          </button>
                        )}
                      </div>
                    ) : (
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                        Select a citation chip in the tender to see the dataset record and provenance behind that clause.
                      </div>
                    )}
                  </Panel>
                </div>
              </div>
            )}

            {/* Red-team report */}
            {findings.length > 0 && (
              <Panel
                title="Red-team review"
                subtitle="The Module 12 auditor attacked the draft as a vigilance officer would. Fixable gaps were corrected and re-audited."
              >
                <div style={{ display: 'grid', gap: '10px' }}>
                  {findings.map((f, i) => (
                    <div
                      key={i}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'auto 1fr auto',
                        gap: '12px',
                        alignItems: 'start',
                        padding: '12px 14px',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <span className={SEVERITY_BADGE[f.severity] || 'badge'}>{f.severity}</span>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', fontWeight: 600 }}>{f.issue}</div>
                        <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '3px' }}>→ {f.fix}</div>
                      </div>
                      <span className={f.auto_fixed ? 'badge badge-green' : 'badge badge-amber'}>
                        {f.auto_fixed ? 'Auto-fixed' : 'Officer action'}
                      </span>
                    </div>
                  ))}
                </div>
              </Panel>
            )}

            {/* Standards bill of materials */}
            {result.standards.length > 0 && (
              <Panel title="Standards bill of materials" subtitle="Every standard Autopilot applied, and why.">
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                    <thead>
                      <tr style={{ textAlign: 'left', color: 'var(--text-muted)' }}>
                        {['Standard', 'Role', 'Component', 'Requirement', 'Scheme', 'Market'].map((h) => (
                          <th key={h} style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.standards.map((s) => (
                        <tr key={s.standard_id}>
                          <td style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
                            <button
                              onClick={() => onExploreStandard(s.is_number)}
                              style={{
                                background: 'none',
                                border: 'none',
                                padding: 0,
                                cursor: 'pointer',
                                fontWeight: 700,
                                color: 'var(--accent-primary-dark)',
                                textAlign: 'left',
                              }}
                            >
                              {s.is_number}
                            </button>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.76rem' }}>{s.title}</div>
                          </td>
                          <td style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
                            {String(s.role).replace(/_/g, ' ').toLowerCase()}
                          </td>
                          <td style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle)' }}>{s.matched_component}</td>
                          <td style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
                            <span
                              className={
                                s.compliance?.requirement_level === 'MANDATORY'
                                  ? 'badge badge-red'
                                  : s.compliance?.requirement_level === 'VOLUNTARY'
                                  ? 'badge badge-green'
                                  : 'badge'
                              }
                            >
                              {s.compliance?.requirement_level || 'UNKNOWN'}
                            </span>
                          </td>
                          <td style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
                            {s.compliance?.scheme || '—'}
                          </td>
                          <td style={{ padding: '8px', borderBottom: '1px solid var(--border-subtle)' }}>
                            {s.market?.licence_count != null
                              ? `${s.market.licence_count} licences`
                              : 'unknown'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '14px' }}>{result.disclaimer}</p>
              </Panel>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
