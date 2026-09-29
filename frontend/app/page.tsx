'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/Sidebar';
import { Header } from '@/components/Header';
import { TabKey } from '@/components/TabNav';
import { RecommendView } from '@/components/views/RecommendView';
import { StandardView } from '@/components/views/StandardView';
import { GraphView } from '@/components/views/GraphView';
import { ComplianceView } from '@/components/views/ComplianceView';
import { TenderView } from '@/components/views/TenderView';
import { SpecView } from '@/components/views/SpecView';
import { VoiceView } from '@/components/views/VoiceView';
import { HistoryView } from '@/components/views/HistoryView';
import { ServiceHubView } from '@/components/views/ServiceHubView';
import { SimplifyView } from '@/components/views/SimplifyView';
import { AutopilotView } from '@/components/views/AutopilotView';
import { RedlineView } from '@/components/views/RedlineView';
import { ToastContainer, ToastMessage } from '@/components/ui/Toast';
import { animateHeroText } from '@/lib/gsap-animations';
import { checkHealth } from '@/lib/api';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabKey>('autopilot');
  const [explorerStandardId, setExplorerStandardId] = useState<string>('IS 12615:2018');
  const [activeQuery, setActiveQuery] = useState<string>('');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [isOnline, setIsOnline] = useState<boolean>(true);

  const heroHeadlineRef = useRef<HTMLHeadingElement>(null);
  const heroSubtitleRef = useRef<HTMLParagraphElement>(null);
  const heroBadgesRef = useRef<HTMLDivElement>(null);

  // Health check polling
  useEffect(() => {
    const runCheck = async () => {
      try {
        await checkHealth();
        setIsOnline(true);
      } catch {
        setIsOnline(false);
      }
    };
    runCheck();
    const timer = setInterval(runCheck, 15000);
    return () => clearInterval(timer);
  }, []);

  // GSAP Hero Text Reveal on mount
  useEffect(() => {
    if (heroHeadlineRef.current) animateHeroText(heroHeadlineRef.current);
    if (heroSubtitleRef.current) animateHeroText(heroSubtitleRef.current);
    if (heroBadgesRef.current) animateHeroText(heroBadgesRef.current);
  }, []);

  const addToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const newToast: ToastMessage = {
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      type,
      message,
    };
    setToasts((prev) => [...prev, newToast]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== newToast.id));
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const handleExploreStandard = (stdId: string) => {
    setExplorerStandardId(stdId);
    setActiveTab('standard');
    addToast(`Opened explorer for ${stdId}`, 'info');
  };

  const handleOpenGraph = (stdId: string) => {
    setExplorerStandardId(stdId);
    setActiveTab('graph');
    addToast(`Opened topology graph for ${stdId}`, 'info');
  };

  const handleOpenCompliance = (stdId: string) => {
    setExplorerStandardId(stdId);
    setActiveTab('compliance');
    addToast(`Opened QCO matrix for ${stdId}`, 'info');
  };

  const handleSelectQueryFromHistory = (query: string) => {
    setActiveQuery(query);
    setActiveTab('recommend');
    addToast('Loaded query from history into matcher.', 'info');
  };

  return (
    <div className="dashboard-layout">
      {/* Left Fixed Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isBackendHealthy={isOnline}
      />

      {/* Main Workspace Stage */}
      <div className="dashboard-main">
        {/* Top App Bar */}
        <Header
          activeTab={activeTab}
          onExploreStandard={handleExploreStandard}
          onNavigateTab={setActiveTab}
          onSearchQuery={handleSelectQueryFromHistory}
        />

        {/* Content Container */}
        <main className="dashboard-content">
          {/* Executive Hero Banner */}
          <section
            style={{
              padding: '24px 0 16px',
              maxWidth: '960px',
              margin: '0 auto',
              textAlign: 'center',
            }}
          >
            <div
              ref={heroBadgesRef}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '4px 16px',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(79, 70, 229, 0.08)',
                border: '1px solid rgba(79, 70, 229, 0.22)',
                marginBottom: '14px',
              }}
            >
              <span style={{ fontSize: '0.78rem', color: 'var(--accent-primary-dark)', fontWeight: 700 }}>
                ⚡ PS 26108 · Indian Standards Intelligence Platform
              </span>
            </div>

            <h1
              ref={heroHeadlineRef}
              style={{
                fontSize: 'clamp(1.85rem, 3.6vw, 2.8rem)',
                fontWeight: 800,
                letterSpacing: '-0.03em',
                lineHeight: 1.18,
                marginBottom: '12px',
                background: 'linear-gradient(135deg, #0f172a 20%, #312e81 60%, #4338ca 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Intelligent Indian Standards Reasoning for Public Procurement
            </h1>

            <p
              ref={heroSubtitleRef}
              style={{
                fontSize: 'clamp(0.9rem, 1.5vw, 1.02rem)',
                color: 'var(--text-secondary)',
                lineHeight: 1.6,
                marginBottom: '18px',
                maxWidth: '780px',
                margin: '0 auto 18px',
              }}
            >
              Real-time BIS ontology reasoning, automated tender compliance auditing, version supersession tracking,
              and specification drafting for enterprise and government procurement.
            </p>

            {/* Trust Markers Bar */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '24px',
                flexWrap: 'wrap',
                fontSize: '0.8rem',
                color: 'var(--text-muted)',
                fontWeight: 600,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--status-success)' }}>✓</span> 268 Verified BIS Standards
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--status-success)' }}>✓</span> 710 Statutory QCO Records
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--status-success)' }}>✓</span> 75 Verified Product Licences
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--status-success)' }}>✓</span> 100% Provenance Coverage
              </div>
            </div>
          </section>

          {/* Animated Dynamic Workspace Container */}
          <div style={{ marginTop: '16px' }}>
            <AnimatePresence mode="wait">
              {activeTab === 'autopilot' && (
                <motion.div
                  key="autopilot"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <AutopilotView onExploreStandard={handleExploreStandard} onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'recommend' && (
                <motion.div
                  key="recommend"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <RecommendView
                    initialQuery={activeQuery || undefined}
                    onExploreStandard={handleExploreStandard}
                    onOpenGraph={handleOpenGraph}
                    onOpenCompliance={handleOpenCompliance}
                    onToast={addToast}
                  />
                </motion.div>
              )}

              {activeTab === 'standard' && (
                <motion.div
                  key="standard"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <StandardView initialStandardId={explorerStandardId} onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'graph' && (
                <motion.div
                  key="graph"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <GraphView
                    initialStandardId={explorerStandardId}
                    onExploreStandard={handleExploreStandard}
                    onToast={addToast}
                  />
                </motion.div>
              )}

              {activeTab === 'compliance' && (
                <motion.div
                  key="compliance"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <ComplianceView
                    initialStandardId={explorerStandardId}
                    onExploreStandard={handleExploreStandard}
                    onToast={addToast}
                  />
                </motion.div>
              )}

              {activeTab === 'tender' && (
                <motion.div
                  key="tender"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <TenderView onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'redline' && (
                <motion.div
                  key="redline"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <RedlineView onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'services' && (
                <motion.div
                  key="services"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <ServiceHubView
                    onExploreStandard={handleExploreStandard}
                    onSelectQuery={handleSelectQueryFromHistory}
                    onToast={addToast}
                  />
                </motion.div>
              )}

              {activeTab === 'simplify' && (
                <motion.div
                  key="simplify"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <SimplifyView
                    initialStandardId={explorerStandardId}
                    onExploreStandard={handleExploreStandard}
                    onGenerateSpec={(stdId) => {
                      setExplorerStandardId(stdId);
                      setActiveTab('spec');
                      addToast(`Drafting procurement spec for ${stdId}`, 'info');
                    }}
                    onToast={addToast}
                  />
                </motion.div>
              )}

              {activeTab === 'spec' && (
                <motion.div
                  key="spec"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <SpecView onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'voice' && (
                <motion.div
                  key="voice"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <VoiceView onExploreStandard={handleExploreStandard} onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'history' && (
                <motion.div
                  key="history"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                >
                  <HistoryView
                    onSelectQuery={handleSelectQueryFromHistory}
                    onExploreStandard={handleExploreStandard}
                    onToast={addToast}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>

        {/* Global Footer */}
        <footer
          style={{
            borderTop: '1px solid var(--border-subtle)',
            padding: '24px 32px',
            background: '#ffffff',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            marginTop: 'auto',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              maxWidth: '1400px',
              margin: '0 auto',
            }}
          >
            <div>
              <strong style={{ color: 'var(--text-primary)' }}>ARISTEA-PROCURE</strong> • Problem Statement 26108 • Smart India Hackathon
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
              All recommendations grounded deterministically in verified Bureau of Indian Standards catalog data.
            </div>
          </div>
        </footer>
      </div>

      {/* Floating System Toasts */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}
