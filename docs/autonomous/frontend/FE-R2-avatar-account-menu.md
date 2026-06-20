Task ID: FE-R2-avatar-account-menu
Branch: feat/frontend-v03-avatar-account-menu
Parent branch: fix/frontend-v03-disabled-clickable-states
Goal: Consolidate identity, profile, security, theme, language, and sign out into an avatar account menu.
Design changes:
- Added an avatar-style account trigger in the sidebar footer.
- Moved Profile, Security, Theme, and Sign out into a single account menu.
- Reduced sidebar navigation to core product destinations plus mailbox settings.
- Removed scattered sidebar Signed in / email / Sign out presentation.
- Added a disabled Language menu item as the FE-R5 i18n handoff point.
Files changed:
- frontend/src/components/account-menu.tsx
- frontend/src/components/account-menu.contract.test.tsx
- frontend/src/components/app-shell.tsx
- frontend/src/styles/globals.css
i18n changes:
- Added a Language menu item placeholder; real switching is reserved for FE-R5.
Theme changes:
- ThemeSwitcher is now inside the account menu.
Accessibility changes:
- Account menu trigger uses aria-haspopup, aria-expanded, and aria-controls.
- Menu closes on Escape, outside pointer interaction, and navigation item selection.
- Sign out keeps the existing real logout flow and disabled state.
Tests/checks:
- npm run typecheck
- npm run lint
- npm install
- npm run build
Validation result:
- npm install, typecheck, lint, and build passed.
Known risks:
- Language item is intentionally disabled until FE-R5 wires i18n.
- The menu uses lightweight custom behavior rather than a menu library.
Next suggested task:
- FE-R3 Visual Identity Redesign.
