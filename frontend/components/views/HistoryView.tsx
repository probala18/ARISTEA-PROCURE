'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Panel } from '@/components/ui/Panel';

interface HistoryViewProps {
  onSelectQuery?: (query: string) => void;
  onExploreStandard?: (stdId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

interface HistoryItem {
  id: string;
  type: 'query' | 'standard' | 'tender';
  title: string;
  subtitle?: string;
  timestamp: string;
}

const STORAGE_KEY = 'aristea_procure_session_history';

export function recordHistoryItem(item: Omit<HistoryItem, 'id' | 'timestamp'>) {
  if (typeof window === 'undefined') return;
  try {
    const existing: HistoryItem[] = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const newItem: HistoryItem = {
      ...item,
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    // Deduplicate identical title
    const filtered = existing.filter((x) => x.title !== item.title);
    const updated = [newItem, ...filtered].slice(0, 30);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // Ignore storage issues
  }
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  onSelectQuery,
  onExploreStandard,
  onToast,
}) => {
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);

  const loadHistory = () => {
    if (typeof window === 'undefined') return;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setHistoryItems(JSON.parse(stored));
      } else {
        setHistoryItems([]);
      }
    } catch {
      setHistoryItems([]);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleClear = () => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(STORAGE_KEY);
    setHistoryItems([]);
    onToast('Search and audit history cleared.', 'info');
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Session Activity & Audit History"
        subtitle="Browser-local activity log of recent queries, explored standards, and audited tenders for the current session only."
        badge="Current Session"
        action={
          historyItems.length > 0 && (
            <button onClick={handleClear} className="btn-secondary" style={{ fontSize: '0.78rem', padding: '6px 14px' }}>
              Clear History 🗑️
            </button>
          )
        }
      >
        {historyItems.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🕒</div>
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
              No recent activity in this session.
            </h4>
            <p style={{ fontSize: '0.84rem' }}>
              Genuine queries run in the Semantic Matcher, standards opened, or tenders audited will be recorded here.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {historyItems.map((item) => (
              <div
                key={item.id}
                className="glass-panel-interactive"
                style={{
                  padding: '16px 20px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                  background: '#ffffff',
                }}
              >
                <div style={{ flex: 1, minWidth: '240px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span className={`badge ${item.type === 'query' ? 'badge-indigo' : item.type === 'standard' ? 'badge-cyan' : 'badge-amber'}`}>
                      {item.type.toUpperCase()}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.timestamp}
                    </span>
                  </div>

                  <h4 style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {item.title}
                  </h4>
                  {item.subtitle && (
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {item.subtitle}
                    </p>
                  )}
                </div>

                <div>
                  {item.type === 'query' && onSelectQuery && (
                    <button
                      onClick={() => onSelectQuery(item.title)}
                      className="btn-primary"
                      style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                    >
                      Re-run Query ⚡
                    </button>
                  )}

                  {item.type === 'standard' && onExploreStandard && (
                    <button
                      onClick={() => onExploreStandard(item.title)}
                      className="btn-primary"
                      style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                    >
                      Open Standard 🏛️
                    </button>
                  )}

                  {item.type === 'tender' && (
                    <span className="badge badge-indigo" style={{ fontSize: '0.74rem' }}>
                      Audit Cached
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
};
