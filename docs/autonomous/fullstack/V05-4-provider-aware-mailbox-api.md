# V05-4 Provider-Aware Mailbox API

## Scope

Expose provider-aware mailbox metadata without breaking the v0.4 mailbox
payload consumed by the existing frontend.

## Implemented

- `GET /api/mailboxes` includes `account_email`, `display_name`, and provider
  `capabilities` for each mailbox.
- `GET /api/mailboxes/{mailbox_id}` returns the same provider-aware mailbox
  payload as the list endpoint.
- `GET /api/mailboxes/{mailbox_id}/capabilities` returns a compact capability
  payload for clients that only need action support flags.
- Provider keys are normalized to lowercase in mailbox API responses.
- Capability values are resolved from the provider registry via
  `provider.get_capabilities()`.

## Compatibility Notes

- `email_address`, `provider_account_id`, `sync_cursor`, and timestamp fields
  remain in the payload for v0.4 consumers.
- Active mailboxes continue to return API status `connected`.
- No cross-mailbox digest behavior was added.
