'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { TabKey } from '@/components/TabNav';

interface DashboardViewProps {
  onSelectTab: (tab: TabKey) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onSelectTab, onToast }) => {
  const kpis = [
    {
      label: 'Authoritative IS Standards',
      value: '25,480+',
      trend: '+142 New Gazette Updates',
      icon: '📚',
      color: '#4f46e5',
      bg: 'rgba(79, 70, 229, 0.08)',
      tab: 'standard' as TabKey,
    },
    {
      label: 'Mandatory QCO Orders',
      value: '184',
      trend: '100% GFR 144(xi) Guard',
      icon: '🛡️',
      color: '#059669',
      bg: 'rgba(5, 150, 105, 0.08)',
      tab: 'compliance' as TabKey,
    },
    {
      label: 'Tenders & RFPs Audited',
      value: '1,420',
      trend: '98.4% Compliance Score',
      icon: '📋',
      color: '#0284c7',
      bg: 'rgba(2, 132, 199, 0.08)',
      tab: 'tender' as TabKey,
    },
    {
      label: 'Energy & Cost Savings',
      value: '₹4.82 Cr',
      trend: '10.5 Mo. Average Payback',
      icon: '🌱',
      color: '#16a34a',
      bg: 'rgba(22, 163, 74, 0.08)',
      tab: 'tender' as TabKey,
    },
  ];

  const quickActions = [
    {
      title: 'Tender Autopilot',
      description: 'End-to-end procurement generation: Describe your requirement and get a fully cited, compliant RFP clause package.',
      icon: '🚀',
      badge: 'Recommended',
      tab: 'autopilot' as TabKey,
      color: 'linear-gradient(135deg, #4338ca 0%, #312e81 100%)',
    },
    {
      title: 'Document Auditor & Visual Redline',
      description: 'Interactive visual document markup with green/red annotations, engineering measurements, eco tracking, and AI budget estimates.',
      icon: '📋',
      badge: 'Visual Redline',
      tab: 'tender' as TabKey,
      color: 'linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%)',
    },
    {
      title: 'Semantic Standards Matcher',
      description: 'Vector-powered neural search across all Indian Standards to discover governing specifications for any material or equipment.',
      icon: '⚡',
      badge: 'AI Discovery',
      tab: 'recommend' as TabKey,
      color: 'linear-gradient(135deg, #7c2d12 0%, #451a03 100%)',
    },
    {
      title: 'Statutory QCO Compliance',
      description: 'Verify mandatory certification orders, DPIIT Make-in-India rules, and conformity assessment schemes.',
      icon: '🛡️',
      badge: 'GFR Guard',
      tab: 'compliance' as TabKey,
      color: 'linear-gradient(135deg, #0369a1 0%, #075985 100%)',
    },
  ];

  const recentTenders = [
    {
      nit: 'CPWD/EE/2026/PUMP-042',
      title: 'Pumping Machinery & Electromechanical Motor Installations',
      dept: 'Central Public Works Department (CPWD)',
      status: 'Audited & Superseded Standard Fixed',
      statusColor: '#059669',
      score: '96%',
      badge: 'Compliant',
      tab: 'tender' as TabKey,
    },
    {
      nit: 'MES/CH/2026/CABLE-109',
      title: '1100V XLPE Armoured Power Cables & Substation Earthing',
      dept: 'Military Engineer Services (MES)',
      status: 'QCO Mandatory Order Verified',
      statusColor: '#0284c7',
      score: '100%',
      badge: 'Verified',
      tab: 'compliance' as TabKey,
    },
    {
      nit: 'NHAI/PIU/2026/CONC-088',
      title: 'Structural Ready-Mix Concrete & High-Strength Rebars',
      dept: 'National Highways Authority of India (NHAI)',
      status: 'Fly-Ash Eco-Blend Recommended',
      statusColor: '#16a34a',
      score: '94%',
      badge: 'Eco Tier-A',
      tab: 'redline' as TabKey,
    },
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Hero Welcome Banner */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        style={{
          padding: '28px 32px',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%)',
          borderRadius: 'var(--radius-lg, 14px)',
          color: '#ffffff',
          boxShadow: '0 8px 24px rgba(15, 23, 42, 0.25)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ position: 'relative', zIndex: 1, maxWidth: '820px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '999px', background: 'rgba(255, 255, 255, 0.12)', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem' }}>🏛️</span>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#e0e7ff', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              National Public Procurement Intelligence Platform • PS 26108
            </span>
          </div>

          <h1 style={{ margin: '0 0 10px 0', fontSize: '1.9rem', fontWeight: 900, color: '#ffffff', lineHeight: 1.2 }}>
            Procurement Command Center
          </h1>
          <p style={{ margin: '0 0 20px 0', fontSize: '0.94rem', color: '#c7d2fe', lineHeight: 1.5 }}>
            Automate Indian Standards compliance, audit draft tender RFPs for outdated citations, track green sustainability footprints, and generate GFR-compliant procurement specifications.
          </p>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => onSelectTab('autopilot')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                borderRadius: '8px',
                background: '#6366f1',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.88rem',
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
              }}
            >
              <span>🚀 Launch Autopilot</span>
            </button>

            <button
              onClick={() => onSelectTab('redline')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.12)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.88rem',
                border: '1px solid rgba(255, 255, 255, 0.25)',
                cursor: 'pointer',
              }}
            >
              <span>🔴 Open Redline & Intelligence</span>
            </button>
          </div>
        </div>
      </motion.div>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        {kpis.map((kpi, idx) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: idx * 0.05 }}
            onClick={() => onSelectTab(kpi.tab)}
            style={{
              padding: '20px',
              background: '#ffffff',
              borderRadius: 'var(--radius-lg, 12px)',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
              cursor: 'pointer',
              transition: 'transform 0.15s ease, box-shadow 0.15s ease',
            }}
            whileHover={{ y: -3, boxShadow: '0 8px 20px rgba(0, 0, 0, 0.06)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '0.76rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {kpi.label}
                </span>
                <div style={{ fontSize: '1.75rem', fontWeight: 900, color: '#0f172a', marginTop: '4px', lineHeight: 1.1 }}>
                  {kpi.value}
                </div>
              </div>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: kpi.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                }}
              >
                {kpi.icon}
              </div>
            </div>

            <div style={{ marginTop: '12px', fontSize: '0.76rem', color: kpi.color, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span>✓</span>
              <span>{kpi.trend}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Quick Launchpad Grid */}
      <div>
        <div style={{ marginBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: '#0f172a' }}>
              ⚡ Core Intelligence Modules
            </h2>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.82rem', color: '#64748b' }}>
              Jump straight into any step of the procurement and standards analysis lifecycle.
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          {quickActions.map((action, idx) => (
            <motion.div
              key={action.title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: idx * 0.05 }}
              onClick={() => onSelectTab(action.tab)}
              style={{
                padding: '22px',
                borderRadius: 'var(--radius-lg, 12px)',
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
              whileHover={{ y: -3, boxShadow: '0 8px 24px rgba(0, 0, 0, 0.07)' }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ fontSize: '1.6rem' }}>{action.icon}</span>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '999px',
                      background: '#f1f5f9',
                      color: '#475569',
                    }}
                  >
                    {action.badge}
                  </span>
                </div>

                <h3 style={{ margin: '0 0 6px 0', fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>
                  {action.title}
                </h3>
                <p style={{ margin: 0, fontSize: '0.82rem', color: '#64748b', lineHeight: 1.45 }}>
                  {action.description}
                </p>
              </div>

              <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: '#4f46e5' }}>
                <span>Launch Workflow</span>
                <span>➔</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recent Audits & Live Surveillance Feed */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg, 12px)',
          border: '1px solid #e2e8f0',
          padding: '20px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>
              📋 Recent Procurement Audits & Standards Surveillance
            </h3>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
              Real-time records of audited tenders with auto-supersession fixes and compliance ratings.
            </p>
          </div>

          <button
            onClick={() => onSelectTab('redline')}
            style={{
              padding: '6px 14px',
              borderRadius: '6px',
              background: '#f1f5f9',
              color: '#334155',
              fontSize: '0.8rem',
              fontWeight: 700,
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Audit New Document ➔
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {recentTenders.map((t, idx) => (
            <div
              key={idx}
              onClick={() => onSelectTab(t.tab)}
              style={{
                padding: '14px 16px',
                borderRadius: '8px',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
                cursor: 'pointer',
                transition: 'background 0.15s ease',
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#4f46e5', fontFamily: 'var(--font-mono)' }}>
                    {t.nit}
                  </span>
                  <span style={{ fontSize: '0.72rem', color: '#64748b' }}>•</span>
                  <span style={{ fontSize: '0.72rem', color: '#64748b' }}>{t.dept}</span>
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a' }}>
                  {t.title}
                </div>
                <div style={{ fontSize: '0.76rem', color: t.statusColor, fontWeight: 600, marginTop: '2px' }}>
                  {t.status}
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span
                  style={{
                    fontSize: '0.74rem',
                    fontWeight: 800,
                    padding: '3px 10px',
                    borderRadius: '999px',
                    background: '#ecfdf5',
                    color: '#065f46',
                    border: '1px solid #a7f3d0',
                  }}
                >
                  {t.badge} ({t.score})
                </span>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>➔</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
