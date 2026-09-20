'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { getStandardCompliance, ComplianceReport } from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface ComplianceViewProps {
  initialStandardId?: string;
  onExploreStandard?: (standardId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const COMMON_QCO_STANDARDS = [
  'IS 12615:2018',
  'IS 694:2010',
  'IS 3043:2018',
  'IS 15652:2006',
  'IS 10500:2012',
  'IS 732:2019',
];

export const ComplianceView: React.FC<ComplianceViewProps> = ({
  initialStandardId = 'IS 12615:2018',
  onExploreStandard,
  onToast,
}) => {
  const [standardInput, setStandardInput] = useState(initialStandardId);
  const [activeStandard, setActiveStandard] = useState(initialStandardId);
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<ComplianceReport | null>(null);

  const fetchCompliance = async (stdId: string) => {
    if (!stdId.trim()) return;
    setIsLoading(true);
    try {
      const data = await getStandardCompliance(stdId.trim());
      setReport(data);
      setActiveStandard(stdId.trim());
      onToast(`Compliance intelligence loaded for ${stdId.trim()}`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Failed to fetch compliance report.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialStandardId) {
      setStandardInput(initialStandardId);
      fetchCompliance(initialStandardId);
    }
  }, [initialStandardId]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCompliance(standardInput);
  };

  const getRequirementBadge = (level: string) => {
    switch (level?.toUpperCase()) {
      case 'MANDATORY':
        return <span className="badge badge-red">MANDATORY COMPLIANCE</span>;
      case 'CONDITIONAL':
        return <span className="badge badge-amber">CONDITIONAL COMPLIANCE</span>;
      case 'VOLUNTARY':
        return <span className="badge badge-indigo">VOLUNTARY SPECIFICATION</span>;
      default:
        return <span className="badge badge-cyan">UNKNOWN STATUS</span>;
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Compliance & Quality Control Orders (QCO) Matrix"
        subtitle="Authoritative regulatory status, ministry Quality Control Orders, mandatory BIS certification schemes, and divergence detection."
        badge="Module 9 Compliance"
      >
        {/* Search Input */}
        <form onSubmit={handleSubmit} style={{ marginBottom: '18px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '260px' }}>
              <input
                type="text"
                value={standardInput}
                onChange={(e) => setStandardInput(e.target.value)}
                placeholder="Enter Indian Standard identifier (e.g. IS 12615:2018, IS 694)..."
                required
              />
            </div>
            <button type="submit" disabled={isLoading} className="btn-primary" style={{ padding: '11px 24px' }}>
              {isLoading ? 'Verifying...' : '🛡️ Check Compliance'}
            </button>
          </div>
        </form>

        {/* Quick Presets */}
        <div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
            Common Regulated Standards:
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {COMMON_QCO_STANDARDS.map((std) => (
              <button
                key={std}
                type="button"
                onClick={() => {
                  setStandardInput(std);
                  fetchCompliance(std);
                }}
                style={{
                  padding: '5px 12px',
                  borderRadius: 'var(--radius-full)',
                  background: activeStandard === std ? 'var(--accent-primary-subtle)' : '#f8fafc',
                  border: `1px solid ${activeStandard === std ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                  color: activeStandard === std ? 'var(--accent-primary-dark)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.76rem',
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

      {/* Loading */}
      {isLoading && (
        <Panel title="Querying Regulatory Intelligence Database...">
          <LoadingSkeleton height="80px" />
          <LoadingSkeleton height="140px" />
        </Panel>
      )}

      {/* Report Content */}
      {!isLoading && report && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          {/* Header Summary Card */}
          <div
            className="glass-panel"
            style={{
              padding: '24px 26px',
              marginBottom: '20px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    {report.standard_id}
                  </span>
                  {getRequirementBadge(report.requirement_level)}
                  <span className="badge badge-indigo">
                    Scheme: {report.governing_scheme}
                  </span>
                  {report.qco_applicable && (
                    <span className="badge badge-red">QCO Enforced</span>
                  )}
                </div>

                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '8px' }}>
                  {report.title || 'Official Bureau of Indian Standards Specification'}
                </h3>
              </div>

              {onExploreStandard && (
                <button
                  onClick={() => onExploreStandard(report.standard_id)}
                  className="btn-secondary"
                  style={{ fontSize: '0.8rem', padding: '6px 14px' }}
                >
                  Explore in Detail ↗
                </button>
              )}
            </div>

            {/* Statutory Disclaimer */}
            <div
              style={{
                marginTop: '16px',
                padding: '12px 16px',
                background: '#f8fafc',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid #e2e8f0',
                fontSize: '0.8rem',
                color: 'var(--text-secondary)',
                lineHeight: 1.55,
              }}
            >
              <strong style={{ color: 'var(--text-primary)' }}>Notice: </strong>
              {report.disclaimer}
            </div>
          </div>

          {/* Quality Control Orders Table */}
          <div
            className="glass-panel"
            style={{
              padding: '24px',
              marginBottom: '20px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <span style={{ fontSize: '1.2rem' }}>📜</span>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                Applicable Quality Control Orders ({report.qco_records?.length || 0})
              </h4>
            </div>

            {report.qco_records && report.qco_records.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {report.qco_records.map((qco, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 18px',
                      background: '#f8fafc',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid #e2e8f0',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary-dark)', fontSize: '0.92rem' }}>
                        {qco.order_number || qco.order_title || 'Statutory Quality Control Order'}
                      </span>
                      {qco.effective_date && (
                        <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
                          Effective: <strong>{qco.effective_date}</strong>
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {qco.title || qco.description || 'Mandates compulsory certification under Bureau of Indian Standards Act.'}
                    </p>
                    {qco.ministry && (
                      <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Notified by: <strong>{qco.ministry}</strong>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '20px', background: '#f8fafc', borderRadius: 'var(--radius-sm)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
                No mandatory Quality Control Orders currently cataloged for this standard in the project dataset. Governed by voluntary certification schemes.
              </div>
            )}
          </div>

          {/* Divergences & Special Observations */}
          {report.regulatory_divergence_detected && (
            <div
              className="glass-panel"
              style={{
                padding: '20px 24px',
                background: 'rgba(220, 38, 38, 0.05)',
                border: '1px solid rgba(220, 38, 38, 0.25)',
                borderRadius: 'var(--radius-lg)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '1.2rem' }}>⚠️</span>
                <h4 style={{ fontSize: '0.98rem', fontWeight: 800, color: 'var(--status-danger)' }}>
                  Regulatory Divergence Detected
                </h4>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                Differences exist between the Indian Standard and international harmonized equivalents (ISO/IEC).
                Review is recommended against the specific Indian Standard test requirements cited in the tender.
              </p>
              {report.regulatory_divergence_notes && report.regulatory_divergence_notes.length > 0 && (
                <ul style={{ marginTop: '8px', paddingLeft: '18px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                  {report.regulatory_divergence_notes.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
};
