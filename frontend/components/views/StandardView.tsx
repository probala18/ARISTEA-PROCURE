'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  getStandardDetail,
  getStandardVersions,
  getStandardRelationships,
  getStandardCompliance,
  getStandardGraph,
  StandardDetail,
  VersionReport,
  RelationshipEdge,
  ComplianceReport,
  DependencyGraph,
} from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface StandardViewProps {
  initialStandardId?: string;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const QUICK_STANDARDS = [
  'IS 12615:2018',
  'IS 694:2010',
  'IS 732:2019',
  'IS 10500:2012',
  'IS 3043:2018',
  'IS 15652:2006',
];

export const StandardView: React.FC<StandardViewProps> = ({ initialStandardId = 'IS 12615:2018', onToast }) => {
  const [standardInput, setStandardInput] = useState(initialStandardId);
  const [selectedStandard, setSelectedStandard] = useState(initialStandardId);
  const [isLoading, setIsLoading] = useState(false);

  const [detail, setDetail] = useState<StandardDetail | null>(null);
  const [versions, setVersions] = useState<VersionReport | null>(null);
  const [relationships, setRelationships] = useState<RelationshipEdge[]>([]);
  const [compliance, setCompliance] = useState<ComplianceReport | null>(null);
  const [graph, setGraph] = useState<DependencyGraph | null>(null);

  const fetchAllData = async (stdId?: string) => {
    if (!stdId || typeof stdId !== 'string' || !stdId.trim()) return;
    setIsLoading(true);
    try {
      const [detailRes, versionRes, relsRes, compRes, graphRes] = await Promise.allSettled([
        getStandardDetail(stdId),
        getStandardVersions(stdId),
        getStandardRelationships(stdId),
        getStandardCompliance(stdId),
        getStandardGraph(stdId, 2),
      ]);

      if (detailRes.status === 'fulfilled') setDetail(detailRes.value);
      else setDetail(null);

      if (versionRes.status === 'fulfilled') setVersions(versionRes.value);
      else setVersions(null);

      if (relsRes.status === 'fulfilled') setRelationships(relsRes.value);
      else setRelationships([]);

      if (compRes.status === 'fulfilled') setCompliance(compRes.value);
      else setCompliance(null);

      if (graphRes.status === 'fulfilled') setGraph(graphRes.value);
      else setGraph(null);

      if (detailRes.status === 'rejected') {
        onToast(`Could not load full record for "${stdId}". Showing available graph data.`, 'info');
      }
    } catch (err: any) {
      onToast(err.message || 'Failed to query standards repository.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialStandardId) {
      setStandardInput(initialStandardId);
      setSelectedStandard(initialStandardId);
      fetchAllData(initialStandardId);
    }
  }, [initialStandardId]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!standardInput.trim()) return;
    setSelectedStandard(standardInput.trim());
    fetchAllData(standardInput.trim());
  };

  const handleSelectQuick = (stdId?: string) => {
    if (!stdId || typeof stdId !== 'string' || !stdId.trim()) return;
    const clean = stdId.trim();
    setStandardInput(clean);
    setSelectedStandard(clean);
    fetchAllData(clean);
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Standards Intelligence Explorer"
        subtitle="Canonical Bureau of Indian Standards lifecycle tracing, multi-version lineage, compliance mandates, and graph edges."
        badge="Standards Explorer"
      >
        {/* Search Input & Quick Select */}
        <form onSubmit={handleSearch} style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '260px' }}>
              <input
                type="text"
                value={standardInput}
                onChange={(e) => setStandardInput(e.target.value)}
                placeholder="Enter IS identifier (e.g. IS 12615:2018, IS 694, IS 10500)..."
                required
                style={{ fontSize: '0.94rem' }}
              />
            </div>
            <button type="submit" disabled={isLoading} className="btn-primary" style={{ padding: '11px 24px' }}>
              {isLoading ? 'Exploring...' : '🏛️ Query Standard'}
            </button>
          </div>
        </form>

        {/* Quick Pick Chips */}
        <div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
            Common Indian Standards:
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {QUICK_STANDARDS.map((std) => (
              <button
                key={std}
                type="button"
                onClick={() => handleSelectQuick(std)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-full)',
                  background: selectedStandard === std ? 'rgba(79, 70, 229, 0.08)' : '#f8fafc',
                  border: `1px solid ${selectedStandard === std ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                  color: selectedStandard === std ? 'var(--accent-primary-dark)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {std}
              </button>
            ))}
          </div>
        </div>
      </Panel>

      {/* Loading Skeleton */}
      {isLoading && (
        <div>
          <Panel title="Querying Knowledge Graph...">
            <LoadingSkeleton height="40px" width="50%" />
            <LoadingSkeleton height="20px" width="90%" />
            <LoadingSkeleton height="20px" width="70%" />
          </Panel>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            <Panel><LoadingSkeleton height="120px" /></Panel>
            <Panel><LoadingSkeleton height="120px" /></Panel>
          </div>
        </div>
      )}

      {/* Loaded Content */}
      {!isLoading && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          {/* Main Standard Header Card */}
          <div
            className="glass-panel"
            style={{
              padding: '24px 26px',
              marginBottom: '22px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <h2
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '1.4rem',
                      fontWeight: 800,
                      color: 'var(--text-primary)',
                      letterSpacing: '-0.01em',
                    }}
                  >
                    {detail?.standard_id || selectedStandard}
                  </h2>
                  {detail?.status && (
                    <span
                      className={`badge ${
                        detail.status.toUpperCase().includes('ACTIVE') || detail.status.toUpperCase().includes('VALID')
                          ? 'badge-green'
                          : 'badge-amber'
                      }`}
                    >
                      {detail.status}
                    </span>
                  )}
                  {detail?.is_mandatory && <span className="badge badge-red">QCO MANDATORY</span>}
                  {detail?.technical_department && (
                    <span className="badge badge-indigo">{detail.technical_department}</span>
                  )}
                </div>

                <h3
                  style={{
                    fontSize: '1.05rem',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    marginTop: '8px',
                    lineHeight: 1.5,
                  }}
                >
                  {detail?.title || 'Authoritative Indian Standard Specification'}
                </h3>
              </div>

              {/* Scope & Date Meta */}
              <div style={{ textAlign: 'right', minWidth: '150px' }}>
                {detail?.publication_year && (
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Published: <strong style={{ color: 'var(--text-secondary)' }}>{detail.publication_year}</strong>
                  </div>
                )}
                {detail?.ics_code && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    ICS Code: <strong style={{ color: 'var(--text-secondary)' }}>{detail.ics_code}</strong>
                  </div>
                )}
                {detail?.page_count && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Pages: <strong style={{ color: 'var(--text-secondary)' }}>{detail.page_count}</strong>
                  </div>
                )}
              </div>
            </div>

            {/* Scope / Description */}
            {detail?.scope && (
              <div
                style={{
                  marginTop: '16px',
                  padding: '14px 16px',
                  background: '#f8fafc',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.88rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.6,
                }}
              >
                <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '4px' }}>
                  Authoritative Scope:
                </strong>
                {detail.scope}
              </div>
            )}
          </div>

          {/* Bento-grid: Version Intelligence & Compliance */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '20px',
              marginBottom: '22px',
            }}
          >
            {/* Version Intelligence */}
            <div className="glass-panel" style={{ padding: '22px', background: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <span style={{ fontSize: '1.2rem' }}>🔄</span>
                <h4 style={{ fontSize: '1.02rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Version & Supersession Lineage
                </h4>
              </div>

              {versions ? (
                <div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: versions.is_current ? 'rgba(5, 150, 105, 0.08)' : 'rgba(245, 158, 11, 0.08)',
                      border: `1px solid ${versions.is_current ? 'rgba(5, 150, 105, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
                      marginBottom: '14px',
                    }}
                  >
                    <span style={{ fontSize: '1.25rem' }}>{versions.is_current ? '✅' : '⚠️'}</span>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                        {versions.is_current ? 'Current & Valid Version' : 'Superseded / Outdated Version'}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Catalog Status: {versions.current_status}
                      </div>
                    </div>
                  </div>

                  {versions.successor_standard_id && (
                    <div style={{ marginBottom: '12px', fontSize: '0.86rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Successor Standard: </span>
                      <button
                        onClick={() => handleSelectQuick(versions.successor_standard_id!)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--accent-primary)',
                          fontWeight: 700,
                          cursor: 'pointer',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.86rem',
                        }}
                      >
                        {versions.successor_standard_id} ↗
                      </button>
                    </div>
                  )}

                  {versions.predecessor_standard_id && (
                    <div style={{ marginBottom: '12px', fontSize: '0.86rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Predecessor Standard: </span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>
                        {versions.predecessor_standard_id}
                      </span>
                    </div>
                  )}

                  {/* Amendment Records */}
                  <div style={{ marginTop: '16px', borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                      <span style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                        Recorded Amendments ({versions.amendments?.length || 0})
                      </span>
                    </div>

                    {versions.amendments && versions.amendments.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {versions.amendments.map((amd, idx) => {
                          const amdNum = amd.amendment_number ?? amd.number ?? idx + 1;
                          const amdYear = amd.amendment_year ?? amd.year;
                          const desc = amd.change_description || amd.notes;
                          const state = amd.current_state || 'RECORDED';

                          return (
                            <div
                              key={amd.id || idx}
                              style={{
                                padding: '10px 12px',
                                background: '#f8fafc',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid #e2e8f0',
                                fontSize: '0.82rem',
                              }}
                            >
                              <div
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  marginBottom: desc ? '4px' : '0',
                                }}
                              >
                                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                                  Amendment {amdNum}
                                  {amdYear ? (
                                    <span style={{ fontWeight: 500, color: 'var(--text-muted)', marginLeft: '6px' }}>
                                      ({amdYear})
                                    </span>
                                  ) : null}
                                </span>
                                {state && (
                                  <span
                                    style={{
                                      fontSize: '0.7rem',
                                      fontWeight: 600,
                                      padding: '2px 8px',
                                      borderRadius: '999px',
                                      background:
                                        state.toUpperCase() === 'CURRENT' || state.toUpperCase() === 'ACTIVE'
                                          ? 'rgba(5, 150, 105, 0.1)'
                                          : 'rgba(100, 116, 139, 0.1)',
                                      color:
                                        state.toUpperCase() === 'CURRENT' || state.toUpperCase() === 'ACTIVE'
                                          ? 'var(--status-success)'
                                          : 'var(--text-muted)',
                                    }}
                                  >
                                    {state}
                                  </span>
                                )}
                              </div>
                              {desc && (
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.78rem', lineHeight: 1.4 }}>
                                  {desc}
                                </div>
                              )}
                              {amd.source_dataset && (
                                <div style={{ marginTop: '4px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                  Dataset: {amd.source_dataset}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                        No amendments cataloged for this standard in the supplied dataset.
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No version records available.</p>
              )}
            </div>

            {/* Compliance Intelligence */}
            <div className="glass-panel" style={{ padding: '22px', background: '#ffffff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <span style={{ fontSize: '1.2rem' }}>🛡️</span>
                <h4 style={{ fontSize: '1.02rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Regulatory Compliance & QCO Mandates
                </h4>
              </div>

              {compliance ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px', flexWrap: 'wrap' }}>
                    <span
                      className={`badge ${
                        compliance.requirement_level === 'MANDATORY'
                          ? 'badge-red'
                          : compliance.requirement_level === 'CONDITIONAL'
                          ? 'badge-amber'
                          : 'badge-indigo'
                      }`}
                    >
                      {compliance.requirement_level} COMPLIANCE
                    </span>
                    {compliance.governing_scheme && (
                      <span className="badge badge-cyan">{compliance.governing_scheme}</span>
                    )}
                  </div>

                  {compliance.qco_records && compliance.qco_records.length > 0 ? (
                    <div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                        Active Quality Control Orders (QCOs):
                      </div>
                      {compliance.qco_records.map((qco, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: '10px 14px',
                            background: '#f8fafc',
                            borderRadius: 'var(--radius-sm)',
                            border: '1px solid #e2e8f0',
                            marginBottom: '6px',
                            fontSize: '0.82rem',
                          }}
                        >
                          <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{qco.order_number || qco.qco_id || 'QCO'}</div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.76rem', marginTop: '2px' }}>{qco.title || qco.qco_title}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                      No mandatory QCO orders cataloged. Governed by voluntary BIS certification schemes.
                    </div>
                  )}

                  {compliance.regulatory_divergence_detected && (
                    <div
                      style={{
                        marginTop: '12px',
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(220, 38, 38, 0.08)',
                        border: '1px solid rgba(220, 38, 38, 0.25)',
                        fontSize: '0.8rem',
                        color: 'var(--status-danger)',
                      }}
                    >
                      ⚠️ Regulatory Divergence Detected: Scope or harmonized international standard differs.
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No compliance data found.</p>
              )}
            </div>
          </div>

          {/* Relationships & Ontology Links */}
          <div className="glass-panel" style={{ padding: '24px', background: '#ffffff' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>🕸️</span>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Ontology Relationships ({relationships.length})
                </h4>
              </div>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Direct graph edges & testing/safety linkages
              </span>
            </div>

            {relationships.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
                {relationships.map((rel, idx) => {
                  const targetIdentifier =
                    rel.target ||
                    rel.target_standard_id ||
                    rel.target_id ||
                    (rel.target_standard_number ? `IS ${rel.target_standard_number}` : '');
                  const isClickable = Boolean(
                    targetIdentifier &&
                    typeof targetIdentifier === 'string' &&
                    !targetIdentifier.startsWith('unresolved:')
                  );
                  return (
                    <div
                      key={idx}
                      className={isClickable ? 'glass-panel-interactive' : 'glass-panel'}
                      onClick={() => isClickable && handleSelectQuick(targetIdentifier)}
                      style={{
                        padding: '14px 16px',
                        borderRadius: 'var(--radius-md)',
                        background: '#f8fafc',
                        border: '1px solid #e2e8f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        cursor: isClickable ? 'pointer' : 'default',
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '6px' }}>
                          <span className="badge badge-indigo" style={{ fontSize: '0.68rem' }}>
                            {rel.relationship_type}
                          </span>
                          {rel.is_unresolved && (
                            <span className="badge badge-amber" style={{ fontSize: '0.65rem' }}>
                              Unresolved
                            </span>
                          )}
                        </div>
                        <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
                          {targetIdentifier || 'IS Standard'}
                        </div>
                        {rel.target_title && (
                          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                            {rel.target_title}
                          </div>
                        )}
                      </div>
                      {isClickable && <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 700 }}>↗</span>}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No direct ontology links recorded for this standard.</p>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};
