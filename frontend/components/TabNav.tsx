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
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(12px)',
          padding: '6px',
          borderRadius: 'var(--radius-full)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
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
                    background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.3) 0%, rgba(13, 148, 136, 0.5) 100%)',
                    border: '1px solid rgba(20, 184, 166, 0.6)',
                    boxShadow: '0 0 15px rgba(20, 184, 166, 0.3)',
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
                    background: isActive ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                    color: isActive ? '#ffffff' : 'var(--text-dim)',
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
