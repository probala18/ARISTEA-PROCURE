'use client';

import React from 'react';
import { TenderOverview } from '@/lib/api';

interface TenderOverviewSectionProps {
  overview?: TenderOverview;
}

export const TenderOverviewSection: React.FC<TenderOverviewSectionProps> = ({ overview }) => {
  if (!overview) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        No tender document analyzed yet. Click <strong>Analyze Document</strong> above to extract measurements and overview.
      </div>
    );
  }

  const categoryColors: Record<string, { bg: string; color: string }> = {
    Electrical: { bg: '#e0f2fe', color: '#0369a1' },
    Hydraulics: { bg: '#e0e7ff', color: '#4338ca' },
    'Electro-Mechanical': { bg: '#fef3c7', color: '#92400e' },
    Thermal: { bg: '#fee2e2', color: '#b91c1c' },
    'Safety & Earthing': { bg: '#dcfce7', color: '#15803d' },
    'Civil & Structural': { bg: '#f1f5f9', color: '#475569' },
    General: { bg: '#f3e8ff', color: '#7e22ce' },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Executive Overview Header Card */}
      <div
        style={{
          padding: '24px',
          background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)',
          borderRadius: 'var(--radius-lg, 12px)',
          color: '#ffffff',
          boxShadow: '0 8px 24px rgba(30, 27, 75, 0.25)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.78rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.2)', fontWeight: 700 }}>
                {overview.nit_number}
              </span>
              <span style={{ fontSize: '0.78rem', color: '#c7d2fe' }}>
                {overview.department}
              </span>
            </div>
            <h2 style={{ margin: '0 0 10px 0', fontSize: '1.35rem', fontWeight: 800, color: '#ffffff' }}>
              {overview.title}
            </h2>
            <p style={{ margin: 0, fontSize: '0.88rem', color: '#e0e7ff', maxWidth: '850px', lineHeight: 1.5 }}>
              {overview.scope_summary}
            </p>
          </div>

          <div
            style={{
              padding: '12px 18px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              textAlign: 'right',
            }}
          >
            <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#c7d2fe' }}>
              Project Timeline
            </div>
            <div style={{ fontSize: '0.92rem', fontWeight: 800, color: '#ffffff', marginTop: '2px' }}>
              {overview.estimated_timeline}
            </div>
          </div>
        </div>
      </div>

      {/* Extracted Measurements Card */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #e2e8f0',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #e2e8f0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: '#f8fafc',
          }}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
              📐 Engineering & Physical Measurements Specification
            </h3>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
              Extracted operational parameters, allowable tolerances, and associated statutory standard thresholds.
            </p>
          </div>
          <span
            style={{
              padding: '4px 10px',
              borderRadius: '999px',
              background: '#e0e7ff',
              color: '#4338ca',
              fontWeight: 700,
              fontSize: '0.76rem',
            }}
          >
            {overview.measurements.length} Parameters Extracted
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Parameter</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Specified Value</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Unit</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Acceptable Tolerance</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Governing Standard</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Domain</th>
              </tr>
            </thead>
            <tbody>
              {overview.measurements.map((m, idx) => {
                const badgeStyle = categoryColors[m.category] || categoryColors.General;
                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid #f1f5f9',
                      background: idx % 2 === 0 ? '#ffffff' : '#fafafa',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: '#1e293b' }}>
                      {m.parameter}
                    </td>
                    <td style={{ padding: '12px 16px', fontWeight: 800, color: '#0f172a', fontFamily: 'var(--font-mono)' }}>
                      {m.value}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#64748b' }}>
                      {m.unit}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#0369a1', fontWeight: 600 }}>
                      {m.tolerance || '—'}
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: '#4338ca' }}>
                      {m.standard_ref || '—'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: badgeStyle.bg,
                          color: badgeStyle.color,
                          fontWeight: 700,
                        }}
                      >
                        {m.category}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
