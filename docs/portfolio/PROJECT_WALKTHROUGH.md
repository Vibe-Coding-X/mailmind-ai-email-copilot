# MailMind — Project Walkthrough

**For:** Technical interviews, portfolio presentations, open-source contributors

---

## 1. The Problem

Email is the #1 productivity tax for knowledge workers. The average professional receives 120+ emails per day, spending 28% of their workweek managing them. Existing solutions fall into two camps:

- **Email clients** (Gmail, Outlook) — great at reading and replying, but offer zero intelligence about what matters
- **AI email tools** — most are cloud-based, requiring you to hand over your inbox credentials to a third party

MailMind occupies a different space: a **local-first AI email copilot** that runs on your machine, connects to your email providers, and uses AI to generate a prioritized daily digest — without your emails ever leaving your infrastructure.

---

## 2. Technical Decisions & Trade-offs

### 2.1 Provider / Mailbox Model

**Decision:** Separate `Provider` (the type of email service) from `Mailbox` (a connected instance).

**Why:**
- A user might have 2 Gmail accounts and 1 IMAP account — each is a Mailbox, but they share the same GmailProvider or ImapProvider logic
- Adding a new provider (Outlook, Yahoo) means implementing the `MailboxProvider` protocol — the rest of the system doesn't change
- Credentials are bound to the Mailbox, not the Provider — this allows per-mailbox token refresh and scope management

**Trade-off:** More abstraction upfront, but the payoff is real — the IMAP provider was added without touching any Gmail-specific code.

```
Provider (type)          Mailbox (instance)
├── GmailProvider        ├── user@gmail.com (Gmail, OAuth2)
├── ImapProvider         ├── user@work.com (IMAP, password)
└── OutlookProvider      └── user@outlook.com (Outlook, OAuth2)
    (stub)
```

### 2.2 Commit-then-Dispatch Celery Model

**The problem:** If you dispatch a Celery task and *then* commit the database, there's a race window where the worker picks up the task before the job row exists. The worker can't find the job and fails.

**The solution:** Commit the job to PostgreSQL *first*, then dispatch the Celery task.

```python
# 1. Create job with status=pending_dispatch
db.add(SyncJob(status="pending_dispatch", ...))
db.commit()  # <-- Job is now visible to workers

# 2. Dispatch to Celery
celery_task = run_email_sync_job.delay(job_id)

# 3. Update with celery_task_id
job.status = "queued"
job.celery_task_id = celery_task.id
db.commit()
```

**What this prevents:**
- Lost jobs if the process crashes after DB write but before Celery dispatch (job stays `pending_dispatch`, recoverable)
- Lost jobs if Celery dispatch fails (job marked `dispatch_failed`, retryable)
- Duplicate execution if Celery retries (idempotent job keys + status checks)

### 2.3 Digest Scope Evolution

**v0.1–v0.4:** Digest was Gmail-only, single mailbox.

**v0.5:** Introduced the Provider/Mailbox abstraction. Digest now supports two scopes:

| Scope | Behavior |
|-------|----------|
| `scope_type=mailbox` | Digest for one specific mailbox |
| `scope_type=all` | Digest across ALL active mailboxes for the user |

**The challenge:** When scope is "all", the LLM prompt includes emails from multiple sources. The AI needs to:
1. Understand that emails come from different mailboxes
2. Generate a unified priority queue across all sources
3. Include per-mailbox summaries alongside the global overview

**The solution:** The prompt includes mailbox metadata (id, provider, email address) alongside each email, and the output schema requires `mailbox_id` on every item. The parser resolves mailbox references defensively.

### 2.4 Theme System Architecture

**Decision:** CSS custom properties with `data-theme-preset` and `data-theme-mode` attributes on `<html>`.

**Why not Tailwind/shadcn?**
- Theme presets need 50+ coordinated variables (colors, shadows, radii, glow amounts)
- CSS custom properties cascade naturally — one attribute change rethemes the entire page
- No JavaScript runtime overhead for theme switching
- Supports pre-hydration application (inline `<script>` sets attributes before React loads)

**6 themes, 12 combinations:**
Each theme defines ~50 CSS custom properties for both light and dark modes. Themes range from cyberpunk (Neon Cyber) to neumorphism (Soft Clay) to glassmorphism (Glass Aurora).

**Verification:** All 12 theme/mode combinations were captured with Playwright screenshots to verify visual consistency.

### 2.5 AI Output Reliability

**The problem:** LLMs return unstructured text that may be malformed, have aliased enum values, or miss required fields.

**The solution:** Defensive parsing with graceful degradation:

```python
# 1. Extract JSON from potentially noisy output
json_str = extract_json_from_text(raw_llm_output)

# 2. Normalize enum aliases
"critical" → "high"
"mail" → "email"
"task" → "todo"

# 3. Resolve references
email_id → look up in provider email map
mailbox_id → infer from email if missing

# 4. Validate cross-field constraints
section="todo" requires item_type="todo"
item_type="email" requires email_id IS NOT NULL

# 5. Clamp numeric ranges
confidence = max(0, min(1, confidence))
```

Every LLM invocation is recorded as an `AIRun` with input hash, token counts, latency, and full output — enabling debugging and future caching.

---

## 3. Architecture Patterns Worth Highlighting

| Pattern | Implementation | Benefit |
|---------|---------------|---------|
| **Unified Job Table** | Single `sync_jobs` table for all job types | Consistent monitoring, retry, and status tracking |
| **Commit-then-Dispatch** | DB commit before Celery dispatch | No lost jobs even on crash |
| **Distributed Locking** | Redis `SET NX EX` with Lua release | Prevents concurrent syncs, handles worker crashes |
| **Versioned Digests** | `(version, is_current)` pattern | History preservation, safe regeneration |
| **Idempotent Job Keys** | Partial unique index on active statuses | No duplicate in-flight jobs |
| **Provider Protocol** | Python Protocol with capabilities | Type-safe extensibility |
| **Defensive LLM Parsing** | Alias maps, reference resolution, validation | Handles malformed AI output gracefully |

---

## 4. What I Learned

### Technical
- **Celery reliability is non-trivial.** The commit-then-dispatch pattern emerged from debugging a race condition where workers couldn't find jobs that hadn't been committed yet.
- **LLM output is inherently unreliable.** The parser handles 10+ edge cases that the LLM *will* eventually produce: missing fields, wrong enum values, JSON wrapped in markdown fences, etc.
- **CSS custom properties are powerful for theming.** One attribute change can retheme 1800+ lines of CSS without touching component code.

### Process
- **Documentation drift is real.** The FRONTEND_DESIGN.md referenced TailwindCSS and shadcn/ui even though the implementation uses plain CSS. Keeping docs in sync with code requires discipline.
- **Playwright verification saved time.** Instead of manually checking 12 theme combinations, automated screenshots caught issues immediately.

---

## 5. Current Limitations & Next Steps

### Limitations
| Limitation | Impact | Planned Resolution |
|-----------|--------|-------------------|
| Outlook provider is a stub | Can't connect Outlook accounts | v0.6: Implement Microsoft Graph API |
| IMAP mark_read/unread not implemented | Can't sync read state back to IMAP servers | v0.6: IMAP flag operations |
| No CI/CD pipeline | No automated testing or deployment | v0.6: GitHub Actions |
| No Docker production config | Only dev Docker Compose | v0.6: Multi-stage Dockerfile |
| No AI settings UI | AI provider configured via env vars only | v0.6: User-configurable AI settings |

### Roadmap
- **v0.5.2** — Demo readiness (this release): Architecture diagrams, documentation refresh, demo script
- **v0.6** — Open source ready: CI/CD, Docker polish, public docs, Outlook provider
- **v1.0** — Personal productivity: AI settings, action execution, calendar integration

---

## 6. Links

| Resource | Location |
|----------|----------|
| Source code | [GitHub Repository](https://github.com/Vibe-Coding-X/mailmind-ai-email-copilot) |
| Architecture diagrams | [`docs/architecture/DIAGRAMS.md`](../architecture/DIAGRAMS.md) |
| Demo script | [`docs/demo/DEMO_SCRIPT.md`](../demo/DEMO_SCRIPT.md) |
| System design | [`docs/architecture/SYSTEM_DESIGN.md`](../architecture/SYSTEM_DESIGN.md) |
| Database schema | [`docs/database/DATABASE_DESIGN.md`](../database/DATABASE_DESIGN.md) |
| API design | [`docs/api/API_DESIGN.md`](../api/API_DESIGN.md) |
| Release notes | [`docs/release-notes/`](../release-notes/) |
