'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  analyzeRedline,
  applyAllRedlineFixes,
  verifyStandards,
  extractTableFromImage,
  extractTableFromText,
  RedlineAnalysisResponse,
  RedlineSegment as RedlineSegmentType,
  RedlineAutoFix,
  AuditorVerificationResponse,
  AuditorVerifiedStandard,
  VisionTableResponse,
} from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { StandardsMigrationCard } from './redline/StandardsMigrationCard';
import { TenderOverviewSection } from './redline/TenderOverviewSection';
import { ComparisonMatrixSection } from './redline/ComparisonMatrixSection';
import { EcoTrackSection } from './redline/EcoTrackSection';
import { BidderRequirementsSection } from './redline/BidderRequirementsSection';
import { PrimarySourceTrackerSection } from './redline/PrimarySourceTrackerSection';
import { CostEstimationSection } from './redline/CostEstimationSection';

interface RedlineViewProps {
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

/* ─── Sample Tender Text ──────────────────────────────── */
const SAMPLE_DOCUMENT = `CENTRAL PUBLIC WORKS DEPARTMENT (CPWD)
NOTICE INVITING TENDER FOR PUMPING MACHINERY & MOTOR INSTALLATIONS
NIT No: CPWD/EE/2026/PUMP-042

SECTION 1: GENERAL INSTRUCTIONS & SCOPE
1.1 The contractor shall supply, install, test, and commission heavy-duty pumping equipment.
1.2 All installations must adhere strictly to current statutory Indian Standard specifications.

SECTION 2: TECHNICAL SPECIFICATIONS FOR INDUCTION MOTORS
Clause 2.1: Motors shall be 3-phase, 415 V, 50 Hz squirrel-cage induction motors conforming to IS 325:1996.
Clause 2.2: Motor insulation class shall be Class F with temperature rise limited to Class B.
Clause 2.3: Efficiency class of the motors shall conform to high efficiency requirements.

SECTION 3: POWER CABLES & EARTHING
Clause 3.1: Heavy-duty PVC insulated electric cables for working voltages up to and including 1100 V conforming to IS 1554 (Part 1):1988 shall be supplied.
Clause 3.2: Earthing installation shall strictly comply with Code of Practice for Earthing as per IS 3043:1987.

SECTION 4: TESTING, INSPECTION & QUALITY ASSURANCE
Clause 4.1: Routine and type test certificates for the electric motors shall be submitted prior to dispatch.
Clause 4.2: Pump performance testing and hydraulic pressure tests shall be carried out in accordance with IS 9137:1979.

SECTION 5: CEMENT & CIVIL WORKS
Clause 5.1: All structural concrete shall use Ordinary Portland Cement conforming to IS 269:2015.
Clause 5.2: Steel reinforcement bars shall conform to IS 1786:2008.`;

/* ─── Color Map ───────────────────────────────────────── */
const ANNOTATION_COLORS: Record<string, { bg: string; border: string; text: string; icon: string; label: string }> = {
  COMPLIANT:    { bg: 'rgba(5, 150, 105, 0.12)',  border: '#059669', text: '#065f46', icon: '✅', label: 'Current & Valid' },
  OUTDATED:     { bg: 'rgba(220, 38, 38, 0.10)',   border: '#dc2626', text: '#991b1b', icon: '🔴', label: 'Outdated / Superseded' },
  UNRECOGNIZED: { bg: 'rgba(245, 158, 11, 0.10)',  border: '#f59e0b', text: '#92400e', icon: '🟠', label: 'Not in BIS Dataset' },
  AMENDED:      { bg: 'rgba(234, 179, 8, 0.10)',   border: '#eab308', text: '#854d0e', icon: '🟡', label: 'Has Amendments' },
  PLAIN:        { bg: 'transparent',                border: 'transparent', text: 'inherit', icon: '',   label: '' },
};

/* ─── Verdict Color Map ───────────────────────────────── */
const VERDICT_COLORS: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  VERIFIED:            { bg: 'rgba(5, 150, 105, 0.08)',  border: '#059669', text: '#065f46', icon: '✅' },
  SUPERSEDED_VERIFIED: { bg: 'rgba(245, 158, 11, 0.08)', border: '#f59e0b', text: '#92400e', icon: '⚠️' },
  SUSPICIOUS:          { bg: 'rgba(234, 179, 8, 0.08)',  border: '#eab308', text: '#854d0e', icon: '🟡' },
  HALLUCINATION:       { bg: 'rgba(220, 38, 38, 0.08)',  border: '#dc2626', text: '#991b1b', icon: '🔴' },
  PARTIAL_MATCH:       { bg: 'rgba(245, 158, 11, 0.08)', border: '#f59e0b', text: '#92400e', icon: '🟠' },
  FORMAT_INVALID:      { bg: 'rgba(220, 38, 38, 0.06)',  border: '#dc2626', text: '#991b1b', icon: '❌' },
};

/* ═══════════════════════════════════════════════════════════
   MAIN VIEW COMPONENT
   ═══════════════════════════════════════════════════════ */
export const RedlineView: React.FC<RedlineViewProps> = ({ onToast }) => {
  const [documentText, setDocumentText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [redlineResult, setRedlineResult] = useState<RedlineAnalysisResponse | null>(null);
  const [hoveredSegment, setHoveredSegment] = useState<number | null>(null);
  const [activeFixId, setActiveFixId] = useState<string | null>(null);

  // Auditor state
  const [auditorRefs, setAuditorRefs] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [auditorResult, setAuditorResult] = useState<AuditorVerificationResponse | null>(null);

  // Vision state
  const [visionFile, setVisionFile] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [visionResult, setVisionResult] = useState<VisionTableResponse | null>(null);
  const visionInputRef = useRef<HTMLInputElement>(null);

  // Active sub-tab
  const [activeSection, setActiveSection] = useState<
    'redline' | 'overview' | 'comparison' | 'eco' | 'bidder' | 'tracker' | 'cost' | 'auditor' | 'vision'
  >('redline');

  /* ─── Redline Actions ─────────────────────────────────── */
  const handleLoadSample = () => {
    setDocumentText(SAMPLE_DOCUMENT);
    setRedlineResult(null);
    onToast('Loaded sample CPWD tender document.', 'info');
  };

  const handleAnalyze = async () => {
    if (!documentText.trim() || documentText.trim().length < 10) {
      onToast('Please enter or paste tender document text (minimum 10 characters).', 'error');
      return;
    }
    setIsAnalyzing(true);
    setRedlineResult(null);
    try {
      const result = await analyzeRedline(documentText);
      setRedlineResult(result);
      const { summary } = result;
      onToast(
        `Redline complete: ${summary.compliant_count} compliant, ${summary.outdated_count} outdated, ${summary.auto_fixes_available} auto-fixes available`,
        summary.outdated_count > 0 ? 'error' : 'success'
      );
    } catch (err: any) {
      onToast(err.message || 'Redline analysis failed.', 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAutoFixAll = async () => {
    if (!documentText.trim()) return;
    setIsFixing(true);
    try {
      const result = await applyAllRedlineFixes(documentText);
      if (result.corrected_text) {
        setDocumentText(result.corrected_text);
        setRedlineResult(null);
        onToast(`${result.fixes_applied} outdated standards auto-corrected! Re-analyze to verify.`, 'success');
      }
    } catch (err: any) {
      onToast(err.message || 'Auto-fix failed.', 'error');
    } finally {
      setIsFixing(false);
    }
  };

  const handleSingleFix = (fix: RedlineAutoFix) => {
    const corrected = documentText.replace(fix.old_text, fix.new_text);
    setDocumentText(corrected);
    setActiveFixId(fix.fix_id);
    setRedlineResult(null);
    onToast(`Fixed: ${fix.old_standard_id} → ${fix.new_standard_id}`, 'success');
  };

  /* ─── Auditor Actions ─────────────────────────────────── */
  const handleVerify = async () => {
    const refs = auditorRefs
      .split('\n')
      .map((r) => r.trim())
      .filter(Boolean);
    if (refs.length === 0) {
      onToast('Enter at least one standard reference (one per line).', 'error');
      return;
    }
    setIsVerifying(true);
    setAuditorResult(null);
    try {
      const result = await verifyStandards(refs);
      setAuditorResult(result);
      if (result.hallucination_count > 0) {
        onToast(`🚨 ${result.hallucination_count} HALLUCINATION(S) DETECTED! Check results.`, 'error');
      } else if (result.suspicious_count > 0) {
        onToast(`⚠️ ${result.suspicious_count} suspicious reference(s) found.`, 'error');
      } else {
        onToast(`✅ All ${result.verified_count} references verified!`, 'success');
      }
    } catch (err: any) {
      onToast(err.message || 'Verification failed.', 'error');
    } finally {
      setIsVerifying(false);
    }
  };

  const loadSampleRefs = () => {
    setAuditorRefs('IS 12615:2018\nIS 325:1996\nIS 9999:2024\nIS 1554 (Part 1):1988\nIS 99999');
    setAuditorResult(null);
    onToast('Loaded sample references including likely hallucinations.', 'info');
  };

  /* ─── Vision Actions ──────────────────────────────────── */
  const handleVisionExtract = async () => {
    if (!visionFile) {
      onToast('Please select an image file.', 'error');
      return;
    }
    setIsExtracting(true);
    setVisionResult(null);
    try {
      const result = await extractTableFromImage(visionFile);
      setVisionResult(result);
      onToast(
        `Extracted ${result.total_tables} table(s), ${result.total_formulas} formula(s). Method: ${result.processing_method}`,
        result.total_tables > 0 ? 'success' : 'info'
      );
    } catch (err: any) {
      onToast(err.message || 'Vision extraction failed.', 'error');
    } finally {
      setIsExtracting(false);
    }
  };

  const [visionText, setVisionText] = useState('');
  const handleTextExtract = async () => {
    if (!visionText.trim()) {
      onToast('Paste table text to extract.', 'error');
      return;
    }
    setIsExtracting(true);
    setVisionResult(null);
    try {
      const result = await extractTableFromText(visionText);
      setVisionResult(result);
      onToast(`Extracted ${result.total_tables} table(s) from text.`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Text extraction failed.', 'error');
    } finally {
      setIsExtracting(false);
    }
  };

  const renderEmptyState = (title: string, desc: string) => (
    <div
      style={{
        padding: '48px 24px',
        textAlign: 'center',
        background: '#ffffff',
        borderRadius: 'var(--radius-lg, 12px)',
        border: '1px solid #e2e8f0',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
      }}
    >
      <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>📊</div>
      <h3 style={{ margin: '0 0 6px 0', fontSize: '1.2rem', fontWeight: 800, color: '#0f172a' }}>{title}</h3>
      <p style={{ margin: '0 0 20px 0', fontSize: '0.86rem', color: '#64748b', maxWidth: '540px', marginInline: 'auto' }}>
        {desc}
      </p>
      <button
        onClick={async () => {
          setDocumentText(SAMPLE_DOCUMENT);
          setIsAnalyzing(true);
          try {
            const res = await analyzeRedline(SAMPLE_DOCUMENT);
            setRedlineResult(res);
            onToast('Sample tender analyzed! All intelligence dashboards unlocked.', 'success');
          } catch (e: any) {
            onToast(e.message || 'Analysis failed', 'error');
          } finally {
            setIsAnalyzing(false);
          }
        }}
        disabled={isAnalyzing}
        className="btn-primary"
        style={{ padding: '10px 24px', fontSize: '0.9rem', fontWeight: 700 }}
      >
        {isAnalyzing ? '🔍 Analyzing Sample...' : '📋 Analyze Sample Tender (Instant Demo)'}
      </button>
    </div>
  );

  /* ═══════════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════ */
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Feature Selector Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '6px',
          marginBottom: '20px',
          background: '#ffffff',
          padding: '6px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border-subtle)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          overflowX: 'auto',
          scrollbarWidth: 'none',
        }}
      >
        {[
          { key: 'redline' as const, icon: '🔴', label: 'Redline & Migration', badge: 'Visual' },
          { key: 'overview' as const, icon: '📐', label: 'Overview & Measurements', badge: 'Specs' },
          { key: 'comparison' as const, icon: '📊', label: 'Comparison Matrix', badge: 'Audit' },
          { key: 'eco' as const, icon: '🌿', label: 'Eco Track', badge: 'Green' },
          { key: 'bidder' as const, icon: '👥', label: 'Bidder Criteria', badge: 'Criteria' },
          { key: 'tracker' as const, icon: '🎯', label: 'Sources & Tasks', badge: 'Tracker' },
          { key: 'cost' as const, icon: '💰', label: 'AI Cost Estimate', badge: 'Budget' },
          { key: 'auditor' as const, icon: '🛡️', label: 'AI Safety Shield', badge: 'Guard' },
          { key: 'vision' as const, icon: '👁️', label: 'Vision Table Reader', badge: 'OCR' },
        ].map((tab) => {
          const isActive = activeSection === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveSection(tab.key)}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 16px',
                borderRadius: 'var(--radius-full)',
                border: 'none',
                background: isActive ? 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? 700 : 600,
                fontSize: '0.84rem',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                boxShadow: isActive ? '0 4px 14px rgba(79, 70, 229, 0.3)' : 'none',
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              <span
                style={{
                  fontSize: '0.62rem',
                  padding: '1px 6px',
                  borderRadius: '999px',
                  background: isActive ? 'rgba(255,255,255,0.25)' : 'rgba(79,70,229,0.08)',
                  color: isActive ? '#fff' : 'var(--accent-primary)',
                  fontWeight: 700,
                }}
              >
                {tab.badge}
              </span>
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        {/* ─── REDLINE EDITOR TAB ─────────────────────────── */}
        {activeSection === 'redline' && (
          <motion.div key="redline" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            <Panel
              title="Redline Document Editor"
              subtitle="Paste your tender document below. Every IS reference will be highlighted: Green = compliant, Red = outdated (with one-click auto-fix)."
              badge="Visual Wow"
            >
              {/* Text Input */}
              <textarea
                value={documentText}
                onChange={(e) => { setDocumentText(e.target.value); setRedlineResult(null); }}
                placeholder="Paste your tender document text here..."
                rows={10}
                style={{
                  width: '100%',
                  padding: '16px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.88rem',
                  lineHeight: 1.7,
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  background: '#fafbfc',
                  color: 'var(--text-primary)',
                  resize: 'vertical',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = 'var(--accent-primary)')}
                onBlur={(e) => (e.target.style.borderColor = 'var(--border-subtle)')}
              />

              {/* Action Bar */}
              <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
                <button onClick={handleLoadSample} className="btn-secondary" style={{ fontSize: '0.84rem' }}>
                  📋 Load Sample Tender
                </button>
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !documentText.trim()}
                  className="btn-primary"
                  style={{ minWidth: '200px' }}
                >
                  {isAnalyzing ? '🔍 Analyzing...' : '🔍 Analyze Document'}
                </button>
                {redlineResult && redlineResult.summary.auto_fixes_available > 0 && (
                  <button
                    onClick={handleAutoFixAll}
                    disabled={isFixing}
                    className="btn-accent"
                    style={{ minWidth: '200px' }}
                  >
                    {isFixing ? 'Fixing...' : `⚡ Auto-Fix All (${redlineResult.summary.auto_fixes_available})`}
                  </button>
                )}
              </div>
            </Panel>

            {/* Loading */}
            {isAnalyzing && (
              <Panel title="Scanning document for IS references...">
                <LoadingSkeleton height="60px" />
                <LoadingSkeleton height="200px" />
              </Panel>
            )}

            {/* Redline Results */}
            {redlineResult && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                {/* Summary Dashboard */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                    gap: '12px',
                    marginBottom: '20px',
                  }}
                >
                  {[
                    { label: 'Compliance Score', value: `${Math.round(redlineResult.summary.compliance_score * 100)}%`, color: redlineResult.summary.compliance_score >= 0.7 ? '#059669' : redlineResult.summary.compliance_score >= 0.4 ? '#d97706' : '#dc2626', bg: redlineResult.summary.compliance_score >= 0.7 ? 'rgba(5,150,105,0.08)' : redlineResult.summary.compliance_score >= 0.4 ? 'rgba(245,158,11,0.08)' : 'rgba(220,38,38,0.08)' },
                    { label: 'Compliant', value: redlineResult.summary.compliant_count, color: '#059669', bg: 'rgba(5,150,105,0.06)' },
                    { label: 'Outdated', value: redlineResult.summary.outdated_count, color: '#dc2626', bg: 'rgba(220,38,38,0.06)' },
                    { label: 'Unrecognized', value: redlineResult.summary.unrecognized_count, color: '#f59e0b', bg: 'rgba(245,158,11,0.06)' },
                    { label: 'Has Amendments', value: redlineResult.summary.amended_count, color: '#eab308', bg: 'rgba(234,179,8,0.06)' },
                    { label: 'Auto-Fixes', value: redlineResult.summary.auto_fixes_available, color: '#4f46e5', bg: 'rgba(79,70,229,0.06)' },
                  ].map((metric) => (
                    <div
                      key={metric.label}
                      style={{
                        padding: '16px',
                        background: metric.bg,
                        borderRadius: 'var(--radius-md)',
                        border: `1px solid ${metric.color}22`,
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>
                        {metric.label}
                      </div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: metric.color, fontFamily: 'var(--font-mono)' }}>
                        {metric.value}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Legend */}
                <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', flexWrap: 'wrap', fontSize: '0.78rem', fontWeight: 600 }}>
                  {Object.entries(ANNOTATION_COLORS)
                    .filter(([key]) => key !== 'PLAIN')
                    .map(([key, colors]) => (
                      <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span
                          style={{
                            width: '14px',
                            height: '14px',
                            borderRadius: '3px',
                            background: colors.bg,
                            border: `2px solid ${colors.border}`,
                            display: 'inline-block',
                          }}
                        />
                        <span style={{ color: colors.text }}>{colors.icon} {colors.label}</span>
                      </div>
                    ))}
                </div>

                {/* Annotated Document Render */}
                <Panel title="Annotated Document" badge="Redline">
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.88rem',
                      lineHeight: 1.9,
                      padding: '20px',
                      background: '#fefefe',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)',
                      whiteSpace: 'pre-wrap',
                      maxHeight: '600px',
                      overflowY: 'auto',
                    }}
                  >
                    {redlineResult.segments.map((seg) => {
                      const colors = ANNOTATION_COLORS[seg.annotation_type] || ANNOTATION_COLORS.PLAIN;
                      const isAnnotated = seg.annotation_type !== 'PLAIN';
                      const isHovered = hoveredSegment === seg.segment_id;

                      if (!isAnnotated) {
                        return <span key={seg.segment_id}>{seg.text}</span>;
                      }

                      return (
                        <span
                          key={seg.segment_id}
                          onMouseEnter={() => setHoveredSegment(seg.segment_id)}
                          onMouseLeave={() => setHoveredSegment(null)}
                          style={{
                            position: 'relative',
                            display: 'inline',
                            background: colors.bg,
                            borderBottom: `3px solid ${colors.border}`,
                            padding: '2px 4px',
                            borderRadius: '3px',
                            color: colors.text,
                            fontWeight: 700,
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                            boxShadow: isHovered ? `0 0 0 2px ${colors.border}40` : 'none',
                          }}
                          title={seg.tooltip || ''}
                        >
                          {seg.text}
                          {/* Hover Tooltip Card */}
                          {isHovered && (
                            <span
                              style={{
                                position: 'absolute',
                                bottom: '100%',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                marginBottom: '8px',
                                background: '#1e293b',
                                color: '#f8fafc',
                                padding: '12px 16px',
                                borderRadius: '10px',
                                fontSize: '0.78rem',
                                fontWeight: 500,
                                lineHeight: 1.5,
                                whiteSpace: 'normal',
                                width: '320px',
                                zIndex: 100,
                                boxShadow: '0 8px 30px rgba(0,0,0,0.25)',
                                pointerEvents: 'auto',
                              }}
                            >
                              <div style={{ fontWeight: 700, marginBottom: '6px', fontSize: '0.82rem' }}>
                                {colors.icon} {seg.standard_id} — {colors.label}
                              </div>
                              {seg.standard_title && (
                                <div style={{ marginBottom: '4px', opacity: 0.9 }}>{seg.standard_title}</div>
                              )}
                              {seg.tooltip && <div style={{ opacity: 0.85 }}>{seg.tooltip}</div>}
                              {seg.auto_fix && (
                                <button
                                  onClick={(e) => { e.stopPropagation(); handleSingleFix(seg.auto_fix!); }}
                                  style={{
                                    marginTop: '8px',
                                    padding: '6px 14px',
                                    background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: '6px',
                                    fontSize: '0.76rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    width: '100%',
                                    boxShadow: '0 2px 8px rgba(5,150,105,0.3)',
                                  }}
                                >
                                  ⚡ Auto-Fix → {seg.auto_fix.new_standard_id}
                                </button>
                              )}
                              {/* Arrow */}
                              <span
                                style={{
                                  position: 'absolute',
                                  bottom: '-6px',
                                  left: '50%',
                                  transform: 'translateX(-50%)',
                                  width: 0,
                                  height: 0,
                                  borderLeft: '6px solid transparent',
                                  borderRight: '6px solid transparent',
                                  borderTop: '6px solid #1e293b',
                                }}
                              />
                            </span>
                          )}
                        </span>
                      );
                    })}
                  </div>
                </Panel>

                {/* Auto-Fix Summary Cards */}
                {redlineResult.auto_fixes.length > 0 && (
                  <Panel title="Available Auto-Fixes" subtitle="Click any fix to apply it to the document." badge={`${redlineResult.auto_fixes.length} Fixes`}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {redlineResult.auto_fixes.map((fix) => (
                        <div
                          key={fix.fix_id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '16px',
                            padding: '14px 18px',
                            background: '#fff',
                            border: '1px solid var(--border-subtle)',
                            borderLeft: '4px solid #dc2626',
                            borderRadius: 'var(--radius-md)',
                            flexWrap: 'wrap',
                          }}
                        >
                          <div style={{ flex: 1, minWidth: '200px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#dc2626', textDecoration: 'line-through' }}>
                                {fix.old_standard_id}
                              </span>
                              <span style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>→</span>
                              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#059669' }}>
                                {fix.new_standard_id}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                              {fix.reason}
                            </div>
                          </div>
                          <button
                            onClick={() => handleSingleFix(fix)}
                            className="btn-primary"
                            style={{ fontSize: '0.8rem', padding: '8px 16px', whiteSpace: 'nowrap' }}
                          >
                            ⚡ Apply Fix
                          </button>
                        </div>
                      ))}
                    </div>
                  </Panel>
                )}

                {/* Standards Migration: Check Old Standard in Red -> Get New Standard with Official Reference */}
                {redlineResult.standards_redline_mappings && redlineResult.standards_redline_mappings.length > 0 && (
                  <StandardsMigrationCard
                    mappings={redlineResult.standards_redline_mappings}
                    onApplyFix={(oldStd, newStd) => {
                      setDocumentText((prev) => prev.replace(oldStd, newStd));
                      onToast(`Replaced ${oldStd} with current standard ${newStd}. Click Analyze to re-evaluate.`, 'success');
                    }}
                  />
                )}
              </motion.div>
            )}
          </motion.div>
        )}

        {/* ─── TENDER OVERVIEW & MEASUREMENTS TAB ─────────── */}
        {activeSection === 'overview' && (
          <motion.div key="overview" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            {redlineResult?.tender_overview ? (
              <TenderOverviewSection overview={redlineResult.tender_overview} />
            ) : (
              renderEmptyState(
                'Tender Overview & Technical Measurements',
                'Extract operational voltages, pump flow rates, motor power ratings, cable parameters, and statutory Indian Standards from your tender document.'
              )
            )}
          </motion.div>
        )}

        {/* ─── COMPARISON MATRIX & CHARTS TAB ─────────────── */}
        {activeSection === 'comparison' && (
          <motion.div key="comparison" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            {redlineResult?.comparison_matrix && redlineResult.comparison_matrix.length > 0 ? (
              <ComparisonMatrixSection rows={redlineResult.comparison_matrix} />
            ) : (
              renderEmptyState(
                'Tender vs Standard Comparison Matrix',
                'Benchmark draft tender clauses against current BIS Indian Standard mandates and best-practice industry engineering thresholds.'
              )
            )}
          </motion.div>
        )}

        {/* ─── ECO TRACK & SUSTAINABILITY TAB ─────────────── */}
        {activeSection === 'eco' && (
          <motion.div key="eco" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            {redlineResult?.eco_track ? (
              <EcoTrackSection ecoTrack={redlineResult.eco_track} />
            ) : (
              renderEmptyState(
                'Eco Track & Green Procurement Analytics',
                'Track BEE Star energy ratings, carbon footprint reduction (CO2 tons/year), and life-cycle electricity cost savings.'
              )
            )}
          </motion.div>
        )}

        {/* ─── BIDDER REQUIREMENTS CRITERIA TAB ───────────── */}
        {activeSection === 'bidder' && (
          <motion.div key="bidder" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            {redlineResult?.bidder_requirements ? (
              <BidderRequirementsSection requirements={redlineResult.bidder_requirements} />
            ) : (
              renderEmptyState(
                'Tender Bidder Eligibility & Qualification Criteria',
                'Summarize technical qualifications, financial solvency certificates, and statutory Make-in-India / GFR Rule 144 declarations.'
              )
            )}
          </motion.div>
        )}

        {/* ─── PRIMARY SOURCE & TASK TRACKER TAB ──────────── */}
        {activeSection === 'tracker' && (
          <motion.div key="tracker" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            <PrimarySourceTrackerSection
              primarySources={redlineResult?.primary_sources}
              initialTasks={redlineResult?.compliance_tasks}
              onToast={onToast}
            />
          </motion.div>
        )}

        {/* ─── AI PROJECT COST ESTIMATION TAB ─────────────── */}
        {activeSection === 'cost' && (
          <motion.div key="cost" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            {redlineResult?.cost_estimation ? (
              <CostEstimationSection estimation={redlineResult.cost_estimation} />
            ) : (
              renderEmptyState(
                'AI Project Cost & Budget Estimation',
                'Generate estimated project expenditures based on CPWD Delhi Schedule of Rates (DSR), line-item schedules, and value engineering savings.'
              )
            )}
          </motion.div>
        )}

        {/* ─── ADVERSARIAL AUDITOR TAB ────────────────────── */}
        {activeSection === 'auditor' && (
          <motion.div key="auditor" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            <Panel
              title="Adversarial AI Double-Check"
              subtitle="Enter standard references (one per line). The Auditor AI will aggressively verify each one against the verified BIS database and catch any hallucinated or fabricated numbers."
              badge="Safety Shield"
            >
              <textarea
                value={auditorRefs}
                onChange={(e) => { setAuditorRefs(e.target.value); setAuditorResult(null); }}
                placeholder={`Enter standard references, one per line:\nIS 12615:2018\nIS 325:1996\nIS 9999 (fake)`}
                rows={6}
                style={{
                  width: '100%',
                  padding: '16px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.9rem',
                  lineHeight: 1.7,
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  background: '#fafbfc',
                  resize: 'vertical',
                  outline: 'none',
                }}
              />

              <div style={{ display: 'flex', gap: '12px', marginTop: '14px', flexWrap: 'wrap' }}>
                <button onClick={loadSampleRefs} className="btn-secondary" style={{ fontSize: '0.84rem' }}>
                  🧪 Load Test References (incl. fakes)
                </button>
                <button
                  onClick={handleVerify}
                  disabled={isVerifying || !auditorRefs.trim()}
                  className="btn-primary"
                  style={{ minWidth: '220px' }}
                >
                  {isVerifying ? '🛡️ Verifying...' : '🛡️ Run Adversarial Audit'}
                </button>
              </div>
            </Panel>

            {isVerifying && (
              <Panel title="Cross-checking references against verified BIS database...">
                <LoadingSkeleton height="80px" />
              </Panel>
            )}

            {auditorResult && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                {/* Trust Score */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: '12px',
                    marginBottom: '20px',
                  }}
                >
                  {[
                    { label: 'Trust Score', value: `${Math.round(auditorResult.overall_trust_score * 100)}%`, color: auditorResult.overall_trust_score >= 0.8 ? '#059669' : '#dc2626', bg: auditorResult.overall_trust_score >= 0.8 ? 'rgba(5,150,105,0.08)' : 'rgba(220,38,38,0.08)' },
                    { label: 'Verified', value: auditorResult.verified_count, color: '#059669', bg: 'rgba(5,150,105,0.06)' },
                    { label: 'Suspicious', value: auditorResult.suspicious_count, color: '#f59e0b', bg: 'rgba(245,158,11,0.06)' },
                    { label: 'Hallucinated', value: auditorResult.hallucination_count, color: '#dc2626', bg: 'rgba(220,38,38,0.06)' },
                    { label: 'Blocked', value: auditorResult.blocked_count, color: '#7c3aed', bg: 'rgba(124,58,237,0.06)' },
                  ].map((m) => (
                    <div key={m.label} style={{ padding: '16px', background: m.bg, borderRadius: 'var(--radius-md)', border: `1px solid ${m.color}22`, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>{m.label}</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: m.color, fontFamily: 'var(--font-mono)' }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                {/* Auditor Warning */}
                {auditorResult.auditor_warning && (
                  <div
                    style={{
                      padding: '16px 20px',
                      background: 'rgba(220, 38, 38, 0.06)',
                      border: '1px solid rgba(220, 38, 38, 0.25)',
                      borderRadius: 'var(--radius-md)',
                      marginBottom: '20px',
                      fontSize: '0.88rem',
                      fontWeight: 600,
                      color: '#991b1b',
                      lineHeight: 1.5,
                    }}
                  >
                    {auditorResult.auditor_warning}
                  </div>
                )}

                {/* Per-Reference Results */}
                <Panel title="Verification Results" badge={`${auditorResult.total_checked} Checked`}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {auditorResult.results.map((r, i) => {
                      const vc = VERDICT_COLORS[r.verdict] || VERDICT_COLORS.SUSPICIOUS;
                      return (
                        <div
                          key={i}
                          style={{
                            padding: '16px 20px',
                            background: vc.bg,
                            border: `1px solid ${vc.border}22`,
                            borderLeft: `4px solid ${vc.border}`,
                            borderRadius: 'var(--radius-md)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px', flexWrap: 'wrap' }}>
                            <span style={{ fontSize: '1.2rem' }}>{vc.icon}</span>
                            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1rem', color: vc.text }}>
                              {r.normalized_reference}
                            </span>
                            <span
                              style={{
                                fontSize: '0.68rem',
                                padding: '2px 8px',
                                borderRadius: '999px',
                                background: `${vc.border}20`,
                                color: vc.text,
                                fontWeight: 700,
                              }}
                            >
                              {r.verdict.replace(/_/g, ' ')}
                            </span>
                            {r.blocked && (
                              <span
                                style={{
                                  fontSize: '0.68rem',
                                  padding: '2px 8px',
                                  borderRadius: '999px',
                                  background: 'rgba(220,38,38,0.15)',
                                  color: '#dc2626',
                                  fontWeight: 700,
                                }}
                              >
                                🚫 BLOCKED
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            {r.reason}
                          </div>
                          {r.matched_title && (
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px', fontStyle: 'italic' }}>
                              Matched: {r.matched_title}
                            </div>
                          )}
                          {r.closest_matches.length > 0 && (
                            <div style={{ marginTop: '8px', padding: '8px 12px', background: '#f8fafc', borderRadius: 'var(--radius-sm)', fontSize: '0.78rem' }}>
                              <div style={{ fontWeight: 700, color: 'var(--text-muted)', marginBottom: '4px' }}>Closest Matches:</div>
                              {r.closest_matches.map((cm, j) => (
                                <div key={j} style={{ display: 'flex', gap: '8px', alignItems: 'center', color: 'var(--text-secondary)' }}>
                                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{cm.standard_id}</span>
                                  <span style={{ opacity: 0.7 }}>— {cm.title}</span>
                                  <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
                                    {Math.round(cm.similarity * 100)}%
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </Panel>
              </motion.div>
            )}
          </motion.div>
        )}

        {/* ─── VISION TABLE READER TAB ────────────────────── */}
        {activeSection === 'vision' && (
          <motion.div key="vision" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
            <Panel
              title="Vision AI Table & Chart Reader"
              subtitle="Upload images of engineering tables, charts, or formulas from Indian Standard books. The AI reads tables like pictures — extracting columns, numbers, and units perfectly."
              badge="Tech Winner"
            >
              {/* Image Upload */}
              <div
                onClick={() => visionInputRef.current?.click()}
                style={{
                  border: '2px dashed rgba(79, 70, 229, 0.4)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '28px 20px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: '#f8fafc',
                  transition: 'all 0.2s ease',
                  marginBottom: '16px',
                }}
              >
                <input
                  ref={visionInputRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  onChange={(e) => { if (e.target.files?.[0]) setVisionFile(e.target.files[0]); }}
                />
                <div style={{ fontSize: '2.2rem', marginBottom: '6px' }}>📊</div>
                <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {visionFile ? visionFile.name : 'Drop table/chart image here'}
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Supports PNG, JPG, WEBP — engineering tables, specification charts, formula sheets
                </p>
                {visionFile && (
                  <span className="badge badge-indigo" style={{ marginTop: '8px' }}>
                    {(visionFile.size / 1024).toFixed(1)} KB — Ready
                  </span>
                )}
              </div>

              <button
                onClick={handleVisionExtract}
                disabled={isExtracting || !visionFile}
                className="btn-primary"
                style={{ marginBottom: '20px', minWidth: '200px' }}
              >
                {isExtracting ? '👁️ Extracting...' : '👁️ Extract Tables'}
              </button>

              {/* Text Fallback */}
              <details style={{ marginTop: '8px' }}>
                <summary style={{ fontSize: '0.84rem', color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: 600 }}>
                  📝 Or paste pre-OCR'd table text...
                </summary>
                <textarea
                  value={visionText}
                  onChange={(e) => setVisionText(e.target.value)}
                  placeholder="Paste table text here (pipe-delimited, tab-delimited, or whitespace-aligned)..."
                  rows={6}
                  style={{
                    width: '100%',
                    padding: '14px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.85rem',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    marginTop: '10px',
                    resize: 'vertical',
                    outline: 'none',
                  }}
                />
                <button
                  onClick={handleTextExtract}
                  disabled={isExtracting || !visionText.trim()}
                  className="btn-secondary"
                  style={{ marginTop: '10px', fontSize: '0.84rem' }}
                >
                  Extract from Text
                </button>
              </details>
            </Panel>

            {isExtracting && (
              <Panel title="Processing image with Vision AI...">
                <LoadingSkeleton height="100px" />
              </Panel>
            )}

            {visionResult && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                {/* Summary */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: '12px',
                    marginBottom: '20px',
                  }}
                >
                  {[
                    { label: 'Tables Found', value: visionResult.total_tables, color: '#4f46e5' },
                    { label: 'Formulas Found', value: visionResult.total_formulas, color: '#7c3aed' },
                    { label: 'IS References', value: visionResult.standard_references.length, color: '#059669' },
                    { label: 'Confidence', value: `${Math.round(visionResult.confidence * 100)}%`, color: '#0284c7' },
                  ].map((m) => (
                    <div key={m.label} style={{ padding: '16px', background: `${m.color}0a`, borderRadius: 'var(--radius-md)', border: `1px solid ${m.color}22`, textAlign: 'center' }}>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '4px' }}>{m.label}</div>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: m.color, fontFamily: 'var(--font-mono)' }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                {/* Extracted Tables */}
                {visionResult.tables.map((table, ti) => (
                  <Panel key={ti} title={table.title || `Table ${ti + 1}`} badge={`${table.row_count}×${table.col_count}`}>
                    <div style={{ overflowX: 'auto' }}>
                      <table
                        style={{
                          width: '100%',
                          borderCollapse: 'collapse',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.84rem',
                        }}
                      >
                        <thead>
                          <tr>
                            {table.headers.map((h, hi) => (
                              <th
                                key={hi}
                                style={{
                                  padding: '10px 14px',
                                  background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                                  color: '#ffffff',
                                  fontWeight: 700,
                                  textAlign: 'left',
                                  fontSize: '0.8rem',
                                  borderBottom: '2px solid #312e81',
                                }}
                              >
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {table.rows.map((row, ri) => (
                            <tr key={ri} style={{ background: ri % 2 === 0 ? '#fafbfc' : '#ffffff' }}>
                              {row.map((cell, ci) => (
                                <td
                                  key={ci}
                                  style={{
                                    padding: '8px 14px',
                                    borderBottom: '1px solid #e2e8f0',
                                    color: 'var(--text-primary)',
                                  }}
                                >
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {table.csv_text && (
                      <div style={{ marginTop: '12px', display: 'flex', gap: '10px' }}>
                        <button
                          className="btn-secondary"
                          style={{ fontSize: '0.8rem' }}
                          onClick={() => {
                            navigator.clipboard.writeText(table.csv_text || '');
                            onToast('CSV copied to clipboard!', 'info');
                          }}
                        >
                          📋 Copy CSV
                        </button>
                      </div>
                    )}
                  </Panel>
                ))}

                {/* Extracted Formulas */}
                {visionResult.formulas.length > 0 && (
                  <Panel title="Detected Formulas" badge={`${visionResult.formulas.length}`}>
                    {visionResult.formulas.map((f) => (
                      <div
                        key={f.formula_index}
                        style={{
                          padding: '12px 16px',
                          marginBottom: '8px',
                          background: 'rgba(124, 58, 237, 0.06)',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid rgba(124, 58, 237, 0.15)',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.88rem',
                        }}
                      >
                        <div style={{ fontWeight: 700, color: '#7c3aed' }}>{f.raw_text}</div>
                        {f.variables.length > 0 && (
                          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                            Variables: {f.variables.join(', ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </Panel>
                )}

                {/* Raw OCR Text */}
                {visionResult.raw_text && (
                  <details style={{ marginBottom: '20px' }}>
                    <summary style={{ fontSize: '0.84rem', color: 'var(--accent-primary)', cursor: 'pointer', fontWeight: 600 }}>
                      View Raw OCR Text
                    </summary>
                    <pre
                      style={{
                        marginTop: '8px',
                        padding: '16px',
                        background: '#f8fafc',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.82rem',
                        fontFamily: 'var(--font-mono)',
                        whiteSpace: 'pre-wrap',
                        maxHeight: '300px',
                        overflowY: 'auto',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      {visionResult.raw_text}
                    </pre>
                  </details>
                )}
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
