# BE-L: Scheduled Sync / Scheduled Digest Foundation

Task ID: BE-L

Branch: feat/backend-v03-scheduled-sync-digest

Parent branch: feat/backend-v03-job-retry-failure-handling

Goal: Provide a local MVP foundation for daily scheduled email sync and scheduled Daily Digest generation without introducing Celery Beat or production distributed scheduling.

Scope:
- Added a scheduler service that scans active Gmail mailboxes and enqueues due scheduled jobs.
- Added user-timezone daily de-dupe using stable `sync_jobs.job_key` values.
- Added local digest-time gating through existing digest schedule settings.
- Added Celery task entrypoints that enqueue scheduled jobs.
- Preserved existing synchronous APIs and async manual job APIs.

Files changed:
- backend/app/jobs/tasks.py
- backend/app/services/digest_service.py
- backend/app/services/scheduled_job_service.py
- backend/tests/test_scheduled_jobs.py
- docs/contracts/v0.3/jobs-api.contract.md
- docs/contracts/v0.3/jobs-api.examples.json
- docs/engineering/LOCAL_DEVELOPMENT.md

API contract changes:
- No new HTTP endpoints.
- Documented scheduler-created `scheduled_email_sync` and `scheduled_digest` jobs.
- Added scheduled job examples to `docs/contracts/v0.3/jobs-api.examples.json`.

Database changes: None. Reuses `sync_jobs.job_key`, `trigger_source`, `target_date`, and existing job types/statuses.

Worker changes:
- Added Celery task `app.jobs.scheduled_email_sync`.
- Added Celery task `app.jobs.scheduled_digest`.
- These tasks enqueue due jobs and rely on the existing email sync and digest workers for actual execution.

Environment variables:
- Uses existing `DIGEST_AUTO_GENERATE`.
- Uses existing `DIGEST_GENERATE_TIME`.

Tests added:
- Scheduled email sync queues active Gmail mailboxes once per user-local day and skips reauth-required mailboxes.
- Scheduled digest queues only after the configured local digest time and de-dupes by mailbox/date.
- Scheduled digest worker execution preserves `scheduled` trigger source on generated digests.

Validation result:
- `uv sync`: passed.
- `uv run alembic upgrade head`: passed.
- `uv run alembic current`: passed at `20260620_0007 (head)`.
- `uv run pytest`: passed, 187 tests.
- `uv run python -m compileall app tests`: passed.
- Secret scan: only existing docs placeholders, terminology, and fake test tokens matched.

Known risks:
- This is a local MVP scheduler foundation. It does not implement Celery Beat, distributed locks, or production-grade scheduling.
- The scheduler scans all active Gmail mailboxes when invoked; deployment cadence remains external to the backend.

Next suggested task: READY backend v0.3 pool is complete unless additional v0.3 backend tasks are added.
