# MailMind v0.6.0 Local Mail Archive Task Breakdown

## Backend

- Add `mailbox_archive_states`.
- Extend `emails` for archive metadata and body cache status.
- Add `email_archive_backfill` job type.
- Add archive service with commit-then-dispatch job creation.
- Add Celery archive task with serializable results.
- Add Gmail archive batch support.
- Add IMAP archive batch support.
- Extend Emails query and detail APIs for local archive browsing.
- Add on-demand body-cache API for one owned email.

## Frontend

- Add local archive type contracts and API client methods.
- Add time range filters to Emails.
- Add local archive state banners and empty states.
- Preserve mailbox/read/search/pagination filters.
- Show source mailbox and attachment indicators in email rows.
- Show mailbox/provider/labels/snippet/body cache status in detail.
- Add full-body load/retry action to email detail.
- Add Local Archive controls to Settings / Mailboxes.
- Show archive jobs in Job Activity.

## Validation

- Alembic upgrade.
- Backend pytest.
- Frontend typecheck, lint, and build.
- Secret scan for `.env.local` and common token patterns.

## Explicit Non-Goals

- Range sync.
- Outlook.
- Dashboard historical digest.
- Single-email AI summary.
- Attachment download.
- Full body sync by default.
