# MailMind Roadmap

This roadmap describes planned product direction after `v0.4.1-config-sync-containment`. It is not a commitment that later items are implemented today.

## v0.1 Local MVP

Status: completed.

Scope:

- Local MailMind account registration, login, logout, and session cookie auth.
- Gmail OAuth connection and disconnect.
- Encrypted Gmail refresh-token storage.
- Manual Gmail "Sync Today".
- Today's email list and email detail pages.
- Gmail read/unread synchronization.
- Backend Daily Digest generation through the mock AI provider.
- `daily_digests`, `digest_items`, `ai_runs`, `sync_jobs`, and `user_actions` persistence.
- Frontend mailbox settings, email list/detail, theme system, and static digest preview.

## v0.2 Digest AI

Status: completed.

- Wire the dashboard to `GET /api/digest/today`.
- Add frontend generate and refresh actions.
- Render digest sections from `digest_items`.
- Expose digest freshness, failure, and empty states.
- Surface digest item actions in the UI.
- Add environment-configured OpenAI-compatible AI provider support.
- Record AI provider/model metadata in `ai_runs`.
- Add email query filters and action-history query filters.
- Harden Gmail sync and secret redaction behavior.

## v0.3 Background Jobs / Scheduled Sync

Status: completed.

- Celery worker and Redis broker/result backend.
- Background jobs foundation with `app.jobs.worker:app` entrypoint.
- Job Status API: `GET /api/jobs`, `GET /api/jobs/{job_id}`, `POST /api/jobs/{job_id}/retry`.
- Async mail sync job: `POST /api/mailboxes/{mailbox_id}/sync-jobs`.
- Async digest generate and refresh jobs.
- Job retry / failure handling with `max_retries = 3` and error redaction.
- Scheduled email sync and scheduled digest local MVP foundation tasks.
- Public job type and status normalization.
- Frontend avatar account menu, theme system redesign (4 themes), i18n foundation (EN/ZH).
- UI consistency pass and runtime regression fixes.
- Celery Beat is not implemented; scheduled tasks require manual or external trigger.

## v0.4 Job Experience

Status: completed.

- Frontend Job API client with typed routes and polling hooks.
- Real-time job status, progress, error, and retry UI components.
- Async mailbox sync with polling and synchronous fallback.
- Async digest generate/refresh with polling and synchronous fallback.
- Recent jobs / background activity display on `/actions`.
- i18n coverage for job-related UI (English and Chinese).
- Theme-compatible job components using existing design tokens.
- Accessible progress bars and retry buttons.
- Backend: no changes; v0.4 wires the existing v0.3 Jobs API.

## v0.4.1 Config Sync Containment

Status: completed.

- Local config loading from `backend/.env.local` and `frontend/.env.local`.
- Shared Settings object between FastAPI and Celery worker.
- Duplicate sync job prevention with Redis per-mailbox lock.
- Retry with exponential backoff and jitter for network failures.
- Frontend job trigger hardening (disable buttons during active jobs).
- Development scripts for backend, worker, frontend, and all-in-one startup.
- No database migrations; no breaking changes.

## v0.5 Open Source Ready / CI / Docker Polish

- Add CI for backend tests, frontend typecheck/lint/build, and migration checks.
- Improve Docker Compose for full-stack local runs.
- Add example data or fixtures without secrets.
- Review docs for public setup clarity.

## v1.0 Personal Productivity Ready

- Stabilize the Daily Digest workflow.
- Harden security and operational behavior for personal daily use.
- Complete provider, scheduling, recovery, and UX polish needed beyond a local MVP.
