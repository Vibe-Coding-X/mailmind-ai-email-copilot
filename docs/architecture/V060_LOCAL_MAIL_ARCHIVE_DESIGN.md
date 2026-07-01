# MailMind v0.6.0 Local Mail Archive Design

## Overview

v0.6.0 adds a mailbox-level local archive pipeline:

1. User starts full-history archive from Settings / Mailboxes.
2. Backend creates a `sync_jobs` row with `job_type=email_archive_backfill`.
3. After commit, the Celery task is dispatched.
4. Worker acquires a mailbox-level lock.
5. Provider returns one archive batch with a cursor/checkpoint.
6. Backend upserts email metadata and snippets into PostgreSQL.
7. Backend updates `mailbox_archive_states`.
8. If the provider reports more history, the user can continue from the checkpoint with another archive job.

## Reliability Model

Archive jobs preserve the existing commit-then-dispatch model. A database job is committed before Celery receives work. Celery tasks return serializable dictionaries for success, failure, ignored orphan tasks, and ignored already-terminal tasks.

Mailbox-level locking prevents a mailbox's today sync and archive backfill from writing the same mailbox concurrently. Different mailboxes can still be processed independently.

## Provider Strategy

Gmail uses `messages.list` pagination and stores the Gmail `nextPageToken` as the cursor. Each listed message is fetched for metadata and snippet, not full body.

IMAP uses conservative date-window batches from newer to older history. The cursor stores the next `window_end`, allowing retries and resumes from the checkpoint.

## Query Strategy

The Emails API reads only local PostgreSQL records. Time ranges are SQL filters over `emails.received_at`. Mailbox, search, read/unread, pagination, and sort are combined in the same query.

## Body and Attachment Policy

Full-history archive stores metadata and snippet. It does not download attachments and does not store full body text or HTML by default.

Full body storage is on demand:

1. The user opens an email detail page.
2. If `body_cache_status` is not `cached`, the UI can call `POST /api/emails/{email_id}/body-cache`.
3. The backend validates ownership, configures the mailbox provider, fetches the provider message body, and writes `body_text`, optional `body_html`, `body_cached_at`, `body_cache_source`, and `body_cache_status=cached`.
4. Later detail opens read the cached body from PostgreSQL without calling Gmail or IMAP.
5. Provider failures write `body_cache_status=failed` and `body_cache_error`; they do not erase existing metadata.
