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
  'Energy efficient induction motors for industrial water pumping installations',
  'PVC insulated copper electric cables for rated voltages up to 1100 V',
  'Electrical installations of buildings wiring safety practices and earthing',
  'Drinking water physical chemical and bacteriological specifications',
];

export const RecommendView: React.FC<RecommendViewProps> = ({ onExploreStandard, onToast }) => {
  const [queryText, setQueryText] = useState(
    'Three phase squirrel cage induction motors for industrial pumping applications with high energy efficiency'
  );
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
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <Panel
        title="Semantic Standards Recommendation"
        subtitle="AI-driven ontology mapping to identify primary, allied, testing, and safety BIS standards."
        badge="Module 7-9"
      >
        <form onSubmit={handleSubmit}>
          {/* Quick preset chips */}
          <div style={{ marginBottom: '16px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '8px' }}>
              Quick Presets:
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {SAMPLE_QUERIES.map((sample, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQueryText(sample)}
                  style={{
                    padding: '5px 12px',
                    borderRadius: 'var(--radius-full)',
                    background: 'rgba(255, 255, 255, 0.04)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    color: 'var(--text-secondary)',
                    fontSize: '0.76rem',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-teal)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)')}
                >
                  {sample.slice(0, 42)}...
                </button>
              ))}
            </div>
          </div>

          {/* Textarea */}
          <div style={{ marginBottom: '18px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.85rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                marginBottom: '6px',
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
            />
          </div>

          {/* Controls row */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              marginBottom: '22px',
            }}
          >
            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Context Type
              </label>
              <select value={contextType} onChange={(e) => setContextType(e.target.value)}>
                <option value="tender_specification">Tender Technical Specification</option>
                <option value="product_design">Product Design & Engineering</option>
                <option value="safety_audit">Safety & Compliance Audit</option>
                <option value="general_procurement">General Procurement</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Min Confidence Threshold ({Math.round(minConfidence * 100)}%)
              </label>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={minConfidence}
                onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-teal)', cursor: 'pointer' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Max Results (Top K)
              </label>
              <select value={topK} onChange={(e) => setTopK(parseInt(e.target.value, 10))}>
                <option value={3}>Top 3</option>
                <option value={5}>Top 5</option>
                <option value={8}>Top 8</option>
                <option value={12}>Top 12</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" disabled={isLoading} className="btn-primary" style={{ minWidth: '180px' }}>
              {isLoading ? (
                <>
                  <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⟳</span>
                  Analyzing...
                </>
              ) : (
                <>
                  <span>🔍</span>
                  Run Recommendation
                </>
              )}
            </button>
          </div>
        </form>
      </Panel>

      {/* Results Section */}
      {isLoading && (
        <Panel title="Analyzing Standards Ontology...">
          <LoadingSkeleton height="70px" />
          <LoadingSkeleton height="70px" />
          <LoadingSkeleton height="70px" />
        </Panel>
      )}

      {!isLoading && results && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              margin: '20px 0 14px',
              padding: '0 4px',
            }}
          >
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Recommended Standards ({results.recommendations?.length || 0})
              </h3>
              {results.execution_time_ms !== undefined && (
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Computed in {results.execution_time_ms.toFixed(1)} ms
                </span>
              )}
            </div>

            {results.primary_standard && (
              <span className="badge badge-teal">
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
            <Panel style={{ textAlign: 'center', padding: '40px' }}>
              <p style={{ color: 'var(--text-muted)' }}>
                No standards met the minimum confidence threshold of {Math.round(minConfidence * 100)}%. Try lowering the
                threshold or expanding your requirement query.
              </p>
            </Panel>
          )}
        </motion.div>
      )}
    </div>
  );
};
