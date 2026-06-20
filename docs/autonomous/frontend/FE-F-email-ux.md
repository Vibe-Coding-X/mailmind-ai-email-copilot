Task ID: FE-F-email-ux
Branch: feat/frontend-v02-email-ux
Parent branch: master
Goal: Improve email list and detail ergonomics without changing backend email APIs.
Scope:
- Added local email search over subject, sender, snippet, recipients, and labels.
- Preserved read filter and search query in the /emails URL.
- Preserved list state when opening an email detail and returning to the list.
- Improved long subject, sender, and snippet wrapping in the email list.
- Improved email detail metadata and body fallback.

Files changed:
- frontend/src/app/emails/page.tsx
- frontend/src/app/emails/[id]/page.tsx
- frontend/src/components/email-detail-view.tsx
- frontend/src/components/email-list.tsx
- frontend/src/components/email-list-item.tsx
- frontend/src/components/email-toolbar.tsx
- frontend/src/lib/emails.contract.test.ts
- frontend/src/lib/emails.ts
- docs/autonomous/frontend/FE-F-email-ux.md

API contract consumed:
- GET /api/emails/today
- GET /api/emails/{email_id}
- POST /api/emails/{email_id}/mark-read
- POST /api/emails/{email_id}/mark-unread
- Existing EmailSummary and EmailDetail DTOs from frontend/src/lib/api-types.ts

New UI:
- Search input on /emails.
- URL state for /emails?filter=<read-state>&q=<query>.
- Detail page back link that preserves the list state.
- Email detail labels metadata.
- Body fallback that can use snippet when stored body text is empty.

State handling:
- Read filter and search query combine locally after today's emails load.
- URL state is parsed after mount and replaced as filter/search changes.
- Empty state differentiates no email from no matching search/filter result.
- Detail page keeps the original list state in its Back to emails link.

Error handling:
- No mock success path was added.
- Existing backend error handling is preserved.
- Search never calls a new backend endpoint.
- Tokens, Google codes, and full hidden/internal IDs are not displayed.

Tests/checks:
- npm run typecheck
- npm run lint
- npm install
- npm run build

Validation result:
- FE-F implementation: npm install, typecheck, lint, and build passed.

Known risks:
- Search is client-side over the emails currently returned by /api/emails/today.
- Runtime browser smoke was not automated in this task.

Next suggested tasks:
- FE-C Product Polish.
