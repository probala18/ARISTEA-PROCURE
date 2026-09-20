'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface PanelProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  title?: string;
  subtitle?: string;
  badge?: string;
  action?: React.ReactNode;
}

export const Panel: React.FC<PanelProps> = ({
  children,
  className = '',
  style = {},
  title,
  subtitle,
  badge,
  action,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`glass-panel ${className}`}
      style={{
        padding: '28px',
        marginBottom: '24px',
        background: '#ffffff',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-card)',
        ...style,
      }}
    >
      {(title || subtitle || action) && (
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            marginBottom: '22px',
            borderBottom: '1px solid #f1f5f9',
            paddingBottom: '16px',
            gap: '16px',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              {title && (
                <h3 style={{ fontSize: '1.22rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.015em' }}>
                  {title}
                </h3>
              )}
              {badge && <span className="badge badge-indigo">{badge}</span>}
            </div>
            {subtitle && (
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.5 }}>
                {subtitle}
              </p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </motion.div>
  );
};
