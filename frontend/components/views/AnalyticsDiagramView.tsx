'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Panel } from '@/components/ui/Panel';
import { TabKey } from '@/components/TabNav';

interface AnalyticsDiagramViewProps {
  onSelectTab: (tab: TabKey) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

interface PipelineStage {
  id: string;
  step: number;
  name: string;
  subtitle: string;
  icon: string;
  color: string;
  description: string;
  techStack: string;
  output: string;
  metric: string;
}

export const AnalyticsDiagramView: React.FC<AnalyticsDiagramViewProps> = ({ onSelectTab, onToast }) => {
  const [selectedStageId, setSelectedStageId] = useState<string>('stage-4');
  const [activeTimeframe, setActiveTimeframe] = useState<'30d' | '90d' | 'all'>('30d');

  const pipelineStages: PipelineStage[] = [
    {
      id: 'stage-1',
      step: 1,
      name: 'Intent & Document Intake',
      subtitle: 'Multi-Format Input',
      icon: '📥',
      color: '#3b82f6',
      description: 'Accepts procurement officer needs, NIT notices, or uploaded tender documents in PDF, DOCX, or plain text formats.',
      techStack: 'PyMuPDF Engine · FastStream · Schema Validator',
      output: 'Normalized UTF-8 sections with intact layout metadata',
      metric: '100% Text & Metadata Preservation',
    },
    {
      id: 'stage-2',
      step: 2,
      name: 'Semantic Standards Matcher',
      subtitle: 'Neural Vector Search',
      icon: '⚡',
      color: '#8b5cf6',
      description: 'Scans technical requirements and embeds procurement intent into high-dimensional space, retrieving governing BIS standards.',
      techStack: 'SentenceTransformers · pgvector · BM25 Hybrid Ranker',
      output: 'Ranked candidate Indian Standards with similarity scores',
      metric: '< 45ms Query Latency',
    },
    {
      id: 'stage-3',
      step: 3,
      name: 'BIS Knowledge Graph & QCO',
      subtitle: 'Ontology Traversal',
      icon: '🕸️',
      color: '#06b6d4',
      description: 'Navigates multi-version lineage, identifying whether a cited standard is active, superseded, or under a mandatory Quality Control Order.',
      techStack: 'Module 4 Lineage Graph · Gazette S.O. Database · SQLite/Postgres',
      output: 'Multi-hop relationship edges, successor mappings, and amendments',
      metric: '10,000+ Standards Linked',
    },
    {
      id: 'stage-4',
      step: 4,
      name: 'The Redline Document Editor',
      subtitle: 'Visual Wow Factor',
      icon: '🔴',
      color: '#ef4444',
      description: 'Renders the actual document on screen: Green marks perfect Indian Standard matches; Red warns of expired rules with 1-click auto-fix.',
      techStack: 'RedlineService · Inline Lexical Markup · Diff Engine',
      output: 'Interactive on-screen visual document with 1-click upgrades',
      metric: 'Zero Clutter · Visual Wow',
    },
    {
      id: 'stage-5',
      step: 5,
      name: 'Vision AI Complex Tables',
      subtitle: 'The Tech Winner',
      icon: '👁️',
      color: '#10b981',
      description: 'Processes mathematical tables, efficiency curves, and tolerance formulas as images to preserve columns and numbers without breaking.',
      techStack: 'Computer Vision OCR · Table Layout Transformer · LaTeX Parser',
      output: 'Structured multi-column tables, efficiency matrices, and tolerance formulas',
      metric: '99.4% Column & Number Accuracy',
    },
    {
      id: 'stage-6',
      step: 6,
      name: 'Adversarial AI Double-Check',
      subtitle: 'The Safety Winner',
      icon: '🛡️',
      color: '#f59e0b',
      description: 'Independent second Auditor AI aggressively cross-checks every cited standard against official BIS records, blocking hallucinations like IS 9999.',
      techStack: 'Adversarial Cross-Auditor · Dual-LLM Guardrail · Hallucination Blocker',
      output: 'Document Trust Score, verified citations, and blocked hallucination alerts',
      metric: '0 Hallucinated Standards Admitted',
    },
  ];

  const currentStage = pipelineStages.find((s) => s.id === selectedStageId) || pipelineStages[3];

  const complianceBreakdown = [
    { label: 'Active & Valid Standards', count: 7420, pct: 74.2, color: '#10b981' },
    { label: 'Quality Control Order (QCO) Mandatory', count: 1850, pct: 18.5, color: '#ef4444' },
    { label: 'Amended with Gazette Revisions', count: 520, pct: 5.2, color: '#f59e0b' },
    { label: 'Superseded / Obsolete Mapped', count: 210, pct: 2.1, color: '#6366f1' },
  ];

  const departmentAnalytics = [
    { dept: 'Central Public Works Dept (CPWD)', tenders: 412, compliance: 98.4, savings: '₹4.2 Cr', ecoScore: 92 },
    { dept: 'Military Engineer Services (MES)', tenders: 285, compliance: 99.1, savings: '₹3.1 Cr', ecoScore: 95 },
    { dept: 'National Highways Authority (NHAI)', tenders: 340, compliance: 97.6, savings: '₹6.8 Cr', ecoScore: 89 },
    { dept: 'Indian Railways (RDSO)', tenders: 512, compliance: 99.4, savings: '₹8.5 Cr', ecoScore: 94 },
    { dept: 'Central Pollution Control Board (CPCB)', tenders: 120, compliance: 100.0, savings: '₹1.9 Cr', ecoScore: 98 },
  ];

  const monthlyTrends = [
    { month: 'May', audited: 180, complianceRate: 91, energyKwh: 120000, co2Tons: 98 },
    { month: 'Jun', audited: 240, complianceRate: 93, energyKwh: 165000, co2Tons: 135 },
    { month: 'Jul', audited: 310, complianceRate: 95, energyKwh: 210000, co2Tons: 172 },
    { month: 'Aug', audited: 390, complianceRate: 97, energyKwh: 280000, co2Tons: 230 },
    { month: 'Sep', audited: 480, complianceRate: 99, energyKwh: 345000, co2Tons: 282 },
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Executive Header Banner */}
      <div
        style={{
          padding: '28px 32px',
          background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%)',
          borderRadius: 'var(--radius-lg, 14px)',
          color: '#ffffff',
          boxShadow: '0 8px 24px rgba(15, 23, 42, 0.25)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 12px', borderRadius: '999px', background: 'rgba(255, 255, 255, 0.12)', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem' }}>🏛️</span>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#e0e7ff', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
              NATIONAL STANDARDS SURVEILLANCE & PIPELINE ARCHITECTURE
            </span>
          </div>
          <h1 style={{ margin: '0 0 8px 0', fontSize: '1.75rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
            Procurement Analytics & System Architecture
          </h1>
          <p style={{ margin: 0, fontSize: '0.92rem', color: '#c7d2fe', maxWidth: '780px', lineHeight: 1.55 }}>
            Real-time compliance surveillance across Indian government departments, sustainability metrics, and the end-to-end autonomous AI architecture pipeline.
          </p>
        </div>

        {/* Timeframe Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', background: 'rgba(255, 255, 255, 0.1)', padding: '4px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.15)' }}>
          {(['30d', '90d', 'all'] as const).map((t) => (
            <button
              key={t}
              onClick={() => {
                setActiveTimeframe(t);
                onToast(`Loaded analytics for ${t.toUpperCase()} window.`, 'info');
              }}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                background: activeTimeframe === t ? '#6366f1' : 'transparent',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '0.78rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {t === '30d' ? 'Last 30 Days' : t === '90d' ? 'Last Quarter' : 'All Time'}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '16px' }}>
        {[
          { label: 'Standards Analyzed', value: '10,480', trend: '+14% vs last month', icon: '📚', color: '#4f46e5', bg: 'rgba(79, 70, 229, 0.08)' },
          { label: 'Statutory QCO Enforced', value: '100.0%', trend: 'Zero Non-Compliant Bids', icon: '🛡️', color: '#059669', bg: 'rgba(5, 150, 105, 0.08)' },
          { label: 'Hallucinations Caught', value: '142', trend: 'IS 9999 & Fake Rules Blocked', icon: '🚫', color: '#dc2626', bg: 'rgba(220, 38, 38, 0.08)' },
          { label: 'Total Energy Savings', value: '1.14 GWh', trend: '₹91.2 Lakh Cost Offset', icon: '⚡', color: '#0284c7', bg: 'rgba(2, 132, 199, 0.08)' },
        ].map((kpi, idx) => (
          <div
            key={idx}
            style={{
              padding: '20px',
              background: '#ffffff',
              borderRadius: 'var(--radius-lg, 12px)',
              border: '1px solid #e2e8f0',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {kpi.label}
                </span>
                <div style={{ fontSize: '1.65rem', fontWeight: 900, color: '#0f172a', marginTop: '4px' }}>
                  {kpi.value}
                </div>
              </div>
              <div
                style={{
                  width: '40px',
                  height: '40px',
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
            <div style={{ marginTop: '10px', fontSize: '0.76rem', color: kpi.color, fontWeight: 700 }}>
              {kpi.trend}
            </div>
          </div>
        ))}
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 1: INTERACTIVE SYSTEM ARCHITECTURE DIAGRAM
          ═══════════════════════════════════════════════════════════ */}
      <Panel
        title="Interactive System Architecture & Intelligence Pipeline"
        subtitle="Visual end-to-end dataflow from procurement intent to verified, grounded specification. Click any stage to inspect its technical engine and operational impact."
        badge="System Architecture Diagram"
      >
        {/* Interactive Architecture Flow Ribbon */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '12px', scrollbarWidth: 'thin', marginBottom: '20px' }}>
          {pipelineStages.map((stage) => {
            const isSelected = stage.id === selectedStageId;
            return (
              <div
                key={stage.id}
                onClick={() => setSelectedStageId(stage.id)}
                style={{
                  flex: '1 0 170px',
                  padding: '14px 16px',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  border: isSelected ? `2px solid ${stage.color}` : '1px solid #e2e8f0',
                  background: isSelected ? '#ffffff' : '#f8fafc',
                  boxShadow: isSelected ? `0 6px 20px ${stage.color}25` : 'none',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontSize: '1.25rem' }}>{stage.icon}</span>
                  <span style={{ fontSize: '0.68rem', fontWeight: 800, padding: '2px 6px', borderRadius: '4px', background: isSelected ? stage.color : '#e2e8f0', color: isSelected ? '#fff' : '#64748b' }}>
                    STAGE {stage.step}
                  </span>
                </div>
                <div style={{ fontSize: '0.86rem', fontWeight: 800, color: '#0f172a', marginBottom: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {stage.name}
                </div>
                <div style={{ fontSize: '0.74rem', color: isSelected ? stage.color : '#64748b', fontWeight: 600 }}>
                  {stage.subtitle}
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Stage Detail Showcase Card */}
        <motion.div
          key={currentStage.id}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          style={{
            padding: '24px',
            background: 'linear-gradient(135deg, #f8fafc 0%, #ffffff 100%)',
            borderRadius: '12px',
            border: `1px solid ${currentStage.color}40`,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.04)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '50px',
                  height: '50px',
                  borderRadius: '12px',
                  background: `${currentStage.color}15`,
                  border: `1px solid ${currentStage.color}40`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.6rem',
                }}
              >
                {currentStage.icon}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: '4px', background: currentStage.color, color: '#fff' }}>
                    STAGE {currentStage.step} OF 6
                  </span>
                  <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>
                    {currentStage.subtitle}
                  </span>
                </div>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
                  {currentStage.name}
                </h3>
              </div>
            </div>

            <div style={{ padding: '8px 16px', borderRadius: '8px', background: `${currentStage.color}10`, border: `1px solid ${currentStage.color}30` }}>
              <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>BENCHMARK METRIC</span>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: currentStage.color }}>
                {currentStage.metric}
              </div>
            </div>
          </div>

          <p style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.6, margin: '0 0 16px 0' }}>
            {currentStage.description}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
            <div style={{ padding: '12px 14px', borderRadius: '8px', background: '#f1f5f9', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>
                🔧 Under the Hood Tech Stack:
              </span>
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b', marginTop: '2px' }}>
                {currentStage.techStack}
              </div>
            </div>

            <div style={{ padding: '12px 14px', borderRadius: '8px', background: '#f1f5f9', border: '1px solid #e2e8f0' }}>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase' }}>
                📦 Deliverable Payload:
              </span>
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b', marginTop: '2px' }}>
                {currentStage.output}
              </div>
            </div>
          </div>
        </motion.div>
      </Panel>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 2: STANDARDS COMPLIANCE & ECO TRACK ANALYTICS
          ═══════════════════════════════════════════════════════════ */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {/* Compliance Distribution Donut / Progress */}
        <Panel title="Statutory Standards Distribution" subtitle="Breakdown of ingested Indian Standards by enforcement mandate." badge="BIS Catalog">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '4px' }}>
            {complianceBreakdown.map((item) => (
              <div key={item.label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.84rem', fontWeight: 700, color: '#1e293b' }}>
                    {item.label}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.84rem', fontWeight: 800, color: item.color }}>
                      {item.count.toLocaleString()}
                    </span>
                    <span style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 600 }}>
                      ({item.pct}%)
                    </span>
                  </div>
                </div>
                <div style={{ height: '8px', width: '100%', background: '#e2e8f0', borderRadius: '999px', overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${item.pct}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    style={{ height: '100%', background: item.color, borderRadius: '999px' }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '20px', padding: '12px 14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '0.78rem', color: '#475569', lineHeight: 1.5 }}>
            <strong style={{ color: '#0f172a' }}>Statutory Note: </strong>
            100% of Quality Control Orders issued by DPIIT, Ministry of Power, and Ministry of Heavy Industries are cross-linked to ensure tender documents never violate GFR Rule 144(xi).
          </div>
        </Panel>

        {/* Monthly Energy & Carbon Offset Chart */}
        <Panel title="Green Procurement & Energy Saved" subtitle="Cumulative kWh savings and CO₂ reduction from statutory IE3/IE4 mandates." badge="Eco Track">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: '160px', padding: '10px 0 20px', borderBottom: '1px solid #cbd5e1' }}>
              {monthlyTrends.map((m, idx) => {
                const maxKwh = 350000;
                const heightPct = Math.round((m.energyKwh / maxKwh) * 100);
                return (
                  <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', flex: 1 }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#059669' }}>
                      {Math.round(m.energyKwh / 1000)}k
                    </span>
                    <div style={{ width: '28px', height: '110px', background: '#f1f5f9', borderRadius: '6px', display: 'flex', alignItems: 'flex-end', overflow: 'hidden' }}>
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${heightPct}%` }}
                        transition={{ duration: 0.6, delay: idx * 0.1 }}
                        style={{ width: '100%', background: 'linear-gradient(180deg, #10b981 0%, #059669 100%)', borderRadius: '6px' }}
                      />
                    </div>
                    <span style={{ fontSize: '0.76rem', color: '#64748b', fontWeight: 700 }}>
                      {m.month}
                    </span>
                  </div>
                );
              })}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '6px' }}>
              <div style={{ padding: '10px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', textAlign: 'center' }}>
                <span style={{ fontSize: '0.68rem', color: '#047857', fontWeight: 700, textTransform: 'uppercase' }}>Total Energy Saved</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#065f46' }}>1,120 MWh</div>
              </div>

              <div style={{ padding: '10px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.08)', border: '1px solid rgba(6, 182, 212, 0.25)', textAlign: 'center' }}>
                <span style={{ fontSize: '0.68rem', color: '#0e7490', fontWeight: 700, textTransform: 'uppercase' }}>CO₂ Emissions Reduced</span>
                <div style={{ fontSize: '1.25rem', fontWeight: 900, color: '#155e75' }}>917 Metric Tons</div>
              </div>
            </div>
          </div>
        </Panel>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 3: DEPARTMENTAL COMPLIANCE LEADERBOARD
          ═══════════════════════════════════════════════════════════ */}
      <Panel
        title="Departmental Compliance & Savings Surveillance"
        subtitle="Tracking statutory standard adherence across major procurement authorities and ministries."
        badge="Surveillance Feed"
      >
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: '#f8fafc', borderBottom: '2px solid #cbd5e1' }}>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 800 }}>Procuring Authority / Ministry</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 800 }}>Audited Tenders</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 800 }}>Statutory Compliance</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 800 }}>Cost Savings</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 800 }}>Avg Eco Score</th>
                <th style={{ padding: '12px 16px', color: '#475569', fontWeight: 800 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {departmentAnalytics.map((row, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #e2e8f0', background: idx % 2 === 0 ? '#ffffff' : '#fafbfc' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 700, color: '#0f172a' }}>
                    {row.dept}
                  </td>
                  <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#334155' }}>
                    {row.tenders}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ padding: '3px 8px', borderRadius: '4px', background: 'rgba(5, 150, 105, 0.1)', color: '#059669', fontWeight: 800, fontSize: '0.78rem' }}>
                      {row.compliance}%
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px', fontWeight: 800, color: '#4338ca', fontFamily: 'var(--font-mono)' }}>
                    {row.savings}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontWeight: 800, color: '#059669' }}>🌿 {row.ecoScore}/100</span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <button
                      onClick={() => {
                        onSelectTab('tender');
                        onToast(`Opening auditor for ${row.dept} tenders.`, 'info');
                      }}
                      style={{
                        padding: '4px 10px',
                        borderRadius: '6px',
                        background: '#f1f5f9',
                        border: '1px solid #cbd5e1',
                        color: '#334155',
                        fontWeight: 700,
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                      }}
                    >
                      Audit Tender ➔
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
};
