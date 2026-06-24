# V05-2 Provider Architecture

## Scope

This phase defines the provider-aware mailbox foundation before implementation.

## Decisions

- `external_id = provider_message_id`.
- Gmail external id is Gmail `message.id`.
- Outlook external id is Microsoft Graph message `id`.
- IMAP external id is generated from `folder + uidvalidity + uid`.
- Provider capabilities are explicit booleans returned by mailbox APIs.
- Unsupported actions must be disabled or rejected with controlled errors.
- v0.5 does not implement cross-mailbox Digest or Multi Mailbox Digest.

## Implementation Follow-Up

- Add `MailboxProvider` and `ProviderCapabilities` in backend providers.
- Register Gmail first, then IMAP MVP.
- Add Outlook skeleton and mocked tests when local Outlook OAuth config is absent.
- Update frontend mailbox types and controls to use capabilities.
