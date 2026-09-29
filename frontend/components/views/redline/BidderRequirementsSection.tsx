'use client';

import React from 'react';
import { BidderRequirements } from '@/lib/api';

interface BidderRequirementsSectionProps {
  requirements?: BidderRequirements;
}

export const BidderRequirementsSection: React.FC<BidderRequirementsSectionProps> = ({ requirements }) => {
  if (!requirements) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        No bidder requirements data available. Click <strong>Analyze Document</strong> above to extract bidder qualification criteria.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header Banner */}
      <div
        style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          borderRadius: 'var(--radius-lg, 12px)',
          color: '#ffffff',
          boxShadow: '0 4px 16px rgba(15, 23, 42, 0.15)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '1.5rem' }}>👥</span>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>
              Tender Bidder Eligibility & Qualification Criteria
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.82rem', color: '#94a3b8' }}>
              Statutory pre-qualification thresholds governing Technical, Financial, and Make-in-India / GFR statutory compliance.
            </p>
          </div>
        </div>
      </div>

      {/* 3 Qualification Pillars Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Technical Eligibility */}
        <div
          style={{
            background: '#ffffff',
            borderRadius: 'var(--radius-lg, 12px)',
            border: '1px solid #e2e8f0',
            padding: '20px',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <span style={{ fontSize: '1.2rem' }}>🛠️</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 700, color: '#0f172a' }}>
                Technical Qualifications
              </h3>
              <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Experience & Quality Accreditations</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
            {requirements.technical_criteria.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.82rem',
                  color: '#334155',
                  lineHeight: 1.45,
                  display: 'flex',
                  gap: '8px',
                }}
              >
                <span style={{ color: '#4f46e5', fontWeight: 800 }}>•</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Financial Eligibility */}
        <div
          style={{
            background: '#ffffff',
            borderRadius: 'var(--radius-lg, 12px)',
            border: '1px solid #e2e8f0',
            padding: '20px',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <span style={{ fontSize: '1.2rem' }}>💰</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 700, color: '#0f172a' }}>
                Financial Capacity & Solvency
              </h3>
              <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Turnover, EMD & Bank Solvency</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
            {requirements.financial_criteria.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.82rem',
                  color: '#334155',
                  lineHeight: 1.45,
                  display: 'flex',
                  gap: '8px',
                }}
              >
                <span style={{ color: '#059669', fontWeight: 800 }}>•</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Statutory & Regulatory */}
        <div
          style={{
            background: '#ffffff',
            borderRadius: 'var(--radius-lg, 12px)',
            border: '1px solid #e2e8f0',
            padding: '20px',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <span style={{ fontSize: '1.2rem' }}>⚖️</span>
            <div>
              <h3 style={{ margin: 0, fontSize: '0.98rem', fontWeight: 700, color: '#0f172a' }}>
                Statutory Declarations
              </h3>
              <span style={{ fontSize: '0.74rem', color: '#64748b' }}>Make-in-India & GFR Rule 144</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
            {requirements.statutory_declarations.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '10px 12px',
                  borderRadius: '8px',
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  fontSize: '0.82rem',
                  color: '#334155',
                  lineHeight: 1.45,
                  display: 'flex',
                  gap: '8px',
                }}
              >
                <span style={{ color: '#d97706', fontWeight: 800 }}>•</span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mandatory Documents Checklist */}
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
          📑 Mandatory Technical & Financial Submission Dossier
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
          {requirements.required_documents.map((doc, idx) => (
            <div
              key={idx}
              style={{
                padding: '12px 14px',
                borderRadius: '8px',
                background: '#f1f5f9',
                border: '1px solid #cbd5e1',
                fontSize: '0.84rem',
                color: '#1e293b',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
              }}
            >
              <span style={{ fontSize: '1.1rem', color: '#059669' }}>📋</span>
              <span style={{ fontWeight: 600 }}>{doc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
