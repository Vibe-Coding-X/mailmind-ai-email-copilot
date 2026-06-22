# BE-K: Job Retry / Failure Handling

Task ID: BE-K

Branch: feat/backend-v03-job-retry-failure-handling

Parent branch: feat/backend-v03-async-digest-generation

Goal: Make failed background jobs traceable and safely retryable without changing existing v0.2 synchronous APIs.

Scope:
- Added a backend retry limit for failed jobs.
- Added worker dispatch when retrying supported email sync and digest job types.
- Added retry metadata to the common job response payload.
- Added retry-limit error semantics to the v0.3 jobs contract.
- Preserved existing safe error messages and job error codes for Gmail/provider and digest failures.

Files changed:
- backend/app/schemas/job.py
- backend/app/services/job_service.py
- backend/tests/test_job_api.py
- docs/contracts/v0.3/jobs-api.contract.md
- docs/contracts/v0.3/jobs-api.examples.json

API contract changes:
- Job payloads now include `retry_count`, `max_retries`, and `retry_of_job_id`.
- `POST /api/jobs/{job_id}/retry` now dispatches supported retry jobs.
- `POST /api/jobs/{job_id}/retry` returns `409 JOB_RETRY_LIMIT_EXCEEDED` when the retry limit is reached.

Database changes: None. Reuses `sync_jobs.retry_count`, `payload_json`, `celery_task_id`, and existing statuses.

Worker changes:
- Retry dispatch routes `sync_today_emails` and `refresh_access_token` jobs to `app.jobs.email_sync`.
- Retry dispatch routes `generate_daily_digest` and `refresh_daily_digest` jobs to `app.jobs.digest`.

Environment variables: None.

Tests added:
- Retrying failed email sync jobs creates a queued retry and dispatches the email sync worker.
- Retrying failed digest jobs creates a queued retry and dispatches the digest worker.
- Retry limit rejection returns `JOB_RETRY_LIMIT_EXCEEDED` and does not create a retry row.
- Job payloads expose retry metadata.

Validation result:
- `uv sync`: passed.
- `uv run alembic upgrade head`: passed.
- `uv run alembic current`: passed at `20260620_0007 (head)`.
- `uv run pytest`: passed, 184 tests.
- `uv run python -m compileall app tests`: passed.
- Secret scan: only existing docs placeholders, terminology, and fake test tokens matched.

Known risks:
- Retry policy is intentionally simple and global (`max_retries = 3`). Per-job-type retry limits can be added later without changing the response shape.

Next suggested task: BE-L Scheduled Sync / Scheduled Digest Foundation.
