'use client';

import React from 'react';
import { ComparisonRow } from '@/lib/api';

interface ComparisonMatrixSectionProps {
  rows?: ComparisonRow[];
}

export const ComparisonMatrixSection: React.FC<ComparisonMatrixSectionProps> = ({ rows }) => {
  if (!rows || rows.length === 0) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        No comparison data available. Click <strong>Analyze Document</strong> above to generate the comparison matrix.
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLIANT':
        return { bg: '#dcfce7', text: '#15803d', label: '✅ Compliant', border: '#86efac' };
      case 'OUTDATED':
        return { bg: '#fee2e2', text: '#b91c1c', label: '🔴 Outdated Ref', border: '#fca5a5' };
      case 'AMENDED':
        return { bg: '#fef3c7', text: '#b45309', label: '🟡 Revised Code', border: '#fde68a' };
      default:
        return { bg: '#f1f5f9', text: '#475569', label: status, border: '#cbd5e1' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Visual Chart Comparison Cards */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #e2e8f0',
          padding: '20px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
        }}
      >
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
            📊 Visual Specification Benchmarking & Delta Comparison
          </h3>
          <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
            Direct visual comparison of Tender Specified levels against Statutory Indian Standards and Industry Benchmarks.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {rows.filter(r => r.chart_value_specified !== undefined && r.chart_value_required !== undefined).map((r, idx) => {
            const specVal = r.chart_value_specified!;
            const reqVal = r.chart_value_required!;
            const isNegative = r.status === 'OUTDATED';

            return (
              <div
                key={idx}
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.86rem', fontWeight: 700, color: '#1e293b' }}>
                    {r.parameter}
                  </span>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: isNegative ? '#fee2e2' : '#dcfce7',
                      color: isNegative ? '#b91c1c' : '#15803d',
                    }}
                  >
                    {r.clause}
                  </span>
                </div>

                {/* Bars */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
                  {/* Specified Bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', marginBottom: '3px' }}>
                      <span style={{ color: '#64748b' }}>Tender Specified:</span>
                      <strong style={{ color: isNegative ? '#b91c1c' : '#0f172a', fontFamily: 'var(--font-mono)' }}>
                        {specVal} {r.chart_unit}
                      </strong>
                    </div>
                    <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, (specVal / Math.max(specVal, reqVal)) * 100)}%`,
                          background: isNegative ? '#ef4444' : '#6366f1',
                          borderRadius: '4px',
                        }}
                      />
                    </div>
                  </div>

                  {/* Required Bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem', marginBottom: '3px' }}>
                      <span style={{ color: '#047857', fontWeight: 600 }}>BIS Standard Mandate:</span>
                      <strong style={{ color: '#047857', fontFamily: 'var(--font-mono)' }}>
                        {reqVal} {r.chart_unit}
                      </strong>
                    </div>
                    <div style={{ height: '8px', background: '#e2e8f0', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, (reqVal / Math.max(specVal, reqVal)) * 100)}%`,
                          background: '#10b981',
                          borderRadius: '4px',
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '0.76rem', color: '#475569', marginTop: '4px', lineHeight: 1.4 }}>
                  <strong>Analysis: </strong> {r.delta}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Full Comparison Matrix Table */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #e2e8f0',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc' }}>
          <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
            📋 Comprehensive Specification vs Standard Comparison Matrix
          </h3>
          <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
            Side-by-side gap audit comparing draft RFP specifications against authoritative BIS standards and industry benchmarks.
          </p>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
                <th style={{ padding: '12px 14px', color: '#475569', fontWeight: 700, minWidth: '150px' }}>Clause & Item</th>
                <th style={{ padding: '12px 14px', color: '#475569', fontWeight: 700, minWidth: '180px' }}>Tender Specified</th>
                <th style={{ padding: '12px 14px', color: '#047857', fontWeight: 700, minWidth: '220px' }}>BIS Standard Mandate</th>
                <th style={{ padding: '12px 14px', color: '#4338ca', fontWeight: 700, minWidth: '180px' }}>Industry Benchmark</th>
                <th style={{ padding: '12px 14px', color: '#475569', fontWeight: 700, minWidth: '120px' }}>Status</th>
                <th style={{ padding: '12px 14px', color: '#475569', fontWeight: 700, minWidth: '240px' }}>Delta / Compliance Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => {
                const badge = getStatusBadge(row.status);
                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: '1px solid #f1f5f9',
                      background: idx % 2 === 0 ? '#ffffff' : '#fafafa',
                      verticalAlign: 'top',
                    }}
                  >
                    <td style={{ padding: '12px 14px' }}>
                      <div style={{ fontWeight: 700, color: '#1e293b' }}>{row.parameter}</div>
                      <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: '2px' }}>{row.clause}</div>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#334155' }}>
                      {row.specified_value}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#065f46', fontWeight: 600, background: 'rgba(16, 185, 129, 0.04)' }}>
                      {row.is_standard_mandate}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#3730a3' }}>
                      {row.industry_benchmark}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: badge.bg,
                          color: badge.text,
                          border: `1px solid ${badge.border}`,
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {badge.label}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#475569', fontSize: '0.8rem', lineHeight: 1.4 }}>
                      {row.delta}
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
