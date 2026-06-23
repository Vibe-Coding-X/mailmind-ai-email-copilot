# Local Development

This document records the current `v0.4.1-config-sync-containment` local setup including backend config hardening, Celery sync containment, and frontend job trigger hardening. It reflects the implemented repository, not future full-stack deployment plans.

## Prerequisites

- Python 3.11+
- `uv`
- Node.js and npm
- Docker Desktop or equivalent local containers

## Environment

Backend and worker settings are loaded from `backend/.env` and
`backend/.env.local` by path, independent of the shell working directory.
Process environment variables still take precedence. For local development,
copy `backend/.env.example` to `backend/.env.local` and fill in local-only test
values.

Frontend public runtime config can live in `frontend/.env.local`. Copy
`frontend/.env.example` when the API base URL differs from the default.

Centralized local env files are kept outside Git at:

```text
F:\WorkSpace\mailmind-local-config\backend.env.local
F:\WorkSpace\mailmind-local-config\frontend.env.local
```

For a new worktree, copy them into place with:

```powershell
.\scripts\bootstrap-local-env.ps1
```

The bootstrap script does not print secret values, does not add env files to
Git, and verifies that `backend/.env.local` and `frontend/.env.local` are
ignored. Keep `APP_ENCRYPTION_KEY` stable across worktrees so existing local
Gmail refresh tokens remain decryptable.

Never commit:

- `.env`
- `.env.local`
- Google Client Secret
- `APP_ENCRYPTION_KEY`
- LLM API key

Do not put real or test keys in docs, README files, or `.env.example` files.

Important warning: if `APP_ENCRYPTION_KEY` is lost, already saved Gmail refresh tokens cannot be decrypted. Reconnect Gmail to recover.

## Local Infrastructure

PostgreSQL and Redis are defined in `docker/docker-compose.yml`.

```powershell
docker compose -f docker/docker-compose.yml up -d postgres redis
```

The current backend uses PostgreSQL. Redis is present for local infrastructure and future background-job/token-cache work.

## Backend

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Windows helper:

```powershell
scripts/dev-backend.ps1
```

Background worker for v0.3 local development:

```powershell
cd backend
uv run celery -A app.jobs.celery_app worker --loglevel=info --pool=solo
```

Windows helper:

```powershell
scripts/dev-worker.ps1
```

The worker uses Redis by default through `REDIS_URL`. Override `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` only when the broker/result backend should differ from Redis. Tests can set `BACKGROUND_JOBS_EAGER=true` to execute Celery tasks in-process without a long-running worker.

Scheduled job foundation for v0.3 local development:

```powershell
cd backend
uv run celery -A app.jobs.celery_app call app.jobs.scheduled_email_sync
uv run celery -A app.jobs.celery_app call app.jobs.scheduled_digest
```

These tasks enqueue due jobs; they do not run Celery Beat or a production scheduler. `app.jobs.scheduled_email_sync` queues at most one scheduled sync per active Gmail mailbox per user-local day. `app.jobs.scheduled_digest` queues at most one scheduled digest per active Gmail mailbox per user-local day after `DIGEST_GENERATE_TIME` when `DIGEST_AUTO_GENERATE=true`.

Backend verification:

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run alembic current
uv run pytest
uv run python -m compileall app tests
```

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Windows helper:

```powershell
scripts/dev-frontend.ps1
```

Frontend verification:

```powershell
cd frontend
npm install
npm run typecheck
npm run lint
npm run build
```

## Google OAuth

Configure a local OAuth client with:

```text
http://localhost:8000/api/auth/gmail/callback
```

Set:

```text
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/gmail/callback
FRONTEND_BASE_URL=http://localhost:3000
```

The v0.1 Gmail workflow uses `gmail.readonly` and `gmail.modify`. Public production distribution requires Google OAuth verification and restricted-scope review.

## v0.1 Runtime Shape

- Backend API runs in-process through FastAPI/Uvicorn.
- Email sync can be triggered synchronously (`POST /api/mailboxes/{id}/sync`) or asynchronously via background jobs.
- Digest generation can be triggered synchronously (`POST /api/digest/today/generate`) or asynchronously via background jobs.
- AI uses the mock provider by default; real providers are configured through environment variables.

## v0.3 Background Job Foundation

- Celery is available as the local background-job runtime.
- Redis is the default broker and result backend.
- `app.jobs.celery_app` is the worker entrypoint.
- `BACKGROUND_JOBS_EAGER=true` runs tasks eagerly for tests and local diagnostics.
- Scheduled sync and scheduled digest foundation tasks can be invoked manually or by an external local scheduler; Celery Beat is not implemented.
- Job status is queryable through `GET /api/jobs` and `GET /api/jobs/{job_id}`.
- Failed jobs can be retried through `POST /api/jobs/{job_id}/retry` (max 3 retries).

## v0.4 Frontend Job Experience

- `/settings/mailboxes` uses async `POST /api/mailboxes/{id}/sync-jobs` for
  Sync Today and falls back to synchronous `POST /api/mailboxes/{id}/sync` when
  async job creation is unavailable.
- `/dashboard` uses async `POST /api/digest/today/generate-jobs` and
  `POST /api/digest/today/refresh-jobs`, then polls `GET /api/jobs/{job_id}`.
- `/actions` shows recent background activity from `GET /api/jobs?limit=8`.
- Failed jobs expose retry through `POST /api/jobs/{job_id}/retry`.
- If the Celery worker is not running, job creation can still return a queued
  job, but the UI will continue to show queued/running status until polling
  reaches a terminal state or times out. The page should not blank or fake
  success.

## v0.4.1 Config And Sync Containment

- Backend, Celery worker, and one-off Celery task calls use the same
  `app.core.config.Settings` object.
- Local secrets belong in ignored `.env.local` files. Examples contain
  placeholders only.
- `POST /api/mailboxes/{id}/sync-jobs` reuses an existing queued/running
  `email_sync` job for the same user and mailbox instead of creating another.
- Scheduled sync uses the same dedupe path as manual sync. Manual and scheduled
  sync cannot create two active jobs for the same mailbox.
- Worker execution acquires `sync:mailbox:{mailbox_id}` with the job id as the
  value and a 20 minute TTL. Release verifies the value before deleting.
- Gmail message storage remains an upsert keyed by
  `emails(mailbox_id, external_id)`, protected by the existing unique
  constraint.
- Celery retries retryable network/rate-limit sync failures with backoff and
  jitter up to 3 attempts. Reauth, permission, duplicate, and lock-conflict
  errors are not retried.
- `/api/emails` and `/api/emails/today` return stable ordering by received time
  and id; the current query shape does not join one-to-many tables.

Local smoke test for the job experience:

```powershell
docker compose -f docker/docker-compose.yml up -d postgres redis

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# In a second terminal:
cd backend
uv run celery -A app.jobs.celery_app worker --loglevel=info --pool=solo

# In a third terminal:
cd frontend
npm install
npm run dev
```

Suggested manual path:

- Sign in.
- Open `/settings/mailboxes` and trigger Sync Today.
- Confirm a job card appears and moves to completed or failed.
- Open `/dashboard` and trigger Generate Digest / Refresh Digest.
- Confirm job status, retry on failed jobs when available, and digest refresh
  after completion.
- Open `/actions` and confirm Background Activity lists recent jobs.
- Switch English/Chinese and all four theme presets to check text and contrast.
