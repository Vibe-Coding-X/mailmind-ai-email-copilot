Task ID: BE-G
Branch: feat/backend-v03-background-jobs-foundation
Parent branch: origin/master
Goal: Establish the v0.3 background job runtime foundation for async sync, async digest, retry, and scheduled jobs.
Scope:
- Added Celery with Redis broker/result backend defaults.
- Added background job settings and eager mode for tests.
- Added importable Celery worker entrypoint and health-check task.
- Added v0.3 Jobs API contract vocabulary for later API tasks.
- Documented local worker startup.
Files changed:
- backend/pyproject.toml
- backend/uv.lock
- backend/app/core/config.py
- backend/app/jobs/__init__.py
- backend/app/jobs/celery_app.py
- backend/app/jobs/tasks.py
- backend/app/jobs/worker.py
- backend/tests/test_background_jobs.py
- backend/tests/test_config.py
- .env.example
- docs/contracts/v0.3/jobs-api.contract.md
- docs/contracts/v0.3/jobs-api.examples.json
- docs/engineering/LOCAL_DEVELOPMENT.md
- docs/autonomous/backend/BE-G-background-jobs-foundation.md
API contract changes:
- Added v0.3 job status, job type, common response field, and planned endpoint contract docs.
Database changes:
- None. Existing sync_jobs columns cover the foundation.
Worker changes:
- Added Celery app factory, worker entrypoint, Redis defaults, and eager-mode test support.
Environment variables:
- BACKGROUND_JOBS_ENABLED
- BACKGROUND_JOBS_EAGER
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND
Tests added:
- Background job settings defaults and eager overrides.
- Celery eager configuration and health-check task execution.
Validation result:
- `uv sync` passed.
- `uv run alembic upgrade head` passed.
- `uv run alembic current` reported `20260620_0007 (head)`.
- `uv run pytest` passed with 167 tests.
- `uv run python -m compileall app tests` passed.
- Secret scan reported only docs terminology, placeholders, and fake test tokens.
Known risks:
- Windows local Celery workers should use `--pool=solo`.
- This task adds runtime foundation only; async API endpoints are implemented in later tasks.
Next suggested task:
- BE-J Job Status API.
