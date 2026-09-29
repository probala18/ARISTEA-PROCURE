'use client';

import React, { useEffect, useState } from 'react';
import { checkHealth, HealthResponse } from '@/lib/api';
import { TabKey } from './TabNav';

interface HeaderProps {
  activeTab?: TabKey;
  onExploreStandard?: (stdId: string) => void;
  onNavigateTab?: (tab: TabKey) => void;
  onSearchQuery?: (query: string) => void;
}

const TAB_TITLES: Record<TabKey, { title: string; desc: string }> = {
  dashboard: {
    title: 'Procurement Command Center',
    desc: 'National public procurement intelligence dashboard, active KPI surveillance, and standard analytics',
  },
  analytics: {
    title: 'System Architecture & Procurement Analytics',
    desc: 'Live interactive pipeline diagram, statutory compliance metrics, energy offset charts & departmental leaderboard',
  },
  autopilot: {
    title: 'ARISTEA Autopilot',
    desc: 'Describe a need in any language — get a compliant, cited, red-teamed tender in minutes',
  },
  recommend: {
    title: 'Semantic Requirement Matcher',
    desc: 'Neural matching & deterministic graph grounding against Bureau of Indian Standards catalog',
  },
  standard: {
    title: 'Standards Directory & Metadata',
    desc: 'Authoritative IS catalog records, publication years, ICS codes, and normative references',
  },
  services: {
    title: 'BIS Service Hub & Regulatory Directory',
    desc: 'Verified product licences, ministry alignments, and conformity assessment schemes',
  },
  simplify: {
    title: 'Clause Explainer & Simplifier',
    desc: 'Plain-language procurement translation grounded in verified standard scope & metadata',
  },
  compliance: {
    title: 'Compliance & Quality Control Orders',
    desc: 'Quality Control Orders (QCO), mandatory vs voluntary schemes, and regulatory divergences',
  },
  tender: {
    title: 'Tender Document Auditor',
    desc: 'Multi-format RFP parsing, visual redline markup, measurements, comparison matrix & gap analysis',
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

export const Header: React.FC<HeaderProps> = ({
  activeTab = 'recommend',
  onExploreStandard,
  onNavigateTab,
  onSearchQuery,
}) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

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

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchQuery.trim();
    if (!q) return;

    // RULE 7: Deterministic Global Search Routing
    // 1. Exact IS standard pattern (e.g., IS 12615:2018, IS 694, IS-302)
    const isPattern = /^IS[\s\-_]*\d+/i;
    if (isPattern.test(q)) {
      if (onExploreStandard) onExploreStandard(q.toUpperCase());
      if (onNavigateTab) onNavigateTab('standard');
      setSearchQuery('');
      return;
    }

    // 2. Explicit service command
    const serviceKeywords = ['service', 'services', 'licence', 'license', 'ministry', 'crs', 'isi', 'hallmark', 'huid', 'schemes'];
    const isService = serviceKeywords.some((kw) => q.toLowerCase().includes(kw));
    if (isService) {
      if (onNavigateTab) onNavigateTab('services');
      setSearchQuery('');
      return;
    }

    // 3. Everything else -> Existing Recommendation API
    if (onSearchQuery) onSearchQuery(q);
    if (onNavigateTab) onNavigateTab('recommend');
    setSearchQuery('');
  };

  const currentTabInfo = TAB_TITLES[activeTab] || TAB_TITLES.recommend;

  return (
    <header className="dashboard-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
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

      {/* Middle: Unified Global Search Bar (Rule 7) */}
      <form onSubmit={handleGlobalSearch} style={{ flex: '1 1 320px', maxWidth: '500px', display: 'flex', alignItems: 'center', position: 'relative' }}>
        <input
          type="text"
          placeholder="Global Search (e.g. 'IS 12615', 'services', 'PVC cables')..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '7px 36px 7px 12px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-subtle)',
            background: '#ffffff',
            fontSize: '0.8rem',
            outline: 'none',
            boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
            transition: 'border-color 0.15s ease',
          }}
        />
        <button
          type="submit"
          style={{
            position: 'absolute',
            right: '6px',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontSize: '0.85rem',
            color: 'var(--text-muted)',
            padding: '4px',
          }}
          title="Search"
        >
          🔍
        </button>
      </form>

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
