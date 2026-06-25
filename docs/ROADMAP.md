# MailMind Roadmap

This roadmap describes MailMind's product direction. It is not a commitment that later items are implemented today.

## v0.1 Local MVP

Status: ✅ completed.

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

Status: ✅ completed.

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

Status: ✅ completed.

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

Status: ✅ completed.

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

Status: ✅ completed.

- Local config loading from `backend/.env.local` and `frontend/.env.local`.
- Shared Settings object between FastAPI and Celery worker.
- Duplicate sync job prevention with Redis per-mailbox lock.
- Retry with exponential backoff and jitter for network failures.
- Frontend job trigger hardening (disable buttons during active jobs).
- Development scripts for backend, worker, frontend, and all-in-one startup.
- No database migrations; no breaking changes.

## v0.5 Provider Mailbox Foundation

Status: ✅ completed.

- Provider-aware mailbox architecture and contract.
- `MailboxProvider` interface with Gmail, IMAP, and Outlook registry entries.
- Gmail behavior preserved behind `GmailProvider`.
- IMAP Provider MVP with encrypted password storage, real connect API, mocked
  provider tests, mailbox-local manual sync, and minimal settings UI.
- Outlook preparation skeleton with honest disabled capabilities; no connect UI
  unless real OAuth configuration is available.
- Mailbox API exposes provider, account email, display name, and capabilities.
- Settings uses Provider Catalog plus Mailbox Instances: Add Gmail/Add IMAP
  remain available for multiple accounts, while Connected Mailboxes renders
  backend mailbox rows.
- IMAP settings persist as non-secret provider config; passwords remain
  encrypted and are never returned.
- Frontend shows provider badges and defaults `/emails` to a selected mailbox,
  with All Mailboxes available only as an explicit mixed view.
- Celery reliability stabilization: PostgreSQL as job source of truth,
  commit-then-dispatch model, `pending_dispatch` and `dispatch_failed` states,
  `celery_task_id` tracking, orphan/stale task safety.
- Digest scope supports `all` (multi-mailbox) and `mailbox` (single-mailbox).
- Cross-mailbox Digest, Multi Mailbox Digest, AI Settings, email sending, and
  Celery Beat remain out of scope.

## v0.5.1 UI/UX Polish

Status: ✅ completed.

- 6 theme presets with full light/dark mode support: Neon Cyber, Glass Aurora, Gradient Flow, Soft Clay, Noir Pulse, Dense Minimal.
- Legacy theme migration: `amber-focus` → `neon-cyber`, `paper-calm` → `glass-aurora`.
- Pre-hydration theme application — no flash of unstyled content (FOUC).
- CSS custom properties architecture with 50+ variables per theme.
- Keyframe animations: fadeSlideUp, scaleIn, pulseGlow, neonFlicker, scanLine, shimmer, bounce.
- Responsive design with sidebar collapse at 780px breakpoint.
- `prefers-reduced-motion` support.
- Playwright-verified screenshots across all 12 theme/mode combinations.
- Theme switcher UI with compact mode (auth pages) and full mode (settings).

## v0.5.2 Demo Readiness

Status: ✅ completed.

- 5 Mermaid architecture diagrams: system context, provider/mailbox, Celery job dispatch, digest scope flow, data model ERD.
- Portfolio-grade README with real dashboard screenshot, updated capabilities, and documentation index.
- Demo script (5–8 min) covering dashboard, themes, multi-mailbox, sync, emails, actions, and architecture highlights.
- Project walkthrough for interviews covering problem, architecture decisions, trade-offs, and lessons learned.
- Architecture diagrams index with instructions for generating SVG/PNG from Mermaid source.
- Documentation hub updated with links to all new docs.

## v0.6 Open Source Ready / CI / Docker Polish

Status: 🧭 planned.

- Add CI for backend tests, frontend typecheck/lint/build, and migration checks.
- Improve Docker Compose for full-stack local runs.
- Add example data or fixtures without secrets.
- Review docs for public setup clarity.
- Full Outlook OAuth provider implementation.
- IMAP mark_read/unread implementation.
- In-app AI provider settings UI.

## v1.0 Personal Productivity Ready

Status: 🧭 planned.

- Stabilize the Daily Digest workflow.
- Harden security and operational behavior for personal daily use.
- Complete provider, scheduling, recovery, and UX polish needed beyond a local MVP.
- Celery Beat for automated scheduling.
- Production deployment and Google OAuth verification.
