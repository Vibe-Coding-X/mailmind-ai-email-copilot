Task ID: FE-R6-ui-consistency-pass
Branch: style/frontend-v03-ui-consistency-pass
Parent branch: feat/frontend-v03-i18n-foundation
Goal: Final consistency pass after visual identity, theme system, account menu, and i18n changes.
Design changes:
- Root route now redirects to the real dashboard instead of rendering an old static preview.
- Removed unused dashboard preview and action-chip scaffold components.
- /emails/new redirects to /emails until a real backend route is intentionally wired.
- Profile and Security pages now follow the same i18n and disabled-state language as the account menu.
- Mailbox sync controls, email empty/loading states, and Actions fallback text use the same language foundation.
Files changed:
- frontend/src/app/page.tsx
- frontend/src/app/emails/new/page.tsx
- frontend/src/app/layout.tsx
- frontend/src/app/actions/page.tsx
- frontend/src/app/settings/profile/page.tsx
- frontend/src/app/settings/security/page.tsx
- frontend/src/components/action-chip.tsx
- frontend/src/components/dashboard-preview.tsx
- frontend/src/components/email-empty-state.tsx
- frontend/src/components/email-loading-state.tsx
- frontend/src/components/mailbox-sync-card.tsx
- frontend/src/i18n/locales/en.json
- frontend/src/i18n/locales/zh.json
- docs/autonomous/frontend/FE-R6-ui-consistency-pass.md
i18n changes:
- Added Profile, Security, mailbox sync, email loading/empty, and Actions fallback translations.
- Kept user/mailbox/email data untranslated.
Theme changes:
- None.
Accessibility changes:
- No new interactive patterns; existing buttons and segmented controls retain semantics.
Tests/checks:
- npm install
- npm run typecheck
- npm run lint
- npm run build
Validation result:
- npm install, typecheck, lint, and build passed for this branch before commit.
Known risks:
- Runtime visual review across all four themes and both languages is still recommended before merging the stacked redesign branches.
Next suggested task:
- Merge/review stacked v0.3 frontend branches in order.
