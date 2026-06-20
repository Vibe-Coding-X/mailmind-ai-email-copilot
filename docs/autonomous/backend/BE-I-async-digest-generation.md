# BE-I: Async Digest Generation

Task ID: BE-I

Branch: feat/backend-v03-async-digest-generation

Parent branch: feat/backend-v03-async-mail-sync

Goal: Add background job triggers for Daily Digest generation and refresh while preserving the existing synchronous v0.2 digest APIs.

Scope:
- Added queued digest generation and refresh service entrypoints.
- Added a Celery task wrapper for queued digest work.
- Added async digest API endpoints that return the common v0.3 job envelope.
- Added mocked tests for queued digest execution and async digest API responses.

Files changed:
- backend/app/api/digests.py
- backend/app/jobs/tasks.py
- backend/app/services/digest_service.py
- backend/tests/test_digest_api.py
- backend/tests/test_digest_service.py
- docs/contracts/v0.3/jobs-api.contract.md
- docs/contracts/v0.3/jobs-api.examples.json

API contract changes:
- Added `POST /api/digest/today/generate-jobs`.
- Added `POST /api/digest/today/refresh-jobs`.
- Both endpoints return the common v0.3 `job` object and do not replace synchronous digest endpoints.

Database changes: None. Reuses `sync_jobs` fields introduced by the background jobs foundation.

Worker changes:
- Added Celery task `app.jobs.digest`.
- Worker execution marks the queued job running, delegates to the existing digest service, then stores safe result metadata or safe failure metadata.

Environment variables: None.

Tests added:
- Queued digest generation job creation and dispatch.
- Queued digest refresh job creation.
- Worker execution success path.
- Worker execution failure path.
- Async digest generate and refresh API responses.

Validation result:
- `uv sync`: passed.
- `uv run alembic upgrade head`: passed.
- `uv run alembic current`: passed at `20260620_0007 (head)`.
- `uv run pytest`: passed, 182 tests.
- `uv run python -m compileall app tests`: passed.
- Secret scan: only existing docs placeholders, terminology, and fake test tokens matched.

Known risks:
- Queued digest execution currently creates an outer queued job plus the existing internal digest generation job. This preserves current service behavior but leaves a richer job model for a later cleanup task.

Next suggested task: BE-K Retry / Failure Handling.
