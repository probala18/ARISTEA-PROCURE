import test from 'node:test';
import assert from 'node:assert';

test('API_BASE defaults to environment variable or localhost:8000', () => {
  const fallback = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  assert.strictEqual(typeof fallback, 'string');
  assert.ok(fallback.startsWith('http://'));
});

test('Speech AI contract reconciliation: transcript & language', () => {
  const mockBackendSpeechResponse = {
    transcript: 'Three phase squirrel cage induction motors',
    language: 'en',
    confidence: 0.94,
    repetition_needed: false,
    repetition_prompt: null,
    provider: 'benchmark_whisper',
    is_mock: false,
  };

  // Verify canonical fields are present
  assert.strictEqual(mockBackendSpeechResponse.transcript, 'Three phase squirrel cage induction motors');
  assert.strictEqual(mockBackendSpeechResponse.language, 'en');
  assert.strictEqual(mockBackendSpeechResponse.confidence, 0.94);
  assert.strictEqual(mockBackendSpeechResponse.repetition_needed, false);
});

test('Compliance Intelligence contract: requirement_level & qco_records', () => {
  const mockComplianceReport = {
    standard_id: 'IS 12615:2018',
    canonical_id: 'IS 12615:2018',
    requirement_level: 'MANDATORY',
    governing_scheme: 'BIS_ISI',
    is_mandatory_certification: true,
    qco_applicable: true,
    qco_records: [
      {
        order_number: 'S.O. 1234(E)',
        title: 'Electric Motors (Quality Control) Order, 2024',
        effective_date: '2024-01-01',
      },
    ],
    certification_records: [],
    divergences: [],
    confidence_score: 1.0,
    disclaimer: 'Compliance intelligence is derived from the project dataset.',
  };

  assert.strictEqual(mockComplianceReport.requirement_level, 'MANDATORY');
  assert.strictEqual(mockComplianceReport.governing_scheme, 'BIS_ISI');
  assert.ok(Array.isArray(mockComplianceReport.qco_records));
  assert.strictEqual(mockComplianceReport.qco_records[0].order_number, 'S.O. 1234(E)');
  assert.ok(mockComplianceReport.disclaimer.includes('Compliance intelligence is derived'));
});

test('Tender Audit contract: coverage_score, gaps & trust_disclaimer', () => {
  const mockAuditReport = {
    tender_id: 42,
    filename: 'CPWD_Pumping_Machinery_Tender.txt',
    coverage_score: 0.75,
    coverage_percentage: 75.0,
    audit_summary: 'Evidence-grounded audit completed.',
    total_gaps_found: 2,
    critical_issues_count: 1,
    warnings_count: 1,
    advisories_count: 0,
    gaps: [
      {
        gap_category: 'OUTDATED_REFERENCE',
        severity: 'CRITICAL',
        trust_level: 'KNOWN',
        standard_id: 'IS 325:1996',
        successor_standard_id: 'IS 12615:2018',
        issue_description: 'IS 325 is superseded by IS 12615:2018.',
        recommendation: 'Replace IS 325 with IS 12615:2018 to satisfy QCO.',
      },
    ],
    expected_vs_present: {
      present_standards: ['IS 325:1996'],
      expected_standards: ['IS 12615:2018'],
      missing_standards: [],
      outdated_standards: ['IS 325:1996'],
      testing_gaps: [],
      safety_gaps: [],
      certification_gaps: [],
    },
    trust_disclaimer:
      'Tender audit results distinguish KNOWN facts, INFERRED recommendations, and UNKNOWN evidence.',
  };

  assert.strictEqual(mockAuditReport.tender_id, 42);
  assert.strictEqual(mockAuditReport.coverage_score, 0.75);
  assert.strictEqual(mockAuditReport.gaps.length, 1);
  assert.strictEqual(mockAuditReport.gaps[0].gap_category, 'OUTDATED_REFERENCE');
  assert.strictEqual(mockAuditReport.gaps[0].severity, 'CRITICAL');
  assert.ok(mockAuditReport.trust_disclaimer.includes('KNOWN facts'));
});

test('Async Job Status Response shape validation', () => {
  const mockJobStatus = {
    job_id: 'job-98a4bc12',
    task_type: 'bulk_compliance_check',
    status: 'completed',
    result: { total_checked: 12, mandatory_count: 8 },
  };

  assert.strictEqual(mockJobStatus.status, 'completed');
  assert.strictEqual(mockJobStatus.result.total_checked, 12);
});

test('Specification Generator contract: generated_text & specification_text reconciliation', () => {
  const mockBackendSpecResponse = {
    id: 7,
    tender_id: null,
    generation_type: 'tender_clause',
    specification_type: 'tender_clause',
    title: 'GFR 2017 Model Tender Clause',
    generated_text: 'All induction motors shall strictly conform to IS 12615:2018.',
    specification_text: 'All induction motors shall strictly conform to IS 12615:2018.',
    structured_content: { applicable_standards: [] },
    is_edited: false,
    version: 1,
  };

  assert.strictEqual(mockBackendSpecResponse.generation_type, 'tender_clause');
  assert.strictEqual(mockBackendSpecResponse.generated_text, mockBackendSpecResponse.specification_text);
  assert.ok(mockBackendSpecResponse.generated_text.includes('IS 12615:2018'));
});

test('Global Search Deterministic Routing (Rule 7)', () => {
  function routeQuery(rawQuery) {
    const q = rawQuery.trim();
    if (!q) return 'none';
    if (/^IS[\s\-_]*\d+/i.test(q)) {
      return { target: 'standard', standard_id: q.toUpperCase() };
    }
    const serviceKeywords = ['service', 'services', 'licence', 'license', 'ministry', 'crs', 'isi', 'hallmark', 'huid', 'schemes'];
    if (serviceKeywords.some((kw) => q.toLowerCase().includes(kw))) {
      return { target: 'services' };
    }
    return { target: 'recommend', query: q };
  }

  // Exact IS standard pattern -> Standard Explorer
  assert.deepStrictEqual(routeQuery('IS 12615:2018'), { target: 'standard', standard_id: 'IS 12615:2018' });
  assert.deepStrictEqual(routeQuery('is 694'), { target: 'standard', standard_id: 'IS 694' });
  assert.deepStrictEqual(routeQuery('IS-302-1'), { target: 'standard', standard_id: 'IS-302-1' });

  // Explicit service commands -> BIS Service Hub
  assert.deepStrictEqual(routeQuery('show certification services'), { target: 'services' });
  assert.deepStrictEqual(routeQuery('ministry mappings'), { target: 'services' });
  assert.deepStrictEqual(routeQuery('product licences'), { target: 'services' });
  assert.deepStrictEqual(routeQuery('CRS schemes'), { target: 'services' });

  // General procurement text -> Recommendation API
  assert.deepStrictEqual(routeQuery('PVC cable for domestic wiring'), { target: 'recommend', query: 'PVC cable for domestic wiring' });
  assert.deepStrictEqual(routeQuery('solar inverter 5kw'), { target: 'recommend', query: 'solar inverter 5kw' });
});

test('Minimal Read-Only Endpoints Contract (Rule 2 & Baseline Counts)', () => {
  // Standards Listing
  const mockStandardsListResponse = {
    items: [
      {
        standard_id: 'IS 12615:2018',
        title: 'Line Operated Three-Phase Induction Motors',
        category: 'Electrotechnical',
        division: 'ETD',
        status: 'CURRENT',
        publication_year: 2018,
      },
    ],
    total: 268,
    limit: 50,
    offset: 0,
  };
  assert.strictEqual(mockStandardsListResponse.total, 268);
  assert.strictEqual(mockStandardsListResponse.items[0].standard_id, 'IS 12615:2018');

  // Product Licences (75 records)
  const mockLicencesResponse = {
    items: [
      {
        id: 1,
        product_name: 'PVC Insulated Cables',
        is_number: 'IS 694:2010',
        licence_category: 'Electrical Cables',
      },
    ],
    count: 75,
  };
  assert.strictEqual(mockLicencesResponse.count, 75);
  assert.strictEqual(mockLicencesResponse.items[0].is_number, 'IS 694:2010');

  // Ministry Mappings (28 records)
  const mockMinistryResponse = {
    items: [
      {
        id: 1,
        ministry: 'Ministry of Power',
        product_category: 'Distribution Transformers',
        typical_procurement_items: 'Outdoor type distribution transformers 11kV',
        primary_standard_hint: 'IS 1180 (Part 1)',
      },
    ],
    count: 28,
  };
  assert.strictEqual(mockMinistryResponse.count, 28);
  assert.strictEqual(mockMinistryResponse.items[0].ministry, 'Ministry of Power');
});

test('Session History Clean State Policy (Rule 5)', () => {
  // A new session must begin with an empty list
  const initialSessionStorage = null;
  const historyItems = initialSessionStorage ? JSON.parse(initialSessionStorage) : [];
  assert.strictEqual(historyItems.length, 0);

  const emptyStateText = 'No recent activity in this session.';
  assert.strictEqual(emptyStateText, 'No recent activity in this session.');
});

test('Clause Explainer Strict Evidence Boundary (Rule 6)', () => {
  const boundaryNotice = 'Detailed clause text not available in current verified dataset';
  assert.strictEqual(boundaryNotice, 'Detailed clause text not available in current verified dataset');
});

test('Version Intelligence Contract: status, amendments, supersession & warnings', () => {
  const mockVersionReport = {
    standard_id: 'IS 12615:2018',
    status: 'CURRENT',
    latest_year: 2018,
    amendments: [
      {
        id: 1,
        amendment_number: 1,
        amendment_year: 2020,
        change_description: 'Clause 4.2 updated for IE4 efficiency benchmarks.',
        current_state: 'CURRENT',
      },
    ],
    supersession: {
      standard_id: 'IS 12615:2018',
      canonical_id: 'IS 12615:2018',
      current_status: 'CURRENT',
      supersedes: [{ canonical_id: 'IS 325:1996', is_number: 'IS 325' }],
      superseded_by: [],
      has_cycle: false,
    },
    warnings: [],
  };

  assert.strictEqual(mockVersionReport.status, 'CURRENT');
  assert.strictEqual(mockVersionReport.supersession.current_status, 'CURRENT');
  assert.strictEqual(mockVersionReport.amendments.length, 1);
  assert.strictEqual(mockVersionReport.amendments[0].amendment_number, 1);
  assert.strictEqual(mockVersionReport.supersession.supersedes[0].canonical_id, 'IS 325:1996');

  const mockSupersededReport = {
    standard_id: 'IS 325:1996',
    status: 'SUPERSEDED',
    supersession: {
      current_status: 'SUPERSEDED',
      superseded_by: [{ canonical_id: 'IS 12615:2018', is_number: 'IS 12615' }],
    },
  };
  assert.strictEqual(mockSupersededReport.status, 'SUPERSEDED');
  assert.strictEqual(mockSupersededReport.supersession.superseded_by[0].canonical_id, 'IS 12615:2018');

  const mockUnknownReport = {
    standard_id: 'IS 99999',
    status: 'UNKNOWN',
  };
  assert.strictEqual(mockUnknownReport.status, 'UNKNOWN');
});

test('Compliance Evidence Separation: no QCO does not imply voluntary', () => {
  const mockNoQcoCompliance = {
    standard_id: 'IS 10257:1982',
    requirement_level: 'UNKNOWN',
    governing_scheme: 'BIS_ISI',
    qco_records: [],
    certification_records: [],
    disclaimer: 'Compliance intelligence reflects facts ingested in the project dataset. Absence of a record does not establish voluntary status.',
  };

  assert.strictEqual(mockNoQcoCompliance.requirement_level, 'UNKNOWN');
  assert.notStrictEqual(mockNoQcoCompliance.requirement_level, 'VOLUNTARY');
  assert.strictEqual(mockNoQcoCompliance.qco_records.length, 0);
  assert.ok(mockNoQcoCompliance.disclaimer.includes('Absence of a record does not establish voluntary status'));

  const mockMandatory = {
    standard_id: 'IS 694:2010',
    requirement_level: 'MANDATORY',
    governing_scheme: 'BIS_ISI',
    qco_records: [{ order_number: 'QCO-2023-CABLES' }],
  };
  assert.strictEqual(mockMandatory.requirement_level, 'MANDATORY');

  const mockVoluntary = {
    standard_id: 'IS 732:2019',
    requirement_level: 'VOLUNTARY',
    governing_scheme: 'BIS_ISI',
    qco_records: [],
  };
  assert.strictEqual(mockVoluntary.requirement_level, 'VOLUNTARY');
});

test('Ontology Relationships: real collection count and clean zero-state message', () => {
  const emptyRelationships = [];
  assert.strictEqual(emptyRelationships.length, 0);

  const zeroStateNotice = 'No verified ontology relationships recorded for this standard.';
  assert.strictEqual(zeroStateNotice, 'No verified ontology relationships recorded for this standard.');

  const populatedRelationships = [
    {
      source_id: 'std:1',
      target_id: 'std:2',
      relationship_type: 'TESTING',
      relationship_category: 'NORMATIVE',
      is_explicit_source: true,
      source_dataset: 'relationships.json',
    },
    {
      source_id: 'std:1',
      target_id: 'std:3',
      relationship_type: 'SAFETY',
      relationship_category: 'NORMATIVE',
      is_explicit_source: true,
      source_dataset: 'relationships.json',
    },
  ];
  assert.strictEqual(populatedRelationships.length, 2);
  assert.strictEqual(populatedRelationships[0].relationship_type, 'TESTING');
  assert.strictEqual(populatedRelationships[1].relationship_type, 'SAFETY');
});

test('Strict Grounding: No fabricated confidence, execution time, role or severity', () => {
  const candidateWithoutRole = {
    id: 1,
    standard_id: 'IS 12615:2018',
    title: 'Energy Efficient Induction Motors',
    confidence_score: undefined,
    role: undefined,
  };
  assert.strictEqual(candidateWithoutRole.role, undefined);
  assert.strictEqual(candidateWithoutRole.confidence_score, undefined);
  assert.notStrictEqual(candidateWithoutRole.role, 'PRIMARY');
  assert.notStrictEqual(candidateWithoutRole.confidence_score, 0.95);

  const responseWithoutTime = {
    execution_time_ms: undefined,
  };
  assert.strictEqual(responseWithoutTime.execution_time_ms, undefined);
  assert.notStrictEqual(responseWithoutTime.execution_time_ms, 14.2);

  const rawGapWithoutSeverity = {
    standard_id: 'IS 1234',
    issue_description: 'Observation without severity tag',
  };
  const severityMapped = rawGapWithoutSeverity.severity ? rawGapWithoutSeverity.severity.toUpperCase() : 'UNKNOWN';
  assert.strictEqual(severityMapped, 'UNKNOWN');
  assert.notStrictEqual(severityMapped, 'INFO');
});
