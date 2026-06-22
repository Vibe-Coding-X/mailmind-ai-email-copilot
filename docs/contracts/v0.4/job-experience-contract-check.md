# MailMind v0.4 Job Experience Contract Check

This check was performed against the `v0.3.0-async-redesign` backend code and
the v0.3 jobs contract before wiring the v0.4 frontend job experience.

## Sources Checked

- `docs/contracts/v0.3/jobs-api.contract.md`
- `docs/contracts/v0.3/jobs-api.examples.json`
- `docs/api/CURRENT_API_SUMMARY.md`
- `docs/engineering/LOCAL_DEVELOPMENT.md`
- `backend/app/api/jobs.py`
- `backend/app/api/mailboxes.py`
- `backend/app/api/digests.py`
- `backend/app/schemas/job.py`
- `backend/app/services/job_service.py`
- `backend/tests/test_job_api.py`

## Actual Jobs API Endpoints

- `GET /api/jobs`
  - Lists jobs owned by the current authenticated user.
  - Supports `limit`, `offset`, `job_type`, `status`, `created_from`, and
    `created_to`.
  - Returns `{ data: { jobs, pagination }, meta: { limit, offset } }`.
- `GET /api/jobs/{job_id}`
  - Returns one job owned by the current authenticated user.
  - Returns `404 INVALID_REQUEST` when the job does not exist or belongs to
    another user.
  - Returns `{ data: { job }, meta: {} }`.
- `POST /api/jobs/{job_id}/retry`
  - Retries a failed job owned by the current authenticated user.
  - Returns `409 JOB_RETRY_LIMIT_EXCEEDED` after the retry limit is reached.
  - Returns `400 INVALID_REQUEST` when the job is not failed or cannot be
    retried.
  - Returns `{ data: { job }, meta: {} }` for the newly queued retry job.

## Async Sync Endpoint

- `POST /api/mailboxes/{mailbox_id}/sync-jobs`
  - Creates an `email_sync` job for the selected mailbox.
  - The existing synchronous fallback remains
    `POST /api/mailboxes/{mailbox_id}/sync`.
  - Returns `{ data: { job }, meta: {} }`.

## Async Digest Generate Endpoint

- `POST /api/digest/today/generate-jobs`
  - Creates a `digest_generate` job for the current user's active mailbox.
  - The existing synchronous fallback remains `POST /api/digest/today/generate`.
  - Returns `{ data: { job }, meta: {} }`.

## Async Digest Refresh Endpoint

- `POST /api/digest/today/refresh-jobs`
  - Creates a `digest_refresh` job for the current user's active mailbox.
  - The existing synchronous fallback remains `POST /api/digest/today/refresh`.
  - Returns `{ data: { job }, meta: {} }`.

## Retry Endpoint

- `POST /api/jobs/{job_id}/retry`
  - Supported for failed `email_sync`, `digest_generate`, and `digest_refresh`
    jobs.
  - Scheduled jobs use the same public shape but retry support depends on the
    underlying internal job type.
  - The retry response is the newly created queued job, not the original failed
    job.

## Job Status Enum

Frontend must use the public status values returned by `job_payload`:

- `queued`
- `running`
- `completed`
- `failed`
- `cancelled`

The backend stores successful jobs as `succeeded` internally and normalizes them
to `completed` in API responses.

## Job Type Enum

Frontend must use the public job type values returned by `job_payload`:

- `email_sync`
- `digest_generate`
- `digest_refresh`
- `scheduled_email_sync`
- `scheduled_digest`

The backend maps legacy internal types such as `sync_today_emails`,
`generate_daily_digest`, and `refresh_daily_digest` to these public values.

## Frontend Response Fields

The frontend should use the following fields from each job response:

- `job_id`
- `job_type`
- `status`
- `progress`
- `created_at`
- `started_at`
- `finished_at`
- `error_code`
- `error_message`
- `retry_count`
- `max_retries`
- `retry_of_job_id`
- `related_resource_type`
- `related_resource_id`
- `result`

Field naming is `job_id`. The frontend should not assume an `id` alias.

## Contract / Implementation Mismatch

- No blocking mismatch was found for the v0.4 frontend job experience scope.
- `GET /api/jobs` defaults to `limit=50` in backend code, while the v0.3
  contract only says `limit` is supported. Frontend can explicitly pass a small
  limit for Recent Jobs.
- Backend job `result` is derived from sanitized `payload_json`, so completed
  digest jobs may not always include a `digest_id`. Frontend must fall back to
  `GET /api/digest/today` after a digest job completes.
- `GET /api/emails/new` remains planned but not implemented. The job experience
  work must not depend on it.

## Backend Fix Needed

No backend compatibility fix is required before frontend implementation.
