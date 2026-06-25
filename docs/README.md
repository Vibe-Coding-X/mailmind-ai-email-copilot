# MailMind Documentation

MailMind documentation hub.

**Product:** MailMind
**Type:** Multi-mailbox AI Email Copilot
**Repo:** `mailmind-ai-email-copilot`

## Recommended Reading Order

1. [`product/PRD.md`](product/PRD.md) — Product goals, MVP scope, and user flows.
2. [`architecture/SYSTEM_DESIGN.md`](architecture/SYSTEM_DESIGN.md) — System-level goals, overall architecture, core principles.
3. [`architecture/DIAGRAMS.md`](architecture/DIAGRAMS.md) — **Architecture diagrams index** with 6 Mermaid diagrams and rendered SVGs.
4. [`architecture/DATA_FLOWS.md`](architecture/DATA_FLOWS.md) — Registration, Gmail auth, sync, digest generation, and refresh flows.
5. [`database/DATABASE_DESIGN.md`](database/DATABASE_DESIGN.md) — Table structure, fields, enums, constraints, and migration strategy.
6. [`api/API_DESIGN.md`](api/API_DESIGN.md) — API routes, auth preconditions, and interaction rules.
7. [`ai/AI_PIPELINE.md`](ai/AI_PIPELINE.md) — AI pipeline, LLM interface, structured output, and security constraints.
8. [`security/SECURITY.md`](security/SECURITY.md) — OAuth, tokens, logging, keys, and public deployment security.
9. [`frontend/FRONTEND_DESIGN.md`](frontend/FRONTEND_DESIGN.md) — Frontend page structure, dashboard zones, and state principles.
10. [`engineering/DEVELOPMENT.md`](engineering/DEVELOPMENT.md) — Local dev setup, service composition, directory structure, and Docker Compose.
11. [`demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md) — **5–8 minute demo walkthrough** for technical presentations.
12. [`portfolio/PROJECT_WALKTHROUGH.md`](portfolio/PROJECT_WALKTHROUGH.md) — **Portfolio/interview walkthrough** covering architecture decisions and trade-offs.

## Topic-Based Docs

| Topic | Document |
|-------|----------|
| Architecture Diagrams | [`architecture/DIAGRAMS.md`](architecture/DIAGRAMS.md) |
| Frontend Design | [`frontend/FRONTEND_DESIGN.md`](frontend/FRONTEND_DESIGN.md) |
| Core Data Flows | [`architecture/DATA_FLOWS.md`](architecture/DATA_FLOWS.md) |
| Async Tasks | [`engineering/ASYNC_TASKS.md`](engineering/ASYNC_TASKS.md) |
| Job Execution Model | [`architecture/JOB_EXECUTION_MODEL.md`](architecture/JOB_EXECUTION_MODEL.md) |
| Mailbox Provider Architecture | [`architecture/MAILBOX_PROVIDER_ARCHITECTURE.md`](architecture/MAILBOX_PROVIDER_ARCHITECTURE.md) |
| Incremental Sync | [`engineering/INCREMENTAL_SYNC.md`](engineering/INCREMENTAL_SYNC.md) |
| Timezone Rules | [`engineering/TIMEZONE_RULES.md`](engineering/TIMEZONE_RULES.md) |
| Task Breakdown | [`engineering/TASK_BREAKDOWN.md`](engineering/TASK_BREAKDOWN.md) |
| Agent Collaboration | [`engineering/AGENTS.md`](engineering/AGENTS.md) |
| Architecture Decision Log | [`engineering/DECISION_LOG.md`](engineering/DECISION_LOG.md) |
| Docs Freeze Checklist | [`engineering/DOCS_FREEZE_CHECKLIST.md`](engineering/DOCS_FREEZE_CHECKLIST.md) |
| Review Checklist | [`engineering/REVIEW_CHECKLIST.md`](engineering/REVIEW_CHECKLIST.md) |

## Mermaid Source Files

All architecture diagrams are available as `.mmd` source files in [`architecture/mermaid/`](architecture/mermaid/):

| # | File | Type | Description |
|---|------|------|-------------|
| 01 | [`01-system-context.mmd`](architecture/mermaid/01-system-context.mmd) | Graph | System context — Frontend, Backend, Workers, Data Stores, External APIs |
| 02 | [`02-provider-mailbox-architecture.mmd`](architecture/mermaid/02-provider-mailbox-architecture.mmd) | ER | Provider → Mailbox → Credential → Email relationships |
| 03 | [`03-celery-job-dispatch-sequence.mmd`](architecture/mermaid/03-celery-job-dispatch-sequence.mmd) | Sequence | Commit-then-dispatch job lifecycle |
| 04 | [`04-digest-scope-flow.mmd`](architecture/mermaid/04-digest-scope-flow.mmd) | Flowchart | All Mailboxes vs Single Mailbox digest scope |
| 05 | [`05-data-model-erd.mmd`](architecture/mermaid/05-data-model-erd.mmd) | ER | Full PostgreSQL data model with all core tables |
| 06 | [`06-frontend-architecture.mmd`](architecture/mermaid/06-frontend-architecture.mmd) | Graph | Next.js App Router pages, providers, components, hooks |

## Demo & Portfolio

| Document | Audience | Duration |
|----------|----------|----------|
| [`demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md) | Technical presentations, live demos | 5–8 min |
| [`portfolio/PROJECT_WALKTHROUGH.md`](portfolio/PROJECT_WALKTHROUGH.md) | Interviews, portfolio reviews | Self-paced |

## UI Documentation

| Document | Description |
|----------|-------------|
| [`ui/V051_UI_AUDIT.md`](ui/V051_UI_AUDIT.md) | Comprehensive UI audit report |
| [`ui/V051_UI_POLISH_SUMMARY.md`](ui/V051_UI_POLISH_SUMMARY.md) | UI polish implementation summary |
| [`ui/V051_THEME_MODE_FIX_REPORT.md`](ui/V051_THEME_MODE_FIX_REPORT.md) | Theme light/dark mode fix report |
| [`ui/screenshots/v051/`](ui/screenshots/v051/) | Playwright-verified screenshots (baseline, final, theme verification) |

## Release Notes

| Version | Document |
|---------|----------|
| v0.1.0 | [`release-notes/v0.1.0-local-mvp.md`](release-notes/v0.1.0-local-mvp.md) |
| v0.2.0 | [`release-notes/v0.2.0-digest-ai.md`](release-notes/v0.2.0-digest-ai.md) |
| v0.3.0 | [`release-notes/v0.3.0-async-redesign.md`](release-notes/v0.3.0-async-redesign.md) |
| v0.4.0 | [`release-notes/v0.4.0-job-experience.md`](release-notes/v0.4.0-job-experience.md) |
| v0.4.1 | [`release-notes/v0.4.1-config-sync-containment.md`](release-notes/v0.4.1-config-sync-containment.md) |
| v0.5.0 | [`release-notes/v0.5.0-provider-mailbox-foundation.md`](release-notes/v0.5.0-provider-mailbox-foundation.md) |
| v0.5.1 | [`release-notes/v0.5.1-ui-ux-polish.md`](release-notes/v0.5.1-ui-ux-polish.md) |
