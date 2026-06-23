# V05-5 IMAP Provider MVP

## Scope

Add a password-based IMAP mailbox foundation that can connect, store encrypted
credentials, expose provider capabilities, and participate in existing
mailbox-local manual sync.

## Implemented

- `ImapProvider` with:
  - capabilities for password auth, folders, body fetch, and read state flags;
  - RFC822 message parsing through Python stdlib email parsing;
  - external IDs encoded as `folder:uidvalidity:uid`;
  - controlled errors for authentication, TLS, timeout, folder, search, and
    fetch failures.
- Provider registry lookup for `imap`.
- `POST /api/auth/imap/connect`:
  - validates the IMAP connection before storing mailbox state;
  - creates or updates the current user's IMAP mailbox;
  - stores only encrypted IMAP password and non-secret connection config;
  - returns the provider-aware mailbox payload.
- Existing sync flow can sync IMAP mailboxes by decrypting
  `imap_password_encrypted` and applying `credentials_json` to the provider.
- `/settings/mailboxes` has a minimal real IMAP connect form wired to the new
  backend endpoint.

## Boundaries

- No plaintext IMAP password is stored or returned.
- No Gmail scopes are required for IMAP.
- No email sending was added.
- No cross-mailbox digest or multi-mailbox digest behavior was added.
- No Celery Beat or production scheduling was added.
