# MailMind v0.3 Jobs API Contract

This contract defines the shared task-status vocabulary for v0.3 background jobs. It is additive to v0.2 APIs.

## Job Status

- `queued`: Job is accepted but not started.
- `running`: Worker is executing the job.
- `completed`: Job finished successfully.
- `failed`: Job finished with a retryable or terminal failure.
- `cancelled`: Job was cancelled before completion.

Backend storage may use `succeeded` internally for legacy `sync_jobs` rows. API responses must normalize that value to `completed`.

## Job Type

- `email_sync`
- `digest_generate`
- `digest_refresh`
- `scheduled_email_sync`
- `scheduled_digest`

Legacy internal job types such as `sync_today_emails`, `generate_daily_digest`, and `refresh_daily_digest` may be mapped to these public values.

## Common Job Response Fields

Every job response object should include:

- `job_id`: UUID string.
- `job_type`: one of the public job type values.
- `status`: one of the public job status values.
- `progress`: integer from `0` to `100`.
- `created_at`: ISO-8601 UTC datetime.
- `started_at`: ISO-8601 UTC datetime or `null`.
- `finished_at`: ISO-8601 UTC datetime or `null`.
- `error_code`: safe machine-readable code or `null`.
- `error_message`: safe redacted message or `null`.
- `retry_count`: integer retry attempt count for this job.
- `max_retries`: integer retry limit enforced by the backend.
- `retry_of_job_id`: original failed job UUID string when this job is a retry, otherwise `null`.
- `related_resource_type`: `mailbox`, `digest`, `email`, or `null`.
- `related_resource_id`: UUID string or `null`.
- `result`: object with safe job output metadata.

## Security Rules

- `error_message` must be redacted before it is stored or returned.
- Job responses must not contain access tokens, refresh tokens, API keys, cookies, authorization headers, raw email bodies, raw Gmail payloads, raw prompts, or raw model responses.
- Examples must use fake UUIDs and fake data only.

## Endpoints

- `POST /api/mailboxes/{mailbox_id}/sync-jobs`
  - Requires login.
  - Creates an `email_sync` job with `queued` status.
  - Returns a common job object.
  - Does not replace the existing synchronous `POST /api/mailboxes/{mailbox_id}/sync`.
- `POST /api/digest/today/generate-jobs`
  - Requires login.
  - Creates a `digest_generate` job with `queued` status for the current user's active mailbox.
  - Returns a common job object.
  - Does not replace the existing synchronous `POST /api/digest/today/generate`.
- `POST /api/digest/today/refresh-jobs`
  - Requires login.
  - Creates a `digest_refresh` job with `queued` status for the current user's active mailbox.
  - Returns a common job object.
  - Does not replace the existing synchronous `POST /api/digest/today/refresh`.
- `GET /api/jobs`
  - Requires login.
  - Query params: `limit`, `offset`, `job_type`, `status`, `created_from`, `created_to`.
  - Returns only current user's jobs.
- `GET /api/jobs/{job_id}`
  - Requires login.
  - Returns `404 INVALID_REQUEST` when the job is absent or belongs to another user.
- `POST /api/jobs/{job_id}/retry`
  - Requires login.
  - Accepts failed jobs owned by the current user.
  - Creates a new `queued` retry row and dispatches it to the matching worker when the job type is supported.
  - Enforces `max_retries = 3`.
  - Returns `409 JOB_RETRY_LIMIT_EXCEEDED` when the failed job has reached the retry limit.
  - Returns `400 INVALID_REQUEST` when the job is not failed or the job type cannot be retried.

All endpoints use the existing project envelope: `{ "data": ..., "meta": ... }` for success and `{ "error": ... }` for errors.

## Scheduler-Created Jobs

The v0.3 local MVP scheduler foundation creates jobs through worker tasks rather than user-facing HTTP endpoints:

- `app.jobs.scheduled_email_sync`
  - Enqueues at most one `scheduled_email_sync` job per active Gmail mailbox per user-local day.
  - Skips inactive, disconnected, and reauth-required mailboxes.
- `app.jobs.scheduled_digest`
  - Enqueues at most one `scheduled_digest` job per active Gmail mailbox per user-local day after the configured local digest time.
  - Skips when a current digest already exists for that mailbox/date.

Scheduled jobs appear in `GET /api/jobs` and `GET /api/jobs/{job_id}` with the same common job object shape.
