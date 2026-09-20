'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { generateSpecification, updateSpecification, GeneratedSpecificationResponse } from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface SpecViewProps {
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const SAMPLE_SPEC_PROMPTS = [
  { label: 'Induction Motor Spec', query: 'Three phase energy efficient squirrel cage induction motor for industrial pumping, 415 V 50 Hz' },
  { label: 'PVC Electric Cable Spec', query: 'PVC insulated electric cables for working voltages up to 1100 V with copper conductors' },
  { label: 'Submersible Pump Spec', query: 'Submersible pump sets for clear, cold water supply in municipal distribution networks' },
];

export const SpecView: React.FC<SpecViewProps> = ({ onToast }) => {
  const [queryText, setQueryText] = useState(SAMPLE_SPEC_PROMPTS[0].query);
  const [specTitle, setSpecTitle] = useState('Technical Procurement Specification for Industrial Machinery');
  const [genType, setGenType] = useState('technical_specification');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const [specResult, setSpecResult] = useState<GeneratedSpecificationResponse | null>(null);
  const [editedText, setEditedText] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) return;

    setIsGenerating(true);
    try {
      const res = await generateSpecification({
        generation_type: genType,
        title: specTitle,
        query_text: queryText,
      });
      setSpecResult(res);
      setEditedText(res.specification_text || '');
      onToast('Grounded specification generated successfully!', 'success');
    } catch (err: any) {
      onToast(err.message || 'Specification generation failed.', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!specResult?.id) {
      onToast('Specification text updated locally.', 'info');
      return;
    }
    setIsSaving(true);
    try {
      const res = await updateSpecification(specResult.id, {
        title: specTitle,
        specification_text: editedText,
      });
      setSpecResult(res);
      onToast('Specification saved to database!', 'success');
    } catch (err: any) {
      onToast(err.message || 'Failed to update specification.', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCopy = () => {
    if (!editedText) return;
    navigator.clipboard.writeText(editedText);
    onToast('Specification copied to clipboard!', 'info');
  };

  const handleDownload = () => {
    if (!editedText) return;
    const blob = new Blob([editedText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${specTitle.replace(/\s+/g, '_')}_Spec.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    onToast('Specification downloaded!', 'success');
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Grounded Specification Drafting Workspace"
        subtitle="Generates legally rigorous procurement specifications and tender clauses grounded strictly in Bureau of Indian Standards specifications."
        badge="Module 13 Spec"
      >
        <form onSubmit={handleGenerate}>
          {/* Preset Prompts */}
          <div style={{ marginBottom: '16px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
              Quick Equipment Templates:
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {SAMPLE_SPEC_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQueryText(prompt.query);
                    setSpecTitle(`Technical Specification for ${prompt.label}`);
                  }}
                  style={{
                    padding: '5px 12px',
                    borderRadius: 'var(--radius-full)',
                    background: queryText === prompt.query ? 'var(--accent-primary-subtle)' : '#f8fafc',
                    border: `1px solid ${queryText === prompt.query ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                    color: queryText === prompt.query ? 'var(--accent-primary-dark)' : 'var(--text-secondary)',
                    fontSize: '0.76rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  📝 {prompt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Title & Type Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Specification Document Title
              </label>
              <input
                type="text"
                value={specTitle}
                onChange={(e) => setSpecTitle(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Clause / Document Type
              </label>
              <select value={genType} onChange={(e) => setGenType(e.target.value)}>
                <option value="technical_specification">Full Technical Specification (Sectional)</option>
                <option value="gfr_compliance_clause">GFR 2017 Model Tender Clause</option>
                <option value="testing_schedule">Inspection & Testing Quality Plan</option>
              </select>
            </div>
          </div>

          {/* Query Textarea */}
          <div style={{ marginBottom: '18px' }}>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Equipment Requirements & Technical Operating Envelope
            </label>
            <textarea
              rows={3}
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Describe required equipment ratings, duty conditions, application environment..."
              required
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" disabled={isGenerating} className="btn-primary" style={{ minWidth: '220px' }}>
              {isGenerating ? 'Drafting Specification...' : '📝 Generate Specification'}
            </button>
          </div>
        </form>
      </Panel>

      {/* Loading */}
      {isGenerating && (
        <Panel title="Formulating Grounded Technical Clauses...">
          <LoadingSkeleton height="70px" />
          <LoadingSkeleton height="180px" />
        </Panel>
      )}

      {/* Result Workspace */}
      {!isGenerating && specResult && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          <Panel
            title={specResult.title || specTitle}
            subtitle={`Grounded in Bureau of Indian Standards | Type: ${specResult.specification_type}`}
            badge="Draft Specification"
            action={
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={handleCopy} className="btn-secondary" style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
                  Copy 📋
                </button>
                <button onClick={handleDownload} className="btn-secondary" style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
                  Download ⬇️
                </button>
                <button onClick={handleSave} disabled={isSaving} className="btn-primary" style={{ fontSize: '0.78rem', padding: '6px 14px' }}>
                  {isSaving ? 'Saving...' : 'Save Changes 💾'}
                </button>
              </div>
            }
          >
            <textarea
              rows={16}
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              style={{
                width: '100%',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.86rem',
                lineHeight: 1.65,
                color: 'var(--text-primary)',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                background: '#ffffff',
                boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.03)',
              }}
            />

            <div style={{ marginTop: '12px', fontSize: '0.76rem', color: 'var(--text-muted)' }}>
              Tip: You can edit or append custom clauses directly above, then copy or save to export.
            </div>
          </Panel>
        </motion.div>
      )}
    </div>
  );
};
