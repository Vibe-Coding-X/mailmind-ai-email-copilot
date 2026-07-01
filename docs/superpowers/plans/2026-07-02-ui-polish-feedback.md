# MailMind UI Polish and Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved A+B visual direction: a calm Swiss-style MailMind workbench with a small blue brand accent, quieter module-local feedback, and less AI-flavored copy.

**Architecture:** Keep the existing Next.js app and component structure. Centralize most visual change in `frontend/src/styles/globals.css` and the shared shell/frame/feedback components, then remove redundant page-level status banners and noisy copy from high-frequency pages.

**Tech Stack:** Next.js 15, React 19, TypeScript, existing CSS variables and `mm-*` utility classes.

## Global Constraints

- Do not change backend sync, archive, digest, or body-cache behavior.
- Do not add new UI dependencies.
- Normal pages should not show persistent "Backend connected" messaging.
- Page headers should not show default "Preview" badges.
- Feedback belongs inside the module it describes.
- Avoid vague or AI-heavy copy: "decision board", "AI workspace", "intelligence", "powered by", "loaded from backend".
- Keep v0.6 flows working: mailbox archive, email archive query, email body cache, digest generation, sync actions.

---

### Task 1: Contract Tests for Copy and Component Defaults

**Files:**
- Modify: `frontend/src/components/page-frame.tsx`
- Modify: `frontend/src/components/page-frame.contract.test.tsx`
- Modify: `frontend/src/i18n/i18n.contract.test.ts`

**Interfaces:**
- Consumes: existing `PageFrame` props.
- Produces: `PageFrame` defaults to no badge unless `badgeLabel` is provided.

- [ ] **Step 1: Add failing PageFrame contract test**

Create `frontend/src/components/page-frame.contract.test.tsx` with type assertions that `badge` is removed and optional `badgeLabel?: string` exists:

```ts
import type { ComponentProps } from "react";
import { PageFrame } from "./page-frame";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;
type Assert<T extends true> = T;

type PageFrameProps = ComponentProps<typeof PageFrame>;
type BadgeLabelContract = Assert<
  Equal<PageFrameProps["badgeLabel"], string | undefined>
>;

const assertions: [BadgeLabelContract] = [true];
void assertions;
```

- [ ] **Step 2: Verify RED**

Run: `npm run typecheck`

Expected: FAIL because `badgeLabel` does not exist.

- [ ] **Step 3: Update PageFrame**

Change `PageFrame` props to `badgeLabel?: string`, remove the default `Preview` badge, and render a badge only when `badgeLabel` is provided.

- [ ] **Step 4: Verify GREEN**

Run: `npm run typecheck`

Expected: PASS.

### Task 2: Global Visual System

**Files:**
- Modify: `frontend/src/styles/globals.css`
- Modify: `frontend/src/components/app-shell.tsx`
- Modify: `frontend/src/components/inline-feedback.tsx`
- Modify: `frontend/src/components/empty-state.tsx`

**Interfaces:**
- Consumes: existing `mm-*` class names.
- Produces: calmer neutral surfaces, 1px borders, smaller card shadows, consistent module feedback.

- [ ] **Step 1: Add style-focused contract**

Add a small TypeScript contract by keeping component props unchanged for `InlineFeedback` and `EmptyState`; run existing contract tests first.

Run: `npm run typecheck`

Expected: PASS before CSS changes.

- [ ] **Step 2: Update CSS tokens and common classes**

In `globals.css`, make the default theme neutral and quiet:

- `--color-bg: #f7f7f8`
- `--color-surface: #ffffff`
- `--color-primary: #2563eb`
- card radius at or below 8px
- remove glow from `.mm-card`, `.mm-btn`, `.mm-feedback`, and `.mm-banner`
- compact `.mm-main`, `.mm-card`, `.mm-row`, `.mm-grid`

- [ ] **Step 3: Update shell/feedback/empty components**

Remove decorative comments and make component markup support quieter CSS. Do not change public prop names except the PageFrame change from Task 1.

- [ ] **Step 4: Verify**

Run: `npm run typecheck && npm run lint`

Expected: both PASS.

### Task 3: Remove Noisy Global Banners and Copy

**Files:**
- Modify: `frontend/src/app/dashboard/page.tsx`
- Modify: `frontend/src/app/emails/page.tsx`
- Modify: `frontend/src/app/emails/[id]/page.tsx`
- Modify: `frontend/src/app/actions/page.tsx`
- Modify: `frontend/src/app/settings/mailboxes/page.tsx`
- Modify: `frontend/src/app/settings/profile/page.tsx`
- Modify: `frontend/src/app/settings/security/page.tsx`
- Modify: `frontend/src/i18n/locales/en.json`
- Modify: `frontend/src/i18n/locales/zh.json`

**Interfaces:**
- Consumes: existing page components.
- Produces: no normal-state `StatusBanner` on core pages and quieter page descriptions.

- [ ] **Step 1: Search noisy copy**

Run:

```powershell
rg -n "Backend connected|loaded from the local backend|Preview|decision board|AI workspace|intelligence|powered by" frontend/src
```

Expected: current matches exist.

- [ ] **Step 2: Remove normal `StatusBanner` usage**

Delete `StatusBanner` imports and JSX from the listed pages. Keep the component file for future exceptional notices.

- [ ] **Step 3: Rewrite copy**

Replace vague descriptions with factual ones:

- Dashboard: today's digest only.
- Emails: browse local archive.
- Mailboxes: connect accounts and run sync/archive actions.
- Actions: review completed actions.

- [ ] **Step 4: Verify copy scan**

Run:

```powershell
rg -n "Backend connected|loaded from the local backend|Preview|decision board|AI workspace|intelligence|powered by" frontend/src
```

Expected: no matches in user-facing page/component/locales files except comments in API docs if any.

### Task 4: Module-Local Feedback Placement

**Files:**
- Modify: `frontend/src/app/emails/page.tsx`
- Modify: `frontend/src/components/email-detail-view.tsx`
- Modify: `frontend/src/app/settings/mailboxes/page.tsx`
- Modify: `frontend/src/components/mailbox-sync-card.tsx`
- Modify: `frontend/src/components/jobs/job-error-panel.tsx`

**Interfaces:**
- Consumes: existing state variables and error strings.
- Produces: feedback shown near archive filters, body card, mailbox card, and job card.

- [ ] **Step 1: Emails archive state**

Keep archive status near email filters/results. Reduce paragraph-style explanatory text and use one compact `InlineFeedback` only when status is `not_started`, `running`, `partial`, or `failed`.

- [ ] **Step 2: Email detail body cache**

Keep body-cache hint and error inside the body card only. Action errors from mark-read stay under the toolbar.

- [ ] **Step 3: Mailbox cards**

Ensure mailbox sync/archive errors display inside the relevant card. Remove duplicated generic page-level `InlineFeedback` where the same error exists on a card.

- [ ] **Step 4: Verify**

Run: `npm run typecheck && npm run lint`

Expected: both PASS.

### Task 5: Final Verification and Push

**Files:**
- All touched frontend and docs files.

**Interfaces:**
- Produces: pushed branch with UI polish.

- [ ] **Step 1: Frontend verification**

Run:

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
```

Expected: all PASS.

- [ ] **Step 2: Backend regression**

Run:

```powershell
cd backend
uv run pytest
```

Expected: PASS.

- [ ] **Step 3: Secret scan**

Run:

```powershell
rg -n --hidden -g '!**/.git/**' -g '!**/.venv/**' -g '!**/node_modules/**' -g '!**/.next/**' '<test-imap-secret>|<test-email>' .
```

Expected: no matches.

- [ ] **Step 4: Commit and push**

Run:

```powershell
git status --short
git add docs/superpowers frontend
git commit -m "style: polish ui feedback experience"
git push origin feat/v060-local-mail-archive
```

Expected: push succeeds.

## Self-Review

- Spec coverage: visual direction, feedback placement, copy reduction, core pages, and no backend behavior changes are covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `PageFrame.badgeLabel` is introduced once and used consistently.
