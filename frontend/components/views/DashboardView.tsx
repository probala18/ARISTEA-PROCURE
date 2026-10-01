'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TabKey } from '@/components/TabNav';

interface DashboardViewProps {
  onSelectTab: (tab: TabKey) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onSelectTab, onToast }) => {
  // Interactive Redline Demo State
  const [redlineSimFixed, setRedlineSimFixed] = useState(false);
  const [selectedArchStage, setSelectedArchStage] = useState<number>(4);

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
      tab: 'standard' as TabKey,
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

  const archStages = [
    {
      step: 1,
      title: 'Intent & Intake',
      icon: '📥',
      badge: 'Input',
      description: 'Upload PDF/DOCX or input natural language requirement in any Indic language.',
      tech: 'PyMuPDF Plain-Text Extractor & Schema Normalizer',
    },
    {
      step: 2,
      title: 'Semantic Matcher',
      icon: '⚡',
      badge: 'Vector',
      description: 'Neural matching against BIS catalog with cosine similarity and BM25 hybrid ranking.',
      tech: 'MiniLM-L6-v2 Embeddings + SQLite Hybrid Index',
    },
    {
      step: 3,
      title: 'KG & QCO Guard',
      icon: '🕸️',
      badge: 'Statutory',
      description: 'Verifies Ministry QCO Gazette orders, mandatory vs voluntary BIS certification schemes.',
      tech: 'Deterministic Knowledge Graph & Gazette DB',
    },
    {
      step: 4,
      title: 'Document Inspector',
      icon: '🖋️',
      badge: 'Live Markup',
      description: 'Green for active standards; Red for expired rules with 1-click legal auto-fixes.',
      tech: 'Dynamic Regex Parser + Real-time DOM Diffing',
    },
    {
      step: 5,
      title: 'Vision AI Tables',
      icon: '👁️',
      badge: 'Vision',
      description: 'Reads complex engineering tables, motor kW curves, and tolerances without broken columns.',
      tech: 'Multi-Modal Vision Pipeline + Tabular OCR',
    },
    {
      step: 6,
      title: 'Adversarial Shield',
      icon: '🛡️',
      badge: 'Safety',
      description: 'Independent validator agent halts execution if citation cannot be verified deterministically.',
      tech: 'Adversarial LLM Auditor + Citation Grounding',
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
      tab: 'tender' as TabKey,
    },
    {
      nit: 'NHAI/PIU/2026/CONC-088',
      title: 'Structural Ready-Mix Concrete & High-Strength Rebars',
      dept: 'National Highways Authority of India (NHAI)',
      status: 'Fly-Ash Eco-Blend Recommended',
      statusColor: '#16a34a',
      score: '94%',
      badge: 'Eco Tier-A',
      tab: 'tender' as TabKey,
    },
  ];

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '32px', paddingBottom: '40px' }}>
      
      {/* 1. Grand Hero Landing Banner */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        style={{
          padding: '36px 40px',
          background: 'linear-gradient(135deg, #090d16 0%, #171c38 45%, #2a2c6d 100%)',
          borderRadius: '16px',
          color: '#ffffff',
          boxShadow: '0 12px 36px rgba(15, 23, 42, 0.28)',
          position: 'relative',
          overflow: 'hidden',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        {/* Subtle Background Glow Elements */}
        <div
          style={{
            position: 'absolute',
            top: '-60px',
            right: '-60px',
            width: '280px',
            height: '280px',
            background: 'radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%)',
            borderRadius: '50%',
            pointerEvents: 'none',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '-40px',
            left: '30%',
            width: '240px',
            height: '240px',
            background: 'radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 70%)',
            borderRadius: '50%',
            pointerEvents: 'none',
          }}
        />

        <div style={{ position: 'relative', zIndex: 1, maxWidth: '900px' }}>
          {/* Initiative Badge */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '999px',
              background: 'rgba(255, 255, 255, 0.12)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              marginBottom: '16px',
              backdropFilter: 'blur(8px)',
            }}
          >
            <span style={{ fontSize: '0.85rem' }}>🇮🇳</span>
            <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#e0e7ff', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              Problem Statement 26108 · Smart India Hackathon
            </span>
          </div>

          <h1
            style={{
              margin: '0 0 14px 0',
              fontSize: '2.3rem',
              fontWeight: 900,
              color: '#ffffff',
              lineHeight: 1.15,
              letterSpacing: '-0.02em',
            }}
          >
            ARISTEA-PROCURE
            <span style={{ display: 'block', fontSize: '1.45rem', fontWeight: 600, color: '#a5b4fc', marginTop: '6px' }}>
              Autonomous Indian Standards Intelligence & Tender Surveillance
            </span>
          </h1>

          <p style={{ margin: '0 0 24px 0', fontSize: '1rem', color: '#cbd5e1', lineHeight: 1.6, maxWidth: '820px' }}>
            Transforming public procurement for Indian government bodies. Eliminating obsolete standard citations, enforcing statutory Quality Control Orders (QCOs), safeguarding against AI hallucinations, and reading complex engineering tables with precision Vision AI.
          </p>

          {/* Primary Action Buttons */}
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'center' }}>
            <button
              onClick={() => {
                onSelectTab('autopilot');
                onToast('Launching Autopilot RFP Engine...', 'info');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 24px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                color: '#ffffff',
                fontWeight: 800,
                fontSize: '0.92rem',
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 4px 18px rgba(99, 102, 241, 0.45)',
                transition: 'transform 0.15s ease',
              }}
            >
              <span>🚀 Launch Autopilot</span>
            </button>

            <button
              onClick={() => {
                onSelectTab('tender');
                onToast('Opening Document Compliance Inspector...', 'info');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 22px',
                borderRadius: '10px',
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#fca5a5',
                fontWeight: 800,
                fontSize: '0.92rem',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                cursor: 'pointer',
                backdropFilter: 'blur(6px)',
              }}
            >
              <span>📝 Open Document Inspector</span>
            </button>

            <button
              onClick={() => {
                onSelectTab('analytics');
                onToast('Loading Architecture & Analytics...', 'info');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 22px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.92rem',
                border: '1px solid rgba(255, 255, 255, 0.22)',
                cursor: 'pointer',
                backdropFilter: 'blur(6px)',
              }}
            >
              <span>📈 View Architecture & Diagram</span>
            </button>
          </div>
        </div>
      </motion.div>

      {/* 2. Key Operational Metrics Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        {kpis.map((kpi, idx) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: idx * 0.05 }}
            onClick={() => onSelectTab(kpi.tab)}
            style={{
              padding: '20px 22px',
              background: '#ffffff',
              borderRadius: '12px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            whileHover={{ y: -3, boxShadow: '0 8px 20px rgba(0, 0, 0, 0.06)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {kpi.label}
                </span>
                <div style={{ fontSize: '1.85rem', fontWeight: 900, color: '#0f172a', marginTop: '4px', lineHeight: 1.1 }}>
                  {kpi.value}
                </div>
              </div>
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: kpi.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.35rem',
                }}
              >
                {kpi.icon}
              </div>
            </div>

            <div style={{ marginTop: '12px', fontSize: '0.76rem', color: kpi.color, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span>✓</span>
              <span>{kpi.trend}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* 3. The 3 Breakthrough Competitive Innovations Showcase */}
      <div>
        <div style={{ marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>🏆</span>
            <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 900, color: '#0f172a', letterSpacing: '-0.01em' }}>
              Why ARISTEA Wins: The 3 Core Tech Differentiators
            </h2>
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.88rem', color: '#64748b' }}>
            Engineered specifically to solve the fatal flaws of generic LLMs in public procurement.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
          
          {/* Card 1: Interactive Document Compliance Inspector */}
          <div
            style={{
              background: '#ffffff',
              borderRadius: '14px',
              border: '1px solid #fed7aa',
              boxShadow: '0 4px 16px rgba(234, 88, 12, 0.06)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.8rem' }}>🖋️</span>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 800,
                    padding: '3px 10px',
                    borderRadius: '999px',
                    background: '#ffedd5',
                    color: '#c2410c',
                  }}
                >
                  Live Clause Intelligence
                </span>
              </div>

              <h3 style={{ margin: '0 0 8px 0', fontSize: '1.12rem', fontWeight: 800, color: '#0f172a' }}>
                Interactive Document Compliance Inspector
              </h3>
              <p style={{ margin: '0 0 14px 0', fontSize: '0.84rem', color: '#64748b', lineHeight: 1.5 }}>
                Displaying the procurement officer&apos;s actual draft tender on screen with immediate color-coded statutory verification:
              </p>

              {/* Interactive Visual Preview Widget */}
              <div
                style={{
                  background: '#f8fafc',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  padding: '14px',
                  marginBottom: '16px',
                  fontSize: '0.8rem',
                  lineHeight: 1.6,
                }}
              >
                <div style={{ marginBottom: '8px', color: '#334155' }}>
                  Clause 4.1:{' '}
                  <span
                    style={{
                      background: 'rgba(34, 197, 94, 0.18)',
                      color: '#15803d',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontWeight: 700,
                      border: '1px solid rgba(34, 197, 94, 0.3)',
                    }}
                  >
                    🟢 Matches Active IS 1786:2008 (High-Strength Rebars)
                  </span>
                </div>
                <div style={{ color: '#334155' }}>
                  Clause 4.2:{' '}
                  {redlineSimFixed ? (
                    <span
                      style={{
                        background: 'rgba(34, 197, 94, 0.22)',
                        color: '#166534',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontWeight: 700,
                        border: '1px solid #86efac',
                      }}
                    >
                      🟢 FIXED: IS 12615:2018 (IE3 Premium Energy Efficiency)
                    </span>
                  ) : (
                    <span
                      style={{
                        background: 'rgba(239, 68, 68, 0.18)',
                        color: '#b91c1c',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: 700,
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                      }}
                    >
                      🔴 EXPIRED: IS 325:1996 (Superseded & Non-Compliant)
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                onClick={() => setRedlineSimFixed(!redlineSimFixed)}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: redlineSimFixed ? '#f1f5f9' : '#fee2e2',
                  color: redlineSimFixed ? '#475569' : '#dc2626',
                  fontSize: '0.78rem',
                  fontWeight: 800,
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                {redlineSimFixed ? '↺ Reset Simulation' : '⚡ 1-Click Auto-Fix to IS 12615'}
              </button>
              <button
                onClick={() => onSelectTab('tender')}
                style={{
                  padding: '8px 14px',
                  borderRadius: '6px',
                  background: '#c2410c',
                  color: '#ffffff',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                Open Inspector ➔
              </button>
            </div>
          </div>

          {/* Card 2: Vision AI for Complex Tables */}
          <div
            style={{
              background: '#ffffff',
              borderRadius: '14px',
              border: '1px solid #bae6fd',
              boxShadow: '0 4px 16px rgba(2, 132, 199, 0.06)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.8rem' }}>👁️</span>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 800,
                    padding: '3px 10px',
                    borderRadius: '999px',
                    background: '#e0f2fe',
                    color: '#0284c7',
                  }}
                >
                  Vision AI Powered
                </span>
              </div>

              <h3 style={{ margin: '0 0 8px 0', fontSize: '1.12rem', fontWeight: 800, color: '#0f172a' }}>
                Reading Complex Tables & Engineering Charts
              </h3>
              <p style={{ margin: '0 0 14px 0', fontSize: '0.84rem', color: '#64748b', lineHeight: 1.5 }}>
                Bureau of Indian Standards publications are loaded with multi-column power curves, tolerance matrices, and mathematical formulas:
              </p>

              <div
                style={{
                  background: '#f8fafc',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  padding: '12px 14px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ fontSize: '0.74rem', color: '#ef4444', fontWeight: 700, marginBottom: '6px' }}>
                  ❌ Generic AI: Fails when columns wrap or split across pages.
                </div>
                <div style={{ fontSize: '0.74rem', color: '#059669', fontWeight: 700 }}>
                  ✓ ARISTEA Vision AI: Treats tables visually as spatial matrices, preserving exact kW values, efficiency tiers, and test norms.
                </div>
              </div>
            </div>

            <button
              onClick={() => onSelectTab('tender')}
              style={{
                width: '100%',
                padding: '9px 14px',
                borderRadius: '6px',
                background: '#0284c7',
                color: '#ffffff',
                fontSize: '0.78rem',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                textAlign: 'center',
              }}
            >
              Inspect Table Extraction in Auditor ➔
            </button>
          </div>

          {/* Card 3: The Adversarial AI Double-Check */}
          <div
            style={{
              background: '#ffffff',
              borderRadius: '14px',
              border: '1px solid #bbf7d0',
              boxShadow: '0 4px 16px rgba(22, 163, 74, 0.06)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.8rem' }}>🛡️</span>
                <span
                  style={{
                    fontSize: '0.7rem',
                    fontWeight: 800,
                    padding: '3px 10px',
                    borderRadius: '999px',
                    background: '#dcfce7',
                    color: '#15803d',
                  }}
                >
                 AI Safety System
                </span>
              </div>

              <h3 style={{ margin: '0 0 8px 0', fontSize: '1.12rem', fontWeight: 800, color: '#0f172a' }}>
                The &ldquo;Adversarial&rdquo; AI Double-Check
              </h3>
              <p style={{ margin: '0 0 14px 0', fontSize: '0.84rem', color: '#64748b', lineHeight: 1.5 }}>
                AI hallucination is catastrophic in government procurement. Citing non-existent rules like &ldquo;IS 9999&rdquo; can stall a ₹100 Crore public tender:
              </p>

              <div
                style={{
                  background: '#f8fafc',
                  borderRadius: '10px',
                  border: '1px solid #e2e8f0',
                  padding: '12px 14px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ fontSize: '0.74rem', color: '#0f172a', fontWeight: 700, marginBottom: '4px' }}>
                  Independent Auditor Agent Guarantee:
                </div>
                <div style={{ fontSize: '0.74rem', color: '#64748b', fontStyle: 'italic', lineHeight: 1.4 }}>
                  &ldquo;If a standard citation cannot be verified deterministically against the BIS database, ARISTEA immediately halts and prompts: &lsquo;I am not 100% sure, please check manually.&rsquo;&rdquo;
                </div>
              </div>
            </div>

            <button
              onClick={() => onSelectTab('autopilot')}
              style={{
                width: '100%',
                padding: '9px 14px',
                borderRadius: '6px',
                background: '#15803d',
                color: '#ffffff',
                fontSize: '0.78rem',
                fontWeight: 700,
                border: 'none',
                cursor: 'pointer',
                textAlign: 'center',
              }}
            >
              Test Adversarial Guard in Autopilot ➔
            </button>
          </div>
        </div>
      </div>

      {/* 4. Interactive System Architecture Pipeline Diagram (Embedded Widget) */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '28px',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.25rem' }}>📊</span>
              <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 900, color: '#0f172a' }}>
                End-to-End System Architecture Pipeline
              </h2>
            </div>
            <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: '#64748b' }}>
              Click any stage below to inspect the underlying technological components, algorithms, and validation metrics.
            </p>
          </div>

          <button
            onClick={() => onSelectTab('analytics')}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
              color: '#ffffff',
              fontSize: '0.84rem',
              fontWeight: 800,
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 2px 10px rgba(79, 70, 229, 0.3)',
            }}
          >
            Open Full Analytics & Charts Page ➔
          </button>
        </div>

        {/* 6-Stage Process Flow Ribbon */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: '12px',
            marginBottom: '20px',
          }}
        >
          {archStages.map((stage) => {
            const isSelected = selectedArchStage === stage.step;
            return (
              <div
                key={stage.step}
                onClick={() => setSelectedArchStage(stage.step)}
                style={{
                  padding: '14px',
                  borderRadius: '10px',
                  background: isSelected ? 'linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)' : '#f8fafc',
                  color: isSelected ? '#ffffff' : '#1e293b',
                  border: isSelected ? '1px solid #4338ca' : '1px solid #e2e8f0',
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                  boxShadow: isSelected ? '0 4px 14px rgba(79, 70, 229, 0.3)' : 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '1.2rem' }}>{stage.icon}</span>
                  <span
                    style={{
                      fontSize: '0.62rem',
                      fontWeight: 800,
                      padding: '1px 6px',
                      borderRadius: '999px',
                      background: isSelected ? 'rgba(255, 255, 255, 0.25)' : '#e2e8f0',
                      color: isSelected ? '#ffffff' : '#475569',
                    }}
                  >
                    Step {stage.step}
                  </span>
                </div>
                <div style={{ fontSize: '0.86rem', fontWeight: 800 }}>
                  {stage.title}
                </div>
                <div
                  style={{
                    fontSize: '0.7rem',
                    color: isSelected ? '#e0e7ff' : '#64748b',
                    marginTop: '2px',
                  }}
                >
                  {stage.badge}
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Architecture Node Detail Card */}
        {(() => {
          const activeNode = archStages.find((s) => s.step === selectedArchStage) || archStages[3];
          return (
            <div
              style={{
                background: '#f8fafc',
                borderRadius: '12px',
                border: '1px solid #cbd5e1',
                padding: '20px 24px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '16px',
              }}
            >
              <div style={{ flex: 1, minWidth: '280px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ fontSize: '1.25rem' }}>{activeNode.icon}</span>
                  <span style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>
                    Stage {activeNode.step}: {activeNode.title}
                  </span>
                </div>
                <p style={{ margin: '0 0 8px 0', fontSize: '0.86rem', color: '#475569', lineHeight: 1.5 }}>
                  {activeNode.description}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', color: '#4f46e5', fontWeight: 700 }}>
                  <span>Tech Stack:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', background: 'rgba(79, 70, 229, 0.08)', padding: '2px 8px', borderRadius: '4px' }}>
                    {activeNode.tech}
                  </span>
                </div>
              </div>

              <button
                onClick={() => onSelectTab('analytics')}
                style={{
                  padding: '9px 16px',
                  borderRadius: '8px',
                  background: '#0f172a',
                  color: '#ffffff',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  border: 'none',
                  cursor: 'pointer',
                  flexShrink: 0,
                }}
              >
                Inspect Live Payloads & Telemetry ➔
              </button>
            </div>
          );
        })()}
      </div>

      {/* 5. Document Auditor 4-Pillar Feature Overview */}
      <div
        style={{
          background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
          borderRadius: '16px',
          border: '1px solid #e2e8f0',
          padding: '28px',
        }}
      >
        <div style={{ marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>📑</span>
            <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 900, color: '#0f172a' }}>
              The 4 Core Pillars of Document Auditor
            </h2>
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: '#64748b' }}>
            Built specifically to answer the RFP compliance and green sustainability requirements requested by government departments.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          <div
            onClick={() => onSelectTab('tender')}
            style={{
              padding: '18px',
              borderRadius: '12px',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              cursor: 'pointer',
              boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
            }}
          >
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>📐</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>
              Overview & Measurements
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.45 }}>
              Automatic extraction of motor kW ratings, pump head meters, pipe schedules, and cement compressive strength.
            </div>
          </div>

          <div
            onClick={() => onSelectTab('tender')}
            style={{
              padding: '18px',
              borderRadius: '12px',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              cursor: 'pointer',
              boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
            }}
          >
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>📊</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>
              Comparison Matrix & Audit
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.45 }}>
              Side-by-side verification comparing tender draft requirements against active Bureau of Indian Standards clauses.
            </div>
          </div>

          <div
            onClick={() => onSelectTab('tender')}
            style={{
              padding: '18px',
              borderRadius: '12px',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              cursor: 'pointer',
              boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
            }}
          >
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>🌿</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>
              Eco Track & Energy ROI
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.45 }}>
              Calculates annual kWh energy savings, ₹ monetary cost benefits, and metric tons of CO2 averted via IE3/IE4 motors.
            </div>
          </div>

          <div
            onClick={() => onSelectTab('tender')}
            style={{
              padding: '18px',
              borderRadius: '12px',
              background: '#ffffff',
              border: '1px solid #e2e8f0',
              cursor: 'pointer',
              boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
            }}
          >
            <div style={{ fontSize: '1.5rem', marginBottom: '8px' }}>👥</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>
              Bidder Requirement Summary
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.45 }}>
              Parses financial turnover thresholds, similar work credentials, and DPIIT Make-in-India Class-I minimum local content.
            </div>
          </div>
        </div>
      </div>

      {/* 6. Recent Audits & Live Departmental Surveillance Feed */}
      <div
        style={{
          background: '#ffffff',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          padding: '24px',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.03)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#0f172a' }}>
              📋 Active Departmental Surveillance & Audit Records
            </h3>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: '#64748b' }}>
              Real-time records of audited tenders with auto-supersession fixes and compliance ratings.
            </p>
          </div>

          <button
            onClick={() => onSelectTab('tender')}
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
