'use client';

import React from 'react';
import { AiCostEstimation } from '@/lib/api';

interface CostEstimationSectionProps {
  estimation?: AiCostEstimation;
}

export const CostEstimationSection: React.FC<CostEstimationSectionProps> = ({ estimation }) => {
  if (!estimation) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        No budget estimation data available. Click <strong>Analyze Document</strong> above to generate the AI cost estimate.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner: Estimated Budget */}
      <div
        style={{
          padding: '24px',
          background: 'linear-gradient(135deg, #1e1b4b 0%, #4338ca 100%)',
          borderRadius: 'var(--radius-lg, 12px)',
          color: '#ffffff',
          boxShadow: '0 8px 24px rgba(67, 56, 202, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ fontSize: '0.74rem', padding: '2px 8px', borderRadius: '4px', background: '#34d399', color: '#064e3b', fontWeight: 800 }}>
              AI ESTIMATION ENGINE
            </span>
            <span style={{ fontSize: '0.78rem', color: '#c7d2fe' }}>
              GFR Rule 149 Reasonableness Benchmark
            </span>
          </div>
          <div style={{ fontSize: '0.82rem', color: '#e0e7ff', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Suggested Expenditure on Project
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 900, marginTop: '2px', lineHeight: 1.1 }}>
            ₹{estimation.estimated_total_inr.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.86rem', color: '#c7d2fe', marginTop: '6px' }}>
            Reasonable Budget Range: <strong>{estimation.estimated_range_inr}</strong>
          </div>
        </div>

        <div
          style={{
            padding: '16px 20px',
            borderRadius: '10px',
            background: 'rgba(255, 255, 255, 0.1)',
            border: '1px solid rgba(255, 255, 255, 0.18)',
            maxWidth: '360px',
          }}
        >
          <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', color: '#a5b4fc', fontWeight: 700 }}>
            Pricing Basis & Indexation
          </div>
          <div style={{ fontSize: '0.84rem', color: '#ffffff', marginTop: '4px', lineHeight: 1.4 }}>
            {estimation.rates_basis}
          </div>
          {estimation.potential_savings_inr > 0 && (
            <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.15)', fontSize: '0.8rem', color: '#6ee7b7' }}>
              ⚡ Identified Life-Cycle Savings: <strong>₹{estimation.potential_savings_inr.toLocaleString('en-IN')}</strong>
            </div>
          )}
        </div>
      </div>

      {/* Line Item Cost Breakdown Table */}
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
            📊 Itemized Cost Breakdown & Schedule of Quantities
          </h3>
          <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
            Structured line-item allocation based on CPWD Delhi Schedule of Rates (DSR 2023) and current market rate index.
          </p>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #cbd5e1' }}>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Scope Component</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Estimated Amount (₹)</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>Share (%)</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 700 }}>DSR / Statutory Basis</th>
              </tr>
            </thead>
            <tbody>
              {estimation.line_items.map((item, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid #f1f5f9',
                    background: idx % 2 === 0 ? '#ffffff' : '#fafafa',
                  }}
                >
                  <td style={{ padding: '12px 16px', fontWeight: 600, color: '#1e293b' }}>
                    {item.category}
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 800, color: '#0f172a', fontFamily: 'var(--font-mono)' }}>
                    ₹{item.amount.toLocaleString('en-IN')}
                  </td>
                  <td style={{ padding: '12px 16px', minWidth: '140px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ flex: 1, height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            height: '100%',
                            width: `${item.percentage}%`,
                            background: '#4f46e5',
                            borderRadius: '3px',
                          }}
                        />
                      </div>
                      <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#475569', width: '38px' }}>
                        {item.percentage}%
                      </span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#64748b', fontSize: '0.8rem' }}>
                    {item.basis}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Cost Optimization Suggestions */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #e2e8f0',
          padding: '20px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
        }}
      >
        <h3 style={{ margin: '0 0 12px 0', fontSize: '1.05rem', fontWeight: 700, color: '#0f172a' }}>
          💡 AI Cost Optimization & Value Engineering Suggestions
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {estimation.cost_optimizations.map((tip, idx) => (
            <div
              key={idx}
              style={{
                padding: '12px 14px',
                borderRadius: '8px',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                fontSize: '0.84rem',
                color: '#334155',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
              }}
            >
              <span style={{ fontSize: '1.1rem', color: '#4f46e5' }}>💡</span>
              <span style={{ lineHeight: 1.45 }}>{tip}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
