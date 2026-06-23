# Current API Summary

This document summarizes the API implemented in `backend/app/api` for
`v0.3.0-async-redesign`, consumed by the `v0.4.0-job-experience` frontend work,
and hardened by `v0.4.1-config-sync-containment`. It intentionally excludes
planned routes that are only described in older design docs.

All application responses use either:

```json
{ "data": {}, "meta": {} }
```

or:

```json
{ "error": { "code": "INVALID_REQUEST", "message": "Invalid request.", "retryable": false, "details": {} } }
```

Authentication uses an HttpOnly session cookie. Browser requests from the frontend must include credentials.

## Health

```text
GET /health
```

Returns backend service health.

## Auth

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

Implemented behavior:

- `register` creates a local user and sets a session cookie.
- `login` authenticates the local user and sets a session cookie.
- `logout` revokes the current session token when present and clears the cookie.
- `me` returns the current authenticated user.

## Gmail OAuth

```text
GET  /api/auth/gmail/login
GET  /api/auth/gmail/callback
POST /api/auth/gmail/disconnect
```

Implemented behavior:

- `login` returns a Gmail authorization URL for the signed-in MailMind user.
- `callback` exchanges the OAuth code, creates or updates the Gmail mailbox, stores encrypted credentials, and redirects to `/settings/mailboxes`.
- `disconnect` disconnects the current user's Gmail mailbox and clears stored credentials.

## Mailboxes

```text
GET  /api/mailboxes
GET  /api/mailboxes/{mailbox_id}
GET  /api/mailboxes/{mailbox_id}/capabilities
GET  /api/mailboxes/{mailbox_id}/sync-status
POST /api/mailboxes/{mailbox_id}/sync
```

Implemented behavior:

- Lists and reads mailboxes owned by the current user.
- Mailbox list and detail payloads preserve v0.4 fields and add v0.5 provider
  fields: `account_email`, `display_name`, and `capabilities`.
- `GET /api/mailboxes/{mailbox_id}/capabilities` returns a compact provider
  capability payload for the selected mailbox.
- Returns latest sync state based on `sync_jobs` and mailbox timestamps.
- Manually syncs today's Gmail messages for the selected mailbox.

### Async Sync Job

```text
POST /api/mailboxes/{mailbox_id}/sync-jobs
```

Creates an `email_sync` job with `queued` status. If the same user/mailbox
already has a queued or running email sync job, the endpoint returns that job
instead of creating a duplicate. Does not replace the existing synchronous
`POST /api/mailboxes/{mailbox_id}/sync`.

## Emails

```text
GET  /api/emails
GET  /api/emails/today
GET  /api/emails/{email_id}
POST /api/emails/{email_id}/mark-read
POST /api/emails/{email_id}/mark-unread
```

`GET /api/emails` accepts:

```text
limit=1..100
offset=0..
is_read=true|false
mailbox_id=<uuid>
received_from=<iso datetime>
received_to=<iso datetime>
q=<keyword>
```

`GET /api/emails/today` accepts:

```text
sort=received_at_desc
is_read=true|false
priority=high|medium|low
source=all|current_digest
```

Implemented behavior:

- Lists current-user emails with filters, descending received time, offset/limit
  pagination, and `has_more` metadata.
- Lists synced emails received during the current user's local day.
- Reads an owned email detail record.
- Writes read/unread state to Gmail first, then updates local `emails.is_read`.
- Records read/unread operations in `user_actions`.

## Digest

The implemented route prefix is singular:

```text
/api/digest
```

Routes:

```text
GET  /api/digest/today
POST /api/digest/today/generate
POST /api/digest/today/refresh
GET  /api/digest/{digest_id}
```

Implemented behavior:

- Reads the current digest for the user's active Gmail mailbox and local date.
- Generates or refreshes today's digest synchronously.
- Uses the configured v0.2 AI provider chain when `AI_PROVIDER_MODE=env`;
  otherwise falls back to the mock provider.
- Creates `daily_digests`, `digest_items`, `ai_runs`, and related `sync_jobs`.

### Async Digest Jobs

```text
POST /api/digest/today/generate-jobs
POST /api/digest/today/refresh-jobs
```

Create `digest_generate` or `digest_refresh` jobs with `queued` status. If an
active job of the same digest type already exists for the current mailbox and
local date, the endpoint returns that active job. Do not replace the existing
synchronous `POST /api/digest/today/generate` and
`POST /api/digest/today/refresh`.

## Jobs

```text
GET  /api/jobs
GET  /api/jobs/{job_id}
POST /api/jobs/{job_id}/retry
```

Implemented behavior:

- `GET /api/jobs` lists current user's jobs with optional filters: `limit`, `offset`, `job_type`, `status`, `created_from`, `created_to`. Returns paginated results with `has_more` metadata.
- `GET /api/jobs/{job_id}` returns a single job detail. Returns `404 INVALID_REQUEST` when the job is absent or belongs to another user.
- `POST /api/jobs/{job_id}/retry` accepts failed jobs owned by the current user. Creates a new `queued` retry row and dispatches it. Enforces `max_retries = 3`. Returns `409 JOB_RETRY_LIMIT_EXCEEDED` when the limit is reached. Returns `400 INVALID_REQUEST` when the job is not failed or cannot be retried.

Public job types: `email_sync`, `digest_generate`, `digest_refresh`, `scheduled_email_sync`, `scheduled_digest`.

Public job statuses: `queued`, `running`, `completed`, `failed`, `cancelled`.

Job responses include: `job_id`, `job_type`, `status`, `progress`, `created_at`, `started_at`, `finished_at`, `error_code`, `error_message` (redacted), `retry_count`, `max_retries`, `retry_of_job_id`, `related_resource_type`, `related_resource_id`, `result`.

Sync error codes used by v0.4.1 containment include `network_tls`,
`network_timeout`, `gmail_rate_limited`, `gmail_quota_exceeded`,
`oauth_invalid_grant`, `gmail_permission_denied`, `gmail_api_error`,
`worker_lock_conflict`, `duplicate_job`, and legacy provider codes retained for
backward compatibility. Error messages are redacted before API serialization.

### v0.4 Frontend Job Experience Usage

The v0.4 frontend job experience uses the existing v0.3 backend endpoints:

- `/settings/mailboxes` calls `POST /api/mailboxes/{mailbox_id}/sync-jobs`,
  polls `GET /api/jobs/{job_id}`, refreshes mailbox sync status on completion,
  and exposes `POST /api/jobs/{job_id}/retry` for failed sync jobs.
- `/dashboard` calls `POST /api/digest/today/generate-jobs` and
  `POST /api/digest/today/refresh-jobs`, polls `GET /api/jobs/{job_id}`, and
  reloads the digest after completion. When a completed job response does not
  include a digest id in `result` or `related_resource_id`, the frontend falls
  back to `GET /api/digest/today`.
- `/actions` shows recent background activity from `GET /api/jobs?limit=8` and
  exposes retry for failed jobs.

No new backend endpoint was added for v0.4 job experience.

## Digest Item Actions

These routes are implemented under the singular digest prefix:

```text
POST /api/digest/items/{item_id}/mark-done
POST /api/digest/items/{item_id}/dismiss
POST /api/digest/items/{item_id}/snooze
```

Implemented behavior:

- Records user intent against a digest item through `user_actions`.
- Does not mutate `digest_items` as if AI suggestions were user state.

## User Actions

```text
GET  /api/actions
GET  /api/actions/{action_id}
POST /api/actions
GET  /api/actions/digest-items/{item_id}
```

Implemented behavior:

- Lists current user's actions with optional filtering by action type, status,
  provider effect, created date range, and related resource. The list endpoint
  supports offset/limit pagination and `has_more` metadata.
- Reads a single user action.
- Creates a user action record.
- Lists actions associated with one digest item.

## Planned But Not Implemented in v0.3

The following appear in earlier design docs or frontend placeholders but are not implemented backend routes in v0.3:

- `GET /api/emails/new`
- `/api/users/*`
- `/api/settings/ai-providers/*`
- `/api/digests/*` plural routes
