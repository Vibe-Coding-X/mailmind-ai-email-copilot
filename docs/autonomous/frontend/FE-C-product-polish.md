Task ID: FE-C-product-polish
Branch: style/frontend-v02-product-polish
Parent branch: master
Goal: Improve common frontend polish without introducing new product behavior.
Scope:
- Added a shared InlineFeedback component for inline success/error/info/warning messages.
- Replaced ad hoc action feedback in auth, email, email detail, and mailbox settings surfaces.
- Added mobile layout rules for the app shell, sidebar, nav links, cards, and feedback blocks.
- Kept this branch independent from FE-A, FE-B, FE-D, FE-E, and FE-F.

Files changed:
- frontend/src/components/inline-feedback.tsx
- frontend/src/components/inline-feedback.contract.test.tsx
- frontend/src/components/auth-form.tsx
- frontend/src/components/email-detail-view.tsx
- frontend/src/app/emails/page.tsx
- frontend/src/app/settings/mailboxes/page.tsx
- frontend/src/styles/globals.css
- docs/autonomous/frontend/FE-C-product-polish.md

API contract consumed:
- No new API contract consumed.
- Existing auth/email/mailbox API behavior is unchanged.

New UI:
- Shared inline feedback block with title, message, tone, and optional action slot.
- Mobile-first shell collapse below 760px.
- Sidebar becomes a top section on narrow screens.
- Feedback blocks stack cleanly on narrow screens.

State handling:
- Existing action error/success state is preserved.
- Existing auth, email, and mailbox page state machines are unchanged.
- Feedback rendering is centralized without changing when messages appear.

Error handling:
- Existing backend error messages are preserved.
- No mock success path was added.
- No retry behavior was added.
- Tokens, Google codes, and email body text are not displayed.

Tests/checks:
- npm run typecheck
- npm run lint
- npm install
- npm run build

Validation result:
- FE-C implementation: npm install, typecheck, lint, and build passed.

Known risks:
- Runtime mobile browser screenshots were not automated in this task.
- Other independently developed branches may need minor conflict resolution because common pages/components were touched.

Next suggested tasks:
- READY task pool is complete except branch integration/review.
