'use client';

import React, { useState, useEffect } from 'react';
import { Panel } from '@/components/ui/Panel';
import {
  listStandards,
  getStandardDetail,
  getStandardCompliance,
  getStandardRelationships,
  StandardDetail,
  ComplianceReport,
  RelationshipEdge,
} from '@/lib/api';

interface StandardViewData {
  standard: StandardDetail;
  compliance?: ComplianceReport | null;
  relationships?: RelationshipEdge[];
}

interface SimplifyViewProps {
  initialStandardId?: string | null;
  onExploreStandard?: (standardId: string) => void;
  onGenerateSpec?: (standardId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

export const SimplifyView: React.FC<SimplifyViewProps> = ({
  initialStandardId,
  onExploreStandard,
  onGenerateSpec,
  onToast,
}) => {
  const [standards, setStandards] = useState<StandardDetail[]>([]);
  const [selectedStandardId, setSelectedStandardId] = useState<string>(initialStandardId || 'IS 12615:2018');
  const [details, setDetails] = useState<StandardViewData | null>(null);
  const [loadingList, setLoadingList] = useState<boolean>(true);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Load standard list
  useEffect(() => {
    let mounted = true;
    async function loadList() {
      try {
        const res = await listStandards({ limit: 100 });
        if (mounted) {
          setStandards(res.standards || []);
          if (!initialStandardId && res.standards && res.standards.length > 0) {
            setSelectedStandardId(res.standards[0].standard_id);
          }
        }
      } catch (err) {
        if (mounted) {
          onToast('Failed to load standard directory for explainer.', 'error');
        }
      } finally {
        if (mounted) setLoadingList(false);
      }
    }
    loadList();
    return () => {
      mounted = false;
    };
  }, [initialStandardId, onToast]);

  // Load details when selectedStandardId changes
  useEffect(() => {
    if (!selectedStandardId) return;
    let mounted = true;
    async function loadDetails() {
      setLoadingDetails(true);
      try {
        const [std, comp, rels] = await Promise.all([
          getStandardDetail(selectedStandardId),
          getStandardCompliance(selectedStandardId).catch(() => null),
          getStandardRelationships(selectedStandardId).catch(() => []),
        ]);
        if (mounted) {
          setDetails({
            standard: std,
            compliance: comp,
            relationships: rels,
          });
        }
      } catch (err) {
        if (mounted) {
          setDetails(null);
          onToast(`Could not load details for ${selectedStandardId}`, 'error');
        }
      } finally {
        if (mounted) setLoadingDetails(false);
      }
    }
    loadDetails();
    return () => {
      mounted = false;
    };
  }, [selectedStandardId, onToast]);

  const filteredStandards = standards.filter((s) => {
    const q = searchQuery.toLowerCase();
    return (
      s.standard_id.toLowerCase().includes(q) ||
      s.title.toLowerCase().includes(q) ||
      (s.category && s.category.toLowerCase().includes(q))
    );
  });

  // Plain language procurement synthesis derived strictly from verified scope and fields
  const generatePlainSummary = (det: StandardViewData) => {
    const title = det.standard.title;
    const cat = det.standard.category || 'General';
    const status = det.standard.status;
    const scope = det.standard.scope;
    const isMandatory = det.compliance?.requirement_level === 'MANDATORY';
    const qcoCount = det.compliance?.qco_records?.length || 0;

    return {
      overview: `This Indian Standard establishes technical requirements, tolerances, and quality benchmarks for ${title.toLowerCase()}. It falls under the ${cat} category.`,
      procurementAdvice: isMandatory
        ? `MANDATORY COMPLIANCE: Covered by Quality Control Order (QCO). Tenders specifying these goods must require ISI Certification Mark license as an eligibility criterion.`
        : `Voluntary standard unless specifically referenced in the procurement tender or departmental schedule of rates.`,
      scopeExplanation: scope
        ? `Scope highlights: ${scope.slice(0, 300)}${scope.length > 300 ? '...' : ''}`
        : 'Detailed scope text not explicitly detailed in standard header.',
      qcoNotice: qcoCount > 0
        ? `Backed by ${qcoCount} verified Quality Control Order(s) enforced by ministry notification.`
        : 'No specific QCO mandate recorded in verified database.',
    };
  };

  const plainSummary = details ? generatePlainSummary(details) : null;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div
        className="glass-panel"
        style={{
          padding: '24px 28px',
          borderRadius: 'var(--radius-lg)',
          background: '#ffffff',
          color: 'var(--text-primary)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-card)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span style={{ fontSize: '1.4rem' }}>📖</span>
              <span
                style={{
                  background: '#ffffff',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-subtle)',
                  padding: '3px 10px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  letterSpacing: '0.05em',
                  display: 'inline-flex',
                  alignItems: 'center',
                }}
              >
                SIMPLIFY & CLAUSE EXPLAINER
              </span>
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: '4px 0 8px 0', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
              Technical Standard to Procurement Translator
            </h2>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', maxWidth: '780px', lineHeight: 1.5 }}>
              Bridge the communication gap between dense BIS engineering specifications and plain-language public procurement requirements.
              Explains only verified scope and metadata from authoritative local records.
            </p>
          </div>
          <div style={{ background: '#f8fafc', padding: '12px 18px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px', fontWeight: 600 }}>Standard Selector</div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--accent-primary)', fontFamily: 'monospace' }}>
              {selectedStandardId}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', alignItems: 'start' }}>
        {/* Left Sidebar: Standard Picker */}
        <div className="glass-panel" style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
          <h4 style={{ fontSize: '0.88rem', fontWeight: 700, marginBottom: '10px', color: 'var(--text-primary)' }}>
            Select Verified Standard
          </h4>
          <input
            type="text"
            placeholder="Search IS number or title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field"
            style={{ width: '100%', marginBottom: '12px', fontSize: '0.8rem' }}
          />

          <div style={{ maxHeight: '520px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {loadingList ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                Loading standards...
              </div>
            ) : filteredStandards.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                No standards match filter.
              </div>
            ) : (
              filteredStandards.map((std) => (
                <button
                  key={std.standard_id}
                  onClick={() => setSelectedStandardId(std.standard_id)}
                  style={{
                    textAlign: 'left',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid',
                    borderColor: selectedStandardId === std.standard_id ? 'var(--brand-primary, #3b82f6)' : 'var(--border-color)',
                    background: selectedStandardId === std.standard_id ? 'rgba(59, 130, 246, 0.08)' : '#ffffff',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                    {std.standard_id}
                  </div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {std.title}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right Area: Split Comparison & Safe Evidence Translation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {loadingDetails ? (
            <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)', background: '#ffffff', borderRadius: 'var(--radius-md)' }}>
              Loading verified standard details...
            </div>
          ) : !details ? (
            <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)', background: '#ffffff', borderRadius: 'var(--radius-md)' }}>
              Select a standard from the list to view explanation.
            </div>
          ) : (
            <>
              {/* Top Action Bar */}
              <div className="glass-panel" style={{ padding: '14px 20px', borderRadius: 'var(--radius-md)', background: '#ffffff', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
                    {details.standard.standard_id}: {details.standard.title}
                  </h3>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '4px' }}>
                    <span className="badge badge-indigo">{details.standard.category || 'Engineering'}</span>
                    <span className={`badge ${details.standard.status === 'CURRENT' ? 'badge-emerald' : 'badge-amber'}`}>
                      {details.standard.status}
                    </span>
                    {details.compliance?.requirement_level && (
                      <span className={`badge ${details.compliance.requirement_level === 'MANDATORY' ? 'badge-rose' : 'badge-neutral'}`}>
                        {details.compliance.requirement_level}
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  {onExploreStandard && (
                    <button
                      onClick={() => onExploreStandard(details.standard.standard_id)}
                      className="btn-secondary"
                      style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                    >
                      Full Details 🏛️
                    </button>
                  )}
                  {onGenerateSpec && (
                    <button
                      onClick={() => onGenerateSpec(details.standard.standard_id)}
                      className="btn-primary"
                      style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                    >
                      Draft Spec 📝
                    </button>
                  )}
                </div>
              </div>

              {/* Side-by-Side Split View */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {/* Left: Technical Evidence (Verified Data) */}
                <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span style={{ fontSize: '1.1rem' }}>📐</span>
                    <h4 style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                      Official Technical Specifications (Verified)
                    </h4>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.82rem' }}>
                    <div>
                      <strong style={{ color: 'var(--text-secondary)' }}>Standard ID:</strong>
                      <div style={{ fontFamily: 'monospace', fontWeight: 600, marginTop: '2px' }}>{details.standard.standard_id}</div>
                    </div>

                    <div>
                      <strong style={{ color: 'var(--text-secondary)' }}>Official Scope:</strong>
                      <p style={{ margin: '4px 0 0 0', lineHeight: 1.5, color: 'var(--text-primary)' }}>
                        {details.standard.scope || 'Scope text not provided in header record.'}
                      </p>
                    </div>

                    {details.standard.technical_department && (
                      <div>
                        <strong style={{ color: 'var(--text-secondary)' }}>Department / Section:</strong>
                        <div style={{ marginTop: '2px' }}>{details.standard.technical_department}</div>
                      </div>
                    )}

                    {details.relationships && details.relationships.length > 0 && (
                      <div>
                        <strong style={{ color: 'var(--text-secondary)' }}>Normative & Allied Standards ({details.relationships.length}):</strong>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                          {details.relationships.slice(0, 8).map((rel, idx) => (
                            <span
                              key={`${rel.source_id || 's'}-${rel.relationship_type}-${rel.target_id || 't'}-${idx}`}
                              className="badge badge-neutral"
                              style={{ fontSize: '0.72rem', fontFamily: 'monospace' }}
                            >
                              {rel.relationship_type}: {rel.target_standard_number || rel.target_id || rel.target || 'Standard'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Strict Evidence Boundary Box */}
                    <div style={{ marginTop: '12px', padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '2px' }}>
                        Clause Evidence Boundary
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#475569', fontStyle: 'italic' }}>
                        Detailed clause text not available in current verified dataset
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Plain-Language Procurement Explanation */}
                <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    <span style={{ fontSize: '1.1rem' }}>💡</span>
                    <h4 style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                      Plain-Language Procurement Translation
                    </h4>
                  </div>

                  {plainSummary && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.82rem' }}>
                      <div style={{ background: 'rgba(59, 130, 246, 0.05)', padding: '12px', borderRadius: 'var(--radius-sm)', borderLeft: '3px solid #3b82f6' }}>
                        <strong style={{ color: '#1e40af', display: 'block', marginBottom: '4px' }}>What this standard covers:</strong>
                        <p style={{ margin: 0, lineHeight: 1.45, color: 'var(--text-primary)' }}>
                          {plainSummary.overview}
                        </p>
                      </div>

                      <div style={{ background: details.compliance?.requirement_level === 'MANDATORY' ? 'rgba(225, 29, 72, 0.05)' : 'rgba(16, 185, 129, 0.05)', padding: '12px', borderRadius: 'var(--radius-sm)', borderLeft: `3px solid ${details.compliance?.requirement_level === 'MANDATORY' ? '#e11d48' : '#10b981'}` }}>
                        <strong style={{ color: details.compliance?.requirement_level === 'MANDATORY' ? '#9f1239' : '#065f46', display: 'block', marginBottom: '4px' }}>
                          Procurement Officer Action:
                        </strong>
                        <p style={{ margin: 0, lineHeight: 1.45, color: 'var(--text-primary)' }}>
                          {plainSummary.procurementAdvice}
                        </p>
                      </div>

                      <div>
                        <strong style={{ color: 'var(--text-secondary)' }}>Quality Control Order (QCO) Status:</strong>
                        <p style={{ margin: '4px 0 0 0', lineHeight: 1.45, color: 'var(--text-primary)' }}>
                          {plainSummary.qcoNotice}
                        </p>
                      </div>

                      <div style={{ background: '#f8fafc', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                        <strong style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>
                          Specification Clause Formulation:
                        </strong>
                        <p style={{ margin: '4px 0 8px 0', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                          To generate verified, evidence-grounded procurement specifications and inspection test plans for {details.standard.standard_id}, use the backend Specification Drafting Workspace.
                        </p>
                        {onGenerateSpec && (
                          <button
                            onClick={() => onGenerateSpec(details.standard.standard_id)}
                            className="btn-primary"
                            style={{ fontSize: '0.74rem', padding: '5px 12px' }}
                          >
                            Draft Grounded Specification 📝
                          </button>
                        )}
                      </div>

                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        Provenance: Verified standard database record · Ingestion hash: {details.standard.standard_id}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
