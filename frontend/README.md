# MailMind Frontend

Next.js (App Router) + TypeScript frontend for MailMind, an AI Email Copilot.

> **Status: static design preview.** Every page is a non-functional UI design
> preview. Nothing is connected — no backend, no Gmail, no AI. There are no real
> network calls, no authentication, no Gmail OAuth, no Daily Digest generation,
> and no mock "success" data. The API client (`src/lib/api-client.ts`) is a safe
> placeholder whose methods throw `Not implemented`.

## Scripts

```bash
npm run dev        # local dev server
npm run build      # production build
npm run typecheck  # tsc --noEmit
npm run lint       # eslint .
```

## Structure

```text
src/
  app/                 App Router pages (design previews)
    page.tsx           Dashboard-first landing (Daily Digest preview)
    dashboard/         Daily Digest decision board preview
    login/ register/   Static auth visual skeletons (no submit)
    emails/            Auxiliary email list + new-emails + detail previews
    settings/          profile / mailboxes / security previews
  components/
    app-shell.tsx      Sidebar + nav + not-connected status block
    status-banner.tsx  Global "design preview / not connected" banner
    page-frame.tsx     Page header with Design Preview badge
    dashboard-preview.tsx
    preview-card.tsx  action-chip.tsx  empty-state.tsx  settings-section.tsx
    ui/                Lightweight presentational primitives
                       (badge, card, button, field, skeleton)
  lib/
    api-routes.ts      Route constants derived from docs/api/API_DESIGN.md
    api-types.ts       { data, meta } / error envelope types
    api-client.ts      Safe placeholder — methods throw Not implemented
  styles/
    globals.css        Plain-CSS design tokens + presentational classes
```

## Design notes

- **Dashboard-first.** `/` and `/dashboard` lead with the Daily Digest decision
  board, not a traditional inbox. `/emails` is an auxiliary view.
- **No real data.** Content regions use neutral skeleton bars and generic
  placeholder copy — never real or mock senders, subjects, or AI output.
- **Plain CSS only.** No Tailwind/shadcn or extra UI dependencies were added.
  `globals.css` defines tokens and reusable classes; structure stays
  Tailwind-ready for a future, intentional migration.

## Theme system

The UI is themeable on two orthogonal axes, both set as data attributes on
`<html>` and read entirely through CSS variables:

- **preset** (`data-theme-preset`) — shape / density / elevation:
  `capsule` (default), `clean`, `minimal`, `soft`.
  `capsule` is the card-pill personality: large radii, pill buttons/inputs,
  soft shadows, light borders, generous spacing.
- **mode** (`data-theme-mode`) — `light` (primary target) or `dark`
  (deep slate, intentionally not pure black so surfaces keep layering).

Implementation:

- `src/lib/theme.ts` — types, preset/mode metadata, validation, and
  localStorage read/write. Persists ONLY the theme preference
  (`mailmind-theme` = `"preset:mode"`) — never user, session, token, or
  mailbox data, and never cookies.
- `src/components/theme-provider.tsx` — `ThemeProvider` / `useTheme`. Initial
  choice resolves from localStorage → `prefers-color-scheme` (mode only) →
  default `capsule light`.
- `src/app/layout.tsx` — a pre-hydration inline script applies the stored
  attributes before first paint, so there is **no theme flash and no
  hydration mismatch**.
- `src/components/theme-switcher.tsx` + `ui/segmented-control.tsx` — the
  switcher (preset + mode) lives in the sidebar; a compact mode toggle sits on
  the login/register cards.

Color tokens (`--color-*`) vary by mode; shape tokens (`--radius-*`,
`--shadow-*`, `--space-*`, `--border-w`) vary by preset. Legacy `--mm-*`
variables are kept as aliases onto the new tokens, so components did not need
per-file edits.
