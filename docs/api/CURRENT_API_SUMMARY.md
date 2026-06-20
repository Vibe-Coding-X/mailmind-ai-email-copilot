# Current API Summary

This document summarizes the API implemented in `backend/app/api` for `v0.2.0-digest-ai`. It intentionally excludes planned routes that are only described in older design docs.

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
GET  /api/mailboxes/{mailbox_id}/sync-status
POST /api/mailboxes/{mailbox_id}/sync
```

Implemented behavior:

- Lists and reads mailboxes owned by the current user.
- Returns latest sync state based on `sync_jobs` and mailbox timestamps.
- Manually syncs today's Gmail messages for the selected mailbox.

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

## Planned But Not Implemented in v0.2

The following appear in earlier design docs or frontend placeholders but are not implemented backend routes in v0.2:

- `GET /api/emails/new`
- `GET /api/jobs/{job_id}`
- `/api/users/*`
- `/api/settings/ai-providers/*`
- `/api/digests/*` plural routes
