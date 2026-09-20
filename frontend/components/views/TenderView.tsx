'use client';

import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

const SAMPLE_TENDER_TEXT = `GOVERNMENT OF INDIA - CENTRAL PUBLIC WORKS DEPARTMENT
NOTICE INVITING TENDER FOR SUPPLY, INSTALLATION, TESTING AND COMMISSIONING OF PUMPING MACHINERY

SECTION 4: TECHNICAL SPECIFICATIONS & STANDARDS COMPLIANCE

Clause 4.1: Electric Motors
All drive motors for clear water centrifugal pump sets shall be three phase squirrel cage induction motors suitable for 415 V ±10%, 50 Hz AC supply. Motors shall conform strictly to IS 325:1996 with Class F insulation and temperature rise limited to Class B. Motor enclosure shall be TEFC IP 55.

Clause 4.2: Power and Control Cabling
Cables shall be heavy duty PVC insulated and PVC sheathed copper conductor electrical cables suitable for rated voltage up to and including 1100 V conforming to IS 1554 (Part 1).

Clause 4.3: Electrical Installations and Earthing
The complete electrical installations of the pump house including switchgear, control panels, and wiring practices shall comply with IS 732 and general code of practice for earthing.

Clause 4.4: Drinking Water Handling Equipment
All components coming into contact with potable water shall be inert and safe for drinking water supply networks.`;

export const TenderView: React.FC<TenderViewProps> = ({ onToast }) => {
  const dropzoneRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [tenderNumber, setTenderNumber] = useState('NIT-CPWD-2026-089');
  const [orgName, setOrgName] = useState('Central Public Works Department');

  const [isUploading, setIsUploading] = useState(false);
  const [isAuditing, setIsAuditing] = useState(false);
  const [isGeneratingSpec, setIsGeneratingSpec] = useState(false);

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
            border: '2px dashed rgba(20, 184, 166, 0.4)',
            borderRadius: 'var(--radius-lg)',
            padding: '36px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            background: 'rgba(15, 23, 42, 0.4)',
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
          <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#ffffff' }}>
            {selectedFile ? selectedFile.name : 'Drag & drop tender document here, or click to browse'}
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Supports PDF, DOCX, and TXT files (up to 10 MB)
          </p>

          {selectedFile && (
            <div style={{ marginTop: '10px' }}>
              <span className="badge badge-teal">
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
          <LoadingSkeleton height="90px" />
          <LoadingSkeleton height="140px" />
        </Panel>
      )}

      {/* Tender Document Summary Card */}
      {uploadResult && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <div
            className="glass-panel"
            style={{
              padding: '20px 24px',
              marginBottom: '20px',
              borderLeft: '4px solid var(--accent-teal)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <span className="badge badge-teal" style={{ marginBottom: '6px' }}>
                  TENDER ID #{uploadResult.tender_id}
                </span>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff' }}>
                  {uploadResult.filename}
                </h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Parsed status: {uploadResult.status}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '20px' }}>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>CLAUSES</span>
                  <span style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                    {uploadResult.total_clauses}
                  </span>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>STANDARDS CITED</span>
                  <span style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-teal)' }}>
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
              padding: '24px',
              marginBottom: '20px',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '16px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                paddingBottom: '16px',
                marginBottom: '20px',
              }}
            >
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>
                  Tender Compliance & Standards Audit
                </h3>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Evidence-grounded audit evaluating cited standards currency, testing allied gaps, and QCO mandates.
                </p>
              </div>

              {/* Coverage Score Metric */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '14px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  padding: '10px 18px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <div>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block' }}>
                    STANDARDS COVERAGE
                  </span>
                  <span
                    style={{
                      fontSize: '1.5rem',
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
                gap: '12px',
                marginBottom: '22px',
              }}
            >
              <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TOTAL GAPS</span>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                  {auditReport.total_gaps_count}
                </div>
              </div>
              <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.08)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-danger)' }}>OUTDATED CITATIONS</span>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--status-danger)', marginTop: '2px' }}>
                  {auditReport.outdated_references_count}
                </div>
              </div>
              <div style={{ padding: '12px', background: 'rgba(245, 158, 11, 0.08)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--status-warning)' }}>MISSING PRIMARY</span>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--status-warning)', marginTop: '2px' }}>
                  {auditReport.missing_primary_references_count}
                </div>
              </div>
              <div style={{ padding: '12px', background: 'rgba(56, 189, 248, 0.08)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '0.7rem', color: '#38bdf8' }}>ALLIED / SAFETY GAPS</span>
                <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                  {auditReport.missing_testing_safety_count}
                </div>
              </div>
            </div>

            {/* Gap cards list */}
            <div>
              <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
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
                padding: '18px 20px',
                background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.15) 0%, rgba(13, 148, 136, 0.25) 100%)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid rgba(20, 184, 166, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '14px',
              }}
            >
              <div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
                  Generate Grounded Procurement Specification
                </h4>
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Automatically rectifies superseded standards (e.g. replaces IS 325 with IS 12615) and appends mandatory compliance clauses.
                </p>
              </div>

              <button
                onClick={handleGenerateSpec}
                disabled={isGeneratingSpec}
                className="btn-primary"
                style={{ background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)', boxShadow: '0 4px 14px rgba(249, 115, 22, 0.35)' }}
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
                background: 'rgba(10, 15, 26, 0.9)',
                borderRadius: 'var(--radius-md)',
                padding: '20px',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.86rem',
                lineHeight: 1.6,
                color: '#e2e8f0',
                whiteSpace: 'pre-wrap',
                maxHeight: '480px',
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
