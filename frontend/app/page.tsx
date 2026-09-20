'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/Sidebar';
import { Header } from '@/components/Header';
import { TabNav, TabKey } from '@/components/TabNav';
import { RecommendView } from '@/components/views/RecommendView';
import { StandardView } from '@/components/views/StandardView';
import { TenderView } from '@/components/views/TenderView';
import { VoiceView } from '@/components/views/VoiceView';
import { ToastContainer, ToastMessage } from '@/components/ui/Toast';
import { animateHeroText } from '@/lib/gsap-animations';
import { checkHealth } from '@/lib/api';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabKey>('recommend');
  const [explorerStandardId, setExplorerStandardId] = useState<string>('IS 12615:2018');
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

  return (
    <div className="dashboard-layout">
      {/* Left Executive Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isBackendHealthy={isOnline}
      />

      {/* Main Workspace Stage */}
      <div className="dashboard-main">
        {/* Top App Bar */}
        <Header activeTab={activeTab} onExploreStandard={handleExploreStandard} />

        {/* Content Container */}
        <main className="dashboard-content">
          {/* Executive Hero Banner */}
          <section
            style={{
              padding: '28px 0 20px',
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
                padding: '5px 16px',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(79, 70, 229, 0.08)',
                border: '1px solid rgba(79, 70, 229, 0.22)',
                marginBottom: '16px',
              }}
            >
              <span style={{ fontSize: '0.78rem', color: 'var(--accent-primary-dark)', fontWeight: 700 }}>
                ⚡ PS 26108 · Indian Standards Intelligence Architecture
              </span>
            </div>

            <h1
              ref={heroHeadlineRef}
              style={{
                fontSize: 'clamp(1.9rem, 3.8vw, 2.9rem)',
                fontWeight: 800,
                letterSpacing: '-0.03em',
                lineHeight: 1.18,
                marginBottom: '14px',
                background: 'linear-gradient(135deg, #0f172a 20%, #312e81 60%, #4338ca 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              AI-Powered Indian Standards Intelligence for Public Procurement
            </h1>

            <p
              ref={heroSubtitleRef}
              style={{
                fontSize: 'clamp(0.92rem, 1.6vw, 1.05rem)',
                color: 'var(--text-secondary)',
                lineHeight: 1.6,
                marginBottom: '20px',
                maxWidth: '780px',
                margin: '0 auto 20px',
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
                <span style={{ color: 'var(--status-success)' }}>✓</span> Grounded BIS Citations
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--status-success)' }}>✓</span> Zero Spec Hallucinations
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--status-success)' }}>✓</span> QCO & Regulatory Tracking
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--status-success)' }}>✓</span> Multilingual Speech AI
              </div>
            </div>
          </section>

          {/* Quick Mobile / Tablet Tab Switcher (Visible on small screens) */}
          <div className="md:hidden" style={{ display: 'none' }}>
            <TabNav activeTab={activeTab} onChange={setActiveTab} />
          </div>

          {/* Animated Dynamic View Container */}
          <div style={{ marginTop: '20px' }}>
            <AnimatePresence mode="wait">
              {activeTab === 'recommend' && (
                <motion.div
                  key="recommend"
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.28, ease: 'easeOut' }}
                >
                  <RecommendView onExploreStandard={handleExploreStandard} onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'standard' && (
                <motion.div
                  key="standard"
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.28, ease: 'easeOut' }}
                >
                  <StandardView initialStandardId={explorerStandardId} onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'tender' && (
                <motion.div
                  key="tender"
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.28, ease: 'easeOut' }}
                >
                  <TenderView onToast={addToast} />
                </motion.div>
              )}

              {activeTab === 'voice' && (
                <motion.div
                  key="voice"
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.28, ease: 'easeOut' }}
                >
                  <VoiceView onExploreStandard={handleExploreStandard} onToast={addToast} />
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
              All recommendations grounded deterministically in verified BIS catalog data.
            </div>
          </div>
        </footer>
      </div>

      {/* Floating System Toasts */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}
