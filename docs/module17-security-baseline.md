# Module 17 Security Baseline

## Scope

This baseline covers the existing FastAPI configuration, upload and speech
routes, Module 14 jobs, Module 15 lifecycle/readiness behavior, Module 16
dataset evaluation, error handling, CORS, and logging before hardening.

## Findings

| Area | Status | Finding |
|---|---|---|
| Environment configuration | Partial | Settings exist, but PostgreSQL credentials have hard-coded development defaults. |
| Database configuration | Partial | `DATABASE_URL` is configurable, but credential fallback is unsafe for deployment. |
| CORS | Unsafe/ambiguous | The application allows every origin unconditionally. |
| Tender uploads | Partial | Extensions and minimum size are checked; maximum size, content type, and filename/path safety are not centralized. |
| Speech uploads | Partial | Minimum size is checked; maximum size and content-type limits are not centralized. |
| Temporary files | Partial | TTS removes its temporary file on the normal path; cleanup is not guaranteed in every failure path. |
| Module 16 dataset path | Unsafe/ambiguous | The evaluation API accepts a filesystem path without an API boundary allowlist. |
| API errors | Partial | Several routes return raw exception text in HTTP 500 responses. |
| Async jobs | Implemented/inherited | Executor is bounded, process-local, lifecycle-managed, and retains bounded completed records. |
| Health/readiness | Implemented/inherited | `/api/health` and `/api/ready` are separate and operational. |
| Logging | Missing | No centralized request/error logging or secret-redaction policy is present. |
| Response headers | Missing | No application-wide baseline security headers are configured. |
| Authentication/authorization | Out of scope | No existing authentication architecture is present. |
| Dependency management | Partial | Existing dependencies are used; no broad upgrade is justified by this module. |

## Pre-implementation gate

Module 17 changes are limited to configuration, request/file safety,
filesystem boundary checks, safe error responses, CORS configuration,
resource bounds, logging hygiene, and baseline response headers. Domain
services, datasets, recommendation behavior, evaluation methodology, and
earlier-module contracts are not changed.
