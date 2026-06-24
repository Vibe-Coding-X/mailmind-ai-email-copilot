# Current Schema Summary

This document summarizes the SQLAlchemy models and Alembic migrations present in
`v0.5.0-provider-mailbox-foundation`.

Current Alembic migration line:

```text
20260618_0001 -> 20260619_0002 -> 20260619_0003 -> 20260619_0004 -> 20260619_0005 -> 20260619_0006 -> 20260620_0007 -> 20260624_0008 -> 20260624_0009
```

Expected Alembic head:

```text
20260624_0009
```

Migration `20260624_0008` expands sync job statuses for reliable Celery
dispatch: `pending_dispatch` and `dispatch_failed`.

## Tables

### `users`

Local MailMind user identity. Stores normalized email, optional display name, password hash, status, timezone, and audit timestamps.

### `auth_accounts`

Login-provider identity records for local auth. Password auth uses this table separately from Gmail mailbox authorization.

### `sessions`

HttpOnly cookie session backing store. Stores hashed session tokens, expiration, optional IP/user-agent metadata, and revocation time.

### `mailboxes`

Connected mailbox records. Provider keys are constrained to `gmail`, `imap`,
and `outlook`. Records include provider account id, email address, optional
display name, permission mode, granted scopes, connection status, sync cursor,
and sync timestamps.

The row is a mailbox instance, not a provider-level singleton. A user may have
multiple Gmail rows and multiple IMAP rows. Gmail rows use the Google account
`sub` as `provider_account_id` when available. IMAP rows use
`lower(host):port:lower(username)` as `provider_account_id`.

### `mailbox_credentials`

Sensitive mailbox credential storage. Gmail refresh tokens and IMAP passwords
are encrypted with `APP_ENCRYPTION_KEY`; access tokens are not persisted as
long-lived database fields. IMAP non-secret connection config is stored in
`credentials_json`, including provider preset, host, port, username, folder,
and SSL preference.

### `emails`

Synced provider message facts for the user's local day. Stores provider ids,
headers, sender/recipient metadata, snippet, cleaned body text, received time,
read state, labels, and sync timestamps.

Uniqueness is enforced by `emails_mailbox_external_id_uq` on
`(mailbox_id, external_id)`. Gmail sync must upsert by this key; subject,
sender, received time, snippet, and labels are not identity fields.

### `sync_jobs`

Tracks sync and digest job attempts. In v0.3, this table is used by both synchronous service calls and Celery background workers. Supports `retry_count`, `error_code`, `error_message` (redacted), `payload_json` (safe structured result), `trigger_source` (`manual` or `scheduled`), `started_at`, and `finished_at`. `digest_id` has a foreign key to `daily_digests.id` with `ON DELETE SET NULL`.

`sync_jobs_active_job_key_uq` prevents duplicate pending/queued/running keyed
jobs.
Manual mailbox sync also performs service-level active job reuse scoped by
`user_id + mailbox_id + job_type + queued/running`. Different mailbox instances
can have independent active sync jobs.

### `daily_digests`

Versioned daily digest snapshots per scope and local date. Tracks current
version, status, trigger source, coverage window, mail count, new-mail count,
overview JSON, and `scope_type`.

- `scope_type='mailbox'` -> `mailbox_id` is required
- `scope_type='all'` -> `mailbox_id` is `NULL`

### `digest_items`

Structured digest rows generated from AI output. Stores email/todo/risk item
type, section, linked email, source `mailbox_id`, title, summary, category,
suggested action, priority, reason, deadline, confidence, and display order.

### `ai_runs`

AI execution audit table. Stores run type, provider/model metadata,
prompt/schema versions, input hash and summary, structured output JSON,
status, errors, token counts, and timing. `mailbox_id` is nullable so an
all-mailboxes digest can still create one audit row.

v0.2 adds nullable `provider_id` and `provider_type` columns so digest AI runs
record which configured provider profile handled the run.

### `user_actions`

User operation audit table. Stores actions against mailboxes, digests, digest items, and emails, including provider effect, before/after state JSON, status, and errors.

## Migration Notes

- There is a linear migration history through `20260624_0009`.
- Migration `20260619_0004` removes the early `sync_jobs.digest_id` digest scope.
- Migration `20260619_0005` creates `daily_digests`, `digest_items`, and `ai_runs`, then re-adds `sync_jobs.digest_id` with a foreign key to `daily_digests`.
- Migration `20260620_0007` adds `ai_runs.provider_id` and `ai_runs.provider_type`.
- Migration `20260624_0008` adds `pending_dispatch` and `dispatch_failed` to
  `sync_jobs.status` and widens the active job-key index to include
  `pending_dispatch`.
- Migration `20260624_0009` adds digest `scope_type`, makes
  `daily_digests.mailbox_id` nullable for `scope_type='all'`, and makes
  `ai_runs.mailbox_id` nullable for all-mailboxes digest audit rows.
- This resolves the half-built digest schema concern in the current head.
- `sync_jobs.digest_id`, when present at head, points to `daily_digests.id`.

## Current Limitations

- The database has digest and AI audit tables with v0.2 provider metadata. Real provider values must come from environment configuration outside Git; the mock provider remains available as fallback.
- `sync_jobs` records both synchronous service work and Celery background job work in v0.3.
- v0.5 digest scope stabilization adds one new migration but does not introduce
  new business tables.
- The schema is local-MVP oriented and has not been hardened for production multi-tenant SaaS operation.
- v0.4.1 did not add a migration because the email uniqueness and active
  job-key index already exist at current head.

## Verification

Run:

```powershell
cd backend
uv sync
uv run alembic upgrade head
uv run alembic current
uv run pytest
uv run python -m compileall app tests
```
