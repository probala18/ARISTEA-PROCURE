'use client';

import React from 'react';
import { StandardRedlineMapping } from '@/lib/api';

interface StandardsMigrationCardProps {
  mappings: StandardRedlineMapping[];
  onApplyFix?: (oldStandard: string, newStandard: string) => void;
}

export const StandardsMigrationCard: React.FC<StandardsMigrationCardProps> = ({
  mappings,
  onApplyFix,
}) => {
  // Filter out any dummy / placeholder entries
  const validMappings = (mappings || []).filter(
    (item) => item.old_standard !== 'No Outdated Standards' && item.old_status !== 'ALL CLEAR'
  );

  if (validMappings.length === 0) {
    return (
      <div
        style={{
          marginTop: '20px',
          marginBottom: '24px',
          padding: '18px 22px',
          background: '#f0fdf4',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #bbf7d0',
          boxShadow: '0 2px 8px rgba(16, 185, 129, 0.06)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>✅</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.02rem', fontWeight: 700, color: '#166534' }}>
                Standard Supersession & Migration Roadmap
              </h3>
              <p style={{ margin: '2px 0 0', fontSize: '0.84rem', color: '#15803d' }}>
                All cited technical requirements adhere to active Indian Standards. No superseded standards detected.
              </p>
            </div>
          </div>
          <span
            style={{
              padding: '4px 12px',
              borderRadius: '999px',
              background: '#dcfce7',
              color: '#166534',
              fontWeight: 700,
              fontSize: '0.78rem',
              border: '1px solid #86efac',
            }}
          >
            0 Outdated Standards • All Compliant
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        marginTop: '20px',
        marginBottom: '24px',
        padding: '20px',
        background: '#ffffff',
        borderRadius: 'var(--radius-lg, 12px)',
        border: '1px solid #e2e8f0',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.4rem' }}>🔄</span>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
              Standard Supersession & Migration Roadmap
            </h3>
          </div>
        </div>
        <span
          style={{
            padding: '4px 12px',
            borderRadius: '999px',
            background: 'rgba(220, 38, 38, 0.1)',
            color: '#dc2626',
            fontWeight: 700,
            fontSize: '0.78rem',
            border: '1px solid rgba(220, 38, 38, 0.25)',
          }}
        >
          {validMappings.length} Outdated Standard{validMappings.length > 1 ? 's' : ''} Requiring Migration
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {validMappings.map((item, idx) => (
          <div
            key={idx}
            style={{
              padding: '16px',
              borderRadius: '10px',
              background: '#f8fafc',
              border: '1px solid #e2e8f0',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {/* Top row: Red Standard -> Arrow -> Green Standard */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
              {/* Outdated Box */}
              <div
                style={{
                  flex: '1 1 260px',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  background: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#b91c1c', letterSpacing: '0.04em' }}>
                    OUTDATED STANDARD
                  </span>
                  <span style={{ fontSize: '0.7rem', padding: '1px 6px', borderRadius: '4px', background: '#dc2626', color: '#fff', fontWeight: 700 }}>
                    {item.old_status}
                  </span>
                </div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#991b1b', fontFamily: 'var(--font-mono)' }}>
                  {item.old_standard}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#7f1d1d', marginTop: '2px' }}>
                  {item.old_title}
                </div>
              </div>

              {/* Arrow */}
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: '1.5rem', color: '#6366f1', fontWeight: 900 }}>➔</span>
                <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#6366f1' }}>SUPERSEDED BY</span>
              </div>

              {/* Successor Box */}
              <div
                style={{
                  flex: '1 1 260px',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.35)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#047857', letterSpacing: '0.04em' }}>
                    CURRENT MANDATORY STANDARD
                  </span>
                  <span style={{ fontSize: '0.7rem', padding: '1px 6px', borderRadius: '4px', background: '#059669', color: '#fff', fontWeight: 700 }}>
                    {item.new_status}
                  </span>
                </div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#065f46', fontFamily: 'var(--font-mono)' }}>
                  {item.new_standard}
                </div>
                <div style={{ fontSize: '0.78rem', color: '#064e3b', marginTop: '2px' }}>
                  {item.new_title}
                </div>
              </div>
            </div>

            {/* Official References and Reason */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '12px',
                paddingTop: '8px',
                borderTop: '1px dashed #cbd5e1',
                fontSize: '0.82rem',
              }}
            >
              <div>
                <strong style={{ color: '#334155' }}>📜 Statutory BIS Reference: </strong>
                <span style={{ color: '#0369a1', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{item.bis_reference}</span>
                <div style={{ marginTop: '2px', color: '#475569' }}>
                  <strong>Circular No: </strong> {item.circular_number}
                </div>
              </div>

              <div>
                <strong style={{ color: '#334155' }}>📍 Tender Clause Impact: </strong>
                <span style={{ color: '#1e293b' }}>{item.clause_impact}</span>
              </div>
            </div>

            <div style={{ fontSize: '0.82rem', color: '#475569', background: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
              <strong style={{ color: '#0f172a' }}>Reason for Migration: </strong>
              {item.reason}
            </div>

            {onApplyFix && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
                <button
                  onClick={() => onApplyFix(item.old_standard, item.new_standard)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 14px',
                    borderRadius: '6px',
                    background: '#059669',
                    color: '#ffffff',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    border: 'none',
                    cursor: 'pointer',
                    boxShadow: '0 2px 8px rgba(5, 150, 105, 0.25)',
                  }}
                >
                  ⚡ Auto-Apply This Replacement
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
