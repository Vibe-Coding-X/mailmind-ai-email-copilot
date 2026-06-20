# MailMind Roadmap

This roadmap describes planned product direction after `v0.2.0-digest-ai`. It is not a commitment that later items are implemented today.

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

- Introduce Celery worker and beat processes.
- Move email sync and digest generation into background jobs.
- Add scheduled sync and scheduled digest generation.
- Add job polling or push-based status updates.
- Revisit Redis usage for token cache and job coordination.

## v0.4 Multi Mailbox

- Support more than one connected mailbox per user.
- Define aggregate digest behavior across mailboxes.
- Add mailbox-level filters and per-mailbox sync controls.
- Evaluate Outlook and IMAP provider implementations.

## v0.5 Open Source Ready / CI / Docker Polish

- Add CI for backend tests, frontend typecheck/lint/build, and migration checks.
- Improve Docker Compose for full-stack local runs.
- Add example data or fixtures without secrets.
- Review docs for public setup clarity.

## v1.0 Personal Productivity Ready

- Stabilize the Daily Digest workflow.
- Harden security and operational behavior for personal daily use.
- Complete provider, scheduling, recovery, and UX polish needed beyond a local MVP.
