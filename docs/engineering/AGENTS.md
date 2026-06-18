# Agents

## 1. Purpose

This file defines how Codex and other AI programming agents must work in this repository. It is a Harness Engineering control document: it constrains how agents read project truth, choose work, modify files, report completion, and avoid unsafe architecture drift.

This file does not define product requirements or system architecture. Those remain in the source-of-truth documents listed below.

## 2. Project Source of Truth

When documents overlap, use this priority order:

1. `docs/product/PRD.md`
2. `docs/architecture/SYSTEM_DESIGN.md`
3. `docs/database/DATABASE_DESIGN.md`
4. `docs/api/API_DESIGN.md`
5. `docs/ai/AI_PIPELINE.md`
6. `docs/security/SECURITY.md`
7. `docs/frontend/FRONTEND_DESIGN.md`
8. `docs/architecture/DATA_FLOWS.md`
9. `docs/engineering/TASK_BREAKDOWN.md`
10. `docs/engineering/AGENTS.md`

If documents conflict in a way that changes product scope, system architecture, database design, API behavior, security posture, or AI output contracts, Codex must stop and report the conflict. Codex must not resolve architectural conflicts by guessing.

## 3. Codex Execution Rules

- Before executing a task, Codex must read the task entry in `docs/engineering/TASK_BREAKDOWN.md`.
- Before editing files, Codex must read every document listed in that task's Input Documents.
- Codex may modify only files listed in the task's Allowed Files.
- Codex must not modify files or behavior listed under Forbidden Changes.
- Codex must not start implementation for a future task unless the current task explicitly allows it.
- Codex must not change database design without a design-review issue and explicit approval.
- Codex must not add, remove, or rename API routes without a design-review issue and explicit approval.
- Codex must not expand the MVP scope.
- Codex must not silently reinterpret Gmail, AI Provider, Digest, or user-action concepts.
- Codex must preserve the separation between system login and mailbox authorization.
- Codex must preserve user ownership checks on every user-owned resource.
- Codex must preserve the separation between provider state, AI suggestion state, and user action state.
- Codex must run the tests required by the task, or explain why they could not be run.
- Codex must include a completion report after every task.

## 4. Forbidden Changes

The following changes are forbidden unless a future approved design decision explicitly changes the project scope:

- Do not add an `ai_actions` table.
- Do not split todos or risks into independent facts or source-of-truth tables.
- Do not bypass `user_id` ownership checks.
- Do not save tokens or API keys in plaintext.
- Do not write tokens, API keys, email body text, or full prompts to logs.
- Do not request `gmail.send` by default.
- Do not implement automatic email sending in the MVP.
- Do not treat Codex or Claude Code as ordinary LLM Provider values.
- Do not modify the `suggested_action` enum without design review.
- Do not remove Daily Digest versioning.
- Do not directly overwrite old Daily Digest versions.
- Do not switch a new Digest to current before its items are safely written.
- Do not bypass `ai_runs` for AI calls.
- Do not bypass `user_actions` for user behavior or Gmail read/unread sync results.
- Do not let the frontend fake successful Gmail synchronization.
- Do not put AI Provider configuration UI into the MVP.
- Do not put Outlook or IMAP runtime support into the MVP.
- Do not store Access Tokens long term in PostgreSQL.
- Do not store full MIME messages or attachment binaries in the MVP.
- Do not store AI conclusions directly on `emails`.
- Do not add Gmail Push Notification, Pub/Sub, or real-time insertion into the MVP.

## 5. Handling Documentation Conflicts

If Codex finds a conflict:

1. Stop implementation work.
2. Identify the conflicting documents and exact sections.
3. Explain the implementation impact.
4. Add or update a design-review issue if GitHub issue work is in scope for the task.
5. Do not change code or architecture until the decision is made.

Known issue to preserve until resolved:

- `docs/product/PRD.md` describes `gmail.modify` in a minimum-permission context, while `docs/security/SECURITY.md` and `docs/architecture/SYSTEM_DESIGN.md` define `gmail.modify` as part of a self-use full-experience permission set. Implementation should follow the security/system design wording unless product docs are updated.

## 6. Completion Report Format

Codex must output this report after every task:

```text
Task ID:
Files changed:
Summary:
Docs consulted:
Tests run:
Known risks:
Unresolved questions:
```
