# V05 Digest Scope Stabilization

This task fixes the Digest mailbox selector and locks the digest product surface to two scopes:

- `scope_type=all`
- `scope_type=mailbox`

## Scope Summary

- The Digest scope selector always starts with `All Mailboxes`.
- Selector options come from `GET /api/mailboxes`, not job state.
- Connected Gmail and IMAP mailbox instances are all eligible digest sources.
- `scope_type=all` generates one digest over the user's currently connected mailboxes.
- `scope_type=mailbox` generates one digest for exactly one mailbox instance.

## Backend Notes

- `daily_digests.scope_type` now records `all` or `mailbox`.
- `daily_digests.mailbox_id` is nullable and only required for `scope_type=mailbox`.
- Digest jobs persist scope in `payload_json` so worker retries and stale-task recovery stay scope-aware.
- Digest candidate email queries now respect:
  - `all`: `emails.mailbox_id IN <connected mailbox ids>`
  - `mailbox`: `emails.mailbox_id = <selected mailbox id>`
- Digest responses now include mailbox source metadata on items and mailbox summaries for all-scope digests.

## Frontend Notes

- The old misleading `No Active mailboxes` path is removed.
- When no mailboxes are connected, the UI now tells the user to add a mailbox.
- When `scope_type=all`, the Digest page shows:
  - `Priority Queue`
  - `By Mailbox`
- When `scope_type=mailbox`, the Digest page shows only that mailbox's digest.

## Celery Notes

- Digest generation still uses the reliable commit-then-dispatch model from the previous stabilization round.
- Worker execution remains safe for orphaned, stale, completed, or already-recovered digest jobs.
- No inline execution mode was added.
