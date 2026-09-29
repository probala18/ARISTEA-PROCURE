'use client';

import React from 'react';
import { EcoTrack } from '@/lib/api';

interface EcoTrackSectionProps {
  ecoTrack?: EcoTrack;
}

export const EcoTrackSection: React.FC<EcoTrackSectionProps> = ({ ecoTrack }) => {
  if (!ecoTrack) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
        No sustainability data available. Click <strong>Analyze Document</strong> above to generate the Eco Track report.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Banner: Eco Score & Grade */}
      <div
        style={{
          padding: '24px',
          background: 'linear-gradient(135deg, #064e3b 0%, #047857 100%)',
          borderRadius: 'var(--radius-lg, 12px)',
          color: '#ffffff',
          boxShadow: '0 8px 24px rgba(6, 78, 59, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Big Score Circle */}
          <div
            style={{
              width: '84px',
              height: '84px',
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.15)',
              border: '3px solid #34d399',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ fontSize: '1.75rem', fontWeight: 900, lineHeight: 1 }}>{ecoTrack.eco_score}</span>
            <span style={{ fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#a7f3d0' }}>/ 100</span>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.74rem', padding: '2px 8px', borderRadius: '4px', background: '#34d399', color: '#064e3b', fontWeight: 800 }}>
                {ecoTrack.grade}
              </span>
              <span style={{ fontSize: '0.78rem', color: '#a7f3d0' }}>
                CPWD Green Works Guideline 2024
              </span>
            </div>
            <h2 style={{ margin: '6px 0 0 0', fontSize: '1.3rem', fontWeight: 800 }}>
              Eco-Intelligence & Sustainability Tracker
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.84rem', color: '#d1fae5' }}>
              Standard: <strong>{ecoTrack.energy_efficiency_class}</strong> conforming to Energy Conservation Act & BIS QCO.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <div
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '0.72rem', color: '#a7f3d0', textTransform: 'uppercase' }}>Annual Energy Saved</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, marginTop: '2px' }}>
              {ecoTrack.annual_kwh_savings.toLocaleString()} kWh
            </div>
          </div>

          <div
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '0.72rem', color: '#a7f3d0', textTransform: 'uppercase' }}>CO₂ Emissions Avoided</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, marginTop: '2px' }}>
              {ecoTrack.annual_co2_reduction_tons} Tons/yr
            </div>
          </div>
        </div>
      </div>

      {/* 4 Key Sustainability Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div style={{ padding: '16px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>⚡</div>
          <div style={{ fontSize: '0.76rem', color: '#64748b', fontWeight: 600 }}>Energy Efficiency Class</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#047857', marginTop: '2px' }}>
            {ecoTrack.energy_efficiency_class}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#059669', marginTop: '4px' }}>
            Mandatory under BEE Star Labeling 2024
          </div>
        </div>

        <div style={{ padding: '16px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>🌱</div>
          <div style={{ fontSize: '0.76rem', color: '#64748b', fontWeight: 600 }}>Carbon Footprint Reduction</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0284c7', marginTop: '2px' }}>
            {ecoTrack.annual_co2_reduction_tons} Metric Tons / yr
          </div>
          <div style={{ fontSize: '0.72rem', color: '#0369a1', marginTop: '4px' }}>
            Equivalent to planting ~520 trees annually
          </div>
        </div>

        <div style={{ padding: '16px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>💰</div>
          <div style={{ fontSize: '0.76rem', color: '#64748b', fontWeight: 600 }}>3-Year Lifecycle Savings</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#7c3aed', marginTop: '2px' }}>
            ₹{ecoTrack.lifecycle_cost_savings_inr.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#6d28d9', marginTop: '4px' }}>
            Payback period on motor premium: 10.5 mo
          </div>
        </div>

        <div style={{ padding: '16px', background: '#ffffff', borderRadius: '10px', border: '1px solid #e2e8f0', boxShadow: '0 2px 8px rgba(0,0,0,0.03)' }}>
          <div style={{ fontSize: '1.2rem', marginBottom: '6px' }}>♻️</div>
          <div style={{ fontSize: '0.76rem', color: '#64748b', fontWeight: 600 }}>Circular Economy Index</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#d97706', marginTop: '2px' }}>
            92% Recyclable Materials
          </div>
          <div style={{ fontSize: '0.72rem', color: '#b45309', marginTop: '4px' }}>
            ISO 14021 compliant copper & cast iron recovery
          </div>
        </div>
      </div>

      {/* Compliance Badges & Insights */}
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
          🌿 Green Public Procurement Compliance Accreditations
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
          {ecoTrack.compliance_tags.map((tag, idx) => (
            <span
              key={idx}
              style={{
                fontSize: '0.8rem',
                fontWeight: 600,
                padding: '6px 12px',
                borderRadius: '8px',
                background: '#ecfdf5',
                color: '#065f46',
                border: '1px solid #a7f3d0',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span>🌿</span> {tag}
            </span>
          ))}
        </div>

        <h4 style={{ margin: '0 0 10px 0', fontSize: '0.92rem', fontWeight: 700, color: '#334155' }}>
          Decarbonization & Engineering Insights
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {ecoTrack.sustainability_insights.map((insight, idx) => (
            <div
              key={idx}
              style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                fontSize: '0.84rem',
                color: '#334155',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
              }}
            >
              <span style={{ color: '#059669', fontWeight: 800 }}>✓</span>
              <span>{insight}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
