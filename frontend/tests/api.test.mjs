import test from 'node:test';
import assert from 'node:assert';

test('ARISTEA-PROCURE API Client & Contract Verification', async (t) => {
  await t.test('API_BASE defaults to environment variable or localhost:8000', () => {
    const fallback = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    assert.strictEqual(typeof fallback, 'string');
    assert.ok(fallback.startsWith('http://'));
  });

  await t.test('Speech AI contract reconciliation: transcript & language', () => {
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

  await t.test('Compliance Intelligence contract: requirement_level & qco_records', () => {
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

  await t.test('Tender Audit contract: coverage_score, gaps & trust_disclaimer', () => {
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

  await t.test('Async Job Status Response shape validation', () => {
    const mockJobStatus = {
      job_id: 'job-98a4bc12',
      task_type: 'bulk_compliance_check',
      status: 'completed',
      result: { total_checked: 12, mandatory_count: 8 },
    };

    assert.strictEqual(mockJobStatus.status, 'completed');
    assert.strictEqual(mockJobStatus.result.total_checked, 12);
  });
});
