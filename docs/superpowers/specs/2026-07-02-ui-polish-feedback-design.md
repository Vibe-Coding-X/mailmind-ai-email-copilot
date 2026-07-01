# MailMind UI Polish and Feedback Design

## Goal

Make MailMind feel like a calm, capable email workspace instead of a flashy prototype. The UI should retain a small amount of brand character while making content, mailbox state, archive state, and errors easier to scan.

## Direction

Use a Swiss workbench foundation with a small Aurora accent:

- Neutral white and light gray surfaces.
- One deliberate blue accent for active state, primary actions, and selected controls.
- Hairline borders and compact spacing for scan-friendly layouts.
- No large glow effects, neon styling, bokeh, decorative gradients, or repeated preview badges.
- A restrained page header accent may use a very soft blue line or tint, but content panels stay quiet.

## Content and Feedback Rules

Normal system health is silent. The interface should not show persistent copy such as "Backend connected" or generic backend availability text on every page.

Feedback appears where the user can act on it:

- Digest generation and refresh feedback stays inside Dashboard digest controls.
- Local archive state stays inside the Emails archive section and each mailbox archive panel.
- Body cache status stays inside the email detail body section.
- Mailbox connection, authorization, sync, and archive errors stay inside the affected mailbox card.
- Page-level errors are only for authentication, missing resources, or backend unavailability.

Copy should name facts and actions. Avoid vague or AI-heavy text such as "decision board", "AI workspace", "preview", "intelligence", "powered by", and generic "loaded from backend" notices. Prefer concrete phrases such as "Today's digest", "Local archive is syncing", "Body not cached", and "Reconnect Gmail".

## Component Changes

### App Shell

- Keep the left navigation, but reduce visual weight.
- Use a cleaner brand block and compact nav sections.
- Remove comments and copy that describe the interface rather than helping the user.
- Make the main content width and spacing consistent across pages.

### Page Frame

- Remove the default "Preview" badge.
- Use a consistent header with title, optional description, and optional right-side actions.
- Keep titles readable but not oversized.

### Status Banner

- Remove default per-page `StatusBanner` from normal pages.
- Keep the component available only for exceptional global notices if needed later.

### Inline Feedback

- Keep `InlineFeedback`, but make it visually quieter and easier to place inside modules.
- Use tone-specific border and background only, without glow.
- Support action placement on the same row for desktop and below text on mobile.

### Empty State

- Remove centered decorative empty panels where they interrupt workflow.
- Make empty states look like ordinary module content with a title, one helpful hint, and optional action.

## Page Scope

### Dashboard

- Remove global backend banner.
- Keep today's digest as the only dashboard concept.
- Place digest errors and job progress next to digest actions.
- Reduce visual decoration around metric and summary cards.

### Emails

- Remove global backend banner.
- Put local archive status near filters and results, not above unrelated content.
- Keep filters compact and aligned: read state, mailbox, range, custom dates, search.
- Show result count and pagination as utility controls, not large narrative copy.
- Keep empty-state copy factual and short.

### Email Detail

- Remove global backend banner.
- Keep action errors near toolbar actions.
- Keep body-cache messages inside the body card.
- Preserve full-body loading behavior added in v0.6.

### Settings / Mailboxes

- Remove global backend banner.
- Keep Gmail and IMAP connection actions clear.
- Put sync/archive errors inside the mailbox card that produced them.
- Keep IMAP form hints close to inputs, and remove nonessential explanatory copy.

## Non-Goals

- No backend changes.
- No new product features.
- No Outlook work.
- No digest logic changes.
- No change to local archive or body-cache semantics.
- No new UI dependency unless the existing app already uses it.

## Acceptance Criteria

- Normal pages do not show a persistent "Backend connected" banner.
- Page headers no longer show a default "Preview" badge.
- No user-facing copy uses "decision board", "AI workspace", "intelligence", or generic backend-loaded messaging.
- Dashboard, Emails, Email Detail, and Mailboxes follow the same spacing and card style.
- Warning/error/info messages appear inside the module they describe.
- Existing v0.6 flows still work: local archive query, mailbox archive job trigger, email detail body cache, digest generation, sync actions.
- `npm run typecheck`, `npm run lint`, and `npm run build` pass.
