Task ID: FE-R5-i18n-foundation
Branch: feat/frontend-v03-i18n-foundation
Parent branch: style/frontend-v03-theme-system-redesign
Goal: Add English/Chinese UI language switching without changing routes or backend contracts.
Design changes:
- Added language switching to the avatar account menu.
- Kept user data, mailbox data, email subjects, senders, recipients, body text, labels, and backend-provided action values untranslated.
Files changed:
- frontend/package.json
- frontend/package-lock.json
- frontend/src/app/actions/page.tsx
- frontend/src/app/dashboard/page.tsx
- frontend/src/app/emails/page.tsx
- frontend/src/app/emails/[id]/page.tsx
- frontend/src/app/layout.tsx
- frontend/src/app/login/page.tsx
- frontend/src/app/register/page.tsx
- frontend/src/app/settings/mailboxes/page.tsx
- frontend/src/components/account-menu.tsx
- frontend/src/components/app-shell.tsx
- frontend/src/components/auth-form.tsx
- frontend/src/components/auth-status.tsx
- frontend/src/components/digest-dashboard.tsx
- frontend/src/components/email-detail-view.tsx
- frontend/src/components/email-list-item.tsx
- frontend/src/components/email-toolbar.tsx
- frontend/src/components/theme-switcher.tsx
- frontend/src/i18n/i18n.contract.test.ts
- frontend/src/i18n/language.ts
- frontend/src/i18n/locales/en.json
- frontend/src/i18n/locales/zh.json
- frontend/src/i18n/provider.tsx
i18n changes:
- Added i18next and react-i18next.
- Added MailMindI18nProvider with localStorage-backed language preference under mailmind-language.
- Added flat English and Chinese locale files.
- Added a type-level i18n contract test for supported languages, storage key, locale key parity, and hook API.
Theme changes:
- None.
Accessibility changes:
- Language switch uses the existing SegmentedControl button group with aria-pressed semantics.
- The provider updates document.documentElement.lang when language changes.
Tests/checks:
- npm install
- npm run typecheck
- npm run lint
- npm run build
Validation result:
- npm install, typecheck, lint, and build passed for this branch before commit.
Known risks:
- Some lower-priority scaffold/preview surfaces still contain English copy and should be handled in the final consistency pass.
Next suggested task:
- FE-R6 Final UI Consistency Pass.
