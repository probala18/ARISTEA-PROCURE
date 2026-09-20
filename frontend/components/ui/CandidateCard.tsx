'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CandidateStandard } from '@/lib/api';

interface CandidateCardProps {
  candidate: CandidateStandard;
  rank?: number;
  onExplore?: (standardId: string) => void;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, rank, onExplore }) => {
  const [showEvidence, setShowEvidence] = useState(false);

  const role = candidate.role?.toUpperCase() || (rank === 1 ? 'PRIMARY' : 'ALLIED');
  const scorePercent = Math.round((candidate.score || 0) * 100);

  const getRoleBadgeClass = () => {
    switch (role) {
      case 'PRIMARY':
        return 'badge-indigo';
      case 'TESTING':
        return 'badge-cyan';
      case 'SAFETY':
        return 'badge-amber';
      case 'ALLIED':
      default:
        return 'badge-purple';
    }
  };

  return (
    <div
      className="glass-panel-interactive"
      style={{
        padding: '20px 22px',
        marginBottom: '14px',
        borderRadius: 'var(--radius-md)',
        background: '#ffffff',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '280px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {rank !== undefined && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '26px',
                  height: '26px',
                  borderRadius: '6px',
                  background: 'rgba(79, 70, 229, 0.08)',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  color: 'var(--accent-primary)',
                }}
              >
                #{rank}
              </span>
            )}
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '1.05rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                letterSpacing: '0.01em',
              }}
            >
              {candidate.standard_id}
            </span>
            <span className={`badge ${getRoleBadgeClass()}`}>{role}</span>
            {candidate.status && (
              <span
                style={{
                  fontSize: '0.75rem',
                  color: candidate.status.toLowerCase().includes('active') || candidate.status.toLowerCase().includes('valid')
                    ? 'var(--status-success)'
                    : 'var(--status-warning)',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: candidate.status.toLowerCase().includes('active') || candidate.status.toLowerCase().includes('valid')
                      ? 'var(--status-success)'
                      : 'var(--status-warning)',
                  }}
                />
                {candidate.status}
              </span>
            )}
          </div>

          <h4
            style={{
              fontSize: '0.98rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              marginTop: '8px',
              lineHeight: 1.45,
            }}
          >
            {candidate.title || 'Standard Title Unavailable'}
          </h4>

          {candidate.matched_terms && candidate.matched_terms.length > 0 && (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '10px' }}>
              {candidate.matched_terms.slice(0, 5).map((term, i) => (
                <span
                  key={i}
                  style={{
                    fontSize: '0.72rem',
                    padding: '3px 9px',
                    borderRadius: 'var(--radius-full)',
                    background: '#f1f5f9',
                    color: 'var(--text-secondary)',
                    fontWeight: 600,
                    border: '1px solid #e2e8f0',
                  }}
                >
                  {term}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Score & Explore Action */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '10px' }}>
          <div style={{ textAlign: 'right' }}>
            <div
              style={{
                fontSize: '1.25rem',
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                color: scorePercent >= 70 ? 'var(--accent-primary)' : scorePercent >= 50 ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              }}
            >
              {scorePercent}%
            </div>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Confidence
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="btn-secondary"
              style={{ padding: '6px 14px', fontSize: '0.8rem' }}
            >
              {showEvidence ? 'Hide Evidence ▲' : 'Evidence ▼'}
            </button>

            {onExplore && (
              <button
                onClick={() => onExplore(candidate.standard_id)}
                className="btn-primary"
                style={{ padding: '6px 14px', fontSize: '0.8rem' }}
              >
                Explorer ↗
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Accordion Evidence Drawer */}
      <AnimatePresence>
        {showEvidence && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
            style={{
              marginTop: '16px',
              paddingTop: '16px',
              borderTop: '1px solid #f1f5f9',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                background: '#f8fafc',
                padding: '14px 18px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #e2e8f0',
                fontSize: '0.84rem',
              }}
            >
              <div style={{ fontWeight: 700, color: 'var(--accent-primary-dark)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>🔍</span> Grounded Provenance & Match Rationale:
              </div>
              {candidate.match_reasons && candidate.match_reasons.length > 0 ? (
                <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {candidate.match_reasons.map((reason, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      {reason}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>
                  Matched through semantic embeddings, canonical keyword resolution, and BIS domain relationship ontology.
                </p>
              )}
              {candidate.evidence?.text_snippet && (
                <div
                  style={{
                    marginTop: '10px',
                    fontStyle: 'italic',
                    color: 'var(--text-secondary)',
                    borderLeft: '3px solid var(--accent-primary)',
                    paddingLeft: '10px',
                    background: '#ffffff',
                    padding: '8px 12px',
                    borderRadius: '0 6px 6px 0',
                  }}
                >
                  "{candidate.evidence.text_snippet}"
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
