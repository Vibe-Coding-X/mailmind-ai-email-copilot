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
- `related_resource_type`: `mailbox`, `digest`, `email`, or `null`.
- `related_resource_id`: UUID string or `null`.
- `result`: object with safe job output metadata.

## Security Rules

- `error_message` must be redacted before it is stored or returned.
- Job responses must not contain access tokens, refresh tokens, API keys, cookies, authorization headers, raw email bodies, raw Gmail payloads, raw prompts, or raw model responses.
- Examples must use fake UUIDs and fake data only.

## Planned Endpoints

- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/retry`

Endpoint implementation is staged after the BE-G background runtime foundation.
