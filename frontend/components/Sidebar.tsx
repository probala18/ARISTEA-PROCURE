'use client';

import React from 'react';
import { motion } from 'framer-motion';
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
      key: 'recommend',
      label: 'Semantic Matcher',
      sublabel: 'Grounded IS Discovery',
      icon: '⚡',
      badge: 'Core',
    },
    {
      key: 'standard',
      label: 'Standards Explorer',
      sublabel: 'Lifecycle, Graph & Compliance',
      icon: '🏛️',
    },
    {
      key: 'tender',
      label: 'Tender Auditor',
      sublabel: 'RFP Parsing & Spec Generator',
      icon: '📋',
      badge: 'Audit',
    },
    {
      key: 'voice',
      label: 'Voice Assistant',
      sublabel: 'Indic Speech Procurement',
      icon: '🎙️',
      badge: 'AI',
    },
  ];

  return (
    <aside className="dashboard-sidebar">
      {/* Brand Header */}
      <div
        style={{
          padding: '24px 24px 20px',
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
            background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            fontSize: '1.2rem',
            fontWeight: 800,
            boxShadow: '0 4px 12px rgba(79, 70, 229, 0.35)',
            flexShrink: 0,
          }}
        >
          A
        </div>
        <div>
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
          <div style={{ fontSize: '0.73rem', color: 'var(--text-muted)', marginTop: '2px' }}>
            PS 26108 · BIS Intelligence
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div style={{ flex: 1, padding: '20px 14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div
          style={{
            fontSize: '0.7rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--text-dim)',
            padding: '4px 10px 8px',
          }}
        >
          Procurement Modules
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
                gap: '12px',
                width: '100%',
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                background: isActive ? 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                boxShadow: isActive ? '0 4px 14px rgba(79, 70, 229, 0.32)' : 'none',
              }}
            >
              <span
                style={{
                  fontSize: '1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '24px',
                }}
              >
                {item.icon}
              </span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: '0.88rem',
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
                        fontSize: '0.65rem',
                        fontWeight: 700,
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
                    fontSize: '0.72rem',
                    color: isActive ? 'rgba(255, 255, 255, 0.8)' : 'var(--text-muted)',
                    marginTop: '2px',
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
        style={{
          padding: '18px 20px',
          borderTop: '1px solid var(--border-subtle)',
          background: '#f8fafc',
        }}
      >
        <div
          style={{
            background: '#ffffff',
            padding: '12px 14px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            boxShadow: '0 1px 2px rgba(0, 0, 0, 0.02)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
              Database
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className={`pulse-dot ${isBackendHealthy ? 'pulse-dot-green' : 'pulse-dot-red'}`} />
              <span style={{ fontSize: '0.72rem', fontWeight: 600, color: isBackendHealthy ? 'var(--status-success)' : 'var(--status-danger)' }}>
                {isBackendHealthy ? 'Grounded' : 'Offline'}
              </span>
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
            sih_bis.db (9.4 MB)
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            14 Modules · Strict Schema
          </div>
        </div>

        <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
            v1.0.0 Enterprise
          </span>
          <a
            href="/api/health"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '0.72rem',
              color: 'var(--accent-primary)',
              textDecoration: 'none',
              fontWeight: 600,
            }}
          >
            API Specs ↗
          </a>
        </div>
      </div>
    </aside>
  );
};
