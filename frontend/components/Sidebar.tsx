'use client';

import React from 'react';
import { TabKey } from './TabNav';

interface SidebarProps {
  activeTab: TabKey;
  onSelectTab: (tab: TabKey) => void;
  isBackendHealthy: boolean;
}

interface NavItem {
  key: TabKey;
  label: string;
  sublabel: string;
  icon: string;
  badge?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  isBackendHealthy,
}) => {
  const navItems: NavItem[] = [
    {
      key: 'dashboard',
      label: 'Dashboard',
      sublabel: 'Procurement Command Center',
      icon: '📊',
      badge: 'Live',
    },
    {
      key: 'autopilot',
      label: 'Autopilot',
      sublabel: 'Need → Cited Tender',
      icon: '🚀',
      badge: 'New',
    },
    {
      key: 'tender',
      label: 'Document Auditor',
      sublabel: 'Visual Redline, Measurements & Audit',
      icon: '📋',
      badge: 'Audit',
    },
    {
      key: 'recommend',
      label: 'Semantic Matcher',
      sublabel: 'Grounded IS Discovery',
      icon: '⚡',
      badge: 'Core',
    },
    {
      key: 'standard',
      label: 'Standards Directory',
      sublabel: 'Official BIS Catalog & Meta',
      icon: '📚',
    },
    {
      key: 'services',
      label: 'BIS Service Hub',
      sublabel: 'Licences & Ministries',
      icon: '🏛️',
      badge: 'Hub',
    },
    {
      key: 'simplify',
      label: 'Clause Explainer',
      sublabel: 'Plain Language Translator',
      icon: '📖',
    },

    {
      key: 'compliance',
      label: 'Compliance & QCO',
      sublabel: 'Statutory Orders & Schemes',
      icon: '🛡️',
      badge: 'GFR',
    },
    {
      key: 'spec',
      label: 'Spec Workspace',
      sublabel: 'Grounded Clause Drafting',
      icon: '📝',
    },
    {
      key: 'voice',
      label: 'Voice Assistant',
      sublabel: 'Indic Speech AI (Whisper)',
      icon: '🎙️',
      badge: 'AI',
    },
    {
      key: 'history',
      label: 'Session History',
      sublabel: 'Recent Queries & Audits',
      icon: '🕒',
    },
  ];

  return (
    <aside className="dashboard-sidebar">
      {/* Brand Header */}
      <div
        style={{
          padding: '22px 20px 18px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#ffffff',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
            flexShrink: 0,
          }}
        >
          <img
            src="/logo.png"
            alt="The BOLD Si6X Logo"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              display: 'block',
            }}
          />
        </div>
        <div className="sidebar-brand-text">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span
              style={{
                fontSize: '1.05rem',
                fontWeight: 800,
                color: 'var(--text-primary)',
                letterSpacing: '-0.02em',
              }}
            >
              ARISTEA
            </span>
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                color: 'var(--accent-primary)',
                background: 'var(--accent-primary-subtle)',
                padding: '2px 6px',
                borderRadius: '4px',
                letterSpacing: '0.04em',
              }}
            >
              PROCURE
            </span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            PS 26108 · Indian Standards Hub
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div style={{ flex: 1, padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto' }}>
        <div
          className="sidebar-section-heading"
          style={{
            fontSize: '0.68rem',
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--text-dim)',
            padding: '2px 10px 6px',
          }}
        >
          Procurement Intelligence
        </div>

        {navItems.map((item) => {
          const isActive = activeTab === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onSelectTab(item.key)}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                width: '100%',
                padding: '10px 12px',
                borderRadius: 'var(--radius-md)',
                background: isActive ? 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: isActive ? '0 4px 14px rgba(79, 70, 229, 0.3)' : 'none',
              }}
            >
              <span
                style={{
                  fontSize: '1.15rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '22px',
                }}
              >
                {item.icon}
              </span>
              <div className="sidebar-nav-text" style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: '0.84rem',
                    fontWeight: isActive ? 700 : 600,
                    color: isActive ? '#ffffff' : 'var(--text-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>{item.label}</span>
                  {item.badge && (
                    <span
                      style={{
                        fontSize: '0.62rem',
                        fontWeight: 800,
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-full)',
                        background: isActive ? 'rgba(255, 255, 255, 0.25)' : 'rgba(79, 70, 229, 0.08)',
                        color: isActive ? '#ffffff' : 'var(--accent-primary)',
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
                <div
                  style={{
                    fontSize: '0.7rem',
                    color: isActive ? 'rgba(255, 255, 255, 0.8)' : 'var(--text-muted)',
                    marginTop: '1px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {item.sublabel}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* System Status Footer */}
      <div
        className="sidebar-footer-text"
        style={{
          padding: '14px 16px',
          borderTop: '1px solid var(--border-subtle)',
          background: '#f8fafc',
        }}
      >
        <div
          style={{
            background: '#ffffff',
            padding: '10px 12px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 1px 2px rgba(0, 0, 0, 0.02)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Database
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className={`pulse-dot ${isBackendHealthy ? 'pulse-dot-green' : 'pulse-dot-red'}`} />
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: isBackendHealthy ? 'var(--status-success)' : 'var(--status-danger)' }}>
                {isBackendHealthy ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
          <div style={{ fontSize: '0.74rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
            sih_bis.db (9.4 MB)
          </div>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            268 Standards · 710 QCOs · 75 Licences
          </div>
        </div>

        <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
            v1.0.0 Enterprise
          </span>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '0.7rem',
              color: 'var(--accent-primary)',
              textDecoration: 'none',
              fontWeight: 700,
            }}
          >
            API Specs ↗
          </a>
        </div>
      </div>
    </aside>
  );
};
