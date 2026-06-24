# V05-6 Outlook Preparation

## Scope

Prepare Outlook as a provider key without enabling a fake OAuth flow or UI.

## Implemented

- `OutlookProvider` skeleton registered under `outlook`.
- Provider capabilities expose OAuth and folder support, but keep message
  fetch, read/unread, archive, and label actions disabled until real Microsoft
  Graph OAuth is configured.
- Provider operations fail with controlled `outlook_not_configured` errors.
- Mailbox API can render an existing Outlook mailbox with honest capabilities.
- Contract examples document the disabled skeleton capability shape.

## Boundaries

- No Outlook connect UI was added.
- No Microsoft Graph network calls were added.
- No sending scopes or email sending were added.
- No cross-mailbox digest behavior was added.
