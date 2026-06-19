Task ID: FE-D-actions-history
Branch: feat/frontend-v02-actions-history
Parent branch: master
Goal: Add an Actions History page for recorded MailMind user actions.
Scope:
- Added typed frontend API client methods for listing actions and reading action detail.
- Added /actions page with action history list and detail panel.
- Added client-side filters for action_type and action_status.
- Added Actions to the primary app navigation.
- Kept action retry out of scope.

Files changed:
- frontend/src/app/actions/page.tsx
- frontend/src/components/app-shell.tsx
- frontend/src/components/status-banner.tsx
- frontend/src/lib/api-client.contract.test.ts
- frontend/src/lib/api-client.ts
- frontend/src/lib/api-routes.ts
- frontend/src/lib/api-types.ts
- docs/autonomous/frontend/FE-D-actions-history.md

API contract consumed:
- GET /api/actions
- GET /api/actions/{action_id}
- Backend response envelope { data: { actions }, meta }
- Backend response envelope { data: { action }, meta }
- User action payload from backend/app/schemas/user_action.py

New UI:
- /actions route.
- Action history list.
- Action detail panel.
- Action type filter.
- Action status filter.
- Status and provider effect badges.

State handling:
- loading: skeleton list and detail panel.
- loaded: action list and selectable detail panel.
- empty: no recorded actions or no matching filtered actions.
- unauthorized: sign-in prompt.
- backend_unavailable: retry prompt.
- error: backend error prompt.
- detail loading/error states are separate from list loading.

Error handling:
- No mock success path was added.
- Backend error messages are shown.
- The UI does not expose email/message IDs, digest IDs, or mailbox IDs.
- The UI does not offer action retry.

Tests/checks:
- npm run typecheck
- npm run lint
- npm install
- npm run build

Validation result:
- FE-D implementation: npm install, typecheck, lint, and build passed.

Known risks:
- Filtering is client-side only; large action histories may need backend pagination later.
- Runtime browser smoke was not automated in this task.

Next suggested tasks:
- FE-C Product Polish.
- FE-E Mailbox Settings Polish.
