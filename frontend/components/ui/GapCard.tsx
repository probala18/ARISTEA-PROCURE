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
        return <span className="badge badge-orange">WARNING</span>;
      case 'ADVISORY':
      case 'INFO':
      default:
        return <span className="badge badge-blue">ADVISORY</span>;
    }
  };

  const getSeverityBorder = () => {
    switch (severityUpper) {
      case 'CRITICAL':
        return 'rgba(220, 38, 38, 0.4)';
      case 'WARNING':
        return 'rgba(217, 119, 6, 0.4)';
      case 'ADVISORY':
      case 'INFO':
      default:
        return 'rgba(2, 132, 199, 0.35)';
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
        padding: '18px 20px',
        marginBottom: '14px',
        borderRadius: 'var(--radius-md)',
        borderLeft: `4px solid ${severityUpper === 'CRITICAL' ? '#dc2626' : severityUpper === 'WARNING' ? '#d97706' : '#0284c7'}`,
        borderColor: getSeverityBorder(),
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {getSeverityBadge()}
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.85rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
            }}
          >
            {gapLabel}
          </span>
        </div>
        {clauseLabel && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            Clause {clauseLabel}
          </span>
        )}
      </div>

      {/* Cited vs Expected standards comparison if available */}
      {(citedStd || expectedStd) && (
        <div
          style={{
            display: 'flex',
            gap: '16px',
            margin: '10px 0',
            padding: '10px 14px',
            background: 'rgba(241, 245, 249, 0.95)',
            borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.85rem',
          }}
        >
          {citedStd && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>CITED IN TENDER:</span>
              <span style={{ color: 'var(--status-danger)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                {citedStd}
              </span>
            </div>
          )}
          {expectedStd && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>EXPECTED / CURRENT:</span>
              <span style={{ color: 'var(--status-success)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
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
            fontSize: '0.86rem',
            color: 'var(--text-secondary)',
            fontStyle: 'italic',
            borderLeft: '2px solid var(--border-subtle)',
            paddingLeft: '10px',
            margin: '10px 0',
          }}
        >
          "{gap.clause_text}"
        </div>
      )}

      {/* Remediation Note */}
      <div
        style={{
          marginTop: '10px',
          padding: '8px 12px',
          background: 'rgba(13, 148, 136, 0.08)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(13, 148, 136, 0.22)',
          fontSize: '0.83rem',
          color: 'var(--text-primary)',
        }}
      >
        <strong style={{ color: 'var(--accent-teal-dark)' }}>Grounding Advice: </strong>
        {adviceNotes}
      </div>
    </div>
  );
};
