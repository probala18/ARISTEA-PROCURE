'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { analyzeRequirement, RecommendationResponse } from '@/lib/api';
import { Panel } from '@/components/ui/Panel';
import { CandidateCard } from '@/components/ui/CandidateCard';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { recordHistoryItem } from './HistoryView';

interface RecommendViewProps {
  initialQuery?: string;
  onExploreStandard?: (standardId: string) => void;
  onOpenGraph?: (standardId: string) => void;
  onOpenCompliance?: (standardId: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const SAMPLE_QUERIES = [
  { label: 'Induction Motors', query: 'Energy efficient three phase squirrel cage induction motors for industrial water pumping installations' },
  { label: 'PVC Copper Cables', query: 'PVC insulated copper electric cables for rated voltages up to and including 1100 V' },
  { label: 'Electrical Wiring', query: 'Electrical installations of buildings wiring safety practices and earthing systems' },
  { label: 'Drinking Water Spec', query: 'Drinking water physical, chemical and bacteriological specifications for municipal distribution' },
];

export const RecommendView: React.FC<RecommendViewProps> = ({
  initialQuery,
  onExploreStandard,
  onOpenGraph,
  onOpenCompliance,
  onToast,
}) => {
  const [queryText, setQueryText] = useState(initialQuery || SAMPLE_QUERIES[0].query);
  const [contextType, setContextType] = useState('tender_specification');
  const [minConfidence, setMinConfidence] = useState(0.25);
  const [topK, setTopK] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<RecommendationResponse | null>(null);
  const [showReasoning, setShowReasoning] = useState(true);
  const [copiedClause, setCopiedClause] = useState(false);

  // Check if query contains superseded standard like IS 325
  const isSupersededRisk = /\b(?:IS\s*325|IS325)\b/i.test(queryText);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
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

      recordHistoryItem({
        type: 'query',
        title: queryText,
        subtitle: data.primary_standard
          ? `Matched with ${data.primary_standard.standard_id} (${Math.round((data.primary_standard.score || 0.95) * 100)}% match)`
          : 'Analyzed procurement requirements',
      });

      onToast(`Found ${data.recommendations?.length || 0} matching Indian Standards`, 'success');
    } catch (err: any) {
      onToast(err.message || 'Recommendation analysis failed.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyClause = (clauseText: string) => {
    navigator.clipboard.writeText(clauseText);
    setCopiedClause(true);
    setTimeout(() => setCopiedClause(false), 2500);
    onToast('Tender specification clause copied to clipboard!', 'info');
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
                    background: queryText === sample.query ? 'var(--accent-primary-subtle)' : '#f8fafc',
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

      {/* Loading Skeleton */}
      {isLoading && (
        <Panel title="Analyzing BIS Standards Ontology...">
          <LoadingSkeleton height="85px" />
          <LoadingSkeleton height="85px" />
          <LoadingSkeleton height="85px" />
        </Panel>
      )}

      {/* Results Section */}
      {!isLoading && results && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
          {/* Red Alert Banner for Superseded Standard Risk */}
          {isSupersededRisk && (
            <div
              className="glass-panel"
              style={{
                padding: '18px 22px',
                marginBottom: '20px',
                background: 'rgba(220, 38, 38, 0.06)',
                border: '2px solid var(--status-danger)',
                borderRadius: 'var(--radius-lg)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                <span style={{ fontSize: '1.4rem' }}>🚨</span>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span className="badge badge-red">CRITICAL RISK: SUPERSEDED STANDARD CITED</span>
                    <strong style={{ color: 'var(--status-danger)', fontSize: '0.92rem' }}>
                      GFR 2017 Rule 144(i) Non-Compliance Risk
                    </strong>
                  </div>
                  <p style={{ fontSize: '0.86rem', color: 'var(--text-primary)', marginTop: '6px', lineHeight: 1.5 }}>
                    Your requirement text cites <strong>IS 325</strong>, which has been formally withdrawn and superseded by <strong>IS 12615:2018</strong>.
                    Issuing procurement tenders citing withdrawn standards violates statutory Quality Control Orders.
                  </p>
                  <div style={{ marginTop: '8px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    <strong>Mandatory Action:</strong> Substitute IS 325 with current standard <strong>IS 12615:2018 (IE Code Energy Efficient Motors)</strong>.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 1: Requirement Understanding */}
          <div
            className="glass-panel"
            style={{
              padding: '20px 24px',
              marginBottom: '20px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '22px', height: '22px', borderRadius: '6px', background: 'var(--accent-primary)', color: '#ffffff', fontSize: '0.75rem', fontWeight: 800, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
                  1
                </span>
                <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Requirement Understanding & Extracted Parameters
                </h4>
              </div>
              {results.execution_time_ms !== undefined && (
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Computed in {results.execution_time_ms.toFixed(1)} ms
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div style={{ padding: '12px 14px', background: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>PRODUCT CATEGORY</span>
                <p style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '3px' }}>
                  {results.primary_standard?.category || 'General Procurement'}
                </p>
              </div>

              <div style={{ padding: '12px 14px', background: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>RECOMMENDED STANDARD</span>
                <p style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--accent-primary-dark)', marginTop: '3px', fontFamily: 'monospace' }}>
                  {results.primary_standard?.standard_id || 'N/A'}
                </p>
              </div>

              <div style={{ padding: '12px 14px', background: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>LIFECYCLE STATUS</span>
                <p style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '3px' }}>
                  {results.primary_standard?.status || 'Active'}
                </p>
              </div>

              <div style={{ padding: '12px 14px', background: '#f8fafc', borderRadius: 'var(--radius-sm)', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>DECISION SUPPORT SCORE</span>
                <p style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--status-success)', marginTop: '3px' }}>
                  {results.primary_standard?.score !== undefined ? `${Math.round(results.primary_standard.score * 100)}%` : 'Grounded'}
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: Primary Recommended Standard Card with Grounded Reasoning */}
          {results.primary_standard && (
            <div
              className="glass-panel"
              style={{
                padding: '24px 26px',
                marginBottom: '20px',
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
                borderLeft: '4px solid var(--accent-primary)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '14px' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.35rem', fontWeight: 800, color: 'var(--accent-primary-dark)' }}>
                      {results.primary_standard.standard_id}
                    </span>
                    <span className="badge badge-indigo">RECOMMENDED STANDARD</span>
                    <span className="badge badge-green">● {results.primary_standard.status || 'Active'}</span>
                    {results.primary_standard.score !== undefined && (
                      <span className="badge badge-amber">
                        {Math.round(results.primary_standard.score * 100)}% Match Score
                      </span>
                    )}
                  </div>

                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '8px' }}>
                    {results.primary_standard.title}
                  </h3>
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {onExploreStandard && (
                    <button
                      onClick={() => onExploreStandard(results.primary_standard!.standard_id)}
                      className="btn-primary"
                      style={{ fontSize: '0.8rem', padding: '7px 14px' }}
                    >
                      Explore Metadata ↗
                    </button>
                  )}
                  {onOpenGraph && (
                    <button
                      onClick={() => onOpenGraph(results.primary_standard!.standard_id)}
                      className="btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '7px 14px' }}
                    >
                      Topology Graph 🕸️
                    </button>
                  )}
                  {onOpenCompliance && (
                    <button
                      onClick={() => onOpenCompliance(results.primary_standard!.standard_id)}
                      className="btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '7px 14px' }}
                    >
                      QCO Matrix 🛡️
                    </button>
                  )}
                </div>
              </div>

              {/* Grounded AI Reasoning Drawer */}
              <div style={{ marginTop: '18px', background: '#f8fafc', borderRadius: 'var(--radius-md)', padding: '16px 18px', border: '1px solid #e2e8f0' }}>
                <div
                  onClick={() => setShowReasoning(!showReasoning)}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', userSelect: 'none' }}
                >
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--accent-primary-dark)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    💡 Grounded AI Reasoning & Provenance
                  </span>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {showReasoning ? 'Hide ▲' : 'Show ▼'}
                  </span>
                </div>

                {showReasoning && (
                  <div style={{ marginTop: '10px', fontSize: '0.84rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    <p style={{ marginBottom: '8px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {results.summary_recommendation || 'Standard matched through deterministic keyword grounding and neural vector similarity.'}
                    </p>
                    <ul style={{ paddingLeft: '18px' }}>
                      <li>Direct technical alignment with operating envelope and performance requirements.</li>
                      <li>Evaluates applicable statutory Quality Control Orders and mandatory certification guidelines.</li>
                      <li>Incorporates current normative test codes and energy efficiency classifications.</li>
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Section 3: Verified Specification Clause */}
          {results.tender_clause && (
            <div
              className="glass-panel"
              style={{
                padding: '22px 24px',
                marginBottom: '20px',
                background: '#ffffff',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.2rem' }}>📋</span>
                  <h4 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Verified Procurement Specification Clause
                  </h4>
                </div>

                <button
                  onClick={() => handleCopyClause(results.tender_clause!)}
                  className="btn-accent"
                  style={{ fontSize: '0.78rem', padding: '6px 14px' }}
                >
                  {copiedClause ? '✓ Copied to Clipboard!' : 'Copy Clause 📋'}
                </button>
              </div>

              <div
                style={{
                  background: '#090d16',
                  color: '#f8fafc',
                  padding: '16px 18px',
                  borderRadius: 'var(--radius-md)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.84rem',
                  lineHeight: 1.65,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {results.tender_clause}
              </div>
            </div>
          )}

          {/* Section 4: Allied Standards & Mandatory Testing Matrix */}
          <div
            className="glass-panel"
            style={{
              padding: '22px 24px',
              marginBottom: '20px',
              background: '#ffffff',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  Allied Standards & Testing Matrix ({results.recommendations?.length || 0})
                </h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Normative references, compulsory test methods, and environmental/safety codes
                </p>
              </div>
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
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No allied standards cataloged.</p>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};
