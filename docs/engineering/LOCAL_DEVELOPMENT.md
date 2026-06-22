# Local Development

This document records the current `v0.3.0-async-redesign` local setup. It reflects the implemented repository, not future full-stack deployment plans.

## Prerequisites

- Python 3.11+
- `uv`
- Node.js and npm
- Docker Desktop or equivalent local containers

## Environment

Copy `.env.example` to `.env` and fill in local-only values.

Never commit:

- `.env`
- Google Client Secret
- `APP_ENCRYPTION_KEY`
- LLM API key

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

Background worker for v0.3 local development:

```powershell
cd backend
uv run celery -A app.jobs.worker:app worker --loglevel=info --pool=solo
```

The worker uses Redis by default through `REDIS_URL`. Override `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` only when the broker/result backend should differ from Redis. Tests can set `BACKGROUND_JOBS_EAGER=true` to execute Celery tasks in-process without a long-running worker.

Scheduled job foundation for v0.3 local development:

```powershell
cd backend
uv run celery -A app.jobs.worker:app call app.jobs.scheduled_email_sync
uv run celery -A app.jobs.worker:app call app.jobs.scheduled_digest
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
- `app.jobs.worker:app` is the worker entrypoint.
- `BACKGROUND_JOBS_EAGER=true` runs tasks eagerly for tests and local diagnostics.
- Scheduled sync and scheduled digest foundation tasks can be invoked manually or by an external local scheduler; Celery Beat is not implemented.
- Job status is queryable through `GET /api/jobs` and `GET /api/jobs/{job_id}`.
- Failed jobs can be retried through `POST /api/jobs/{job_id}/retry` (max 3 retries).
