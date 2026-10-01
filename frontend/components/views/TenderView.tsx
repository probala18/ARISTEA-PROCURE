'use client';

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  uploadTenderDocument,
  getTenderAudit,
  generateSpecification,
  analyzeRedline,
  applyAllRedlineFixes,
  verifyStandards,
  extractTableFromImage,
  extractTableFromText,
  TenderUploadResponse,
  TenderAuditReport,
  GeneratedSpecificationResponse,
  RedlineAnalysisResponse,
  RedlineSegment as RedlineSegmentType,
  RedlineAutoFix,
  AuditorVerificationResponse,
  VisionTableResponse,
} from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { GapCard } from '@/components/ui/GapCard';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { springDropzone } from '@/lib/gsap-animations';
import { StandardsMigrationCard } from './redline/StandardsMigrationCard';
import { TenderOverviewSection } from './redline/TenderOverviewSection';
import { ComparisonMatrixSection } from './redline/ComparisonMatrixSection';
import { EcoTrackSection } from './redline/EcoTrackSection';
import { BidderRequirementsSection } from './redline/BidderRequirementsSection';
import { CostEstimationSection } from './redline/CostEstimationSection';
import { PrimarySourceTrackerSection } from './redline/PrimarySourceTrackerSection';

interface TenderViewProps {
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const SAMPLE_TENDER_TEXT = `CENTRAL PUBLIC WORKS DEPARTMENT (CPWD)
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

const ANNOTATION_COLORS: Record<string, { bg: string; border: string; text: string; icon: string; label: string }> = {
  COMPLIANT:    { bg: 'rgba(5, 150, 105, 0.12)',  border: '#059669', text: '#065f46', icon: '✅', label: 'This part is perfect and matches the correct Indian Standard.' },
  OUTDATED:     { bg: 'rgba(220, 38, 38, 0.12)',   border: '#dc2626', text: '#991b1b', icon: '🔴', label: 'Warning! This requirement is using an old, expired rule from 2010. The law changed in 2024. Click here to auto-fix it.' },
  UNRECOGNIZED: { bg: 'rgba(245, 158, 11, 0.12)',  border: '#f59e0b', text: '#92400e', icon: '🟠', label: 'Not in Authoritative BIS Catalog' },
  AMENDED:      { bg: 'rgba(234, 179, 8, 0.12)',   border: '#eab308', text: '#854d0e', icon: '🟡', label: 'Revised with Gazette Amendments' },
  PLAIN:        { bg: 'transparent',                border: 'transparent', text: 'inherit', icon: '',   label: '' },
};

export const TenderView: React.FC<TenderViewProps> = ({ onToast }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentContent, setDocumentContent] = useState<string>('');
  const [tenderNumber, setTenderNumber] = useState('');
  const [orgName, setOrgName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isFixing, setIsFixing] = useState(false);
  const [isGeneratingSpec, setIsGeneratingSpec] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);

  const [uploadResult, setUploadResult] = useState<TenderUploadResponse | null>(null);
  const [auditReport, setAuditReport] = useState<TenderAuditReport | null>(null);
  const [redlineResult, setRedlineResult] = useState<RedlineAnalysisResponse | null>(null);
  const [generatedSpec, setGeneratedSpec] = useState<GeneratedSpecificationResponse | null>(null);

  // Active feature mode inside Document Auditor
  const [activeFeature, setActiveFeature] = useState<
    'overview' | 'comparison' | 'eco' | 'bidder' | 'gaps' | 'auditor' | 'vision' | 'cost' | 'redline'
  >('overview');

  // Redline hover state
  const [hoveredSegment, setHoveredSegment] = useState<number | null>(null);

  // Document Reader expansion & quick-filter controls
  const [isDocExpanded, setIsDocExpanded] = useState(false);
  const [filterOutdatedOnly, setFilterOutdatedOnly] = useState(false);
  const docContainerRef = useRef<HTMLDivElement>(null);

  const jumpToSegment = (idx: number) => {
    const el = document.getElementById(`redline-segment-${idx}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setHoveredSegment(idx);
      setTimeout(() => setHoveredSegment(null), 3000);
    }
  };

  // Adversarial Auditor state
  const [auditorRefs, setAuditorRefs] = useState('IS 12615:2018\nIS 325:1996\nIS 9999\nIS 694:2010\nIS 12345');
  const [isVerifying, setIsVerifying] = useState(false);
  const [auditorResult, setAuditorResult] = useState<AuditorVerificationResponse | null>(null);

  // Vision AI state
  const [visionFile, setVisionFile] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [visionResult, setVisionResult] = useState<VisionTableResponse | null>(null);
  const [visionText, setVisionText] = useState('');
  const visionInputRef = useRef<HTMLInputElement>(null);

  const isBinaryDoc = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    return ext === 'pdf' || ext === 'docx' || ext === 'doc';
  };

  const handleFileSelection = async (file: File) => {
    setSelectedFile(file);
    setUploadResult(null);
    setAuditReport(null);
    setRedlineResult(null);
    setGeneratedSpec(null);

    // Auto-update tender reference number and organization from filename
    const cleanBase = file.name.replace(/\.[^/.]+$/, '').replace(/[^a-zA-Z0-9_-]/g, ' ').trim();
    const slug = cleanBase.replace(/\s+/g, '-').slice(0, 20).toUpperCase();
    setTenderNumber(`TND-${slug || 'DOC-2026'}`);
    setOrgName('');

    if (!isBinaryDoc(file.name)) {
      try {
        const text = await file.text();
        setDocumentContent(text);
      } catch {
        setDocumentContent('');
      }
    } else {
      // PDF or DOCX: Clean notification in workspace
      setDocumentContent(
        `📄 [${file.name} (${(file.size / 1024).toFixed(1)} KB) selected.\nClick 'Upload & Audit Tender' below to parse and extract clauses with PyMuPDF Engine.]`
      );
    }
    onToast(`Selected file: ${file.name}`, 'info');
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (dropzoneRef.current) springDropzone(dropzoneRef.current);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleUseSampleTender = async () => {
    const blob = new Blob([SAMPLE_TENDER_TEXT], { type: 'text/plain' });
    const file = new File([blob], 'CPWD_Pumping_Machinery_Tender.txt', { type: 'text/plain' });
    setSelectedFile(file);
    setDocumentContent(SAMPLE_TENDER_TEXT);
    setTenderNumber('CPWD/EE/2026/PUMP-042');
    setOrgName('Central Public Works Department (CPWD)');
    onToast('Loaded sample tender document for Pumping Machinery.', 'info');

    // Automatically run redline analysis so all features populate immediately
    try {
      const redline = await analyzeRedline(SAMPLE_TENDER_TEXT);
      setRedlineResult(redline);
      setActiveFeature('redline');
    } catch {}
  };

  const handleUploadAndAudit = async () => {
    if (!selectedFile && !documentContent) {
      onToast('Please select a tender document or load the sample tender.', 'error');
      return;
    }

    setIsUploading(true);
    setUploadResult(null);
    setAuditReport(null);
    setGeneratedSpec(null);
    setRedlineResult(null);

    try {
      let fileToUpload = selectedFile;
      if (!fileToUpload) {
        const blob = new Blob([documentContent], { type: 'text/plain' });
        fileToUpload = new File([blob], 'tender_document.txt', { type: 'text/plain' });
        setSelectedFile(fileToUpload);
      }

      // 1. Upload & Parse via Backend Engine (PyMuPDF for PDF, python-docx for Word)
      const uploadRes = await uploadTenderDocument(
        fileToUpload,
        tenderNumber || undefined,
        fileToUpload.name.replace(/\.[^/.]+$/, '') || 'Procurement Tender',
        orgName || undefined
      );
      setUploadResult(uploadRes);

      // Clean extracted text from document
      let cleanText = '';
      if (uploadRes.extracted_text && uploadRes.extracted_text.trim()) {
        cleanText = uploadRes.extracted_text;
        setDocumentContent(uploadRes.extracted_text);
      } else if (!isBinaryDoc(fileToUpload.name) && documentContent.trim() && !documentContent.startsWith('📄 [')) {
        cleanText = documentContent;
      }

      if (!cleanText.trim()) {
        cleanText = (!isBinaryDoc(fileToUpload.name) ? documentContent : '') || '';
      }

      if (!cleanText.trim()) {
        onToast('Document uploaded, but no text could be extracted. Please check file formatting.', 'error');
        return;
      }

      // 2. Concurrently Audit & Run Redline Intelligence on clean text
      setIsAuditing(true);
      const [auditRes, redlineRes] = await Promise.allSettled([
        getTenderAudit(uploadRes.tender_id, true),
        analyzeRedline(cleanText),
      ]);

      if (auditRes.status === 'fulfilled') setAuditReport(auditRes.value);
      if (redlineRes.status === 'fulfilled') {
        const redline = redlineRes.value;
        setRedlineResult(redline);
        setActiveFeature('redline');

        // Dynamically populate Adversarial AI double-check with detected standards from uploaded document
        const detectedCodes = redline.segments
          .filter((s) => s.standard_id)
          .map((s) => s.standard_id!);
        const uniqueCodes = Array.from(new Set(detectedCodes));
        if (uniqueCodes.length > 0) {
          setAuditorRefs([...uniqueCodes, 'IS 9999'].join('\n'));
        }
      }

      onToast('Tender successfully audited with Visual Redline & Grounded Compliance!', 'success');
    } catch (err: any) {
      onToast(err.message || 'Tender processing failed.', 'error');
    } finally {
      setIsUploading(false);
      setIsAuditing(false);
    }
  };

  const handleAutoFixAll = async () => {
    const currentText = documentContent && !documentContent.startsWith('📄 [')
      ? documentContent
      : (redlineResult ? redlineResult.segments.map((s) => s.text).join('') : '');

    if (!currentText) return;
    setIsFixing(true);
    try {
      const result = await applyAllRedlineFixes(currentText);
      if (result.corrected_text) {
        setDocumentContent(result.corrected_text);
        const reanalyzed = await analyzeRedline(result.corrected_text);
        setRedlineResult(reanalyzed);
        onToast(`Auto-fixed ${result.fixes_applied} outdated standards! Document updated on screen.`, 'success');
      }
    } catch (err: any) {
      onToast(err.message || 'Auto-fix failed.', 'error');
    } finally {
      setIsFixing(false);
    }
  };

  const handleSingleFix = (fix: RedlineAutoFix) => {
    const updated = (documentContent || '').replace(fix.old_text, fix.new_text);
    setDocumentContent(updated);
    if (redlineResult) {
      const remainingFixes = redlineResult.auto_fixes.filter((f) => f.fix_id !== fix.fix_id);
      const updatedSegments = redlineResult.segments.map((s) => {
        if (s.auto_fix && s.auto_fix.fix_id === fix.fix_id) {
          return {
            ...s,
            text: fix.new_text,
            standard_id: fix.new_standard_id,
            standard_title: fix.new_standard_title || s.successor_title,
            status: 'CURRENT',
            annotation_type: 'COMPLIANT' as const,
            auto_fix: undefined,
            tooltip: `✅ Fixed: Upgraded from ${fix.old_standard_id} to ${fix.new_standard_id}. Fully compliant.`,
          };
        }
        return s;
      });

      const remainingMappings = (redlineResult.standards_redline_mappings || []).filter(
        (m) => m.old_standard !== fix.old_standard_id && m.old_standard !== fix.old_text
      );

      setRedlineResult({
        ...redlineResult,
        segments: updatedSegments,
        auto_fixes: remainingFixes,
        standards_redline_mappings: remainingMappings,
        summary: {
          ...redlineResult.summary,
          outdated_count: Math.max(0, redlineResult.summary.outdated_count - 1),
          compliant_count: redlineResult.summary.compliant_count + 1,
          auto_fixes_available: remainingFixes.length,
        },
      });
    }
    onToast(`Replaced "${fix.old_standard_id}" with current "${fix.new_standard_id}".`, 'success');
  };

  const handleVerifyHallucinations = async () => {
    const refs = auditorRefs.split('\n').map(s => s.trim()).filter(Boolean);
    if (refs.length === 0) {
      onToast('Enter at least one standard reference to verify.', 'error');
      return;
    }
    setIsVerifying(true);
    setAuditorResult(null);
    try {
      const result = await verifyStandards(refs, true);
      setAuditorResult(result);
      if (result.hallucination_count > 0) {
        onToast(`Auditor AI caught ${result.hallucination_count} hallucinated standard(s)!`, 'error');
      } else {
        onToast('All verified! No fabricated standards detected.', 'success');
      }
    } catch (err: any) {
      onToast(err.message || 'Verification failed.', 'error');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleVisionImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];
    setVisionFile(file);
    setIsExtracting(true);
    setVisionResult(null);
    try {
      const result = await extractTableFromImage(file);
      setVisionResult(result);
      onToast(`Vision AI extracted ${result.total_tables} table(s) and ${result.total_formulas} formula(s)!`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Table extraction failed.', 'error');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleGenerateSpec = async () => {
    if (!uploadResult?.tender_id) return;
    setIsGeneratingSpec(true);
    try {
      const spec = await generateSpecification({
        tender_id: uploadResult.tender_id,
        generation_type: 'technical_specification',
        title: `Corrected Technical Specification for ${uploadResult.tender_number || 'Tender'}`,
      });
      setGeneratedSpec(spec);
      onToast('Grounded specification generated successfully!', 'success');
    } catch (err: any) {
      onToast(err.message || 'Specification generation failed.', 'error');
    } finally {
      setIsGeneratingSpec(false);
    }
  };

  const handleCopySpec = () => {
    if (!generatedSpec?.specification_text) return;
    navigator.clipboard.writeText(generatedSpec.specification_text);
    onToast('Specification text copied to clipboard!', 'info');
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Upload & Grounding Control Panel */}
      <Panel
        title="Tender Document Engine & Grounded Audit"
        subtitle="Upload your RFP / tender document (PDF, TXT, DOCX). The AI performs multi-clause extraction, visual redline markup, gap analysis, and GFR verification."
        badge="Audit Engine"
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '6px', color: 'var(--text-secondary)' }}>
              Procuring Organization / Ministry
            </label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="e.g. Central Public Works Department (CPWD)"
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.86rem',
                background: '#fafbfc',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, marginBottom: '6px', color: 'var(--text-secondary)' }}>
              Tender / NIT Reference Number
            </label>
            <input
              type="text"
              value={tenderNumber}
              onChange={(e) => setTenderNumber(e.target.value)}
              placeholder="e.g. CPWD/EE/2026/PUMP-042"
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.86rem',
                background: '#fafbfc',
              }}
            />
          </div>
        </div>

        {/* Dropzone */}
        <div
          ref={dropzoneRef}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '24px',
            textAlign: 'center',
            cursor: 'pointer',
            background: selectedFile ? 'rgba(5, 150, 105, 0.04)' : '#fafbfc',
            transition: 'border-color 0.2s ease, background 0.2s ease',
            marginBottom: '16px',
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.docx"
            style={{ display: 'none' }}
            onChange={async (e) => {
              if (e.target.files && e.target.files[0]) {
                await handleFileSelection(e.target.files[0]);
              }
            }}
          />
          <div style={{ fontSize: '2rem', marginBottom: '8px' }}>📄</div>
          {selectedFile ? (
            <div>
              <span style={{ fontWeight: 700, color: 'var(--accent-primary)', fontSize: '0.94rem' }}>
                Selected: {selectedFile.name}
              </span>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                {(selectedFile.size / 1024).toFixed(1)} KB · Click or drag to replace
              </span>
            </div>
          ) : (
            <div>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                Drop RFP document here, or click to browse
              </span>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginTop: '2px' }}>
                Supports PDF, DOCX, and TXT files up to 20 MB
              </span>
            </div>
          )}
        </div>

        {/* Direct Text Preview / Editor */}
        <div style={{ marginBottom: '16px' }}>
          <details open={Boolean(documentContent && !documentContent.startsWith('📄 ['))} style={{ fontSize: '0.84rem', color: '#64748b' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 600, userSelect: 'none', marginBottom: '8px' }}>
              ✍️ View, edit, or paste tender document text directly
            </summary>
            <textarea
              value={documentContent}
              onChange={(e) => setDocumentContent(e.target.value)}
              placeholder="Paste tender document clauses here or review extracted text from uploaded PDF/Word file..."
              rows={6}
              style={{
                width: '100%',
                padding: '12px 14px',
                fontFamily: 'var(--font-mono, monospace)',
                fontSize: '0.84rem',
                lineHeight: 1.6,
                borderRadius: '8px',
                border: '1px solid #cbd5e1',
                background: '#fafbfc',
              }}
            />
          </details>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            type="button"
            onClick={handleUseSampleTender}
            className="btn-secondary"
            style={{ fontSize: '0.84rem' }}
          >
            📋 Load Sample CPWD Pumping Machinery Tender
          </button>

          {(selectedFile || documentContent) && (
            <button
              type="button"
              onClick={() => {
                setSelectedFile(null);
                setDocumentContent('');
                setTenderNumber('');
                setOrgName('');
                setUploadResult(null);
                setAuditReport(null);
                setRedlineResult(null);
                setGeneratedSpec(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
                onToast('Cleared workspace. Ready to upload your tender document.', 'info');
              }}
              className="btn-secondary"
              style={{ fontSize: '0.84rem', color: '#dc2626' }}
            >
              🗑️ Clear & Upload New Document
            </button>
          )}

          <button
            onClick={handleUploadAndAudit}
            disabled={(!selectedFile && !documentContent) || isUploading || isAuditing}
            className="btn-primary"
            style={{ minWidth: '220px' }}
          >
            {isUploading ? 'Parsing Document...' : isAuditing ? 'Auditing Standards...' : 'Upload & Audit Tender 🚀'}
          </button>
        </div>
      </Panel>

      {/* Loading Skeletons */}
      {(isUploading || isAuditing) && (
        <Panel title="Auditing Tender Clauses against Authoritative BIS Standards...">
          <LoadingSkeleton height="75px" />
          <LoadingSkeleton height="130px" />
        </Panel>
      )}

      {/* ═══════════════════════════════════════════════════════
          AUDITED DOCUMENT INTELLIGENCE WORKSPACE
          ═══════════════════════════════════════════════════════ */}
      {(uploadResult || redlineResult || auditReport) && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Executive Coverage & Summary Strip */}
          <div
            style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-lg, 12px)',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: '4px', background: '#e0e7ff', color: '#4338ca' }}>
                  {uploadResult?.tender_number || tenderNumber}
                </span>
                <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
                  {orgName}
                </span>
              </div>
              <h3 style={{ margin: '4px 0 0 0', fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>
                Tender Compliance & Standards Intelligence Report
              </h3>
            </div>

            <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
              {redlineResult && (
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>COMPLIANCE SCORE</span>
                  <div style={{ fontSize: '1.3rem', fontWeight: 900, color: redlineResult.summary.compliance_score >= 0.8 ? '#059669' : '#dc2626' }}>
                    {Math.round(redlineResult.summary.compliance_score * 100)}%
                  </div>
                </div>
              )}

              {redlineResult && redlineResult.summary.auto_fixes_available > 0 && (
                <button
                  onClick={handleAutoFixAll}
                  disabled={isFixing}
                  className="btn-accent"
                  style={{ padding: '8px 16px', fontSize: '0.84rem' }}
                >
                  {isFixing ? 'Fixing...' : `⚡ Auto-Fix All (${redlineResult.summary.auto_fixes_available})`}
                </button>
              )}
            </div>
          </div>

          {/* Direct-View Feature Navigation Bar */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '8px',
              background: '#ffffff',
              padding: '10px',
              borderRadius: 'var(--radius-lg, 12px)',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 10px rgba(0, 0, 0, 0.03)',
            }}
          >
            {[
              { key: 'redline' as const, icon: '📝', label: 'Redline Document Markup', badge: 'Redline' },
              { key: 'overview' as const, icon: '📐', label: 'Overview & Measurements', badge: 'Specs' },
              { key: 'comparison' as const, icon: '📊', label: 'Comparison Matrix', badge: 'Audit' },
              { key: 'eco' as const, icon: '🌿', label: 'Eco Track', badge: 'Green' },
              { key: 'bidder' as const, icon: '👥', label: 'Bidder Criteria', badge: 'Criteria' },
              { key: 'gaps' as const, icon: '📋', label: 'Clause Findings & Gaps', badge: 'GFR' },
              { key: 'auditor' as const, icon: '🛡️', label: 'Adversarial AI Shield', badge: 'Double-Check' },
              { key: 'vision' as const, icon: '👁️', label: 'Vision AI Tables', badge: 'OCR' },
              { key: 'cost' as const, icon: '💰', label: 'AI Cost Estimate', badge: 'Budget' },
            ].map((tab) => {
              const isActive = activeFeature === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveFeature(tab.key)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    border: isActive ? '1px solid #4338ca' : '1px solid #e2e8f0',
                    background: isActive
                      ? 'linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)'
                      : '#f8fafc',
                    color: isActive ? '#ffffff' : '#1e293b',
                    fontWeight: isActive ? 700 : 600,
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    boxShadow: isActive ? '0 4px 12px rgba(79, 70, 229, 0.25)' : 'none',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '1.1rem' }}>{tab.icon}</span>
                    <span style={{ fontWeight: isActive ? 800 : 600 }}>{tab.label}</span>
                  </div>
                  <span
                    style={{
                      fontSize: '0.66rem',
                      padding: '2px 7px',
                      borderRadius: '999px',
                      background: isActive ? 'rgba(255, 255, 255, 0.22)' : 'rgba(79, 70, 229, 0.08)',
                      color: isActive ? '#ffffff' : '#4338ca',
                      fontWeight: 800,
                      letterSpacing: '0.02em',
                      flexShrink: 0,
                    }}
                  >
                    {tab.badge}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Feature Contents */}
          <AnimatePresence mode="wait">
            {/* 1. INTERACTIVE DOCUMENT COMPLIANCE INSPECTOR */}
            {activeFeature === 'redline' && (
              <motion.div key="redline" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <Panel
                  title="Redline Document Compliance Inspector"
                  subtitle="Full draft tender document rendered with inline statutory redlining: Green confirms alignment with active Indian Standards; Red flags outdated or superseded specifications with 1-click legal auto-fixes."
                  badge="Redline Markup"
                  action={
                    redlineResult ? (
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <button
                          type="button"
                          onClick={() => setFilterOutdatedOnly(!filterOutdatedOnly)}
                          className="btn-outline"
                          style={{
                            fontSize: '0.8rem',
                            padding: '6px 12px',
                            background: filterOutdatedOnly ? 'var(--primary-subtle, #e0e7ff)' : '#ffffff',
                            borderColor: filterOutdatedOnly ? 'var(--primary)' : 'var(--border-subtle)',
                            fontWeight: filterOutdatedOnly ? 700 : 500,
                          }}
                        >
                          {filterOutdatedOnly ? '📄 Show Full Text' : '🎯 View Outdated Clauses Only'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setIsDocExpanded(!isDocExpanded)}
                          className="btn-outline"
                          style={{ fontSize: '0.8rem', padding: '6px 12px', background: '#ffffff' }}
                        >
                          {isDocExpanded ? '🔼 Collapse View' : '📖 Expand Full Document'}
                        </button>
                        {redlineResult.summary.auto_fixes_available > 0 && (
                          <button onClick={handleAutoFixAll} disabled={isFixing} className="btn-accent" style={{ fontSize: '0.82rem' }}>
                            ⚡ Auto-Fix All Outdated ({redlineResult.summary.auto_fixes_available})
                          </button>
                        )}
                      </div>
                    ) : undefined
                  }
                >
                  {redlineResult ? (
                    <div>
                      {/* Quick-Jump Citation Navigator */}
                      <div
                        style={{
                          marginBottom: '16px',
                          padding: '12px 16px',
                          background: '#f8fafc',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '10px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                          <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span>🎯 Quick Citation Navigator:</span>
                            <span style={{ background: '#e2e8f0', color: '#334155', padding: '2px 8px', borderRadius: '12px', fontSize: '0.74rem', fontWeight: 700 }}>
                              {redlineResult.segments.filter(s => s.annotation_type !== 'PLAIN').length} citations detected
                            </span>
                            {redlineResult.summary.outdated_count > 0 && (
                              <span style={{ background: '#fee2e2', color: '#991b1b', padding: '2px 8px', borderRadius: '12px', fontSize: '0.74rem', fontWeight: 700 }}>
                                {redlineResult.summary.outdated_count} outdated
                              </span>
                            )}
                            <span style={{ background: '#dcfce7', color: '#166534', padding: '2px 8px', borderRadius: '12px', fontSize: '0.74rem', fontWeight: 700 }}>
                              {redlineResult.summary.compliant_count} compliant
                            </span>
                          </div>
                          <div style={{ fontSize: '0.76rem', color: '#64748b' }}>
                            Click any citation badge below to jump directly to its clause in the document.
                          </div>
                        </div>

                        {/* Citation Chips */}
                        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '4px', maxWidth: '100%', scrollbarWidth: 'thin' }}>
                          {redlineResult.segments.map((seg, idx) => {
                            if (seg.annotation_type === 'PLAIN') return null;
                            const isOutdated = seg.annotation_type === 'OUTDATED';
                            const isCompliant = seg.annotation_type === 'COMPLIANT';

                            return (
                              <button
                                key={idx}
                                type="button"
                                onClick={() => {
                                  if (filterOutdatedOnly && !isOutdated) {
                                    setFilterOutdatedOnly(false);
                                  }
                                  jumpToSegment(idx);
                                }}
                                title={`Click to jump to ${seg.text}`}
                                style={{
                                  flexShrink: 0,
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '5px',
                                  padding: '4px 10px',
                                  borderRadius: '16px',
                                  fontSize: '0.76rem',
                                  fontWeight: 700,
                                  fontFamily: 'var(--font-mono)',
                                  border: `1px solid ${isOutdated ? '#f87171' : isCompliant ? '#86efac' : '#cbd5e1'}`,
                                  background: isOutdated ? '#fee2e2' : isCompliant ? '#dcfce7' : '#f1f5f9',
                                  color: isOutdated ? '#991b1b' : isCompliant ? '#166534' : '#334155',
                                  cursor: 'pointer',
                                  transition: 'all 0.15s ease',
                                }}
                              >
                                <span>{isOutdated ? '🔴' : isCompliant ? '🟢' : '🟡'}</span>
                                <span>{seg.text}</span>
                                {isOutdated && seg.successor_id && (
                                  <span style={{ fontSize: '0.7rem', color: '#047857' }}>➔ {seg.successor_id}</span>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      {/* Outdated-Only Filtered View */}
                      {filterOutdatedOnly ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '16px' }}>
                          {redlineResult.segments.filter(s => s.annotation_type === 'OUTDATED').length === 0 ? (
                            <div style={{ textAlign: 'center', padding: '36px 20px', background: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🎉</div>
                              <h4 style={{ color: '#166534', fontWeight: 700, margin: '0 0 6px' }}>No Outdated Standards Detected</h4>
                              <p style={{ color: '#15803d', fontSize: '0.88rem', margin: '0 0 16px' }}>
                                All standard citations in this document are aligned with active Gazette editions.
                              </p>
                              <button onClick={() => setFilterOutdatedOnly(false)} className="btn-primary" style={{ fontSize: '0.82rem' }}>
                                View Full Document
                              </button>
                            </div>
                          ) : (
                            redlineResult.segments.map((seg, idx) => {
                              if (seg.annotation_type !== 'OUTDATED') return null;
                              const prevText = idx > 0 ? redlineResult.segments[idx - 1].text.slice(-160) : '';
                              const nextText = idx < redlineResult.segments.length - 1 ? redlineResult.segments[idx + 1].text.slice(0, 160) : '';

                              return (
                                <div
                                  key={idx}
                                  id={`redline-segment-${idx}`}
                                  style={{
                                    padding: '16px 20px',
                                    borderRadius: '8px',
                                    border: '1px solid #fecaca',
                                    background: '#fffbfb',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '12px',
                                    boxShadow: hoveredSegment === idx ? '0 0 0 3px rgba(239, 68, 68, 0.35)' : '0 1px 3px rgba(0,0,0,0.05)',
                                    transition: 'all 0.2s ease',
                                  }}
                                >
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                      <span style={{ background: '#ef4444', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontSize: '0.74rem', fontWeight: 800 }}>
                                        OUTDATED CITATION
                                      </span>
                                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.92rem', color: '#991b1b' }}>
                                        {seg.text}
                                      </span>
                                      {seg.successor_id && (
                                        <span style={{ fontSize: '0.84rem', color: '#059669', fontWeight: 700 }}>
                                          ➔ Active Successor: {seg.successor_id}
                                        </span>
                                      )}
                                    </div>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                      <button
                                        type="button"
                                        onClick={() => {
                                          setFilterOutdatedOnly(false);
                                          setTimeout(() => jumpToSegment(idx), 80);
                                        }}
                                        className="btn-outline"
                                        style={{ fontSize: '0.78rem', padding: '5px 10px', background: '#fff' }}
                                      >
                                        📍 Locate in Full Text
                                      </button>
                                      {seg.auto_fix && (
                                        <button
                                          type="button"
                                          onClick={() => handleSingleFix(seg.auto_fix!)}
                                          className="btn-accent"
                                          style={{ fontSize: '0.78rem', padding: '5px 12px' }}
                                        >
                                          ⚡ Auto-Fix Clause
                                        </button>
                                      )}
                                    </div>
                                  </div>

                                  <div
                                    style={{
                                      fontSize: '0.88rem',
                                      color: '#334155',
                                      lineHeight: 1.65,
                                      background: '#ffffff',
                                      padding: '12px 16px',
                                      borderRadius: '6px',
                                      border: '1px solid #fed7aa',
                                      fontFamily: 'Georgia, serif',
                                    }}
                                  >
                                    <span style={{ opacity: 0.65 }}>...{prevText} </span>
                                    <span
                                      style={{
                                        background: '#fee2e2',
                                        borderBottom: '2px solid #ef4444',
                                        color: '#991b1b',
                                        fontWeight: 700,
                                        padding: '2px 6px',
                                        borderRadius: '3px',
                                      }}
                                    >
                                      {seg.text}
                                    </span>
                                    <span style={{ opacity: 0.65 }}> {nextText}...</span>
                                  </div>

                                  <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                                    <span><strong>Statutory Note:</strong> {seg.tooltip || 'Superseded by updated Indian Standard specification.'}</span>
                                    {seg.publication_year && <span><strong>Year Cited:</strong> {seg.publication_year}</span>}
                                  </div>
                                </div>
                              );
                            })
                          )}
                        </div>
                      ) : (
                        /* Full Document View with Constrained Scroll / Expand */
                        <div style={{ position: 'relative' }}>
                          <div
                            ref={docContainerRef}
                            style={{
                              padding: '24px',
                              background: '#ffffff',
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--border-subtle)',
                              lineHeight: 1.85,
                              fontSize: '0.94rem',
                              fontFamily: 'Georgia, serif',
                              color: '#1e293b',
                              whiteSpace: 'pre-wrap',
                              boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.03)',
                              maxHeight: isDocExpanded ? 'none' : '480px',
                              overflowY: isDocExpanded ? 'visible' : 'auto',
                              scrollBehavior: 'smooth',
                            }}
                          >
                            {redlineResult.segments.map((seg, idx) => {
                              const style = ANNOTATION_COLORS[seg.annotation_type] || ANNOTATION_COLORS.PLAIN;
                              const isOutdated = seg.annotation_type === 'OUTDATED';
                              const isCompliant = seg.annotation_type === 'COMPLIANT';

                              if (seg.annotation_type === 'PLAIN') {
                                return (
                                  <span key={idx} id={`redline-segment-${idx}`}>
                                    {seg.text}
                                  </span>
                                );
                              }

                              return (
                                <span
                                  key={idx}
                                  id={`redline-segment-${idx}`}
                                  onMouseEnter={() => setHoveredSegment(idx)}
                                  onMouseLeave={() => setHoveredSegment(null)}
                                  style={{
                                    position: 'relative',
                                    display: 'inline-block',
                                    padding: '2px 8px',
                                    margin: '0 2px',
                                    borderRadius: '4px',
                                    background: style.bg,
                                    borderBottom: `2px solid ${style.border}`,
                                    color: style.text,
                                    fontWeight: 700,
                                    fontFamily: 'var(--font-mono)',
                                    fontSize: '0.86rem',
                                    cursor: 'pointer',
                                    boxShadow: hoveredSegment === idx ? '0 0 0 3px rgba(239, 68, 68, 0.4)' : 'none',
                                    transform: hoveredSegment === idx ? 'scale(1.04)' : 'none',
                                    transition: 'all 0.15s ease',
                                  }}
                                >
                                  <span>{style.icon} {seg.text}</span>

                                  {/* Hover Tooltip */}
                                  {hoveredSegment === idx && (
                                    <div
                                      style={{
                                        position: 'absolute',
                                        bottom: '100%',
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        marginBottom: '8px',
                                        padding: '12px 16px',
                                        background: '#0f172a',
                                        color: '#ffffff',
                                        borderRadius: '8px',
                                        fontSize: '0.78rem',
                                        fontFamily: 'var(--font-sans)',
                                        lineHeight: 1.45,
                                        width: '320px',
                                        boxShadow: '0 10px 25px rgba(0,0,0,0.25)',
                                        zIndex: 100,
                                        pointerEvents: 'auto',
                                      }}
                                    >
                                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                                        <span style={{ fontWeight: 800, color: isCompliant ? '#34d399' : '#f87171' }}>
                                          {style.label}
                                        </span>
                                        {seg.publication_year && (
                                          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                                            Year: {seg.publication_year}
                                          </span>
                                        )}
                                      </div>

                                      <div style={{ color: '#e2e8f0', marginBottom: '6px' }}>
                                        {seg.standard_title || seg.tooltip || 'Authoritative Indian Standard Specification'}
                                      </div>

                                      {isOutdated && seg.auto_fix && (
                                        <div style={{ paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.15)' }}>
                                          <div style={{ color: '#fca5a5', fontWeight: 700, marginBottom: '4px' }}>
                                            Changed in Gazette! Successor: {seg.successor_id}
                                          </div>
                                          <button
                                            type="button"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleSingleFix(seg.auto_fix!);
                                            }}
                                            style={{
                                              width: '100%',
                                              padding: '5px 10px',
                                              borderRadius: '4px',
                                              background: '#059669',
                                              color: '#ffffff',
                                              border: 'none',
                                              fontWeight: 700,
                                              fontSize: '0.75rem',
                                              cursor: 'pointer',
                                            }}
                                          >
                                            ⚡ Click to Auto-Fix Clause
                                          </button>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </span>
                              );
                            })}
                          </div>

                          {/* Gradient Bottom Fade with Expand Button when Collapsed */}
                          {!isDocExpanded ? (
                            <div
                              style={{
                                position: 'sticky',
                                bottom: 0,
                                left: 0,
                                right: 0,
                                padding: '24px 16px 12px',
                                background: 'linear-gradient(to bottom, rgba(255,255,255,0) 0%, rgba(255,255,255,0.92) 50%, #ffffff 100%)',
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                gap: '10px',
                                marginTop: '-42px',
                                zIndex: 10,
                              }}
                            >
                              <button
                                type="button"
                                onClick={() => setIsDocExpanded(true)}
                                className="btn-primary"
                                style={{
                                  display: 'inline-flex',
                                  alignItems: 'center',
                                  gap: '8px',
                                  boxShadow: '0 4px 14px rgba(0,0,0,0.18)',
                                  fontSize: '0.84rem',
                                  padding: '8px 18px',
                                }}
                              >
                                <span>📖 Read Full Document (Expand View)</span>
                                <span style={{ opacity: 0.8, fontSize: '0.76rem' }}>
                                  ({redlineResult.segments.length} segments)
                                </span>
                              </button>
                              <button
                                type="button"
                                onClick={() => setFilterOutdatedOnly(true)}
                                className="btn-outline"
                                style={{
                                  fontSize: '0.84rem',
                                  padding: '8px 14px',
                                  background: '#ffffff',
                                  boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
                                }}
                              >
                                🎯 Focus Outdated Only
                              </button>
                            </div>
                          ) : (
                            <div
                              style={{
                                marginTop: '16px',
                                display: 'flex',
                                justifyContent: 'center',
                                gap: '12px',
                                padding: '12px',
                                borderTop: '1px solid var(--border-subtle)',
                              }}
                            >
                              <button
                                type="button"
                                onClick={() => {
                                  setIsDocExpanded(false);
                                  docContainerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                }}
                                className="btn-secondary"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem' }}
                              >
                                🔼 Collapse Document Preview
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div
                      style={{
                        padding: '24px',
                        background: '#f8fafc',
                        borderRadius: '8px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.86rem',
                        whiteSpace: 'pre-wrap',
                        maxHeight: '400px',
                        overflowY: 'auto',
                      }}
                    >
                      {documentContent}
                    </div>
                  )}

                  {/* Standards Supersession Migration Roadmap */}
                  {redlineResult?.standards_redline_mappings && (
                    <StandardsMigrationCard
                      mappings={redlineResult.standards_redline_mappings}
                      onApplyFix={(oldStd, newStd) => {
                        const matchingFix = redlineResult.auto_fixes?.find(
                          (f) => f.old_standard_id === oldStd || f.old_text.includes(oldStd)
                        );
                        if (matchingFix) {
                          handleSingleFix(matchingFix);
                        } else {
                          const updated = (documentContent || '').replace(oldStd, newStd);
                          setDocumentContent(updated);
                          const remainingMappings = (redlineResult.standards_redline_mappings || []).filter(
                            (m) => m.old_standard !== oldStd
                          );
                          setRedlineResult({
                            ...redlineResult,
                            standards_redline_mappings: remainingMappings,
                            summary: {
                              ...redlineResult.summary,
                              outdated_count: Math.max(0, redlineResult.summary.outdated_count - 1),
                              compliant_count: redlineResult.summary.compliant_count + 1,
                            },
                          });
                          onToast(`Replaced ${oldStd} with ${newStd}.`, 'success');
                        }
                      }}
                    />
                  )}
                </Panel>
              </motion.div>
            )}

            {/* 2. OVERVIEW & MEASUREMENTS SPECS */}
            {activeFeature === 'overview' && (
              <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <TenderOverviewSection overview={redlineResult?.tender_overview} />
              </motion.div>
            )}

            {/* 3. COMPARISON MATRIX AUDIT */}
            {activeFeature === 'comparison' && (
              <motion.div key="comparison" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <ComparisonMatrixSection rows={redlineResult?.comparison_matrix} />
              </motion.div>
            )}

            {/* 4. ECO TRACK GREEN PROCUREMENT */}
            {activeFeature === 'eco' && (
              <motion.div key="eco" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <EcoTrackSection ecoTrack={redlineResult?.eco_track} />
              </motion.div>
            )}

            {/* 5. BIDDER CRITERIA SUMMARY */}
            {activeFeature === 'bidder' && (
              <motion.div key="bidder" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <BidderRequirementsSection requirements={redlineResult?.bidder_requirements} />
              </motion.div>
            )}

            {/* 6. AUDIT FINDINGS & GAPS (ORIGINAL GAP AUDIT) */}
            {activeFeature === 'gaps' && (
              <motion.div key="gaps" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                {auditReport ? (
                  <Panel title="Audit Findings & Discrepancies" badge={`${auditReport.total_gaps_count} Gaps`}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                      <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>COVERAGE SCORE</span>
                        <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#059669', marginTop: '2px' }}>
                          {Math.round(auditReport.standards_coverage_score * 100)}%
                        </div>
                      </div>
                      <div style={{ padding: '14px', background: 'rgba(220, 38, 38, 0.08)', borderRadius: '8px', border: '1px solid rgba(220, 38, 38, 0.2)' }}>
                        <span style={{ fontSize: '0.7rem', color: '#dc2626', fontWeight: 700, textTransform: 'uppercase' }}>OUTDATED REFS</span>
                        <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#dc2626', marginTop: '2px' }}>
                          {auditReport.outdated_references_count}
                        </div>
                      </div>
                      <div style={{ padding: '14px', background: 'rgba(245, 158, 11, 0.08)', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                        <span style={{ fontSize: '0.7rem', color: '#d97706', fontWeight: 700, textTransform: 'uppercase' }}>MISSING MANDATES</span>
                        <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#d97706', marginTop: '2px' }}>
                          {auditReport.missing_primary_references_count}
                        </div>
                      </div>
                      <div style={{ padding: '14px', background: 'rgba(2, 132, 199, 0.08)', borderRadius: '8px', border: '1px solid rgba(2, 132, 199, 0.2)' }}>
                        <span style={{ fontSize: '0.7rem', color: '#0284c7', fontWeight: 700, textTransform: 'uppercase' }}>ALLIED SAFETY GAPS</span>
                        <div style={{ fontSize: '1.4rem', fontWeight: 900, color: '#0284c7', marginTop: '2px' }}>
                          {auditReport.missing_testing_safety_count}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {auditReport.gaps && auditReport.gaps.length > 0 ? (
                        auditReport.gaps.map((gap, i) => <GapCard key={i} gap={gap} index={i} />)
                      ) : (
                        <p style={{ color: '#059669', fontSize: '0.88rem' }}>
                          ✅ All cited standards adhere to current statutory specifications.
                        </p>
                      )}
                    </div>

                    <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
                      <button onClick={handleGenerateSpec} disabled={isGeneratingSpec} className="btn-accent">
                        {isGeneratingSpec ? 'Drafting Spec...' : 'Draft Grounded Technical Specification 📝'}
                      </button>
                    </div>
                  </Panel>
                ) : (
                  <Panel title="Audit Findings">
                    <p style={{ color: '#64748b' }}>Click "Upload & Audit Tender" above to view detailed gap findings.</p>
                  </Panel>
                )}
              </motion.div>
            )}

            {/* 7. ADVERSARIAL AI DOUBLE-CHECK (SAFETY WINNER) */}
            {activeFeature === 'auditor' && (
              <motion.div key="auditor" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <Panel
                  title="The Adversarial AI Double-Check"
                  subtitle="AI can sometimes hallucinate fake rule numbers (like 'IS 9999'). A second 'Auditor AI' aggressively double-checks the first AI. If a rule looks made up or uncertain, it blocks it and warns: 'I am not 100% sure, please check this manually.'"
                  badge="AI Safety System"  
                > 
                  {/* Safety Alert Banner */}
                  <div
                    style={{
                      padding: '16px 20px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
                      border: '1px solid #fde68a',
                      marginBottom: '16px',
                      color: '#92400e',
                      fontSize: '0.84rem',
                      lineHeight: 1.5,
                    }}
                  >
                    <strong>Why this matters in Government Buying:</strong> AI hallucinating a fake standard number like <code>IS 9999</code> can cause legal disqualification, CAG audit objections, or tender cancellation. The <strong>Auditor AI</strong> acts as an independent watchdog blocking unverified citations.
                  </div>

                  <textarea
                    value={auditorRefs}
                    onChange={(e) => setAuditorRefs(e.target.value)}
                    rows={5}
                    style={{
                      width: '100%',
                      padding: '12px 14px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.88rem',
                      lineHeight: 1.6,
                      borderRadius: '8px',
                      border: '1px solid #cbd5e1',
                      background: '#fafbfc',
                      marginBottom: '12px',
                    }}
                  />

                  <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
                    <button
                      onClick={handleVerifyHallucinations}
                      disabled={isVerifying}
                      className="btn-primary"
                    >
                      {isVerifying ? '🛡️ Auditing References...' : '🛡️ Run Adversarial Double-Check'}
                    </button>
                  </div>

                  {auditorResult && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' }}>
                        <div style={{ padding: '14px', background: auditorResult.overall_trust_score >= 0.8 ? 'rgba(5,150,105,0.08)' : 'rgba(220,38,38,0.08)', borderRadius: '8px', textAlign: 'center' }}>
                          <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 700 }}>DOCUMENT TRUST SCORE</span>
                          <div style={{ fontSize: '1.5rem', fontWeight: 900, color: auditorResult.overall_trust_score >= 0.8 ? '#059669' : '#dc2626' }}>
                            {Math.round(auditorResult.overall_trust_score * 100)}%
                          </div>
                        </div>

                        <div style={{ padding: '14px', background: '#f8fafc', borderRadius: '8px', textAlign: 'center' }}>
                          <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 700 }}>VERIFIED REAL</span>
                          <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#059669' }}>
                            {auditorResult.verified_count}
                          </div>
                        </div>

                        <div style={{ padding: '14px', background: 'rgba(220,38,38,0.08)', borderRadius: '8px', textAlign: 'center' }}>
                          <span style={{ fontSize: '0.7rem', color: '#dc2626', fontWeight: 700 }}>HALLUCINATIONS CAUGHT</span>
                          <div style={{ fontSize: '1.5rem', fontWeight: 900, color: '#dc2626' }}>
                            {auditorResult.hallucination_count}
                          </div>
                        </div>
                      </div>

                      {/* Verified items list */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {auditorResult.results.map((r, idx) => {
                          const isBad = r.verdict === 'HALLUCINATION' || r.verdict === 'FORMAT_INVALID';
                          return (
                            <div
                              key={idx}
                              style={{
                                padding: '12px 16px',
                                borderRadius: '8px',
                                background: isBad ? '#fee2e2' : '#f0fdf4',
                                border: `1px solid ${isBad ? '#fca5a5' : '#bbf7d0'}`,
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                flexWrap: 'wrap',
                                gap: '8px',
                              }}
                            >
                              <div>
                                <span style={{ fontWeight: 800, fontFamily: 'var(--font-mono)', color: isBad ? '#991b1b' : '#065f46' }}>
                                  {r.input_reference}
                                </span>
                                <div style={{ fontSize: '0.78rem', color: isBad ? '#7f1d1d' : '#047857', marginTop: '2px' }}>
                                  {r.reason}
                                </div>
                              </div>

                              <span style={{ fontSize: '0.74rem', fontWeight: 800, padding: '3px 8px', borderRadius: '4px', background: isBad ? '#dc2626' : '#059669', color: '#fff' }}>
                                {r.verdict}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </Panel>
              </motion.div>
            )}

            {/* 8. VISION AI TABLE READER (TECH WINNER) */}
            {activeFeature === 'vision' && (
              <motion.div key="vision" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <Panel
                  title="Reading Complex Tables"
                  subtitle="Indian Standard books are full of mathematical formulas, engineering charts, and tables. Vision AI processes them as pictures, reading columns and numbers without breaking them."
                  badge="Vision AI Powered"
                >
                  {/* Competitive Advantage Card */}
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                      gap: '12px',
                      marginBottom: '16px',
                    }}
                  >
                    <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)' }}>
                      <strong style={{ color: '#b91c1c', fontSize: '0.82rem', display: 'block', marginBottom: '2px' }}>
                        ❌ Issues:Others
                      </strong>
                      <span style={{ fontSize: '0.8rem', color: '#7f1d1d', lineHeight: 1.45 }}>
                        Their AI will only read plain text. When it hits an engineering table, it gets confused and fails.
                      </span>
                    </div>

                    <div style={{ padding: '12px 14px', borderRadius: '8px', background: 'rgba(5, 150, 105, 0.08)', border: '1px solid rgba(5, 150, 105, 0.25)' }}>
                      <strong style={{ color: '#047857', fontSize: '0.82rem', display: 'block', marginBottom: '2px' }}>
                        ✅ Your Solution:
                      </strong>
                      <span style={{ fontSize: '0.8rem', color: '#065f46', lineHeight: 1.45 }}>
                        Your AI looks at tables like a picture (using Vision AI). It reads columns and numbers perfectly without breaking them.
                      </span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '20px' }}>
                    <input
                      ref={visionInputRef}
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={handleVisionImageUpload}
                    />

                    <button
                      onClick={() => visionInputRef.current?.click()}
                      disabled={isExtracting}
                      className="btn-primary"
                    >
                      {isExtracting ? '👁️ Reading Table Image...' : '📷 Upload Engineering Table / Chart Image'}
                    </button>

                    <button
                      onClick={async () => {
                        setIsExtracting(true);
                        try {
                          const res = await extractTableFromText(
                            `Table 4.1: Permissible Hydraulic Deviations
Flow Rate (Q) | Dynamic Head (H) | Motor kW | Allowable Delta
120 m3/h | 45 m | 37 kW | ±4.0%
80 m3/h | 55 m | 30 kW | ±3.5%
40 m3/h | 65 m | 22 kW | ±2.5%`
                          );
                          setVisionResult(res);
                          onToast('Sample engineering table extracted by Vision AI!', 'success');
                        } catch (err: any) {
                          onToast(err.message || 'Extraction failed', 'error');
                        } finally {
                          setIsExtracting(false);
                        }
                      }}
                      className="btn-secondary"
                    >
                      📋 Load Sample Motor Tolerance Chart
                    </button>
                  </div>

                  {visionResult && visionResult.tables.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {visionResult.tables.map((tbl, i) => (
                        <div key={i} style={{ borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
                          <div style={{ padding: '10px 16px', background: '#f8fafc', fontWeight: 700, fontSize: '0.86rem', color: '#0f172a' }}>
                            {tbl.title || `Table #${i + 1}`} ({tbl.row_count} rows × {tbl.col_count} columns)
                          </div>
                          <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                              <thead>
                                <tr style={{ background: '#f1f5f9' }}>
                                  {tbl.headers.map((h, hi) => (
                                    <th key={hi} style={{ padding: '10px 14px', textAlign: 'left', fontWeight: 700, color: '#475569' }}>
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {tbl.rows.map((row, ri) => (
                                  <tr key={ri} style={{ borderTop: '1px solid #f1f5f9' }}>
                                    {row.map((cell, ci) => (
                                      <td key={ci} style={{ padding: '10px 14px', fontFamily: 'var(--font-mono)' }}>
                                        {cell}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Panel>
              </motion.div>
            )}

            {/* 9. AI PROJECT COST ESTIMATION */}
            {activeFeature === 'cost' && (
              <motion.div key="cost" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
                <CostEstimationSection estimation={redlineResult?.cost_estimation} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Generated Specification Output (if triggered) */}
      {generatedSpec && (
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
          <Panel
            title={generatedSpec.title || 'Draft Technical Procurement Specification'}
            subtitle={`Type: ${generatedSpec.specification_type} | Grounded in BIS ontology`}
            badge="Generated Specification"
            action={
              <button onClick={handleCopySpec} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
                Copy Text 📋
              </button>
            }
          >
            <div
              style={{
                background: '#ffffff',
                borderRadius: 'var(--radius-md)',
                padding: '22px',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.86rem',
                lineHeight: 1.65,
                whiteSpace: 'pre-wrap',
                maxHeight: '450px',
                overflowY: 'auto',
              }}
            >
              {generatedSpec.specification_text}
            </div>
          </Panel>
        </motion.div>
      )}
    </div>
  );
};
