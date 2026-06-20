Task ID: BE-J
Branch: feat/backend-v03-job-status-api
Parent branch: feat/backend-v03-background-jobs-foundation
Goal: Add a unified authenticated Job Status API for v0.3 background work.
Scope:
- Added `GET /api/jobs`.
- Added `GET /api/jobs/{job_id}`.
- Added `POST /api/jobs/{job_id}/retry`.
- Normalized legacy internal sync_jobs statuses and job types to the v0.3 public contract.
- Redacted error messages and result payloads in API responses.
- Enforced current-user ownership for list/detail/retry.
Files changed:
- backend/app/api/jobs.py
- backend/app/main.py
- backend/app/schemas/job.py
- backend/app/services/job_service.py
- backend/tests/test_job_api.py
- docs/contracts/v0.3/jobs-api.contract.md
- docs/contracts/v0.3/jobs-api.examples.json
- docs/autonomous/backend/BE-J-job-status-api.md
API contract changes:
- Marked the v0.3 Jobs API endpoints as implemented.
- Added retry response example.
Database changes:
- None.
Worker changes:
- None. Retry creates a queued job row; worker dispatch is staged for later async tasks.
Environment variables:
- None.
Tests added:
- Login requirement.
- Current-user visibility.
- Public status/job-type mapping.
- Type/status/date filters.
- Detail ownership blocking.
- Error redaction.
- Failed-job retry creation.
Validation result:
- `uv sync` passed.
- `uv run alembic upgrade head` passed.
- `uv run alembic current` reported `20260620_0007 (head)`.
- `uv run pytest` passed with 173 tests.
- `uv run python -m compileall app tests` passed.
- Secret scan reported only docs terminology, placeholders, and fake test tokens.
Known risks:
- Retry is a foundation behavior only. It queues a retry row but does not dispatch a worker until BE-H/BE-I/BE-K.
Next suggested task:
- BE-H Async Mail Sync.
