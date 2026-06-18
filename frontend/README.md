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
