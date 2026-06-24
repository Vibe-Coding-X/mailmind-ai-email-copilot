# Job Execution Model

MailMind v0.5 keeps Celery. PostgreSQL is the source of truth for background
jobs. Redis is used only as Celery broker/result storage and mailbox lock
storage.

## Roles

- PostgreSQL: durable job state, mailbox ownership, digest scope, and retry
  history.
- Redis: Celery broker, Celery result backend, and mailbox lock storage.
- Celery: asynchronous delivery and worker execution.

## Sync Job Lifecycle

- `pending_dispatch`: the `sync_jobs` row exists in PostgreSQL and has been
  flushed, but Celery dispatch has not yet succeeded.
- `queued`: Celery accepted the task and `celery_task_id` is stored.
- `running`: worker accepted the queued DB job and wrote `started_at`.
- `completed`: public API status mapped from internal `succeeded`.
- `failed`: terminal business failure, including stale recovery via
  `error_code=stale_sync_job`.
- `dispatch_failed`: Celery dispatch failed after the DB row was committed.
- `cancelled`: reserved terminal state.

## Dispatch Rule

The required order is:

1. create DB job with `pending_dispatch`
2. `flush`
3. `commit`
4. dispatch Celery task with `job.id`
5. persist `celery_task_id`
6. update job to `queued`

If Celery dispatch fails, the committed DB job is updated to:

- `status=dispatch_failed`
- `error_code=celery_dispatch_failed`
- redacted `error_message`

## Worker Safety

Workers always receive `job.id`, never `celery_task_id`, and always load the DB
job first.

- missing DB job: return `ignored/orphaned_*_task`
- non-dispatchable DB job (`failed`, `completed`, `dispatch_failed`,
  `cancelled`, stale-recovered rows): return
  `ignored/stale_or_completed_*_task`
- business exceptions are serialized into result dicts and never bubble to
  Celery as custom Python exceptions

## Mailbox Isolation

- duplicate active sync lookup is scoped by `user_id + mailbox_id + job_type`
- Redis lock key is `sync:mailbox:{mailbox_id}`
- different mailbox instances can each queue and run independent sync jobs

## Digest Scope

v0.5 digest scope now supports two request shapes:

- `scope_type=all`: digest across all connected active mailboxes for the user
- `scope_type=mailbox`: digest only for the selected mailbox

For `scope_type=all`:

- PostgreSQL stores the digest row with `daily_digests.scope_type='all'`
- `daily_digests.mailbox_id` is `NULL`
- the digest still uses the same DB-first Celery dispatch model
- digest items keep their source `mailbox_id`
- overview payloads can include `mailbox_summaries` so the frontend can render
  `Priority Queue + By Mailbox`

For `scope_type=mailbox`:

- `daily_digests.scope_type='mailbox'`
- `daily_digests.mailbox_id=<selected mailbox id>`
- digest items and summaries stay mailbox-local
