'use client';

import React, { useState, useEffect } from 'react';
import { Panel } from '@/components/ui/Panel';
import {
  getProductLicences,
  getMinistryMappings,
  ProductLicenceRecord,
  MinistryMappingRecord,
} from '@/lib/api';

interface ServiceHubViewProps {
  onExploreStandard?: (standardId: string) => void;
  onSelectQuery?: (query: string) => void;
  onToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

export const ServiceHubView: React.FC<ServiceHubViewProps> = ({
  onExploreStandard,
  onSelectQuery,
  onToast,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'licences' | 'ministries' | 'schemes'>('overview');
  const [licences, setLicences] = useState<ProductLicenceRecord[]>([]);
  const [ministries, setMinistries] = useState<MinistryMappingRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [licenceSearch, setLicenceSearch] = useState<string>('');
  const [ministrySearch, setMinistrySearch] = useState<string>('');

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setLoading(true);
      try {
        const [licRes, minRes] = await Promise.all([
          getProductLicences(),
          getMinistryMappings(),
        ]);
        if (mounted) {
          setLicences(licRes || []);
          setMinistries(minRes || []);
        }
      } catch (err: any) {
        if (mounted) {
          onToast('Failed to load verified BIS service directory data.', 'error');
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      mounted = false;
    };
  }, [onToast]);

  const filteredLicences = licences.filter((lic) => {
    const q = licenceSearch.toLowerCase();
    return (
      lic.product_category.toLowerCase().includes(q) ||
      (lic.raw_count_str && lic.raw_count_str.toLowerCase().includes(q))
    );
  });

  const filteredMinistries = ministries.filter((m) => {
    const q = ministrySearch.toLowerCase();
    return (
      m.ministry_department.toLowerCase().includes(q) ||
      m.product_name.toLowerCase().includes(q) ||
      m.standard_number.toLowerCase().includes(q)
    );
  });

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Hero Banner */}
      <div
        className="glass-panel"
        style={{
          padding: '24px 28px',
          borderRadius: 'var(--radius-lg)',
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98))',
          color: '#ffffff',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span style={{ fontSize: '1.4rem' }}>🏛️</span>
              <span className="badge badge-cyan" style={{ fontSize: '0.75rem', letterSpacing: '0.05em' }}>
                REGULATORY & SERVICE DIRECTORY
              </span>
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: '4px 0 8px 0', letterSpacing: '-0.02em' }}>
              BIS Service Hub & Public Procurement Portal
            </h2>
            <p style={{ fontSize: '0.88rem', color: '#94a3b8', maxWidth: '750px', lineHeight: 1.5 }}>
              Access verified Bureau of Indian Standards (BIS) regulatory frameworks, product licence categories,
              and ministry procurement mappings from the authoritative local repository.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                padding: '10px 16px',
                borderRadius: 'var(--radius-md)',
                textAlign: 'center',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#38bdf8' }}>75</div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>Verified Licences</div>
            </div>
            <div
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                padding: '10px 16px',
                borderRadius: 'var(--radius-md)',
                textAlign: 'center',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399' }}>28</div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase' }}>Ministry Mappings</div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '8px', marginTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px', overflowX: 'auto' }}>
          {[
            { id: 'overview', label: 'Service Catalog & Guidance', icon: '📋' },
            { id: 'licences', label: `Product Licences (${licences.length})`, icon: '📜' },
            { id: 'ministries', label: `Ministry Mappings (${ministries.length})`, icon: '🏢' },
            { id: 'schemes', label: 'Certification Schemes & Policy', icon: '🛡️' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                background: activeTab === tab.id ? 'var(--brand-primary, #3b82f6)' : 'rgba(255,255,255,0.06)',
                color: activeTab === tab.id ? '#ffffff' : '#94a3b8',
                border: 'none',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.15s ease',
                whiteSpace: 'nowrap',
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* TAB 1: OVERVIEW & SERVICES */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
          {/* Card: Know Your Standard */}
          <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Know Your Standard</h3>
              <span className="badge badge-emerald">Verified Ingested</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Direct search and semantic matching over 268 verified Indian Standards across electrotechnical, civil, mechanical, chemical, and metallurgy divisions.
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => onSelectQuery && onSelectQuery('solar photovoltaic modules')}
                className="btn-primary"
                style={{ fontSize: '0.78rem', padding: '6px 12px' }}
              >
                Find Solar Modules 🔍
              </button>
              <button
                onClick={() => onExploreStandard && onExploreStandard('IS 12615:2018')}
                className="btn-secondary"
                style={{ fontSize: '0.78rem', padding: '6px 12px' }}
              >
                IS 12615:2018 ⚡
              </button>
            </div>
          </div>

          {/* Card: Product Certification / ISI */}
          <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Product Certification (ISI Scheme-I)</h3>
              <span className="badge badge-emerald">Verified Ingested</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Marking schemes for domestic and foreign manufacturers under Quality Control Orders (QCO) issued by DPIIT and parent ministries.
            </p>
            <button
              onClick={() => setActiveTab('licences')}
              className="btn-secondary"
              style={{ fontSize: '0.78rem', padding: '6px 12px' }}
            >
              Browse 75 Licence Records 📜
            </button>
          </div>

          {/* Card: Ministry Procurement Mappings */}
          <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Ministry Procurement Mappings</h3>
              <span className="badge badge-emerald">Verified Ingested</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Authoritative departmental procurement alignments linking 28 government ministries (MoP, MoHUA, MoRTH, etc.) to standard requirements.
            </p>
            <button
              onClick={() => setActiveTab('ministries')}
              className="btn-secondary"
              style={{ fontSize: '0.78rem', padding: '6px 12px' }}
            >
              Explore 28 Ministry Frameworks 🏢
            </button>
          </div>

          {/* Card: Compulsory Registration Scheme (CRS) */}
          <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>CRS (Scheme-II Electronics & IT)</h3>
              <span className="badge badge-cyan">Policy Grounded</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Self-declaration of conformity under MeitY orders for IT equipment, power adapters, displays, and battery storage systems.
            </p>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', background: 'var(--bg-secondary)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
              Self-declaration test reports required from BIS-recognized labs prior to portal registration.
            </div>
          </div>

          {/* Card: Testing Standards vs Laboratories (Strict Data Boundary) */}
          <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Testing Standards & Methods</h3>
              <span className="badge badge-emerald">Relationship Graph</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '10px' }}>
              Allied test methods (e.g. IS 10810 series for cables, IS 9000 environmental testing) linked via ARISTEA knowledge graph edges.
            </p>
            <div style={{ fontSize: '0.74rem', color: '#e11d48', background: '#ffe4e6', padding: '6px 10px', borderRadius: 'var(--radius-sm)', marginBottom: '8px' }}>
              Live GPS Lab Locator: <strong>Not available in current verified dataset</strong>
            </div>
          </div>

          {/* Card: Hallmarking & HUID (Strict Data Boundary) */}
          <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Hallmarking & Fineness (IS 1417)</h3>
              <span className="badge badge-amber">Standard Info Only</span>
            </div>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '10px' }}>
              Standards governing precious metal purities (Gold & Silver Jewellery).
            </p>
            <div style={{ fontSize: '0.74rem', color: '#e11d48', background: '#ffe4e6', padding: '6px 10px', borderRadius: 'var(--radius-sm)' }}>
              Real-time 6-digit HUID Serial Registry: <strong>Not available in current verified dataset</strong>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: PRODUCT LICENCES (75 Records) */}
      {activeTab === 'licences' && (
        <Panel
          title="Verified Product Licences"
          subtitle="Directory of 75 product licence categories ingested from official BIS certification records."
          badge="75 Records"
        >
          <div style={{ marginBottom: '16px', display: 'flex', gap: '12px' }}>
            <input
              type="text"
              placeholder="Search by product name, IS standard (e.g. IS 694), or licence category..."
              value={licenceSearch}
              onChange={(e) => setLicenceSearch(e.target.value)}
              className="input-field"
              style={{ flex: 1 }}
            />
            {licenceSearch && (
              <button onClick={() => setLicenceSearch('')} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
                Clear
              </button>
            )}
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Loading licence records...</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: 'var(--bg-secondary)', borderBottom: '2px solid var(--border-color)' }}>
                    <th style={{ padding: '10px 14px', fontWeight: 700 }}>ID</th>
                    <th style={{ padding: '10px 14px', fontWeight: 700 }}>Product Category</th>
                    <th style={{ padding: '10px 14px', fontWeight: 700 }}>Licence Count</th>
                    <th style={{ padding: '10px 14px', fontWeight: 700 }}>Source Dataset</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLicences.length === 0 ? (
                    <tr>
                      <td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                        No product licences matched "{licenceSearch}".
                      </td>
                    </tr>
                  ) : (
                    filteredLicences.map((lic) => (
                      <tr key={lic.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '10px 14px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>#{lic.id}</td>
                        <td style={{ padding: '10px 14px', fontWeight: 600, color: 'var(--text-primary)' }}>{lic.product_category}</td>
                        <td style={{ padding: '10px 14px' }}>
                          <span className="badge badge-cyan">
                            {lic.licence_count.toLocaleString()} licences
                          </span>
                        </td>
                        <td style={{ padding: '10px 14px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {lic.source_dataset}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}

      {/* TAB 3: MINISTRY MAPPINGS (28 Records) */}
      {activeTab === 'ministries' && (
        <Panel
          title="Ministry Procurement Mappings"
          subtitle="28 official ministry-to-standard frameworks ingested from verified government procurement guidelines."
          badge="28 Mappings"
        >
          <div style={{ marginBottom: '16px', display: 'flex', gap: '12px' }}>
            <input
              type="text"
              placeholder="Search ministry name (e.g. Power, Railways, Defence) or procurement item..."
              value={ministrySearch}
              onChange={(e) => setMinistrySearch(e.target.value)}
              className="input-field"
              style={{ flex: 1 }}
            />
            {ministrySearch && (
              <button onClick={() => setMinistrySearch('')} className="btn-secondary" style={{ fontSize: '0.8rem' }}>
                Clear
              </button>
            )}
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Loading ministry mappings...</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '16px' }}>
              {filteredMinistries.length === 0 ? (
                <div style={{ gridColumn: '1 / -1', padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No ministry mappings matched "{ministrySearch}".
                </div>
              ) : (
                filteredMinistries.map((m) => (
                  <div
                    key={m.id}
                    className="glass-panel-interactive"
                    style={{
                      padding: '16px 20px',
                      borderRadius: 'var(--radius-md)',
                      background: '#ffffff',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                        <span className="badge badge-indigo" style={{ fontSize: '0.74rem' }}>
                          {m.ministry_department}
                        </span>
                        {m.standard_number && (
                          <span className="badge badge-emerald" style={{ fontFamily: 'monospace', fontSize: '0.72rem' }}>
                            {m.standard_number}
                          </span>
                        )}
                      </div>

                      <h4 style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
                        {m.product_name}
                      </h4>

                      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.4, marginTop: '6px' }}>
                        <strong>Verified Framework:</strong> {m.standard_number} ({m.source_dataset})
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', marginTop: '14px', paddingTop: '10px', borderTop: '1px solid var(--border-color)' }}>
                      {m.standard_number && onExploreStandard && (
                        <button
                          onClick={() => onExploreStandard(m.standard_number)}
                          className="btn-primary"
                          style={{ fontSize: '0.74rem', padding: '4px 10px' }}
                        >
                          View {m.standard_number} 🏛️
                        </button>
                      )}
                      {onSelectQuery && (
                        <button
                          onClick={() => onSelectQuery(`${m.product_name} ${m.standard_number}`)}
                          className="btn-secondary"
                          style={{ fontSize: '0.74rem', padding: '4px 10px' }}
                        >
                          Match Tenders ⚡
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </Panel>
      )}

      {/* TAB 4: CERTIFICATION SCHEMES & POLICY */}
      {activeTab === 'schemes' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Panel
            title="Overview of BIS Conformity Assessment Schemes"
            subtitle="Authoritative regulatory framework under Bureau of Indian Standards Act, 2016."
            badge="Regulatory Reference"
          >
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
              <div style={{ padding: '16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)' }}>
                <h4 style={{ fontWeight: 700, fontSize: '0.92rem', marginBottom: '6px' }}>Scheme I — ISI Mark</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.45 }}>
                  Factory audit plus independent lab testing. Covers mandatory QCO items (e.g. steel, cement, cables, domestic appliances).
                </p>
              </div>

              <div style={{ padding: '16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)' }}>
                <h4 style={{ fontWeight: 700, fontSize: '0.92rem', marginBottom: '6px' }}>Scheme II — CRS (MeitY)</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.45 }}>
                  Compulsory Registration Scheme for electronics, IT goods, and solar inverters based on self-declaration and lab test reports.
                </p>
              </div>

              <div style={{ padding: '16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)' }}>
                <h4 style={{ fontWeight: 700, fontSize: '0.92rem', marginBottom: '6px' }}>Scheme IV — Certificate of Conformity</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.45 }}>
                  Batch-level inspection or targeted conformance certificate where continuous ISI licensing is not required.
                </p>
              </div>
            </div>

            <div style={{ marginTop: '20px', padding: '14px 18px', borderRadius: 'var(--radius-sm)', background: '#fffbeb', border: '1px solid #fef3c7' }}>
              <h5 style={{ fontWeight: 700, fontSize: '0.84rem', color: '#92400e', marginBottom: '4px' }}>
                Note on Real-Time Redressal & Portal Lookups:
              </h5>
              <p style={{ fontSize: '0.78rem', color: '#78350f', lineHeight: 1.4 }}>
                Real-time grievance filing, automated license renewals, and live laboratory inventory tracking operate exclusively on the central ManakOnline portal.
                ARISTEA-PROCURE acts as an intelligent, evidence-grounded procurement auditor and local standard compliance engine.
              </p>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
};
