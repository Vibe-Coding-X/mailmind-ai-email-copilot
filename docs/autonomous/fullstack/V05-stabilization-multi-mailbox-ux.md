# V05 Stabilization: Multi-Mailbox UX

## Scope

This stabilization pass fixes the v0.5 product model around Provider Catalog
and Mailbox Instances.

- Provider Catalog entries are Gmail, IMAP, and Outlook.
- Mailbox Instances are user-connected accounts returned by `GET /api/mailboxes`.
- Add Gmail and Add IMAP create or refresh mailbox instances; they are not
  provider-level singleton toggles.
- Credentials, emails, and sync jobs bind to `mailbox_id`.
- Outlook remains skeleton-only and unavailable in the UI.

## Backend

- Gmail supports multiple mailbox instances through Google account `sub`.
- IMAP supports multiple mailbox instances through `host + port + username`.
- Duplicate Gmail/IMAP connects update the matching mailbox instance.
- IMAP payloads return non-secret `provider_config`, `provider_preset`, and
  `credential_status`.
- IMAP passwords are encrypted in `mailbox_credentials` and are not returned.
- Sync job duplicate detection is scoped to one mailbox instance.
- Stale queued/running sync job recovery remains in place.
- `GET /api/emails?mailbox_id=<uuid>` filters emails by mailbox.

## Frontend

- `/settings/mailboxes` has Connected Mailboxes and Add mailbox sections.
- Connected cards are rendered from backend mailbox instances only.
- Add Gmail and Add IMAP remain visible after existing accounts are connected.
- IMAP cards show persisted host, port, SSL, and credential saved/missing state.
- Outlook shows unavailable and has no clickable fake connect flow.
- `/emails` defaults to a concrete mailbox and keeps All Mailboxes as an
  explicit optional view with source labels.

## Out of Scope

- Real Outlook OAuth.
- Cross-mailbox Digest or Multi Mailbox Digest.
- AI Settings UI.
- Email sending or auto-reply.
- Celery Beat or production scheduling.
