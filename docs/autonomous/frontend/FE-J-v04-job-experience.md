Task ID: FE-J-v04-job-experience
Branch: feat/v04-job-experience
Parent branch: master
Goal: Connect the v0.3 Jobs API, async sync, async digest, and retry capabilities to the frontend job experience.
Scope:
- Added typed frontend Jobs API routes and client functions.
- Added reusable job status, progress, error, retry, polling, and recent activity UI.
- Wired `/settings/mailboxes` Sync Today to async `email_sync` jobs with synchronous fallback.
- Wired `/dashboard` Generate Digest and Refresh Digest to async digest jobs with synchronous fallback.
- Added Recent Jobs / Background Activity to `/actions`.
- Added English and Chinese job-experience text.
Files changed:
- docs/contracts/v0.4/job-experience-contract-check.md
- frontend/src/lib/api-routes.ts
- frontend/src/lib/api-types.ts
- frontend/src/lib/api-client.ts
- frontend/src/lib/api-client.contract.test.ts
- frontend/src/lib/jobs.ts
- frontend/src/components/jobs/*
- frontend/src/components/mailbox-sync-card.tsx
- frontend/src/components/digest-dashboard.tsx
- frontend/src/app/settings/mailboxes/page.tsx
- frontend/src/app/actions/page.tsx
- frontend/src/i18n/locales/en.json
- frontend/src/i18n/locales/zh.json
User flows:
- `/settings/mailboxes`: Sync Today creates `POST /api/mailboxes/{mailbox_id}/sync-jobs`, polls `GET /api/jobs/{job_id}`, refreshes mailbox status on completion, and shows retry on failure.
- `/dashboard`: Generate Digest creates `POST /api/digest/today/generate-jobs`, polls job status, then loads the digest by `digest_id` when available or falls back to `GET /api/digest/today`.
- `/dashboard`: Refresh Digest creates `POST /api/digest/today/refresh-jobs` with the same completion fallback behavior.
- `/actions`: Background Activity lists recent `GET /api/jobs?limit=8` results and supports failed-job retry.
Worker behavior:
- If the worker is not running, jobs remain queued/running and the UI keeps showing the job card until terminal status or polling timeout.
- If async job creation fails, mailbox sync and digest actions fall back to existing synchronous endpoints.
Security:
- The frontend displays only backend-provided redacted `error_message` / `error_code`.
- No token, session, prompt, API key, or email body is written to localStorage.
i18n changes:
- Added job, mailbox sync job, and digest job copy to English and Chinese locale files.
Theme changes:
- Job components use existing MailMind tokens, cards, badges, feedback panels, and progress rails.
- No new theme preset or external UI dependency was added.
Accessibility changes:
- Job progress uses `role="progressbar"` with numeric aria values.
- Retry buttons use native disabled semantics.
Backend changes:
- None.
Tests/checks:
- npm run typecheck
- npm run lint
Known risks:
- Real Gmail and real worker smoke testing still require local credentials and Redis/Celery runtime.
Next suggested task:
- Run full backend/frontend validation and local manual smoke test with Docker, worker, backend, and frontend.
