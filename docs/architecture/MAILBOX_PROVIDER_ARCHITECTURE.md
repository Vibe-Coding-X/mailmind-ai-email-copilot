# Mailbox Provider Architecture

MailMind v0.5 moves mailbox integration from Gmail-only service calls to a
provider-aware mailbox architecture. The scope is intentionally foundational:
providers can describe capabilities, normalize message identity, and expose a
shared interface, while digest generation remains single-mailbox.

## Goals

- Keep existing Gmail behavior stable.
- Define a `MailboxProvider` interface for sync, message body fetch, and
  read/unread actions.
- Make mailbox APIs expose provider identity and capabilities.
- Add IMAP as an MVP provider without requiring real IMAP smoke in tests.
- Prepare Outlook through contract, skeleton, and mocked provider tests unless
  local Outlook OAuth configuration is complete.

## Non-Goals

- Cross-mailbox digest aggregation.
- Multi Mailbox Digest.
- AI Provider Settings UI.
- User-level AI key storage.
- Email sending or auto-reply.
- Production scheduler or Celery Beat.

## Provider Identity

`mailboxes.provider` is the normalized provider key. v0.5 provider keys are:

- `gmail`
- `imap`
- `outlook`

The current mailbox schema already stores provider identity. Provider-aware
services must use the provider registry rather than directly instantiating a
provider-specific class.

## Provider Catalog vs Mailbox Instances

Provider keys describe mailbox types. Mailbox rows describe user-connected
instances.

- Provider catalog entries: Gmail, IMAP, Outlook.
- Mailbox instances: `main@gmail.com`, `work@gmail.com`,
  `123@qq.com via imap.qq.com`, and each additional account the user adds.
- Credentials bind to one mailbox instance.
- Emails bind to one mailbox instance.
- Sync jobs bind to one mailbox instance.

The frontend must treat `GET /api/mailboxes` as the source of truth for
connected mailbox instances. Add Gmail and Add IMAP remain available even when
mailboxes of the same provider already exist, because those actions create or
re-authorize mailbox instances rather than toggling one provider-level config.
Outlook remains unavailable in v0.5 UI until a real OAuth flow is implemented.

## External ID Semantics

`external_id = provider_message_id`.

The value must be stable within a mailbox and must be suitable for the existing
unique constraint on `(mailbox_id, external_id)`.

Provider mappings:

- Gmail: Gmail `message.id`.
- Outlook: Microsoft Graph message `id`.
- IMAP: stable string generated from `folder + uidvalidity + uid`.

Do not use subject, sender, received time, snippet, labels, or body content as
identity fields.

## Capabilities

Providers expose capabilities so APIs and UI can avoid fake controls.

```json
{
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
```

Baseline capability expectations:

| Provider | OAuth | Password/App Password | Read/Unread | Body Fetch | Thread Fetch | Folders |
| --- | --- | --- | --- | --- | --- | --- |
| Gmail | Yes | No | Yes | Yes | Yes | No |
| IMAP | No | Yes | Yes when flags are supported | Yes | No | Yes |
| Outlook | Yes | No | Yes | Yes | Yes | Yes |

## MailboxProvider Interface

Provider implementations should expose:

- `provider_key`
- `get_capabilities()`
- `refresh_access_token()` when OAuth is supported
- `sync_window()` or equivalent message listing over a time window
- `get_message_detail()`
- `mark_as_read()`
- `mark_as_unread()`

Provider methods must raise classified provider errors with safe messages.
Access tokens, refresh tokens, API keys, authorization headers, passwords, and
message bodies must not be included in error messages.

## Provider Registry

The registry maps `mailboxes.provider` to a provider implementation. `gmail` is
the first formal implementation. `imap` is registered once its MVP provider is
available. `outlook` is registered only when its provider implementation is real
enough for backend use; otherwise it remains a skeleton/contract.

Unsupported providers must return controlled errors such as
`unsupported_mailbox_provider`.

## Provider-Aware Actions

Read/unread actions must check provider capabilities before calling a provider.
If a provider cannot perform an action, the backend returns a controlled error
and the frontend displays a disabled reason instead of showing a fake action.

## Emails View

The v0.5 UI is mailbox-based. `/emails` defaults to a concrete mailbox when no
query parameter is present, using the most recently synced/updated mailbox. All
Inboxes can exist as an explicit optional view, but mixed lists must show the
source mailbox for each email.

## Future Route

v0.5 creates the provider and mailbox foundation needed for later provider
expansion. Cross-mailbox digest aggregation remains a separate future design.
