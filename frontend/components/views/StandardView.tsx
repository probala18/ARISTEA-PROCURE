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

  const fetchAllData = async (stdId: string) => {
    if (!stdId.trim()) return;
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
        onToast(`Standard '${stdId}' not found or error fetching details.`, 'error');
      } else {
        onToast(`Loaded standard intelligence for ${stdId}`, 'success');
      }
    } catch (err: any) {
      onToast(err.message || 'Error fetching standard data.', 'error');
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
    setSelectedStandard(standardInput);
    fetchAllData(standardInput);
  };

  const handleSelectQuick = (stdId: string) => {
    setStandardInput(stdId);
    setSelectedStandard(stdId);
    fetchAllData(stdId);
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Indian Standards Explorer & Knowledge Graph"
        subtitle="Lookup canonical BIS records, supersession lineage, QCO regulatory compliance, and multi-hop relationships."
        badge="Module 7 & 8"
      >
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
          <input
            type="text"
            value={standardInput}
            onChange={(e) => setStandardInput(e.target.value)}
            placeholder="Enter standard ID (e.g. IS 12615:2018, IS 694)..."
            style={{ flex: 1 }}
            required
          />
          <button type="submit" disabled={isLoading} className="btn-primary" style={{ minWidth: '140px' }}>
            {isLoading ? 'Loading...' : 'Explore ↗'}
          </button>
        </form>

        {/* Quick pills */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Quick Standards:</span>
          {QUICK_STANDARDS.map((std) => (
            <button
              key={std}
              type="button"
              onClick={() => handleSelectQuick(std)}
              style={{
                padding: '4px 10px',
                borderRadius: 'var(--radius-full)',
                background: selectedStandard === std ? 'rgba(20, 184, 166, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                border: selectedStandard === std ? '1px solid var(--accent-teal)' : '1px solid rgba(255, 255, 255, 0.08)',
                color: selectedStandard === std ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '0.78rem',
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
              }}
            >
              {std}
            </button>
          ))}
        </div>
      </Panel>

      {isLoading && (
        <Panel title={`Retrieving intelligence for ${selectedStandard}...`}>
          <LoadingSkeleton height="80px" />
          <LoadingSkeleton height="120px" />
          <LoadingSkeleton height="100px" />
        </Panel>
      )}

      {!isLoading && detail && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          {/* Header Card */}
          <div
            className="glass-panel"
            style={{
              padding: '24px',
              marginBottom: '20px',
              borderLeft: '4px solid var(--accent-teal)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '1.4rem',
                      fontWeight: 800,
                      color: '#ffffff',
                    }}
                  >
                    {detail.standard_id}
                  </span>
                  <span
                    className={`badge ${
                      detail.status?.toLowerCase().includes('active') || detail.status?.toLowerCase().includes('valid')
                        ? 'badge-teal'
                        : 'badge-orange'
                    }`}
                  >
                    {detail.status || 'ACTIVE'}
                  </span>
                </div>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '8px' }}>
                  {detail.title}
                </h2>
              </div>

              <div style={{ display: 'flex', gap: '16px', textAlign: 'right' }}>
                {detail.publication_year && (
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>YEAR</span>
                    <span style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      {detail.publication_year}
                    </span>
                  </div>
                )}
                {detail.category && (
                  <div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>CATEGORY</span>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-teal)' }}>
                      {detail.category}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Grid: Version & Compliance */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
              gap: '20px',
              marginBottom: '20px',
            }}
          >
            {/* Version Intelligence */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <span style={{ fontSize: '1.1rem' }}>🔄</span>
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Version & Supersession Intelligence</h4>
              </div>

              {versions ? (
                <div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-sm)',
                      background: versions.is_current ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                      border: `1px solid ${versions.is_current ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                      marginBottom: '14px',
                    }}
                  >
                    <span style={{ fontSize: '1.2rem' }}>{versions.is_current ? '✅' : '⚠️'}</span>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                        {versions.is_current ? 'Current & Valid Version' : 'Superseded / Outdated Version'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Status: {versions.current_status}
                      </div>
                    </div>
                  </div>

                  {versions.successor_standard_id && (
                    <div style={{ marginBottom: '12px', fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Successor Standard: </span>
                      <button
                        onClick={() => handleSelectQuick(versions.successor_standard_id!)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'var(--accent-teal)',
                          fontWeight: 700,
                          cursor: 'pointer',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {versions.successor_standard_id} ↗
                      </button>
                    </div>
                  )}

                  {versions.predecessor_standard_id && (
                    <div style={{ marginBottom: '12px', fontSize: '0.85rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Predecessor Standard: </span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        {versions.predecessor_standard_id}
                      </span>
                    </div>
                  )}

                  <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Total Amendments Recorded: {versions.total_amendments || 0}
                  </div>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No version records available.</p>
              )}
            </div>

            {/* Compliance Intelligence */}
            <div className="glass-panel" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <span style={{ fontSize: '1.1rem' }}>🛡️</span>
                <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Regulatory Compliance & QCO Mandates</h4>
              </div>

              {compliance ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                    <span
                      className={`badge ${
                        compliance.requirement_level === 'MANDATORY'
                          ? 'badge-red'
                          : compliance.requirement_level === 'CONDITIONAL'
                          ? 'badge-orange'
                          : 'badge-teal'
                      }`}
                    >
                      {compliance.requirement_level} COMPLIANCE
                    </span>
                    {compliance.governing_scheme && (
                      <span className="badge badge-blue">{compliance.governing_scheme}</span>
                    )}
                  </div>

                  {compliance.qco_orders && compliance.qco_orders.length > 0 ? (
                    <div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                        Active Quality Control Orders (QCOs):
                      </div>
                      {compliance.qco_orders.map((qco, idx) => (
                        <div
                          key={idx}
                          style={{
                            padding: '8px 12px',
                            background: 'rgba(255, 255, 255, 0.04)',
                            borderRadius: 'var(--radius-sm)',
                            marginBottom: '6px',
                            fontSize: '0.8rem',
                          }}
                        >
                          <div style={{ fontWeight: 600, color: '#ffffff' }}>{qco.order_number}</div>
                          <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{qco.title}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                      No mandatory QCO orders cataloged. Governed by voluntary BIS certification schemes.
                    </div>
                  )}

                  {compliance.divergence_detected && (
                    <div
                      style={{
                        marginTop: '12px',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        fontSize: '0.78rem',
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
          <div className="glass-panel" style={{ padding: '22px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.1rem' }}>🕸️</span>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700 }}>
                  Ontology Relationships ({relationships.length})
                </h4>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Direct edges & testing/safety linkages
              </span>
            </div>

            {relationships.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px' }}>
                {relationships.map((rel, idx) => (
                  <div
                    key={idx}
                    className="glass-panel-interactive"
                    onClick={() => handleSelectQuick(rel.target)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(15, 23, 42, 0.6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <span className="badge badge-blue" style={{ fontSize: '0.68rem', marginBottom: '4px' }}>
                        {rel.relationship_type}
                      </span>
                      <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.9rem', color: '#ffffff' }}>
                        {rel.target}
                      </div>
                    </div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>↗</span>
                  </div>
                ))}
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
