'use client';

import React from 'react';
import { motion } from 'framer-motion';

export type TabKey =
  | 'dashboard'
  | 'autopilot'
  | 'recommend'
  | 'standard'
  | 'compliance'
  | 'tender'
  | 'spec'
  | 'services'
  | 'simplify'
  | 'voice'
  | 'history';

interface TabNavProps {
  activeTab: TabKey;
  onChange: (tab: TabKey) => void;
}

interface TabItem {
  key: TabKey;
  label: string;
  badge?: string;
  icon: string;
}

const TABS: TabItem[] = [
  { key: 'dashboard', label: 'Dashboard', badge: 'Live', icon: '📊' },
  { key: 'autopilot', label: 'Autopilot', badge: 'New', icon: '🚀' },
  { key: 'recommend', label: 'Semantic Matcher', icon: '⚡' },
  { key: 'standard', label: 'Standards Directory', icon: '📚' },
  { key: 'services', label: 'BIS Service Hub', badge: 'Hub', icon: '🏛️' },
  { key: 'simplify', label: 'Clause Explainer', icon: '📖' },
  { key: 'compliance', label: 'QCO Compliance', badge: 'GFR', icon: '🛡️' },
  { key: 'tender', label: 'Document Auditor & Redline', badge: 'Audit', icon: '📋' },
  { key: 'spec', label: 'Spec Workspace', icon: '📝' },
  { key: 'voice', label: 'Voice AI', badge: 'Speech', icon: '🎙️' },
  { key: 'history', label: 'Session History', icon: '🕒' },
];

export const TabNav: React.FC<TabNavProps> = ({ activeTab, onChange }) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '14px 0 24px',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: '4px',
          background: '#ffffff',
          padding: '5px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border-subtle)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
          overflowX: 'auto',
          maxWidth: '100%',
        }}
      >
        {TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onChange(tab.key)}
              style={{
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                borderRadius: 'var(--radius-full)',
                border: 'none',
                background: 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? 700 : 600,
                fontSize: '0.84rem',
                cursor: 'pointer',
                transition: 'color 0.2s ease',
                zIndex: 1,
                whiteSpace: 'nowrap',
              }}
            >
              {isActive && (
                <motion.div
                  layoutId="activeTabPill"
                  transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                  style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: 'var(--radius-full)',
                    background: 'linear-gradient(135deg, #4f46e5 0%, #4338ca 100%)',
                    boxShadow: '0 4px 14px rgba(79, 70, 229, 0.35)',
                    zIndex: -1,
                  }}
                />
              )}
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  style={{
                    fontSize: '0.62rem',
                    padding: '1px 6px',
                    borderRadius: '999px',
                    background: isActive ? 'rgba(255, 255, 255, 0.25)' : 'rgba(79, 70, 229, 0.08)',
                    color: isActive ? '#ffffff' : 'var(--accent-primary)',
                    fontWeight: 700,
                  }}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
