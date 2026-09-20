'use client';

import React from 'react';
import { motion } from 'framer-motion';

export type TabKey = 'recommend' | 'standard' | 'tender' | 'voice';

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
  { key: 'recommend', label: 'Semantic Recommendation', icon: '🔍' },
  { key: 'standard', label: 'Standards Explorer & Graph', icon: '📚' },
  { key: 'tender', label: 'Tender Audit & Spec Gen', badge: 'Module 11-13', icon: '📑' },
  { key: 'voice', label: 'Voice Query AI', badge: 'Module 10', icon: '🎙️' },
];

export const TabNav: React.FC<TabNavProps> = ({ activeTab, onChange }) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '28px 0',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: '4px',
          background: 'rgba(241, 245, 249, 0.9)',
          backdropFilter: 'blur(12px)',
          padding: '6px',
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
                gap: '8px',
                padding: '10px 20px',
                borderRadius: 'var(--radius-full)',
                border: 'none',
                background: 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.9rem',
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
                    background: 'linear-gradient(135deg, #0d9488 0%, #0f766e 100%)',
                    boxShadow: '0 4px 12px rgba(13, 148, 136, 0.3)',
                    zIndex: -1,
                  }}
                />
              )}
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  style={{
                    fontSize: '0.65rem',
                    padding: '2px 7px',
                    borderRadius: '999px',
                    background: isActive ? 'rgba(255, 255, 255, 0.25)' : 'rgba(15, 23, 42, 0.06)',
                    color: isActive ? '#ffffff' : 'var(--text-muted)',
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
