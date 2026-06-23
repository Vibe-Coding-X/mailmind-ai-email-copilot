# BE v0.4.1 Config Sync Containment

## Scope

- Load backend settings from `backend/.env` and `backend/.env.local`.
- Share the same Settings object between FastAPI and Celery.
- Reuse active queued/running sync jobs instead of creating duplicates.
- Guard worker execution with a per-mailbox Redis lock.
- Preserve email upsert behavior under the existing `(mailbox_id, external_id)` unique constraint.

## Implemented

- `app.core.config.BACKEND_DIR` anchors env files independent of shell cwd.
- `enqueue_sync_today_job` returns an active job for the same user/mailbox.
- Scheduled email sync calls the same enqueue path as manual sync.
- `execute_queued_sync_job` acquires `sync:mailbox:{mailbox_id}` before running.
- Gmail timeout and TLS failures map to stable network error codes.
- Celery retries retryable sync failures with backoff and jitter up to 3 attempts.

## Limitations

- No production scheduler or Celery Beat was added.
- Historical duplicate email rows are not deleted automatically.
- Real Gmail smoke depends on local network/VPN and valid test OAuth credentials.
