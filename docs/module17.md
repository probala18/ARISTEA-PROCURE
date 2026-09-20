# Module 17 — Security, Configuration & Operational Hardening

## Status

Complete for the scoped controls supported by the existing architecture.
Authentication, authorization, distributed rate limiting, deployment
infrastructure, and formal penetration testing remain out of scope.

## Baseline

The baseline is recorded in
[module17-security-baseline.md](./module17-security-baseline.md). Before this
module, uploads had only local extension/minimum-size checks, CORS was
unrestricted, evaluation paths were not API-constrained, and several route
handlers returned raw exception messages.

## Implemented controls

- Centralized environment-backed settings for environment, logging, CORS,
  upload limits, audio limits, and evaluation query limits.
- Removed the hard-coded PostgreSQL password fallback; credentials must be
  supplied through environment configuration.
- Bounded tender and speech uploads with safe filename and extension checks.
- Constrained the Module 16 API dataset path to the supplied
  `csvfiles/query_dataset.json`.
- Added safe application response headers for MIME sniffing, framing, and
  referrer behavior.
- Added centralized unexpected-error handling with internal logging and safe
  external responses.
- Replaced raw worker exception exposure with a generic job failure response.
- Preserved bounded, process-local job behavior and Module 15 lifecycle
  shutdown.

## Configuration

Supported environment settings include `ENVIRONMENT`, `LOG_LEVEL`,
`CORS_ALLOWED_ORIGINS`, `MAX_UPLOAD_BYTES`, `MAX_AUDIO_BYTES`,
`MAX_EVALUATION_QUERIES`, and the existing database settings. In development,
`CORS_ALLOWED_ORIGINS=*` remains permissive for backward compatibility. A
production deployment should provide an explicit comma-separated allowlist.

## Error and upload behavior

Upload failures return bounded generic validation messages rather than raw
parser or filesystem details. Unexpected API exceptions are logged internally
and return `500` with `internal_server_error`. Existing validation, not-found,
capacity, health, readiness, and job status contracts remain intact.

## Data integrity

No BIS/procurement dataset or domain service was changed. Module 16's
evaluation methodology and benchmark ground truth were not changed.

## Verification

Module 17 focused tests: **5 passed, 0 failed**.  
Combined Modules 14–17 integration tests: **18 passed, 0 failed**.  
Full cumulative regression: **196 passed, 0 failed, 463 warnings**.  
Ingestion validation: **passed** with 268 standards, 111 relationships,
275 versions, 710 QCO records, 1,573 certification records, 75 product
licences, 28 ministry mappings, 14 evaluation queries, and 100% core
provenance coverage.

The previously established Module 16 benchmark remains unchanged:
intent accuracy **9/14 (64.29%)**, clarification **14/14 (100%)**,
out-of-scope agreement **14/14 (100%)**, evidence availability **14/14
(100%)**, and mean measured recommendation latency **8.713 ms**. Retrieval
precision, recall, and MRR remain **UNKNOWN** because the supplied dataset
contains no structured relevance labels.

## Limitations and out-of-scope items

- No authentication or authorization architecture exists.
- No distributed rate limiting, WAF, external secret manager, or monitoring
  platform was added.
- Job state remains process-local and in-memory.
- Upload validation is bounded application-level validation, not malware
  scanning or content sandboxing.
- No formal security certification or complete penetration test is claimed.
