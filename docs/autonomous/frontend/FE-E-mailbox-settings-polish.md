Task ID: FE-E-mailbox-settings-polish
Branch: style/frontend-v02-mailbox-settings-polish
Parent branch: master
Goal: Make Gmail mailbox and sync states clearer without changing backend contracts.
Scope:
- Improved Gmail connected, disconnected, error, and reauth-required state messaging.
- Added relative timestamp display for mailbox updates and last successful sync.
- Added sync status detail text for completed, running, failed, not_started, and unknown states.
- Added a browser confirmation before disconnecting Gmail.
- Kept multi-mailbox support as a visible list only; no aggregation behavior was added.

Files changed:
- frontend/src/app/settings/mailboxes/page.tsx
- frontend/src/components/mailbox-sync-card.tsx
- frontend/src/lib/mailboxes.ts
- docs/autonomous/frontend/FE-E-mailbox-settings-polish.md

API contract consumed:
- GET /api/mailboxes
- GET /api/mailboxes/{mailbox_id}/sync-status
- POST /api/mailboxes/{mailbox_id}/sync
- GET /api/auth/gmail/login
- POST /api/auth/gmail/disconnect
- Existing mailbox and sync DTOs from frontend/src/lib/api-types.ts

New UI:
- Clear mailbox state helper text.
- Last updated and last successful sync timestamps with relative time.
- Sync status detail sentence below the sync summary.
- Disconnect Gmail confirmation dialog.
- Multi-mailbox copy that does not imply mailbox aggregation.

State handling:
- connected: explains Gmail is ready for manual sync.
- reauth_required / reauthorization_required: tells user to reconnect before syncing.
- disconnected: explains mailbox is disconnected.
- error: tells user Gmail connection needs attention.
- sync failed: shows the backend job error message when present.

Error handling:
- No mock success path was added.
- Existing backend error messages are preserved.
- Disconnect action can be cancelled before the backend request is sent.
- Tokens, Google codes, and email body text are not displayed.

Tests/checks:
- npm run typecheck
- npm run lint
- npm install
- npm run build

Validation result:
- FE-E implementation: npm install, typecheck, lint, and build passed.

Known risks:
- Browser confirm is intentionally simple; a custom modal can be added later in FE-C Product Polish.
- Runtime browser smoke was not automated in this task.

Next suggested tasks:
- FE-C Product Polish.
- FE-F Email UX v2.
