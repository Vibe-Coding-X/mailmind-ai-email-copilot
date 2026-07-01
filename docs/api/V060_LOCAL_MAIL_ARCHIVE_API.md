# MailMind v0.6.0 Local Mail Archive API

## Emails

`GET /api/emails`

Query parameters:

- `range`: `today`, `last_7_days`, `last_30_days`, `custom`, or `all_synced`
- `from`: custom range start date
- `to`: custom range end date
- `mailbox_id`: optional mailbox filter
- `is_read`: optional read/unread filter
- `q`: optional local search over subject, sender, snippet, recipients, and labels
- `limit`, `offset`: pagination
- `sort`: `received_at_desc` or `received_at_asc`

This endpoint must query only PostgreSQL. It must not request Gmail or IMAP.

`GET /api/emails/{email_id}`

Returns metadata, snippet, labels, source mailbox fields, read state, attachment flag, body cache status, and cached body fields. v0.6.0 may return `body_text=null` and `body_html=null` until the user caches that email body.

`POST /api/emails/{email_id}/body-cache`

Fetches the full body for one owned email from the connected Gmail or IMAP mailbox and stores it in PostgreSQL.

Response:

```json
{
  "email": {
    "id": "email-id",
    "body_text": "Cached body text",
    "body_html": null,
    "body_cache_status": "cached",
    "body_cached_at": "2026-07-02T00:00:00Z",
    "body_cache_source": "opened",
    "body_cache_error": null
  }
}
```

If the provider request fails, the endpoint returns the email detail payload with `body_cache_status=failed` and `body_cache_error` set to a safe error code. It does not call providers when a body is already cached.

## Mailbox Archive

`POST /api/mailboxes/{mailbox_id}/archive-jobs`

Creates a full-history archive job:

```json
{
  "job": {
    "job_type": "email_archive_backfill",
    "status": "queued"
  },
  "archive_state": {
    "status": "running"
  }
}
```

The endpoint does not create range sync jobs.

`GET /api/mailboxes/{mailbox_id}/archive-state`

Returns mailbox archive progress, including status, synced count, batch count, oldest/newest synced timestamps, and last error fields.
