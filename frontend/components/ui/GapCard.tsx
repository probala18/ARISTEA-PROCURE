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

  useEffect(() => {
    if (gap.severity === 'CRITICAL' && cardRef.current) {
      pulseAttention(cardRef.current);
    }
  }, [gap.severity]);

  const getSeverityBadge = () => {
    switch (gap.severity) {
      case 'CRITICAL':
        return <span className="badge badge-red">CRITICAL GAP</span>;
      case 'WARNING':
        return <span className="badge badge-orange">WARNING</span>;
      case 'INFO':
      default:
        return <span className="badge badge-blue">ADVISORY</span>;
    }
  };

  const getSeverityBorder = () => {
    switch (gap.severity) {
      case 'CRITICAL':
        return 'rgba(220, 38, 38, 0.4)';
      case 'WARNING':
        return 'rgba(217, 119, 6, 0.4)';
      case 'INFO':
      default:
        return 'rgba(2, 132, 199, 0.35)';
    }
  };

  return (
    <div
      ref={cardRef}
      className="glass-panel"
      style={{
        padding: '18px 20px',
        marginBottom: '14px',
        borderRadius: 'var(--radius-md)',
        borderLeft: `4px solid ${gap.severity === 'CRITICAL' ? '#dc2626' : gap.severity === 'WARNING' ? '#d97706' : '#0284c7'}`,
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
            {gap.gap_type.replace(/_/g, ' ')}
          </span>
        </div>
        {gap.requirement_id && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            Clause #{gap.requirement_id}
          </span>
        )}
      </div>

      {/* Cited vs Expected standards comparison if available */}
      {(gap.cited_standard || gap.expected_standard) && (
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
          {gap.cited_standard && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>CITED IN TENDER:</span>
              <span style={{ color: 'var(--status-danger)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                {gap.cited_standard}
              </span>
            </div>
          )}
          {gap.expected_standard && (
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem', display: 'block' }}>EXPECTED / CURRENT:</span>
              <span style={{ color: 'var(--status-success)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                {gap.expected_standard}
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
        {gap.recommendation_notes}
      </div>
    </div>
  );
};
