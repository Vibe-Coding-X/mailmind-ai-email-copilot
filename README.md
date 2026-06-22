# MailMind

MailMind is a local-first AI email copilot that connects to Gmail, syncs today's email, and turns it into an actionable Daily Digest.

Current release: `v0.3.0-async-redesign`

MailMind is not a production SaaS product. The current codebase is a local release for validating authentication, Gmail connectivity, email sync, Daily Digest generation, configured AI provider calls, and the first connected frontend workflows.

## What It Does

MailMind adds a decision layer on top of email:

- Authenticates a local MailMind user with an HttpOnly cookie session.
- Connects one Gmail mailbox through OAuth.
- Encrypts and stores the Gmail refresh token locally.
- Syncs Gmail messages received today.
- Shows today's synced emails and individual email detail pages.
- Writes read/unread changes back to Gmail when the mailbox has `gmail.modify`.
- Generates a Daily Digest through the mock provider or configured OpenAI-compatible AI providers.
- Records AI runs, provider/model metadata, digest items, sync jobs, and user actions for auditability.
- Provides dashboard digest controls, digest item actions, and action history.

## Current v0.3 Features

- Background jobs foundation with Celery worker and Redis broker.
- Job Status API: list, detail, and retry endpoints for async jobs.
- Async mail sync, digest generate, and digest refresh jobs.
- Job retry / failure handling with max retries and error redaction.
- Scheduled email sync and scheduled digest local MVP foundation.
- Frontend avatar account menu with sign-out.
- Theme system redesign: Amber Focus, Noir Pulse, Paper Calm, Dense Minimal.
- i18n foundation with English and Chinese language resources.
- UI consistency pass and runtime regression fixes.

## Current v0.2 Features

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
- Mock AI fallback and environment-configured OpenAI-compatible provider chain.
- Robust digest prompt/parser handling for real provider output.
- `ai_runs` records for provider/model metadata and output traceability.
- `digest_items` records for actionable digest rows.
- Digest dashboard connected to `/api/digest/today`.
- Digest generation and refresh controls in the frontend.
- Digest item `mark-done`, `dismiss`, and `snooze` actions.
- `/actions` action history page with filters and pagination.
- Email list search, read-state filters, date filters, and pagination.
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
- AI: in-process mock provider plus OpenAI-compatible provider profiles from environment variables.
- Local infrastructure: PostgreSQL and Redis through Docker Compose.

## Architecture Overview

```text
Next.js frontend
  login/register, mailbox settings, email list/detail, digest dashboard, actions
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

The v0.3 release adds Celery background workers for async sync and digest jobs. Scheduled sync/digest tasks are available as local MVP foundation (manual/external trigger). In-app AI provider management is not implemented.

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
- `AI_PROVIDER_MODE`: set to `env` to use configured AI provider profiles; leave empty to use the mock fallback.
- `AI_DEFAULT_PROVIDER`: default provider profile id.
- `AI_PROVIDER_ORDER`: comma-separated provider profile fallback order.
- `AI_PROVIDER_<ID>_TYPE`: currently `openai_compatible`.
- `AI_PROVIDER_<ID>_BASE_URL`: OpenAI-compatible API base URL.
- `AI_PROVIDER_<ID>_API_KEY`: local AI provider API key.
- `AI_PROVIDER_<ID>_MODEL`: provider model id.

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

The current Gmail integration uses:

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
- Jobs: `/api/jobs/*`
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
- `sync_jobs` (extended in v0.3 with retry, error, and payload fields)
- `daily_digests`
- `digest_items`
- `ai_runs`
- `user_actions`

## Current Limitations

- Real AI provider calls are configured through local environment variables only.
- No in-app AI provider settings UI is implemented.
- Real AI provider behavior depends on external model/network availability.
- Scheduled jobs require manual or external trigger; Celery Beat is not implemented.
- Production-grade distributed scheduling is not included.
- Multi-mailbox aggregate Digest is not complete.
- Outlook and IMAP are not implemented.
- Production deployment, Google OAuth verification, and security review are not complete.
- The current target is a local MVP, not a production SaaS product.

## Roadmap

- v0.1 Local MVP: completed.
- v0.2 Digest AI: completed.
- v0.3 Background Jobs / Scheduled Sync: completed.
- v0.4 Multi Mailbox.
- v0.5 Open Source Ready / CI / Docker polish.
- v1.0 Personal Productivity Ready.

See `docs/ROADMAP.md` for more detail.

## License

Apache-2.0
