/**
 * ARISTEA-PROCURE Next.js Typed API Client Layer
 * Authoritative integration with FastAPI backend for Indian Standards Intelligence (PS 26108).
 * 
 * Reconciles all backend Pydantic contracts:
 * - Speech AI: uses transcript & language (with backward-compatible aliases)
 * - Compliance: uses requirement_level, governing_scheme, qco_records, divergences, disclaimer
 * - Tender Audit: uses coverage_score, expected_vs_present, gaps, trust_disclaimer
 * - Specifications: generate, retrieve (GET), update (PUT)
 * - Async Jobs: submit and poll
 */

function getApiBase(): string {
  let envUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || '').trim();
  if (envUrl.includes(',')) {
    const urls = envUrl.split(',').map((u) => u.trim()).filter(Boolean);
    envUrl = urls[0] || '';
  }
  envUrl = envUrl.replace(/\/+$/, '');

  if (typeof window !== 'undefined') {
    const isLocalhost =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';
    if (isLocalhost) {
      if (!envUrl || envUrl.includes('onrender.com') || envUrl.includes('localhost') || envUrl.includes('127.0.0.1')) {
        return 'http://localhost:8000';
      }
    }
    if (envUrl) {
      return envUrl;
    }
    return isLocalhost ? 'http://localhost:8000' : '';
  }
  if (envUrl) {
    return envUrl;
  }
  return 'http://localhost:8000';
}

export const API_BASE = getApiBase();

// ==========================================
// Base Response Handler
// ==========================================

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errData = await res.json();
      if (errData.fields && Array.isArray(errData.fields)) {
        const fieldMsgs = errData.fields
          .map((f: any) => `${f.loc ? f.loc.filter((x: any) => x !== 'body').join('.') : 'field'}: ${f.msg}`)
          .join('; ');
        errorDetail = fieldMsgs || errData.detail || errorDetail;
      } else if (errData.detail) {
        errorDetail = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      } else if (errData.error) {
        errorDetail = errData.error;
      }
    } catch {
      // Non-JSON response
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

// ==========================================
// Health & System Readiness
// ==========================================

export interface HealthResponse {
  status: string;
  version: string;
  module: string;
  modules?: Record<string, string>;
  async_jobs?: Record<string, string>;
}

export interface ReadyResponse {
  status: string;
  database: string;
  async_jobs: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/api/health`, { cache: 'no-store' });
  return handleResponse<HealthResponse>(res);
}

export async function checkReady(): Promise<ReadyResponse> {
  const res = await fetch(`${API_BASE}/api/ready`, { cache: 'no-store' });
  return handleResponse<ReadyResponse>(res);
}

// ==========================================
// Recommendation & Semantic Requirement Matcher
// ==========================================

export interface CandidateStandard {
  id?: number;
  standard_id: string;
  is_number?: string;
  title: string;
  score: number;
  role?: string; // PRIMARY, ALLIED, TESTING, SAFETY
  status?: string;
  category?: string;
  match_reasons?: string[];
  matched_terms?: string[];
  evidence?: {
    clause?: string;
    section?: string;
    text_snippet?: string;
    score_breakdown?: Record<string, number>;
  };
}

export interface RecommendationResponse {
  query_text: string;
  normalized_query?: string;
  context_type?: string;
  total_candidates: number;
  primary_standard?: CandidateStandard | null;
  allied_standards?: CandidateStandard[];
  testing_standards?: CandidateStandard[];
  safety_standards?: CandidateStandard[];
  recommendations: CandidateStandard[];
  overall_confidence_score?: number;
  execution_time_ms?: number;
  summary_recommendation?: string;
  tender_clause?: string;
  warnings?: Array<{
    level: string;
    badge?: string;
    title: string;
    message: string;
    action_required?: string;
  }>;
  qco?: {
    applicable: boolean;
    order_title?: string;
    badge?: string;
  };
  certification?: {
    popular_name?: string;
    scheme?: string;
  };
}

export async function analyzeRequirement(params: {
  requirement_text: string;
  context_type?: string;
  min_confidence?: number;
  top_k?: number;
}): Promise<RecommendationResponse> {
  const query = params.requirement_text;
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query_text: query,
      requirement_text: query,
      max_primary: params.top_k ?? 5,
      include_allied: true,
    }),
  });
  const raw = await handleResponse<any>(res);

  // Normalize candidate records
  const candidates: any[] = [];
  if (Array.isArray(raw.primary_standards)) {
    candidates.push(...raw.primary_standards);
  }
  if (Array.isArray(raw.candidate_spectrum)) {
    for (const cand of raw.candidate_spectrum) {
      if (!candidates.some((c) => c.standard_id === cand.standard_id)) {
        candidates.push(cand);
      }
    }
  }
  if (raw.allied_standards && typeof raw.allied_standards === 'object') {
    for (const group of Object.values(raw.allied_standards)) {
      if (Array.isArray(group)) {
        for (const cand of group) {
          if (!candidates.some((c) => c.standard_id === cand.standard_id)) {
            candidates.push(cand);
          }
        }
      }
    }
  }

  const normalizedRecommendations: CandidateStandard[] = candidates.map((c) => ({
    id: c.id,
    standard_id: c.standard_id,
    is_number: c.is_number,
    title: c.title,
    score: c.confidence_score !== undefined ? c.confidence_score : c.relevance_score !== undefined ? c.relevance_score : undefined,
    role: c.role ? c.role.toUpperCase() : undefined,
    status: c.status || 'ACTIVE',
    category: c.category || c.technical_department,
    match_reasons: c.match_reasons || c.rationale || [],
    matched_terms: c.matched_terms || c.keywords || [],
    evidence: {
      clause: c.clause,
      section: c.section,
      text_snippet: c.text_snippet || c.scope_snippet,
      score_breakdown: c.score_breakdown,
    },
  }));

  const primary = raw.primary_standards?.[0]
    ? {
        id: raw.primary_standards[0].id,
        standard_id: raw.primary_standards[0].standard_id,
        is_number: raw.primary_standards[0].is_number,
        title: raw.primary_standards[0].title,
        score: raw.primary_standards[0].confidence_score !== undefined ? raw.primary_standards[0].confidence_score : undefined,
        role: raw.primary_standards[0].role ? raw.primary_standards[0].role.toUpperCase() : undefined,
        status: raw.primary_standards[0].status || 'UNKNOWN',
        category: raw.primary_standards[0].category,
        match_reasons: raw.primary_standards[0].match_reasons || [],
        matched_terms: raw.primary_standards[0].matched_terms || [],
      }
    : normalizedRecommendations[0] || null;

  return {
    query_text: raw.query_text || query,
    normalized_query: raw.query_text || query,
    context_type: params.context_type || 'tender_specification',
    total_candidates: normalizedRecommendations.length,
    primary_standard: primary,
    recommendations: normalizedRecommendations,
    overall_confidence_score: primary ? primary.score : undefined,
    execution_time_ms: raw.execution_time_ms !== undefined ? raw.execution_time_ms : undefined,
    summary_recommendation: raw.summary || (primary
      ? `Procurement requirements align with verified standard ${primary.standard_id} (${primary.title}).`
      : undefined),
    tender_clause: raw.tender_clause || undefined,
  };
}

// ==========================================
// Standards Details, Versions & Relationships
// ==========================================

export interface StandardDetail {
  id: number;
  standard_id: string;
  is_number: string;
  title: string;
  status: string;
  category?: string;
  subject_area?: string;
  publication_year?: number;
  ics_code?: string;
  page_count?: number;
  scope?: string;
  is_mandatory?: boolean;
  technical_department?: string;
  source_file?: string;
}

export interface StandardsListResponse {
  total: number;
  offset: number;
  limit: number;
  standards: StandardDetail[];
}

export interface ProductLicenceRecord {
  id: number;
  product_category: string;
  licence_count: number;
  raw_count_str?: string;
  source_dataset: string;
}

export interface MinistryMappingRecord {
  id: number;
  ministry_department: string;
  product_name: string;
  standard_number: string;
  standard_id?: number | null;
  source_dataset: string;
}

export async function listStandards(params?: {
  q?: string;
  category?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<StandardsListResponse> {
  const query = new URLSearchParams();
  if (params?.q) query.set('q', params.q);
  if (params?.category) query.set('category', params.category);
  if (params?.status) query.set('status', params.status);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));

  const qs = query.toString();
  const url = qs ? `${API_BASE}/api/standards?${qs}` : `${API_BASE}/api/standards`;
  const res = await fetch(url, { cache: 'no-store' });
  return handleResponse<StandardsListResponse>(res);
}

export async function getProductLicences(category?: string): Promise<ProductLicenceRecord[]> {
  const url = category
    ? `${API_BASE}/api/licences?category=${encodeURIComponent(category)}`
    : `${API_BASE}/api/licences`;
  const res = await fetch(url, { cache: 'no-store' });
  return handleResponse<ProductLicenceRecord[]>(res);
}

export async function getMinistryMappings(ministry?: string): Promise<MinistryMappingRecord[]> {
  const url = ministry
    ? `${API_BASE}/api/ministry-mappings?ministry=${encodeURIComponent(ministry)}`
    : `${API_BASE}/api/ministry-mappings`;
  const res = await fetch(url, { cache: 'no-store' });
  return handleResponse<MinistryMappingRecord[]>(res);
}

export interface AmendmentRecord {
  id?: number;
  standard_id?: number;
  is_number?: string;
  amendment_number?: number | null;
  amendment_year?: number | null;
  change_description?: string | null;
  current_state?: string;
  source_dataset?: string;
  source_provenance?: Record<string, any> | null;
  number?: number;
  year?: number;
  notes?: string;
}

export interface VersionReport {
  standard_id: string;
  canonical_id?: string;
  is_number?: string;
  title?: string;
  status?: string;
  current_status: string;
  is_current: boolean;
  publication_year?: number;
  latest_year?: number;
  active_version?: string;
  successor_standard_id?: string;
  predecessor_standard_id?: string;
  total_amendments?: number;
  amendments: AmendmentRecord[];
  warnings?: Array<{
    warning_type: string;
    message: string;
    severity: string;
    evidence?: any;
    source_dataset?: string;
  }>;
  supersession?: {
    standard_id?: string;
    canonical_id?: string;
    current_status?: string;
    supersedes?: any[];
    superseded_by?: any[];
    has_cycle?: boolean;
  };
  version_records?: any[];
  source_file?: string;
  disclaimer?: string;
}

export interface RelationshipEdge {
  source_id?: string;
  target_id?: string;
  source?: string;
  target?: string;
  source_standard_number?: string;
  target_standard_number?: string;
  target_standard_id?: string;
  target_title?: string;
  relationship_type: string;
  relationship_category?: string;
  is_explicit?: boolean;
  is_unresolved?: boolean;
}

export interface DependencyGraph {
  root_standard: string;
  nodes: Array<{
    id: string;
    label: string;
    title?: string;
    status?: string;
    type?: string;
    group?: string;
  }>;
  edges: Array<{
    source: string;
    target: string;
    relationship_type: string;
    is_unresolved?: boolean;
  }>;
}

export async function getStandardDetail(standardId: string): Promise<StandardDetail> {
  const res = await fetch(`${API_BASE}/api/standards/${encodeURIComponent(standardId)}`, { cache: 'no-store' });
  return handleResponse<StandardDetail>(res);
}

export async function getStandardVersions(standardId: string): Promise<VersionReport> {
  const res = await fetch(`${API_BASE}/api/standards/${encodeURIComponent(standardId)}/versions`, { cache: 'no-store' });
  const data = await handleResponse<any>(res);
  if (!data) return data;

  const current_status = data.current_status || data.status || data.supersession?.current_status || 'CURRENT';
  const is_current =
    typeof data.is_current === 'boolean'
      ? data.is_current
      : current_status.toUpperCase() === 'CURRENT';

  const successor_standard_id =
    data.successor_standard_id ||
    data.supersession?.superseded_by?.[0]?.canonical_id ||
    data.supersession?.superseded_by?.[0]?.is_number ||
    (typeof data.supersession?.superseded_by?.[0] === 'string' ? data.supersession.superseded_by[0] : undefined);

  const predecessor_standard_id =
    data.predecessor_standard_id ||
    data.supersession?.supersedes?.[0]?.canonical_id ||
    data.supersession?.supersedes?.[0]?.is_number ||
    (typeof data.supersession?.supersedes?.[0] === 'string' ? data.supersession.supersedes[0] : undefined);

  const rawAmendments = Array.isArray(data.amendments) ? data.amendments : [];
  const amendments: AmendmentRecord[] = rawAmendments.map((a: any) => ({
    ...a,
    amendment_number: a.amendment_number ?? a.number ?? null,
    amendment_year: a.amendment_year ?? a.year ?? null,
    change_description: a.change_description ?? a.notes ?? null,
  }));

  return {
    ...data,
    current_status,
    is_current,
    successor_standard_id,
    predecessor_standard_id,
    amendments,
    total_amendments: amendments.length,
  };
}

export async function getStandardRelationships(standardId: string): Promise<RelationshipEdge[]> {
  const res = await fetch(`${API_BASE}/api/standards/${encodeURIComponent(standardId)}/relationships`, { cache: 'no-store' });
  const rawList = await handleResponse<any[]>(res);
  return (rawList || []).map((edge) => {
    const target =
      edge.target_standard_id ||
      edge.target_id ||
      (edge.target_standard_number ? `IS ${edge.target_standard_number}` : '') ||
      edge.target ||
      '';
    const source = edge.source_standard_number || edge.source_id || edge.source || '';
    return {
      ...edge,
      target,
      source,
    };
  });
}

export async function getStandardGraph(standardId: string, maxDepth = 2, direction = 'both'): Promise<DependencyGraph> {
  const res = await fetch(
    `${API_BASE}/api/standards/${encodeURIComponent(standardId)}/graph?max_depth=${maxDepth}&direction=${direction}`,
    { cache: 'no-store' }
  );
  return handleResponse<DependencyGraph>(res);
}

// ==========================================
// Compliance Intelligence & QCO Mandates
// ==========================================

export interface ComplianceReport {
  standard_id: string;
  canonical_id: string;
  is_number?: string | null;
  title?: string | null;
  status?: string | null;
  requirement_level: string; // MANDATORY, VOLUNTARY, CONDITIONAL, UNKNOWN
  governing_scheme: string; // BIS_ISI, CRS, HALLMARKING, UNKNOWN
  is_mandatory_certification?: boolean | null;
  qco_applicable?: boolean | null;
  certification_records: Array<Record<string, any>>;
  qco_records: Array<Record<string, any>>;
  qco_orders?: Array<Record<string, any>>; // Backward compat alias
  product_licences: Array<Record<string, any>>;
  ministry_mappings: Array<Record<string, any>>;
  regulatory_divergence_detected: boolean;
  regulatory_divergence_notes: string[];
  divergences: Array<Record<string, any>>;
  confidence_score: number;
  evidence_count: number;
  disclaimer: string;
}

export async function getStandardCompliance(standardId: string): Promise<ComplianceReport> {
  const res = await fetch(`${API_BASE}/api/standards/${encodeURIComponent(standardId)}/compliance`, { cache: 'no-store' });
  const raw = await handleResponse<any>(res);
  return {
    standard_id: raw.standard_id || standardId,
    canonical_id: raw.canonical_id || standardId,
    is_number: raw.is_number || null,
    title: raw.title || null,
    status: raw.status || null,
    requirement_level: raw.requirement_level || 'UNKNOWN',
    governing_scheme: raw.governing_scheme || 'UNKNOWN',
    is_mandatory_certification: raw.is_mandatory_certification ?? null,
    qco_applicable: raw.qco_applicable ?? null,
    qco_records: raw.qco_records || [],
    qco_orders: raw.qco_records || raw.qco_mandates || [],
    certification_records: raw.certification_records || [],
    product_licences: raw.product_licences || [],
    ministry_mappings: raw.ministry_mappings || [],
    regulatory_divergence_detected: Boolean(raw.regulatory_divergence_detected),
    regulatory_divergence_notes: raw.regulatory_divergence_notes || [],
    divergences: raw.divergences || [],
    confidence_score: raw.confidence_score ?? 1.0,
    evidence_count: raw.evidence_count ?? 0,
    disclaimer: raw.disclaimer || 'Compliance intelligence is derived from the project dataset.',
  };
}

export async function getStandardCertification(standardId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/standards/${encodeURIComponent(standardId)}/certification`, { cache: 'no-store' });
  return handleResponse<any>(res);
}

export async function batchEvaluateCompliance(standardIds: string[]): Promise<any> {
  const res = await fetch(`${API_BASE}/api/standards/compliance/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ standard_ids: standardIds }),
  });
  return handleResponse<any>(res);
}

// ==========================================
// Tender Engine & Document Auditing
// ==========================================

export interface TenderUploadResponse {
  tender_id: number;
  tender_number?: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  total_pages: number;
  total_sections: number;
  total_clauses: number;
  total_standards_detected: number;
  created_at?: string;
}

export interface TenderAuditGap {
  gap_category: string;
  gap_type?: string;
  severity: 'CRITICAL' | 'WARNING' | 'ADVISORY' | 'INFO';
  trust_level?: string;
  standard_id?: string;
  cited_standard?: string;
  title?: string;
  clause_reference?: string;
  clause_text?: string;
  successor_standard_id?: string;
  expected_standard?: string;
  successor_title?: string;
  issue_description: string;
  recommendation: string;
  recommendation_notes?: string;
  evidence?: Record<string, any>;
  requirement_id?: number;
}

export interface ExpectedVsPresentComparison {
  present_standards: Array<Record<string, any>>;
  expected_standards: Array<Record<string, any>>;
  missing_standards: Array<Record<string, any>>;
  outdated_standards: Array<Record<string, any>>;
  testing_gaps: Array<Record<string, any>>;
  safety_gaps: Array<Record<string, any>>;
  certification_gaps: Array<Record<string, any>>;
}

export interface TenderAuditReport {
  tender_id: number;
  tender_number?: string;
  filename: string;
  coverage_score: number;
  coverage_percentage: number;
  audit_summary: string;
  total_gaps_found: number;
  critical_issues_count: number;
  warnings_count: number;
  advisories_count: number;
  gaps: TenderAuditGap[];
  expected_vs_present: ExpectedVsPresentComparison;
  trust_disclaimer: string;
  created_at?: string;
  // Legacy backward-compat accessors
  standards_coverage_score: number;
  total_gaps_count: number;
  outdated_references_count: number;
  missing_primary_references_count: number;
  missing_testing_safety_count: number;
  total_clauses_analyzed: number;
  total_standards_cited: number;
}

export async function uploadTenderDocument(
  file: File,
  tenderNumber?: string,
  title?: string,
  organization?: string
): Promise<TenderUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (tenderNumber) formData.append('tender_number', tenderNumber);
  if (title) formData.append('title', title);
  if (organization) formData.append('organization', organization);

  const res = await fetch(`${API_BASE}/api/tenders/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<TenderUploadResponse>(res);
}

export async function getTenderDetails(tenderId: number): Promise<any> {
  const res = await fetch(`${API_BASE}/api/tenders/${tenderId}`, { cache: 'no-store' });
  return handleResponse<any>(res);
}

export async function getTenderRequirements(tenderId: number): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/tenders/${tenderId}/requirements`, { cache: 'no-store' });
  return handleResponse<any[]>(res);
}

export async function getTenderReferences(tenderId: number): Promise<any[]> {
  const res = await fetch(`${API_BASE}/api/tenders/${tenderId}/references`, { cache: 'no-store' });
  return handleResponse<any[]>(res);
}

export async function getTenderAudit(tenderId: number, forceRecompute = false): Promise<TenderAuditReport> {
  const res = await fetch(`${API_BASE}/api/tenders/${tenderId}/audit?force_recompute=${forceRecompute}`, {
    cache: 'no-store',
  });
  const raw = await handleResponse<any>(res);
  const rawGaps = raw.gaps || [];
  const normalizedGaps: TenderAuditGap[] = rawGaps.map((gap: any) => ({
    ...gap,
    gap_category: gap.gap_category || gap.gap_type || 'GAP_OBSERVATION',
    gap_type: gap.gap_category || gap.gap_type || 'GAP_OBSERVATION',
    severity: gap.severity ? gap.severity.toUpperCase() : 'UNKNOWN',
    cited_standard: gap.standard_id || gap.cited_standard || '',
    expected_standard: gap.successor_standard_id || gap.expected_standard || '',
    recommendation_notes: gap.recommendation || gap.issue_description || gap.recommendation_notes || '',
    clause_text: gap.clause_text || '',
    requirement_id: gap.clause_reference || gap.requirement_id,
  }));

  const expectedVsPresent = raw.expected_vs_present || {
    present_standards: [],
    expected_standards: [],
    missing_standards: [],
    outdated_standards: [],
    testing_gaps: [],
    safety_gaps: [],
    certification_gaps: [],
  };

  const coverageScore =
    raw.coverage_score !== undefined
      ? raw.coverage_score
      : raw.coverage_percentage !== undefined
      ? raw.coverage_percentage / 100
      : 0;

  return {
    tender_id: raw.tender_id,
    tender_number: raw.tender_number,
    filename: raw.filename || 'tender_document',
    coverage_score: coverageScore,
    coverage_percentage: raw.coverage_percentage ?? (coverageScore !== undefined ? coverageScore * 100 : undefined),
    audit_summary: raw.audit_summary || 'Evidence-grounded audit completed.',
    total_gaps_found: raw.total_gaps_found ?? normalizedGaps.length,
    critical_issues_count: raw.critical_issues_count,
    warnings_count: raw.warnings_count,
    advisories_count: raw.advisories_count,
    gaps: normalizedGaps,
    expected_vs_present: expectedVsPresent,
    trust_disclaimer:
      raw.trust_disclaimer ||
      'Tender audit results distinguish KNOWN facts, INFERRED recommendations, and UNKNOWN evidence.',
    created_at: raw.created_at,
    // Backward-compat accessors
    standards_coverage_score: coverageScore,
    total_gaps_count: raw.total_gaps_found ?? normalizedGaps.length,
    outdated_references_count: (expectedVsPresent.outdated_standards || []).length,
    missing_primary_references_count: (expectedVsPresent.missing_standards || []).length,
    missing_testing_safety_count:
      (expectedVsPresent.testing_gaps || []).length + (expectedVsPresent.safety_gaps || []).length,
    total_clauses_analyzed: raw.total_clauses_analyzed || (raw.gaps ? raw.gaps.length : 0),
    total_standards_cited: (expectedVsPresent.present_standards || []).length,
  };
}

// ==========================================
// Grounded Specification Generation & Workspace
// ==========================================

export interface GeneratedSpecificationResponse {
  id?: number;
  tender_id?: number;
  analysis_id?: string;
  title: string;
  generation_type?: string;
  specification_type?: string;
  generated_text?: string;
  specification_text: string;
  structured_content?: any;
  sections?: Array<{ title: string; content: string }>;
  grounded_standards?: string[];
  total_standards_referenced?: number;
  is_edited?: boolean;
  version?: number;
  created_at?: string;
  updated_at?: string;
  disclaimer?: string;
}

export async function generateSpecification(params: {
  tender_id?: number;
  generation_type?: string;
  title?: string;
  query_text?: string;
}): Promise<GeneratedSpecificationResponse> {
  let genType = params.generation_type || 'technical_specification';
  if (genType === 'gfr_compliance_clause' || genType === 'clause' || genType === 'gfr_clause') {
    genType = 'tender_clause';
  } else if (genType === 'testing_schedule' || genType === 'checklist' || genType === 'inspection_schedule') {
    genType = 'compliance_checklist';
  } else if (genType === 'correction' || genType === 'audit_correction') {
    genType = 'corrective_clause';
  }

  const res = await fetch(`${API_BASE}/api/specifications/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tender_id: params.tender_id,
      generation_type: genType,
      title: params.title || 'Draft Technical Specification',
      query_text: params.query_text,
    }),
  });
  const raw = await handleResponse<any>(res);
  const text = raw.generated_text || raw.specification_text || '';
  return {
    ...raw,
    specification_text: text,
    generated_text: text,
    specification_type: raw.generation_type || raw.specification_type || genType,
  };
}

export async function getSpecification(specId: number): Promise<GeneratedSpecificationResponse> {
  const res = await fetch(`${API_BASE}/api/specifications/${specId}`, { cache: 'no-store' });
  const raw = await handleResponse<any>(res);
  const text = raw.generated_text || raw.specification_text || '';
  return {
    ...raw,
    specification_text: text,
    generated_text: text,
    specification_type: raw.generation_type || raw.specification_type || 'technical_specification',
  };
}

export async function updateSpecification(
  specId: number,
  data: { title?: string; specification_text?: string; generated_text?: string }
): Promise<GeneratedSpecificationResponse> {
  const text = data.generated_text || data.specification_text || '';
  const res = await fetch(`${API_BASE}/api/specifications/${specId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: data.title,
      generated_text: text,
      specification_text: text,
    }),
  });
  const raw = await handleResponse<any>(res);
  const updatedText = raw.generated_text || raw.specification_text || text;
  return {
    ...raw,
    specification_text: updatedText,
    generated_text: updatedText,
    specification_type: raw.generation_type || raw.specification_type || 'technical_specification',
  };
}

// ==========================================
// Speech AI (Module 10)
// ==========================================

export interface TranscriptionResult {
  transcript: string;
  transcription?: string; // Backward compat alias
  language: string;
  detected_language?: string; // Backward compat alias
  confidence: number;
  repetition_needed: boolean;
  repetition_prompt?: string | null;
  duration_seconds?: number | null;
  provider: string;
  is_mock?: boolean;
}

export interface SynthesisResult {
  audio_base64?: string;
  mime_type: string;
  duration_seconds?: number | null;
  provider: string;
  is_mock?: boolean;
  error?: string | null;
}

export interface VoiceQueryResponse {
  transcription: TranscriptionResult;
  recommendation?: RecommendationResponse | null;
  spoken_summary?: string | null;
  synthesized_audio?: {
    audio_base64?: string;
    mime_type?: string;
    duration_seconds?: number;
  } | null;
}

export async function transcribeAudio(audioFile: File, languageHint?: string): Promise<TranscriptionResult> {
  const formData = new FormData();
  formData.append('file', audioFile);
  const url = languageHint
    ? `${API_BASE}/api/speech/transcribe?language_hint=${encodeURIComponent(languageHint)}`
    : `${API_BASE}/api/speech/transcribe`;
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });
  const raw = await handleResponse<any>(res);
  const transcript = raw.transcript || raw.transcription || '';
  const language = raw.language || raw.detected_language || 'en';
  return {
    transcript,
    transcription: transcript,
    language,
    detected_language: language,
    confidence: raw.confidence ?? 0,
    repetition_needed: Boolean(raw.repetition_needed),
    repetition_prompt: raw.repetition_prompt || null,
    duration_seconds: raw.duration_seconds || null,
    provider: raw.provider || 'default',
    is_mock: raw.is_mock || false,
  };
}

export async function synthesizeSpeech(text: string, language = 'en'): Promise<SynthesisResult> {
  const res = await fetch(`${API_BASE}/api/speech/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, language }),
  });
  return handleResponse<SynthesisResult>(res);
}

export async function submitVoiceQuery(
  audioFile: File,
  languageHint?: string,
  synthesizeAudio = true
): Promise<VoiceQueryResponse> {
  const formData = new FormData();
  formData.append('file', audioFile);
  const params = new URLSearchParams();
  if (languageHint) params.append('language_hint', languageHint);
  params.append('synthesize_audio', String(synthesizeAudio));

  const res = await fetch(`${API_BASE}/api/speech/voice-query?${params.toString()}`, {
    method: 'POST',
    body: formData,
  });
  const raw = await handleResponse<any>(res);
  const transcript = raw.transcription?.transcript || raw.transcription?.transcription || '';
  const language = raw.transcription?.language || raw.transcription?.detected_language || 'en';

  const transcription: TranscriptionResult = {
    transcript,
    transcription: transcript,
    language,
    detected_language: language,
    confidence: raw.transcription?.confidence ?? 0,
    repetition_needed: Boolean(raw.transcription?.repetition_needed),
    repetition_prompt: raw.transcription?.repetition_prompt || null,
    duration_seconds: raw.transcription?.duration_seconds || null,
    provider: raw.transcription?.provider || 'default',
    is_mock: raw.transcription?.is_mock || false,
  };

  return {
    ...raw,
    transcription,
  };
}

// ==========================================
// Async Background Jobs
// ==========================================

export interface AsyncJobSubmitResponse {
  job_id: string;
  task_type: string;
  status: string;
  message?: string;
  created_at?: string;
}

export interface JobStatusResponse {
  job_id: string;
  task_type?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled' | string;
  progress_percent?: number;
  result?: any;
  error?: string | null;
  created_at?: string;
  completed_at?: string;
}

export async function submitJob(taskType: string, payload: Record<string, any>): Promise<AsyncJobSubmitResponse> {
  const res = await fetch(`${API_BASE}/api/jobs/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_type: taskType, payload }),
  });
  return handleResponse<AsyncJobSubmitResponse>(res);
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE}/api/jobs/${encodeURIComponent(jobId)}`, { cache: 'no-store' });
  return handleResponse<JobStatusResponse>(res);
}

export async function pollJob(jobId: string, intervalMs = 1000, timeoutMs = 30000): Promise<any> {
  const startTime = Date.now();
  while (Date.now() - startTime < timeoutMs) {
    const status = await getJobStatus(jobId);
    if (status.status?.toLowerCase() === 'completed') {
      return status.result;
    }
    if (status.status?.toLowerCase() === 'failed') {
      throw new Error(status.error || 'Async task execution failed.');
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error(`Task ${jobId} timed out after ${timeoutMs}ms.`);
}

// ==========================================
// ARISTEA Autopilot (need → cited tender)
// ==========================================

export type AutopilotStepStatus = 'pending' | 'running' | 'done' | 'blocked' | 'error';

export interface AutopilotStepEvent {
  type: 'step';
  step: string;
  title: string;
  status: AutopilotStepStatus;
  summary: string;
  data: Record<string, any>;
  elapsed_ms?: number | null;
}

export interface AutopilotClause {
  text: string;
  citations: string[];
  kind: 'clause' | 'advisory' | 'autofix';
}

export interface AutopilotSection {
  id: string;
  heading: string;
  clauses: AutopilotClause[];
}

export interface AutopilotCitation {
  key: string;
  source_type: string;
  label: string;
  source_dataset: string;
  details: string;
  provenance?: any;
}

export interface AutopilotFinding {
  severity: string;
  category: string;
  issue: string;
  fix: string;
  auto_fixed: boolean;
}

export interface AutopilotResult {
  run_id: string;
  need: string;
  readiness: 'READY_FOR_APPROVAL' | 'NEEDS_REVIEW' | 'BLOCKED';
  facts: Record<string, any> | null;
  standards: Record<string, any>[];
  clarifications: { component: string; missing: string[] }[];
  sections: AutopilotSection[];
  tender_text: string;
  redteam: {
    findings?: AutopilotFinding[];
    coverage_before?: number;
    coverage_after?: number;
    auto_fixes?: number;
  };
  citations: AutopilotCitation[];
  disclaimer: string;
}

export type AutopilotEvent =
  | { type: 'start'; run_id: string; need: string; steps: { step: string; title: string }[] }
  | AutopilotStepEvent
  | { type: 'result'; run_id: string; result: AutopilotResult }
  | { type: 'error'; detail: string };

/** Runs Autopilot and invokes onEvent for every streamed pipeline event. */
export async function runAutopilot(
  need: string,
  onEvent: (event: AutopilotEvent) => void,
  opts: { language?: string; signal?: AbortSignal } = {},
): Promise<void> {
  const MAX_RETRIES = 3;
  const RETRY_DELAY_MS = [5000, 10000, 15000]; // escalating back-off

  let res: Response | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      res = await fetch(`${API_BASE}/api/autopilot/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({ need, language: opts.language }),
        signal: opts.signal,
      });
    } catch (err: any) {
      // Network-level failure (e.g. DNS, connection refused)
      if (err?.name === 'AbortError') throw err;
      if (attempt < MAX_RETRIES) {
        onEvent({
          type: 'error',
          detail: `Backend unreachable — retrying in ${RETRY_DELAY_MS[attempt] / 1000}s… (attempt ${attempt + 1}/${MAX_RETRIES})`,
        } as AutopilotEvent);
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS[attempt]));
        continue;
      }
      throw new Error('Backend is unreachable. It may be sleeping on the free tier — please try again in a minute.');
    }

    // 502/503 = Render proxy error (cold start) — worth retrying
    if (res && (res.status === 502 || res.status === 503) && attempt < MAX_RETRIES) {
      onEvent({
        type: 'error',
        detail: `Backend is waking up (${res.status}) — retrying in ${RETRY_DELAY_MS[attempt] / 1000}s… (attempt ${attempt + 1}/${MAX_RETRIES})`,
      } as AutopilotEvent);
      await new Promise((r) => setTimeout(r, RETRY_DELAY_MS[attempt]));
      continue;
    }
    break; // success or non-retryable error
  }

  if (!res || !res.ok || !res.body) {
    if (res) await handleResponse(res);
    throw new Error('Autopilot stream unavailable.');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  const processChunk = (rawChunk: string) => {
    // Normalise lines and trim trailing carriage returns
    const lines = rawChunk.split('\n').map((l) => l.replace(/\r$/, ''));
    // Filter out comments (e.g. ": keep-alive") and extract data lines
    const dataLines = lines
      .filter((l) => l.startsWith('data:'))
      .map((l) => l.replace(/^data:\s?/, ''));

    if (dataLines.length > 0) {
      const payload = dataLines.join('\n').trim();
      if (payload) {
        try {
          const ev = JSON.parse(payload) as AutopilotEvent;
          onEvent(ev);
        } catch (e) {
          console.error('Failed to parse SSE payload:', e, payload);
        }
      }
    }
  };

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (value) {
        buffer += decoder.decode(value, { stream: !done });
        // Normalize CRLF to LF
        buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
        let sep: number;
        while ((sep = buffer.indexOf('\n\n')) !== -1) {
          const chunk = buffer.slice(0, sep).trim();
          buffer = buffer.slice(sep + 2);
          if (chunk) processChunk(chunk);
        }
      }
      if (done) break;
    }
    // Flush remaining buffer upon completion
    buffer += decoder.decode();
    buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim();
    if (buffer) {
      const chunks = buffer.split('\n\n');
      for (const c of chunks) {
        if (c.trim()) processChunk(c.trim());
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function exportAutopilotDocx(result: AutopilotResult): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/autopilot/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(result),
  });
  if (!res.ok) await handleResponse(res);
  return res.blob();
}

// ==========================================
// Redline Document Editor
// ==========================================

export interface RedlineAutoFix {
  fix_id: string;
  old_text: string;
  new_text: string;
  old_standard_id: string;
  new_standard_id: string;
  new_standard_title?: string;
  reason: string;
  year_old?: number;
  year_new?: number;
  confidence: number;
}

export interface RedlineSegment {
  segment_id: number;
  text: string;
  annotation_type: 'COMPLIANT' | 'OUTDATED' | 'UNRECOGNIZED' | 'AMENDED' | 'PLAIN';
  standard_id?: string;
  standard_title?: string;
  status?: string;
  publication_year?: number;
  successor_id?: string;
  successor_title?: string;
  successor_year?: number;
  tooltip?: string;
  auto_fix?: RedlineAutoFix;
  amendments_count?: number;
  evidence?: Record<string, any>;
}

export interface RedlineSummary {
  total_segments: number;
  compliant_count: number;
  outdated_count: number;
  unrecognized_count: number;
  amended_count: number;
  auto_fixes_available: number;
  compliance_score: number;
}

export interface RedlineAnalysisResponse {
  segments: RedlineSegment[];
  summary: RedlineSummary;
  corrected_text?: string;
  auto_fixes: RedlineAutoFix[];
  disclaimer: string;
}

export async function analyzeRedline(documentText: string, autoFixAll = false): Promise<RedlineAnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/redline/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_text: documentText,
      auto_fix_all: autoFixAll,
    }),
  });
  return handleResponse<RedlineAnalysisResponse>(res);
}

export async function applyAllRedlineFixes(documentText: string): Promise<{
  corrected_text: string;
  fixes_applied: number;
  auto_fixes: RedlineAutoFix[];
  summary: RedlineSummary;
}> {
  const res = await fetch(`${API_BASE}/api/redline/apply-all-fixes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      document_text: documentText,
      auto_fix_all: true,
    }),
  });
  return handleResponse<any>(res);
}

// ==========================================
// Adversarial Auditor AI
// ==========================================

export interface AuditorVerifiedStandard {
  input_reference: string;
  normalized_reference: string;
  verdict: 'VERIFIED' | 'SUPERSEDED_VERIFIED' | 'SUSPICIOUS' | 'HALLUCINATION' | 'PARTIAL_MATCH' | 'FORMAT_INVALID';
  confidence: number;
  matched_standard_id?: string;
  matched_title?: string;
  matched_status?: string;
  successor_id?: string;
  closest_matches: Array<{
    standard_id: string;
    title: string;
    status: string;
    similarity: number;
  }>;
  reason: string;
  blocked: boolean;
  evidence?: Record<string, any>;
}

export interface AuditorVerificationResponse {
  total_checked: number;
  verified_count: number;
  suspicious_count: number;
  hallucination_count: number;
  blocked_count: number;
  results: AuditorVerifiedStandard[];
  overall_trust_score: number;
  auditor_warning?: string;
  disclaimer: string;
}

export async function verifyStandards(
  references: string[],
  strictMode = true
): Promise<AuditorVerificationResponse> {
  const res = await fetch(`${API_BASE}/api/auditor/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      references,
      strict_mode: strictMode,
      include_closest_matches: true,
    }),
  });
  return handleResponse<AuditorVerificationResponse>(res);
}

export async function verifyStandardsInText(text: string, strictMode = true): Promise<AuditorVerificationResponse> {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('strict_mode', String(strictMode));

  const res = await fetch(`${API_BASE}/api/auditor/verify-text`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<AuditorVerificationResponse>(res);
}

// ==========================================
// Vision AI Table Reader
// ==========================================

export interface ExtractedCell {
  row: number;
  col: number;
  text: string;
  is_header: boolean;
  numeric_value?: number;
  unit?: string;
}

export interface ExtractedTable {
  table_index: number;
  title?: string;
  headers: string[];
  rows: string[][];
  cells: ExtractedCell[];
  row_count: number;
  col_count: number;
  standard_references: string[];
  csv_text?: string;
  confidence: number;
}

export interface ExtractedFormula {
  formula_index: number;
  raw_text: string;
  latex?: string;
  context?: string;
  variables: string[];
}

export interface VisionTableResponse {
  tables: ExtractedTable[];
  formulas: ExtractedFormula[];
  raw_text: string;
  standard_references: string[];
  total_tables: number;
  total_formulas: number;
  processing_method: string;
  confidence: number;
  disclaimer: string;
}

export async function extractTableFromImage(
  file: File,
  extractionMode = 'auto',
  enhanceOcr = true,
  detectStandards = true
): Promise<VisionTableResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('extraction_mode', extractionMode);
  formData.append('enhance_ocr', String(enhanceOcr));
  formData.append('detect_standards', String(detectStandards));

  const res = await fetch(`${API_BASE}/api/vision/extract-table`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<VisionTableResponse>(res);
}

export async function extractTableFromText(
  text: string,
  detectStandards = true
): Promise<VisionTableResponse> {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('detect_standards', String(detectStandards));

  const res = await fetch(`${API_BASE}/api/vision/extract-from-text`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse<VisionTableResponse>(res);
}
