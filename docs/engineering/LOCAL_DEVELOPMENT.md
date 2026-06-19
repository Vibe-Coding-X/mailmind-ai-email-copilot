# Local Development

This document records the current `v0.1.0-local-mvp` local setup. It reflects the implemented repository, not future full-stack deployment plans.

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
- Email sync is triggered by an HTTP request and runs synchronously.
- Digest generation is triggered by an HTTP request and runs synchronously.
- AI uses the mock provider by default.
- Celery worker, Celery beat, scheduled sync, and scheduled digest generation are not implemented.
