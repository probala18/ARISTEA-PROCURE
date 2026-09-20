'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { analyzeRequirement, RecommendationResponse } from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { CandidateCard } from '@/components/ui/CandidateCard';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

interface RecommendViewProps {
  onExploreStandard?: (standardId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const SAMPLE_QUERIES = [
  { label: 'Induction Motors', query: 'Energy efficient three phase squirrel cage induction motors for industrial water pumping installations' },
  { label: 'PVC Copper Cables', query: 'PVC insulated copper electric cables for rated voltages up to and including 1100 V' },
  { label: 'Electrical Wiring', query: 'Electrical installations of buildings wiring safety practices and earthing systems' },
  { label: 'Drinking Water', query: 'Drinking water physical, chemical and bacteriological specifications for municipal distribution' },
];

export const RecommendView: React.FC<RecommendViewProps> = ({ onExploreStandard, onToast }) => {
  const [queryText, setQueryText] = useState(SAMPLE_QUERIES[0].query);
  const [contextType, setContextType] = useState('tender_specification');
  const [minConfidence, setMinConfidence] = useState(0.25);
  const [topK, setTopK] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<RecommendationResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!queryText.trim()) {
      onToast('Please enter a procurement requirement query.', 'error');
      return;
    }

    setIsLoading(true);
    try {
      const data = await analyzeRequirement({
        requirement_text: queryText,
        context_type: contextType,
        min_confidence: minConfidence,
        top_k: topK,
      });
      setResults(data);
      onToast(`Found ${data.recommendations?.length || 0} matching Indian Standards`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Recommendation analysis failed.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <Panel
        title="Semantic Procurement Matcher"
        subtitle="Hybrid vector embeddings and BIS ontology graph mapping to identify primary, allied, testing, and safety standards."
        badge="Module 7-9"
      >
        <form onSubmit={handleSubmit}>
          {/* Quick preset chips */}
          <div style={{ marginBottom: '18px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px', fontWeight: 600 }}>
              Quick Scenario Presets:
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {SAMPLE_QUERIES.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQueryText(sample.query)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 'var(--radius-full)',
                    background: queryText === sample.query ? 'rgba(79, 70, 229, 0.08)' : '#f8fafc',
                    border: `1px solid ${queryText === sample.query ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                    color: queryText === sample.query ? 'var(--accent-primary-dark)' : 'var(--text-secondary)',
                    fontSize: '0.78rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  ⚡ {sample.label}
                </button>
              ))}
            </div>
          </div>

          {/* Textarea */}
          <div style={{ marginBottom: '18px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.86rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: '8px',
              }}
            >
              Procurement Technical Requirement / Clause
            </label>
            <textarea
              rows={4}
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              placeholder="Describe equipment specifications, technical parameters, or paste tender clauses..."
              required
              style={{
                fontSize: '0.94rem',
                lineHeight: 1.5,
              }}
            />
          </div>

          {/* Controls row */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '22px',
              background: '#f8fafc',
              padding: '16px 18px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Procurement Context Type
              </label>
              <select value={contextType} onChange={(e) => setContextType(e.target.value)}>
                <option value="tender_specification">Tender Technical Specification</option>
                <option value="product_design">Product Design & Engineering</option>
                <option value="safety_audit">Safety & Compliance Audit</option>
                <option value="general_procurement">General Procurement</option>
              </select>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Min Confidence Threshold
                </label>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                  {Math.round(minConfidence * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={minConfidence}
                onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-primary)', cursor: 'pointer' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Max Results (Top K)
              </label>
              <select value={topK} onChange={(e) => setTopK(parseInt(e.target.value, 10))}>
                <option value={3}>Top 3 Candidates</option>
                <option value={5}>Top 5 Candidates</option>
                <option value={8}>Top 8 Candidates</option>
                <option value={12}>Top 12 Candidates</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" disabled={isLoading} className="btn-primary" style={{ minWidth: '190px' }}>
              {isLoading ? (
                <>
                  <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>
                  Analyzing Ontology...
                </>
              ) : (
                <>
                  <span>⚡</span>
                  Run Matcher
                </>
              )}
            </button>
          </div>
        </form>
      </Panel>

      {/* Results Section */}
      {isLoading && (
        <Panel title="Analyzing BIS Standards Ontology...">
          <LoadingSkeleton height="85px" />
          <LoadingSkeleton height="85px" />
          <LoadingSkeleton height="85px" />
        </Panel>
      )}

      {!isLoading && results && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              margin: '22px 0 16px',
              padding: '0 4px',
              flexWrap: 'wrap',
              gap: '10px',
            }}
          >
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
                Recommended Indian Standards ({results.recommendations?.length || 0})
              </h3>
              {results.execution_time_ms !== undefined && (
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Grounded in {results.execution_time_ms.toFixed(1)} ms via hybrid semantic retrieval
                </span>
              )}
            </div>

            {results.primary_standard && (
              <span className="badge badge-indigo">
                Primary Standard: {results.primary_standard.standard_id}
              </span>
            )}
          </div>

          {results.recommendations && results.recommendations.length > 0 ? (
            <div>
              {results.recommendations.map((cand, idx) => (
                <CandidateCard
                  key={cand.standard_id || idx}
                  candidate={cand}
                  rank={idx + 1}
                  onExplore={onExploreStandard}
                />
              ))}
            </div>
          ) : (
            <Panel style={{ textAlign: 'center', padding: '48px 24px' }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>🔍</div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
                No Standards Exceeded Threshold
              </h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', maxWidth: '500px', margin: '0 auto' }}>
                No standards met the minimum confidence threshold of {Math.round(minConfidence * 100)}%. Try lowering the
                threshold or adding technical keywords to your requirement.
              </p>
            </Panel>
          )}
        </motion.div>
      )}
    </div>
  );
};
