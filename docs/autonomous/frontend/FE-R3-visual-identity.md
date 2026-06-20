Task ID: FE-R3-visual-identity
Branch: style/frontend-v03-visual-identity
Parent branch: feat/frontend-v03-avatar-account-menu
Goal: Establish a distinct MailMind visual identity centered on amber, ink, and canvas.
Design changes:
- Replaced the default indigo/gray palette with Amber Primary #F59E0B, Amber Deep #B45309, Ink #111827, Slate #64748B, Canvas #FFF7ED, Surface #FFFFFF, Success #16A34A, and Danger #DC2626.
- Added a serif display stack for headings and brand text while keeping sans-serif body text.
- Increased page title scale and removed negative letter spacing.
- Added lightweight inline SVG navigation anchors without adding dependencies.
- Strengthened current nav state with a color block, left indicator, and icon.
- Distinguished digest summary cards from metric cards with amber surface treatment and a left color rail.
- Reduced scaffold feel in the old soft-light preset by removing purple-tinted leftovers.
Files changed:
- frontend/src/components/app-shell.tsx
- frontend/src/components/digest-dashboard.tsx
- frontend/src/components/page-frame.tsx
- frontend/src/styles/globals.css
- docs/autonomous/frontend/FE-R3-visual-identity.md
i18n changes:
- None.
Theme changes:
- Existing light/dark mode color tokens now use the MailMind amber/ink palette.
- Full multi-theme redesign is reserved for FE-R4.
Accessibility changes:
- Navigation icons are aria-hidden and paired with text labels.
- Current page remains text-visible and receives a stronger visual state.
Tests/checks:
- npm run typecheck
- npm run lint
- npm install
- npm run build
Validation result:
- npm install, typecheck, lint, and build passed for this branch before commit.
Known risks:
- This branch changes shared CSS and will affect all pages; runtime visual review is still recommended.
Next suggested task:
- FE-R4 Theme System Redesign.
