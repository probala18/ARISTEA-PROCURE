'use client';

import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import {
  uploadTenderDocument,
  getTenderAudit,
  generateSpecification,
  TenderUploadResponse,
  TenderAuditReport,
  GeneratedSpecificationResponse,
} from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { GapCard } from '@/components/ui/GapCard';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { springDropzone } from '@/lib/gsap-animations';

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
`;

export const TenderView: React.FC<TenderViewProps> = ({ onToast }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [tenderNumber, setTenderNumber] = useState('');
  const [orgName, setOrgName] = useState('Central Public Works Department (CPWD)');
  const [isUploading, setIsUploading] = useState(false);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isGeneratingSpec, setIsGeneratingSpec] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);

  const [uploadResult, setUploadResult] = useState<TenderUploadResponse | null>(null);
  const [auditReport, setAuditReport] = useState<TenderAuditReport | null>(null);
  const [generatedSpec, setGeneratedSpec] = useState<GeneratedSpecificationResponse | null>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (dropzoneRef.current) springDropzone(dropzoneRef.current);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleUseSampleTender = () => {
    const blob = new Blob([SAMPLE_TENDER_TEXT], { type: 'text/plain' });
    const file = new File([blob], 'CPWD_Pumping_Machinery_Tender.txt', { type: 'text/plain' });
    setSelectedFile(file);
    onToast('Loaded sample tender document for Pumping Machinery.', 'info');
  };

  const handleUploadAndAudit = async () => {
    if (!selectedFile) {
      onToast('Please select a tender document or load the sample tender.', 'error');
      return;
    }

    setIsUploading(true);
    setUploadResult(null);
    setAuditReport(null);
    setGeneratedSpec(null);

    try {
      // 1. Upload & Parse
      const uploadRes = await uploadTenderDocument(
        selectedFile,
        tenderNumber || undefined,
        'Procurement Tender',
        orgName || undefined
      );
      setUploadResult(uploadRes);
      onToast(`Tender parsed: ${uploadRes.total_clauses} clauses, ${uploadRes.total_standards_detected} standards detected`, 'success');

      // 2. Audit
      setIsAuditing(true);
      const auditRes = await getTenderAudit(uploadRes.tender_id);
      setAuditReport(auditRes);
      onToast(`Audit completed! Standards coverage score: ${Math.round(auditRes.standards_coverage_score * 100)}%`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Tender processing failed.', 'error');
    } finally {
      setIsUploading(false);
      setIsAuditing(false);
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
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Tender Document Engine & Grounded Audit"
        subtitle="Upload RFP/tender documents (PDF, DOCX, TXT) to extract technical clauses, detect outdated BIS citations, and generate compliant procurement specs."
        badge="Module 11-13"
      >
        {/* Upload Zone */}
        <div
          ref={dropzoneRef}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: '2px dashed rgba(79, 70, 229, 0.4)',
            borderRadius: 'var(--radius-lg)',
            padding: '36px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            background: '#f8fafc',
            transition: 'all 0.2s ease',
            marginBottom: '20px',
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            style={{ display: 'none' }}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                setSelectedFile(e.target.files[0]);
              }
            }}
          />

          <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>📄</div>
          <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {selectedFile ? selectedFile.name : 'Drag & drop tender document here, or click to browse'}
          </h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Supports PDF, DOCX, and TXT files (up to 10 MB)
          </p>

          {selectedFile && (
            <div style={{ marginTop: '12px' }}>
              <span className="badge badge-indigo">
                {(selectedFile.size / 1024).toFixed(1)} KB — Ready to Process
              </span>
            </div>
          )}
        </div>

        {/* Action Buttons & Presets */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '14px',
          }}
        >
          <button
            type="button"
            onClick={handleUseSampleTender}
            className="btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            📋 Use Sample Pumping Machinery Tender
          </button>

          <button
            onClick={handleUploadAndAudit}
            disabled={!selectedFile || isUploading || isAuditing}
            className="btn-primary"
            style={{ minWidth: '220px' }}
          >
            {isUploading ? 'Parsing Document...' : isAuditing ? 'Auditing Standards...' : 'Upload & Audit Tender 🚀'}
          </button>
        </div>
      </Panel>

      {/* Loading Skeletons */}
      {(isUploading || isAuditing) && (
        <Panel title="Analyzing Tender Clauses & BIS Grounding...">
          <LoadingSkeleton height="85px" />
          <LoadingSkeleton height="140px" />
        </Panel>
      )}

      {/* Tender Document Summary Card */}
      {uploadResult && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <span className="badge badge-indigo" style={{ marginBottom: '6px' }}>
                  TENDER ID #{uploadResult.tender_id}
                </span>
                <h3 style={{ fontSize: '1.18rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {uploadResult.filename}
                </h3>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  Status: {uploadResult.status} · Reference: {uploadResult.tender_number || 'Auto-generated'}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '24px' }}>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', fontWeight: 700, textTransform: 'uppercase' }}>CLAUSES</span>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                    {uploadResult.total_clauses}
                  </span>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', fontWeight: 700, textTransform: 'uppercase' }}>STANDARDS CITED</span>
                  <span style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary-dark)' }}>
                    {uploadResult.total_standards_detected}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Audit Report */}
      {auditReport && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          <div
            className="glass-panel"
            style={{
              padding: '26px',
              marginBottom: '20px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
                borderBottom: '1px solid #f1f5f9',
                paddingBottom: '18px',
                marginBottom: '22px',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.015em' }}>
                  Tender Compliance & Standards Audit
                </h3>
                <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Evidence-grounded audit evaluating cited standards currency, testing allied gaps, and QCO mandates.
                </p>
              </div>

              {/* Coverage Score Metric */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  background: '#f8fafc',
                  padding: '12px 20px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', fontWeight: 700, textTransform: 'uppercase' }}>
                    STANDARDS COVERAGE
                  </span>
                  <span
                    style={{
                      fontSize: '1.6rem',
                      fontWeight: 800,
                      fontFamily: 'var(--font-mono)',
                      color:
                        auditReport.standards_coverage_score >= 0.7
                          ? 'var(--status-success)'
                          : auditReport.standards_coverage_score >= 0.4
                          ? 'var(--status-warning)'
                          : 'var(--status-danger)',
                    }}
                  >
                    {Math.round(auditReport.standards_coverage_score * 100)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Metric counters */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
                gap: '14px',
                marginBottom: '24px',
              }}
            >
              <div style={{ padding: '14px', background: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>TOTAL GAPS</span>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }}>
                  {auditReport.total_gaps_count}
                </div>
              </div>
              <div style={{ padding: '14px', background: 'rgba(220, 38, 38, 0.06)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(220, 38, 38, 0.2)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-danger)', fontWeight: 700, textTransform: 'uppercase' }}>OUTDATED CITATIONS</span>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--status-danger)', marginTop: '4px' }}>
                  {auditReport.outdated_references_count}
                </div>
              </div>
              <div style={{ padding: '14px', background: 'rgba(245, 158, 11, 0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(245, 158, 11, 0.22)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-warning)', fontWeight: 700, textTransform: 'uppercase' }}>MISSING PRIMARY</span>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--status-warning)', marginTop: '4px' }}>
                  {auditReport.missing_primary_references_count}
                </div>
              </div>
              <div style={{ padding: '14px', background: 'rgba(2, 132, 199, 0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(2, 132, 199, 0.22)' }}>
                <span style={{ fontSize: '0.7rem', color: '#0284c7', fontWeight: 700, textTransform: 'uppercase' }}>ALLIED / SAFETY GAPS</span>
                <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0284c7', marginTop: '4px' }}>
                  {auditReport.missing_testing_safety_count}
                </div>
              </div>
            </div>

            {/* Gap cards list */}
            <div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '14px', color: 'var(--text-primary)' }}>
                Audit Findings & Discrepancies ({auditReport.gaps?.length || 0})
              </h4>
              {auditReport.gaps && auditReport.gaps.length > 0 ? (
                auditReport.gaps.map((gap, i) => <GapCard key={i} gap={gap} index={i} />)
              ) : (
                <p style={{ color: 'var(--status-success)', fontSize: '0.85rem' }}>
                  ✅ No gaps or non-compliant standard citations detected in this document.
                </p>
              )}
            </div>

            {/* One-Click Spec Generation Trigger */}
            <div
              style={{
                marginTop: '28px',
                padding: '20px 24px',
                background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.06) 0%, #f8fafc 100%)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid rgba(79, 70, 229, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
              }}
            >
              <div>
                <h4 style={{ fontSize: '1.08rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Generate Grounded Procurement Specification
                </h4>
                <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Automatically rectifies superseded standards (e.g. replaces IS 325 with IS 12615) and appends mandatory compliance clauses.
                </p>
              </div>

              <button
                onClick={handleGenerateSpec}
                disabled={isGeneratingSpec}
                className="btn-accent"
              >
                {isGeneratingSpec ? 'Generating Spec...' : 'Generate Specification 📝'}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Generated Specification Output */}
      {generatedSpec && (
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
          <Panel
            title={generatedSpec.title || 'Draft Technical Procurement Specification'}
            subtitle={`Type: ${generatedSpec.specification_type} | Grounded in BIS ontology`}
            badge="Module 13 Spec"
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
                color: 'var(--text-primary)',
                whiteSpace: 'pre-wrap',
                maxHeight: '480px',
                overflowY: 'auto',
                boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.03)',
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
