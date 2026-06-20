Task ID: FE-R1-disabled-clickable-states
Branch: fix/frontend-v03-disabled-clickable-states
Parent branch: master
Goal: Make clickable and disabled states visually and semantically distinct.
Design changes:
- Converted the shared Button component from a static preview-only control into a real reusable button.
- Added disabledReason support for unavailable actions.
- Added a ghost button variant for future low-emphasis actions.
- Strengthened global disabled button styling and removed hover effects from disabled controls.
- Made non-interactive chips visually non-clickable with cursor and selection behavior.
- Added inline reasons for disabled Profile and Security actions.
Files changed:
- frontend/src/components/ui/button.tsx
- frontend/src/components/ui/button.contract.test.tsx
- frontend/src/app/settings/profile/page.tsx
- frontend/src/app/settings/security/page.tsx
- frontend/src/styles/globals.css
i18n changes:
- None.
Theme changes:
- Button disabled/ghost styles apply across the existing theme tokens.
Accessibility changes:
- Disabled buttons now expose aria-disabled and an accessible disabled reason when provided.
- Disabled preview actions now include visible inline reason text.
- Screen-reader-only helper class added for button descriptions.
Tests/checks:
- npm install
- npm run typecheck
- npm run lint
- npm run build
Validation result:
- npm install, typecheck, lint, and build passed.
Known risks:
- Native browser tooltip behavior on disabled buttons varies, so visible inline reason text is used for unavailable actions.
Next suggested task:
- FE-R2 Identity Avatar Menu Refactor.
