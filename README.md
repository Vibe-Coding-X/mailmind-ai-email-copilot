# MailMind

MailMind is a local-first AI email copilot that connects to Gmail, syncs today's email, and turns it into an actionable Daily Digest.

Current release: `v0.1.0-local-mvp`

MailMind is not a production SaaS product. The current codebase is a local MVP for validating authentication, Gmail connectivity, email sync, a mock Daily Digest pipeline, and the first frontend workflows.

## What It Does

MailMind adds a decision layer on top of email:

- Authenticates a local MailMind user with an HttpOnly cookie session.
- Connects one Gmail mailbox through OAuth.
- Encrypts and stores the Gmail refresh token locally.
- Syncs Gmail messages received today.
- Shows today's synced emails and individual email detail pages.
- Writes read/unread changes back to Gmail when the mailbox has `gmail.modify`.
- Generates a Daily Digest through a deterministic mock AI provider.
- Records AI runs, digest items, sync jobs, and user actions for auditability.

## Current v0.1 Features

- User registration, login, logout, and `GET /api/auth/me`.
- HttpOnly cookie-backed sessions persisted in `sessions`.
- Gmail OAuth login/callback/disconnect.
- Mailbox connected state and reauthorization state management.
- Encrypted Gmail refresh-token storage in `mailbox_credentials`.
- Manual "Sync Today" Gmail email sync.
- Today's email list through `GET /api/emails/today`.
- Email detail through `GET /api/emails/{email_id}`.
- Gmail-backed `mark-read` and `mark-unread`.
- `user_actions` audit records for user and digest-item actions.
- Daily Digest generation and refresh in the backend.
- Mock AI pipeline with structured digest output.
- `ai_runs` records for model metadata and output traceability.
- `digest_items` records for actionable digest rows.
- Frontend theme system with light/dark modes and multiple presets.
- `/settings/mailboxes` for Gmail connection, disconnect, state, and sync.
- `/emails` for today's email list and read filter.
- `/emails/[id]` for email detail and read/unread actions.
- Frontend mailbox sync entry point.
- Capsule-style UI theme, plus clean, minimal, and soft presets.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic Settings, PostgreSQL, `uv`.
- Frontend: Next.js, React, TypeScript, plain CSS theme tokens.
- Provider: Gmail API through a provider adapter.
- AI: in-process mock LLM provider for v0.1.
- Local infrastructure: PostgreSQL and Redis through Docker Compose.

## Architecture Overview

```text
Next.js frontend
  login/register, mailbox settings, email list/detail, static digest preview
        |
FastAPI backend
  auth, Gmail OAuth, mailboxes, emails, digest, actions
        |
Services
  session, OAuth, credential encryption, email sync, digest, AI run, actions
        |
Provider adapters
  GmailProvider
        |
PostgreSQL
  users, sessions, mailboxes, credentials, emails, digests, ai_runs, actions
```

The v0.1 digest path is synchronous and local. Celery, scheduled sync, and a real LLM provider are not implemented yet.

## Local Development

Prerequisites:

- Python 3.11+
- `uv`
- Node.js compatible with Next.js 15
- npm
- Docker Desktop or a local PostgreSQL 15-compatible database

Start local infrastructure:

```powershell
docker compose -f docker/docker-compose.yml up -d postgres redis
```

Install and run the backend:

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Install and run the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:3000`. The backend defaults to `http://127.0.0.1:8000`.

## Environment Variables

Use `.env.example` as a template and create a local `.env`. Do not commit `.env`.

Important variables:

- `APP_SECRET_KEY`: local session/signing secret.
- `APP_ENCRYPTION_KEY`: key used to encrypt stored Gmail refresh tokens.
- `APP_ENCRYPTION_KEY_VERSION`: local key version label.
- `DATABASE_URL`: SQLAlchemy PostgreSQL URL.
- `REDIS_URL`: Redis URL reserved for local infrastructure and future async work.
- `FRONTEND_BASE_URL`: frontend URL used after Gmail OAuth callback.
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins for credentialed CORS.
- `GOOGLE_CLIENT_ID`: Google OAuth client ID.
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret.
- `GOOGLE_REDIRECT_URI`: callback URL, usually `http://localhost:8000/api/auth/gmail/callback`.
- `LLM_PROVIDER`: leave empty or set to `mock` for v0.1.

Security requirements:

- Do not commit `.env`.
- Do not commit a Google Client Secret.
- Do not commit `APP_ENCRYPTION_KEY`.
- Do not commit an LLM API key.
- If `APP_ENCRYPTION_KEY` is lost, existing encrypted Gmail refresh tokens cannot be decrypted.
- Gmail restricted scopes such as `gmail.modify` require Google review before production/public distribution.

## Google OAuth Setup

Create a Google OAuth app for local testing and configure:

```text
Authorized redirect URI:
http://localhost:8000/api/auth/gmail/callback
```

The v0.1 Gmail integration uses:

```text
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.modify
```

`gmail.readonly` is used for message sync. `gmail.modify` is used for read/unread writeback. Public SaaS usage requires a permission and Google verification review.

## Running Backend Tests

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run alembic current
uv run pytest
uv run python -m compileall app tests
```

## Running Frontend Checks

```powershell
cd frontend
npm install
npm run typecheck
npm run lint
npm run build
```

## Current API Summary

The current backend API is documented in `docs/api/CURRENT_API_SUMMARY.md`.

Key route groups:

- Auth: `/api/auth/*`
- Gmail OAuth: `/api/auth/gmail/*`
- Mailboxes: `/api/mailboxes/*`
- Emails: `/api/emails/*`
- Digest: `/api/digest/*`
- User actions: `/api/actions/*`

Note that the digest routes are singular: `/api/digest`, not `/api/digests`.

## Current Database Summary

The current schema is documented in `docs/database/CURRENT_SCHEMA_SUMMARY.md`.

Current tables:

- `users`
- `auth_accounts`
- `sessions`
- `mailboxes`
- `mailbox_credentials`
- `emails`
- `sync_jobs`
- `daily_digests`
- `digest_items`
- `ai_runs`
- `user_actions`

## Current Limitations

- Real LLM providers are not integrated; v0.1 uses the mock provider only.
- Digest frontend dashboard is a static preview and is not fully wired to `/api/digest`.
- Celery and background workers are not implemented.
- Scheduled sync is not implemented.
- Multi-mailbox aggregate Digest is not complete.
- Outlook and IMAP are not implemented.
- Production deployment, Google OAuth verification, and security review are not complete.
- The current target is a local MVP, not a production SaaS product.

## Roadmap

- v0.1 Local MVP: completed.
- v0.2 Digest Dashboard / Frontend Digest UI.
- v0.3 Real AI Provider.
- v0.4 Background Jobs / Scheduled Sync.
- v0.5 Multi Mailbox.
- v0.6 Open Source Ready / CI / Docker polish.
- v1.0 Personal Productivity Ready.

See `docs/ROADMAP.md` for more detail.

## License

Apache-2.0
