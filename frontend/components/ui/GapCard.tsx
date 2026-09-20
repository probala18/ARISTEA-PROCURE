'use client';

import React, { useRef, useEffect } from 'react';
import { TenderAuditGap } from '@/lib/api';
import { pulseAttention } from '@/lib/gsap-animations';

interface GapCardProps {
  gap: TenderAuditGap;
  index: number;
}

export const GapCard: React.FC<GapCardProps> = ({ gap, index }) => {
  const cardRef = useRef<HTMLDivElement>(null);

  const severityUpper = (gap.severity || 'INFO').toUpperCase();

  useEffect(() => {
    if (severityUpper === 'CRITICAL' && cardRef.current) {
      pulseAttention(cardRef.current);
    }
  }, [severityUpper]);

  const getSeverityBadge = () => {
    switch (severityUpper) {
      case 'CRITICAL':
        return <span className="badge badge-red">CRITICAL GAP</span>;
      case 'WARNING':
        return <span className="badge badge-amber">WARNING</span>;
      case 'ADVISORY':
      case 'INFO':
      default:
        return <span className="badge badge-cyan">ADVISORY</span>;
    }
  };

  const getSeverityBorderColor = () => {
    switch (severityUpper) {
      case 'CRITICAL':
        return 'var(--status-danger)';
      case 'WARNING':
        return 'var(--status-warning)';
      case 'ADVISORY':
      case 'INFO':
      default:
        return 'var(--accent-primary)';
    }
  };

  const gapLabel = String(gap.gap_category || gap.gap_type || gap.issue_description || 'OBSERVATION').replace(/_/g, ' ');
  const clauseLabel = gap.clause_reference || (gap.requirement_id !== undefined ? `#${gap.requirement_id}` : null);
  const adviceNotes = gap.recommendation || gap.recommendation_notes || gap.issue_description || 'Review requirement and update to current Indian Standard.';
  const citedStd = gap.standard_id || gap.cited_standard;
  const expectedStd = gap.successor_standard_id || gap.expected_standard;

  return (
    <div
      ref={cardRef}
      className="glass-panel"
      style={{
        padding: '20px 22px',
        marginBottom: '14px',
        borderRadius: 'var(--radius-md)',
        background: '#ffffff',
        border: '1px solid var(--border-subtle)',
        borderLeft: `4px solid ${getSeverityBorderColor()}`,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {getSeverityBadge()}
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.88rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
            }}
          >
            {gapLabel}
          </span>
        </div>
        {clauseLabel && (
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
            Clause {clauseLabel}
          </span>
        )}
      </div>

      {/* Cited vs Expected standards comparison if available */}
      {(citedStd || expectedStd) && (
        <div
          style={{
            display: 'flex',
            gap: '20px',
            margin: '12px 0',
            padding: '12px 16px',
            background: '#f8fafc',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid #e2e8f0',
            fontSize: '0.85rem',
            flexWrap: 'wrap',
          }}
        >
          {citedStd && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block', fontWeight: 600, textTransform: 'uppercase' }}>CITED IN TENDER:</span>
              <span style={{ color: 'var(--status-danger)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                {citedStd}
              </span>
            </div>
          )}
          {expectedStd && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block', fontWeight: 600, textTransform: 'uppercase' }}>EXPECTED / CURRENT:</span>
              <span style={{ color: 'var(--status-success)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                {expectedStd}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Clause Text */}
      {gap.clause_text && (
        <div
          style={{
            fontSize: '0.875rem',
            color: 'var(--text-secondary)',
            fontStyle: 'italic',
            borderLeft: '2px solid #cbd5e1',
            paddingLeft: '12px',
            margin: '12px 0',
            lineHeight: 1.5,
          }}
        >
          "{gap.clause_text}"
        </div>
      )}

      {/* Remediation Note */}
      <div
        style={{
          marginTop: '12px',
          padding: '10px 14px',
          background: 'var(--accent-primary-subtle)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(79, 70, 229, 0.2)',
          fontSize: '0.84rem',
          color: 'var(--text-primary)',
          lineHeight: 1.5,
        }}
      >
        <strong style={{ color: 'var(--accent-primary-dark)' }}>Grounding Advice: </strong>
        {adviceNotes}
      </div>
    </div>
  );
};
