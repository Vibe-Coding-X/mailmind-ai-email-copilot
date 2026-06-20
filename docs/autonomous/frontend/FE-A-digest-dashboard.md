Task ID: FE-A-digest-dashboard
Branch: feat/frontend-v02-digest-dashboard
Parent branch: master
Goal: Show today's Daily Digest on the dashboard using the existing backend digest API.
Scope:
- Added typed frontend digest API client methods for today's digest, generate, refresh, and digest detail.
- Replaced the dashboard static digest preview with a live dashboard client component.
- Added generate and refresh actions that call the backend and never fabricate success.
- Kept the existing theme system and responsive card/grid primitives.

Files changed:
- frontend/src/app/dashboard/page.tsx
- frontend/src/components/digest-dashboard.tsx
- frontend/src/components/status-banner.tsx
- frontend/src/lib/api-client.contract.test.ts
- frontend/src/lib/api-client.ts
- frontend/src/lib/api-routes.ts
- frontend/src/lib/api-types.ts
- docs/autonomous/frontend/FE-A-digest-dashboard.md

API contract consumed:
- GET /api/digest/today
- POST /api/digest/today/generate
- POST /api/digest/today/refresh
- GET /api/digest/{digest_id}
- Backend response envelope { data: { digest }, meta }
- Backend error envelope { error: { code, message, retryable, details } }
- Digest payload shape from backend/app/schemas/digest.py

New UI:
- Dashboard status card with digest state, version, generated time, Generate Digest, and Refresh Digest.
- Metrics for mail_count, new_mail_count_after_digest, and digest coverage.
- Summary card that preserves long summaries without breaking layout.
- Sectioned digest item list with priority, category, suggested_action, confidence, and reason.

State handling:
- loading: skeleton metric cards and summary skeleton.
- loaded: real digest summary and items from backend.
- empty: DIGEST_NOT_READY, NOT_FOUND, or 404 shows a Generate Digest action.
- unauthorized: system login 401 shows a sign-in path.
- backend_unavailable: network/CORS/backend failure shows retry.
- error: backend error message is shown without masking it as success.

Error handling:
- No mock success path was added.
- Generate and Refresh keep item/page state stable on non-auth action errors and show inline error text.
- Auth/backend unavailable errors move the page into the corresponding state.
- Backend error messages are shown; tokens, Google codes, and email body text are not displayed.

Tests/checks:
- npm install
- npm run typecheck
- npm run lint
- npm run build

Validation result:
- Baseline before edits: typecheck, lint, and build passed.
- FE-A implementation: npm install, typecheck, lint, and build passed.

Known risks:
- Runtime browser smoke was not automated in this task; manual dashboard checks should use a local backend session.
- Digest item action buttons are intentionally not included; they belong to FE-B.
- The sidebar still has older static product status copy outside the FE-A surface.

Next suggested tasks:
- FE-B Digest Item Actions UI.
- FE-D Actions History Page.
