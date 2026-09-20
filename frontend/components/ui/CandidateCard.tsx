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
        return 'badge-teal';
      case 'TESTING':
        return 'badge-blue';
      case 'SAFETY':
        return 'badge-red';
      case 'ALLIED':
      default:
        return 'badge-purple';
    }
  };

  return (
    <div
      className="glass-panel-interactive"
      style={{
        padding: '18px 20px',
        marginBottom: '14px',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            {rank !== undefined && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '24px',
                  height: '24px',
                  borderRadius: '6px',
                  background: 'rgba(15, 23, 42, 0.06)',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  color: 'var(--text-secondary)',
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
                letterSpacing: '0.02em',
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
                  fontWeight: 500,
                }}
              >
                ● {candidate.status}
              </span>
            )}
          </div>

          <h4
            style={{
              fontSize: '0.98rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              marginTop: '6px',
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
                    padding: '2px 8px',
                    borderRadius: '4px',
                    background: 'rgba(15, 23, 42, 0.05)',
                    color: 'var(--text-secondary)',
                    fontWeight: 500,
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
            <span
              style={{
                fontSize: '1.15rem',
                fontWeight: 800,
                fontFamily: 'var(--font-mono)',
                color: scorePercent >= 70 ? 'var(--accent-teal)' : scorePercent >= 50 ? '#0284c7' : 'var(--text-secondary)',
              }}
            >
              {scorePercent}%
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block' }}>
              Confidence
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.78rem' }}
            >
              {showEvidence ? 'Hide Evidence ▲' : 'Evidence ▼'}
            </button>

            {onExplore && (
              <button
                onClick={() => onExplore(candidate.standard_id)}
                className="btn-primary"
                style={{ padding: '6px 12px', fontSize: '0.78rem' }}
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
              paddingTop: '14px',
              borderTop: '1px solid var(--border-subtle)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                background: 'rgba(241, 245, 249, 0.95)',
                padding: '12px 16px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.82rem',
              }}
            >
              <div style={{ fontWeight: 600, color: 'var(--accent-teal-dark)', marginBottom: '6px' }}>
                Provenance & Evidence Grounding:
              </div>
              {candidate.match_reasons && candidate.match_reasons.length > 0 ? (
                <ul style={{ paddingLeft: '18px', color: 'var(--text-secondary)' }}>
                  {candidate.match_reasons.map((reason, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      {reason}
                    </li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>
                  Matched through semantic similarity and domain relationship ontology.
                </p>
              )}
              {candidate.evidence?.text_snippet && (
                <div
                  style={{
                    marginTop: '8px',
                    fontStyle: 'italic',
                    color: 'var(--text-secondary)',
                    borderLeft: '2px solid var(--accent-teal)',
                    paddingLeft: '8px',
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
