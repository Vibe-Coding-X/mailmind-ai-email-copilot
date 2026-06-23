# v0.5 Provider Mailbox Contract

This contract defines provider-aware mailbox behavior for
`v0.5.0-provider-mailbox-foundation`.

## Provider Keys

Supported provider keys:

- `gmail`
- `imap`
- `outlook`

Backends may reject unsupported provider keys with
`unsupported_mailbox_provider`.

## External ID

`external_id = provider_message_id`.

Provider-specific source:

- Gmail: Gmail `message.id`.
- Outlook: Microsoft Graph message `id`.
- IMAP: `folder + uidvalidity + uid` encoded as a stable string.

The uniqueness rule is `(mailbox_id, external_id)`.

## Capabilities

Mailbox API payloads include:

```json
{
  "capabilities": {
    "can_mark_read": true,
    "can_mark_unread": true,
    "can_fetch_body": true,
    "can_fetch_thread": true,
    "can_archive": false,
    "can_label": false,
    "supports_oauth": true,
    "supports_password_auth": false,
    "supports_folders": false
  }
}
```

Capability fields are booleans. Missing fields are contract violations.

## Mailbox Payload

Mailbox list and detail payloads include at least:

- `id`
- `provider`
- `account_email`
- `display_name`
- `email_address`
- `status`
- `last_successful_sync_at`
- `capabilities`

`email_address` remains for v0.4 compatibility. `account_email` is the provider
account email shown by v0.5 UI.

## Actions

Read/unread actions must check capabilities:

- `can_mark_read=false`: mark-read is disabled or returns a controlled error.
- `can_mark_unread=false`: mark-unread is disabled or returns a controlled
  error.

The frontend must not show fake enabled controls for unsupported actions.

## IMAP MVP

IMAP MVP may support:

- Host, port, username, password/app password, and SSL configuration.
- Encrypted credential storage through existing credential encryption.
- Message listing over a window.
- Body fetch.
- `POST /api/auth/imap/connect` to create or update an IMAP mailbox.
- Manual mailbox-local sync via existing mailbox sync endpoints.

IMAP errors:

- `MAILBOX_REAUTH_REQUIRED`
- `imap_connection_failed`
- `network_tls`
- `network_timeout`
- `imap_folder_unavailable`
- `imap_search_failed`
- `imap_fetch_failed`

IMAP MVP must not store plaintext passwords, require Gmail scopes, share sync
cursors across mailboxes, send email, or enable production scheduling.

## Outlook Preparation

Outlook preparation includes skeleton, contract, and mock tests unless local
`OUTLOOK_*` OAuth configuration is complete.

If implemented, Outlook uses Microsoft Graph with minimal scopes:

- `offline_access`
- `User.Read`
- `Mail.ReadWrite`

Sending scopes are not allowed.

Outlook errors:

- `outlook_oauth_failed`
- `outlook_token_refresh_failed`
- `outlook_graph_error`
- `outlook_rate_limited`
- `outlook_permission_denied`
- `outlook_network_error`

## Digest Boundary

v0.5 does not implement cross-mailbox Digest or Multi Mailbox Digest. Digest
services continue to operate on the current active Gmail mailbox unless a later
version explicitly changes that contract.
