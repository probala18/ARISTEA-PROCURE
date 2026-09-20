'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Header } from '@/components/Header';
import { TabNav, TabKey } from '@/components/TabNav';
import { RecommendView } from '@/components/views/RecommendView';
import { StandardView } from '@/components/views/StandardView';
import { TenderView } from '@/components/views/TenderView';
import { VoiceView } from '@/components/views/VoiceView';
import { ToastContainer, ToastMessage } from '@/components/ui/Toast';
import { animateHeroText } from '@/lib/gsap-animations';

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabKey>('recommend');
  const [explorerStandardId, setExplorerStandardId] = useState<string>('IS 12615:2018');
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const heroHeadlineRef = useRef<HTMLHeadingElement>(null);
  const heroSubtitleRef = useRef<HTMLParagraphElement>(null);
  const heroBadgesRef = useRef<HTMLDivElement>(null);

  // Run GSAP Hero Text Reveal on mount
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
    addToast(`Switched to explorer for ${stdId}`, 'info');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />

      {/* Main Container */}
      <main className="container" style={{ flex: 1, paddingBottom: '60px' }}>
        {/* Hero Section */}
        <section
          style={{
            textAlign: 'center',
            padding: '48px 0 24px',
            maxWidth: '850px',
            margin: '0 auto',
          }}
        >
          <div
            ref={heroBadgesRef}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 14px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(20, 184, 166, 0.1)',
              border: '1px solid rgba(20, 184, 166, 0.3)',
              marginBottom: '16px',
            }}
          >
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-teal)', fontWeight: 600 }}>
              ⚡ PS 26108 Grounded Architecture
            </span>
          </div>

          <h1
            ref={heroHeadlineRef}
            style={{
              fontSize: 'clamp(2rem, 5vw, 3.2rem)',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              lineHeight: 1.15,
              marginBottom: '16px',
              background: 'linear-gradient(135deg, #ffffff 30%, #94a3b8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Intelligent Procurement Grounded in Indian Standards
          </h1>

          <p
            ref={heroSubtitleRef}
            style={{
              fontSize: 'clamp(0.95rem, 2vw, 1.12rem)',
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
              marginBottom: '24px',
            }}
          >
            Real-time BIS ontology reasoning, automated tender compliance auditing, version supersession tracking,
            and specification drafting for enterprise and government procurement.
          </p>

          {/* Quick Metrics Bar */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '24px',
              flexWrap: 'wrap',
              fontSize: '0.82rem',
              color: 'var(--text-muted)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: 'var(--accent-teal)' }}>✓</span> 100% Grounded BIS Citations
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: 'var(--accent-teal)' }}>✓</span> Zero Spec Hallucinations
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: 'var(--accent-teal)' }}>✓</span> QCO & Regulatory Tracking
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: 'var(--accent-teal)' }}>✓</span> Multilingual Speech AI
            </div>
          </div>
        </section>

        {/* Tab Navigation */}
        <TabNav activeTab={activeTab} onChange={setActiveTab} />

        {/* Animated Tab View Container */}
        <AnimatePresence mode="wait">
          {activeTab === 'recommend' && (
            <motion.div
              key="recommend"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25 }}
            >
              <RecommendView onExploreStandard={handleExploreStandard} onToast={addToast} />
            </motion.div>
          )}

          {activeTab === 'standard' && (
            <motion.div
              key="standard"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25 }}
            >
              <StandardView initialStandardId={explorerStandardId} onToast={addToast} />
            </motion.div>
          )}

          {activeTab === 'tender' && (
            <motion.div
              key="tender"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25 }}
            >
              <TenderView onToast={addToast} />
            </motion.div>
          )}

          {activeTab === 'voice' && (
            <motion.div
              key="voice"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25 }}
            >
              <VoiceView onExploreStandard={handleExploreStandard} onToast={addToast} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid rgba(255, 255, 255, 0.06)',
          padding: '28px 0',
          background: 'rgba(7, 9, 14, 0.95)',
          fontSize: '0.82rem',
          color: 'var(--text-dim)',
          textAlign: 'center',
        }}
      >
        <div className="container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <div>
            ARISTEA-PROCURE • Problem Statement 26108 • Built for Smart India Hackathon
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.76rem' }}>
            Disclaimer: Grounded in verified BIS catalog records. All recommendations and specification clauses are decision-support outputs.
          </div>
        </div>
      </footer>

      {/* Floating Toasts */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}
