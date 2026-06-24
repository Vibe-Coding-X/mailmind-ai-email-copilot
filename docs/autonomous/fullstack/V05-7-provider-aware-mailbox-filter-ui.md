# V05-7 Provider-Aware Mailbox Filter UI

## Scope

Teach the frontend to understand mailbox providers and capabilities without
adding fake Outlook UI or cross-mailbox digest behavior.

## Implemented

- Mailbox DTO includes provider capabilities and account display fields.
- Added `MailboxProviderBadge` for provider display.
- `/settings/mailboxes` shows provider badges and includes a real IMAP connect
  form wired to `POST /api/auth/imap/connect`.
- `/emails` loads mailbox metadata alongside today's emails.
- `/emails` supports a URL-backed mailbox filter using `mailbox=<mailbox_id>`.
- Email read/unread buttons are disabled when the source mailbox capabilities
  do not support the action.
- Unsupported action controls include a disabled reason.
- English and Chinese i18n strings were added.

## Boundaries

- Outlook connect UI remains absent because `OUTLOOK_*` config is absent.
- No Multi Mailbox Digest or cross-mailbox Digest was added.
- No AI Settings UI was added.
