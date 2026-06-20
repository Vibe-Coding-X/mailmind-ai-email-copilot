Task ID: FE-R4-theme-system-redesign
Branch: style/frontend-v03-theme-system-redesign
Parent branch: style/frontend-v03-visual-identity
Goal: Replace the weak preset theme names with four distinct MailMind theme languages.
Design changes:
- Replaced Capsule, Clean, Minimal, and Soft with Amber Focus, Noir Pulse, Paper Calm, and Dense Minimal.
- Amber Focus keeps the warm production default with amber emphasis, serif headings, rounded controls, and balanced spacing.
- Noir Pulse is dark-first with higher contrast surfaces, saturated amber signal color, faster transitions, and stronger active navigation.
- Paper Calm uses paper-toned reading surfaces, lower contrast borders, slower motion, and more generous spacing.
- Dense Minimal uses compact spacing, flat elevation, square controls, and reduced decoration for scanning.
Files changed:
- frontend/src/app/layout.tsx
- frontend/src/lib/theme.ts
- frontend/src/styles/globals.css
- docs/autonomous/frontend/FE-R4-theme-system-redesign.md
i18n changes:
- None.
Theme changes:
- Updated theme preset type, metadata, default theme, localStorage parser values, and pre-hydration theme script.
- Preserved the existing localStorage-only theme preference model.
- Preserved light/dark mode switching and added preset-specific light/dark differences where needed.
Accessibility changes:
- Theme switcher remains a button-based segmented control with aria-pressed semantics.
- Dark-oriented presets use readable text, border, and accent contrast.
Tests/checks:
- npm install
- npm run typecheck
- npm run lint
- npm run build
Validation result:
- npm install, typecheck, lint, and build passed for this branch before commit.
Known risks:
- Existing browsers with old localStorage theme values will fall back to Amber Focus until the user selects a new theme.
Next suggested task:
- FE-R5 i18n Foundation.
