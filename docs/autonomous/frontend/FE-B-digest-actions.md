Task ID: FE-B-digest-actions
Branch: feat/frontend-v02-digest-actions
Parent branch: feat/frontend-v02-digest-dashboard
Goal: Add real digest item action controls to the digest dashboard.
Scope:
- Added typed frontend API client methods for mark done, dismiss, and snooze digest item actions.
- Added item-level controls to each digest item row.
- Added item-level busy state and feedback for success/failure.
- Refreshes the digest after successful item action recording.
- Kept the implementation stacked on FE-A because the UI builds on the new digest dashboard component.

Files changed:
- frontend/src/components/digest-dashboard.tsx
- frontend/src/lib/api-client.contract.test.ts
- frontend/src/lib/api-client.ts
- frontend/src/lib/api-routes.ts
- frontend/src/lib/api-types.ts
- docs/autonomous/frontend/FE-B-digest-actions.md

API contract consumed:
- POST /api/digest/items/{item_id}/mark-done
- POST /api/digest/items/{item_id}/dismiss
- POST /api/digest/items/{item_id}/snooze
- Snooze request body: { "snoozed_until": string }
- Backend response envelope { data: { action }, meta }
- User action payload from backend/app/schemas/user_action.py

New UI:
- Mark done button per digest item.
- Dismiss button per digest item.
- Snooze select with Tomorrow, In 3 days, and Next week options.
- Snooze button per digest item.
- Inline item feedback badge.

State handling:
- Item-level loading disables all action controls for the active item.
- Page-level digest state remains intact while an item action is recording.
- Successful action records a success badge and reloads the digest.
- Failed action records a danger badge on the item.

Error handling:
- No mock success path was added.
- Backend error messages are shown inline.
- Repeated clicks are blocked while an item action is in progress.
- Tokens, Google codes, and email body text are not displayed.

Tests/checks:
- npm run typecheck
- npm run lint
- npm install
- npm run build

Validation result:
- FE-B implementation: npm install, typecheck, lint, and build passed.

Known risks:
- Backend currently records actions but does not mutate digest item visibility/status, so dismissed/done items may remain visible after refresh.
- Runtime browser smoke was not automated in this task.

Next suggested tasks:
- FE-D Actions History Page.
- FE-C Product Polish for common feedback components and responsive refinements.
