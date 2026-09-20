'use client';

import React, { useEffect, useState } from 'react';
import { checkHealth, HealthResponse } from '@/lib/api';
import { TabKey } from './TabNav';

interface HeaderProps {
  activeTab?: TabKey;
  onExploreStandard?: (stdId: string) => void;
}

const TAB_TITLES: Record<TabKey, { title: string; desc: string }> = {
  recommend: {
    title: 'Semantic Requirement Matcher',
    desc: 'Neural matching & deterministic graph grounding against Bureau of Indian Standards catalog',
  },
  standard: {
    title: 'Standards Directory & Metadata',
    desc: 'Authoritative IS catalog records, publication years, ICS codes, and normative references',
  },
  graph: {
    title: 'Knowledge Graph Topology',
    desc: 'Interactive radial node visualization of direct, allied, and testing relationships',
  },
  compliance: {
    title: 'Compliance & Quality Control Orders',
    desc: 'Quality Control Orders (QCO), mandatory vs voluntary schemes, and regulatory divergences',
  },
  tender: {
    title: 'Tender Document Auditor',
    desc: 'Multi-format RFP parsing (PDF, DOCX, TXT), clause detection, and gap analysis',
  },
  spec: {
    title: 'Specification Drafting Workspace',
    desc: 'Formulate, edit, and export legally grounded technical clauses and inspection plans',
  },
  voice: {
    title: 'Voice Procurement Assistant',
    desc: 'Multi-lingual voice query input, Whisper STT transcription & audio response playback',
  },
  history: {
    title: 'Session Activity & History',
    desc: 'Local history of analyzed requirements, explored standards, and audited tenders',
  },
};

export const Header: React.FC<HeaderProps> = ({ activeTab = 'recommend' }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOnline, setIsOnline] = useState<boolean | null>(null);

  const fetchHealth = async () => {
    try {
      const res = await checkHealth();
      setHealth(res);
      setIsOnline(true);
    } catch {
      setIsOnline(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const currentTabInfo = TAB_TITLES[activeTab] || TAB_TITLES.recommend;

  return (
    <header className="dashboard-header">
      {/* Left: Breadcrumbs & Current Workspace */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            ARISTEA-PROCURE
          </span>
          <span style={{ fontSize: '0.76rem', color: 'var(--text-dim)' }}>/</span>
          <span style={{ fontSize: '0.82rem', color: 'var(--accent-primary)', fontWeight: 800 }}>
            {currentTabInfo.title}
          </span>
        </div>
      </div>

      {/* Right: Live Status, BIS Certification Pill & Docs */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '4px 12px',
            borderRadius: 'var(--radius-full)',
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.76rem',
            boxShadow: '0 1px 2px rgba(0, 0, 0, 0.03)',
          }}
        >
          <span
            className={`pulse-dot ${
              isOnline === true ? 'pulse-dot-green' : isOnline === false ? 'pulse-dot-red' : ''
            }`}
            style={{ backgroundColor: isOnline === null ? '#94a3b8' : undefined }}
          />
          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>
            {isOnline === true
              ? `API Ready (v${health?.version || '1.0'})`
              : isOnline === false
              ? 'Backend Offline'
              : 'Connecting...'}
          </span>
        </div>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: 'var(--radius-full)',
            background: 'rgba(79, 70, 229, 0.08)',
            border: '1px solid rgba(79, 70, 229, 0.2)',
            fontSize: '0.74rem',
            fontWeight: 700,
            color: 'var(--accent-primary-dark)',
          }}
        >
          <span>🛡️</span> BIS Grounded
        </div>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="btn-secondary"
          style={{ fontSize: '0.76rem', padding: '5px 12px', borderRadius: 'var(--radius-sm)' }}
        >
          OpenAPI ↗
        </a>
      </div>
    </header>
  );
};
