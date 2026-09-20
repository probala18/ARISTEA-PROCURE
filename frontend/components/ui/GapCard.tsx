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
        return 'rgba(239, 68, 68, 0.4)';
      case 'WARNING':
        return 'rgba(245, 158, 11, 0.35)';
      case 'INFO':
      default:
        return 'rgba(56, 189, 248, 0.25)';
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
        borderLeft: `4px solid ${gap.severity === 'CRITICAL' ? '#ef4444' : gap.severity === 'WARNING' ? '#f59e0b' : '#38bdf8'}`,
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
            background: 'rgba(15, 23, 42, 0.6)',
            borderRadius: 'var(--radius-sm)',
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
            borderLeft: '2px solid rgba(255, 255, 255, 0.1)',
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
          background: 'rgba(20, 184, 166, 0.08)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(20, 184, 166, 0.2)',
          fontSize: '0.83rem',
          color: 'var(--text-primary)',
        }}
      >
        <strong style={{ color: 'var(--accent-teal)' }}>Grounding Advice: </strong>
        {gap.recommendation_notes}
      </div>
    </div>
  );
};
