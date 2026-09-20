'use client';

import React, { useEffect, useState } from 'react';
import { checkHealth, HealthResponse } from '@/lib/api';

export const Header: React.FC = () => {
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
    const interval = setInterval(fetchHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        backgroundColor: 'rgba(255, 255, 255, 0.88)',
        borderBottom: '1px solid var(--border-subtle)',
        boxShadow: '0 1px 4px rgba(0, 0, 0, 0.04)',
        padding: '14px 0',
      }}
    >
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Brand & Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #0d9488 0%, #0f766e 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 2px 10px rgba(13, 148, 136, 0.3)',
              fontWeight: 800,
              fontSize: '1.2rem',
              color: '#ffffff',
            }}
          >
            A
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '1.15rem', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                ARISTEA<span style={{ color: 'var(--accent-teal)' }}>-PROCURE</span>
              </span>
              <span className="badge badge-teal" style={{ fontSize: '0.65rem' }}>
                PS 26108
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Indian Standards Intelligence & Tender Compliance Engine
            </p>
          </div>
        </div>

        {/* Right Status Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              background: 'rgba(241, 245, 249, 0.9)',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.8rem',
            }}
          >
            <span
              className={`pulse-dot ${
                isOnline === true ? 'pulse-dot-green' : isOnline === false ? 'pulse-dot-red' : ''
              }`}
              style={{ backgroundColor: isOnline === null ? '#94a3b8' : undefined }}
            />
            <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
              {isOnline === true
                ? `Backend Online v${health?.version || '1.0'}`
                : isOnline === false
                ? 'Backend Offline'
                : 'Connecting...'}
            </span>
          </div>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            API Docs ↗
          </a>
        </div>
      </div>
    </header>
  );
};
