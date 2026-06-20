Task ID: BE-H
Branch: feat/backend-v03-async-mail-sync
Parent branch: feat/backend-v03-job-status-api
Goal: Add asynchronous Gmail Sync Today foundation without breaking the existing synchronous sync API.
Scope:
- Added `POST /api/mailboxes/{mailbox_id}/sync-jobs`.
- Added service support to enqueue a queued email sync job.
- Added a Celery task to execute queued sync jobs.
- Refactored synchronous sync and queued-worker sync to share the same execution path.
- Preserved existing `POST /api/mailboxes/{mailbox_id}/sync` behavior.
- Redacted sync job error messages through the shared redaction helper.
Files changed:
- backend/app/api/mailboxes.py
- backend/app/jobs/tasks.py
- backend/app/services/email_sync_service.py
- backend/tests/test_email_sync_service.py
- backend/tests/test_mailbox_sync_api.py
- docs/contracts/v0.3/jobs-api.contract.md
- docs/contracts/v0.3/jobs-api.examples.json
- docs/autonomous/backend/BE-H-async-mail-sync.md
API contract changes:
- Added `POST /api/mailboxes/{mailbox_id}/sync-jobs` to the v0.3 jobs contract.
- Added async mailbox sync response example.
Database changes:
- None.
Worker changes:
- Added `app.jobs.email_sync` Celery task.
- Worker task opens its own DB session and updates the queued sync job row.
Environment variables:
- None.
Tests added:
- Async sync enqueue creates queued job and stores Celery task id.
- Queued worker execution updates the same job, mailbox sync timestamp, and emails.
- API async sync creates queued job and blocks other users.
- Existing synchronous sync tests continue to pass.
Validation result:
- `uv sync` passed.
- `uv run alembic upgrade head` passed.
- `uv run alembic current` reported `20260620_0007 (head)`.
- `uv run pytest` passed with 177 tests.
- `uv run python -m compileall app tests` passed.
- Secret scan reported only docs terminology, placeholders, and fake redaction-test tokens.
Known risks:
- Dispatch is queued through Celery, but production-grade duplicate suppression and retry limits are deferred to BE-K.
Next suggested task:
- BE-I Async Digest Generation.
