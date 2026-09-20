'use client';

import React, { useEffect, useState } from 'react';
import { checkHealth, HealthResponse } from '@/lib/api';
import { motion } from 'framer-motion';

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
        backgroundColor: 'rgba(7, 9, 14, 0.82)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
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
              background: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(20, 184, 166, 0.4)',
              fontWeight: 800,
              fontSize: '1.2rem',
              color: '#ffffff',
            }}
          >
            A
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: 800, fontSize: '1.15rem', letterSpacing: '-0.02em' }}>
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
              background: 'rgba(15, 23, 42, 0.7)',
              borderRadius: 'var(--radius-full)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              fontSize: '0.8rem',
            }}
          >
            <span
              className={`pulse-dot ${
                isOnline === true ? 'pulse-dot-green' : isOnline === false ? 'pulse-dot-red' : ''
              }`}
              style={{ backgroundColor: isOnline === null ? '#94a3b8' : undefined }}
            />
            <span style={{ color: 'var(--text-secondary)' }}>
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
