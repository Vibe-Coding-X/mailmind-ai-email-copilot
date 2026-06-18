# Task Breakdown

This document breaks the MailMind MVP into Codex-executable engineering tasks. It is not a backlog of ideas. Each task is a bounded work order with source documents, file boundaries, forbidden changes, acceptance criteria, test expectations, dependencies, and a required completion report.

## Global Rules

- Follow `docs/engineering/AGENTS.md` before executing any task.
- Read every file listed in a task's Input Documents before editing.
- Modify only files listed in Allowed Files.
- Do not implement work from a later phase unless the current task explicitly allows it.
- Do not change MVP scope, product positioning, database design, API surface, AI output schema, or security rules without a design-review issue.
- If a required source document conflicts with another source document, stop and report the conflict.
- Dependencies override the visual phase order. If a task depends on a later-numbered task, complete the dependency first or open a design-review issue to reorder the task graph.

## Completion Report Format

Every task completion report must use this format:

```text
Task ID:
Files changed:
Summary:
Docs consulted:
Tests run:
Known risks:
Unresolved questions:
```

## Phase 0: Documentation Freeze

### T000 Final documentation hardening

**Task ID:** T000
**Task Name:** Final documentation hardening
**Phase:** Phase 0: Documentation Freeze
**Goal:** Confirm that product, architecture, database, API, AI, security, frontend, and engineering docs are indexed and ready for implementation planning.
**Input Documents:** `README.md`, `docs/README.md`, `docs/product/PRD.md`, `docs/architecture/SYSTEM_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/database/DATABASE_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/ai/AI_PIPELINE.md`, `docs/security/SECURITY.md`, `docs/frontend/FRONTEND_DESIGN.md`, `docs/engineering/DEVELOPMENT.md`, `docs/engineering/ASYNC_TASKS.md`, `docs/engineering/INCREMENTAL_SYNC.md`, `docs/engineering/TIMEZONE_RULES.md`, `docs/engineering/TASK_BREAKDOWN.md`, `docs/engineering/AGENTS.md`, `docs/engineering/DECISION_LOG.md`, `docs/engineering/DOCS_FREEZE_CHECKLIST.md`, `docs/engineering/REVIEW_CHECKLIST.md`
**Allowed Files:** Documentation files under `docs/`; `README.md`; `CHANGELOG.md`; `.github/ISSUE_TEMPLATE/*.md`; `.github/PULL_REQUEST_TEMPLATE.md`
**Forbidden Changes:** Do not create `backend/`, `frontend/`, `docker/`, migrations, application code, tests, or dependency manifests. Do not change MVP scope.
**Implementation Notes:** Update only documentation inconsistencies, missing indexes, or checklist statuses. If a conflict affects product or architecture, mark it as unresolved instead of resolving it silently.
**Acceptance Criteria:** Documentation index lists all current governance documents; freeze checklist has no unexamined rows; unresolved conflicts are explicitly marked.
**Test Requirements:** Run `git diff --name-only` and verify only docs/templates changed.
**Dependencies:** None.
**Completion Report Format:** Use the global completion report format.

## Phase 1: Project Scaffold

### T001 Initialize repository scaffold

**Task ID:** T001
**Task Name:** Initialize repository scaffold
**Phase:** Phase 1: Project Scaffold
**Goal:** Create the top-level project directories described in development docs without implementing business logic.
**Input Documents:** `docs/engineering/DEVELOPMENT.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/`, `frontend/`, `docker/`, `data/.gitkeep`, `README.md`
**Forbidden Changes:** Do not add FastAPI routes, Next.js pages, database models, OAuth logic, AI logic, or dependencies beyond placeholder project files.
**Implementation Notes:** Create empty or minimal scaffold files only where needed to anchor the directory layout.
**Acceptance Criteria:** Repository contains the documented top-level structure; no business modules contain logic.
**Test Requirements:** Run a file listing command and verify expected directories exist.
**Dependencies:** T000.
**Completion Report Format:** Use the global completion report format.

### T002 Add environment files and gitignore

**Task ID:** T002
**Task Name:** Add environment files and gitignore
**Phase:** Phase 1: Project Scaffold
**Goal:** Add local configuration templates and ignore rules for secrets, generated data, caches, and build artifacts.
**Input Documents:** `docs/security/SECURITY.md`, `docs/engineering/DEVELOPMENT.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `.env.example`, `.gitignore`, `README.md`
**Forbidden Changes:** Do not add real secrets, tokens, API keys, Gmail credentials, or local database dumps.
**Implementation Notes:** Include placeholders for `APP_ENCRYPTION_KEY`, Gmail OAuth settings, database URL, Redis URL, session settings, and MVP `.env` AI provider settings.
**Acceptance Criteria:** `.env.example` contains no real secret; `.gitignore` excludes `.env`, local data volumes, Python/Node caches, logs, and build output.
**Test Requirements:** Run `git status --short` and verify no generated secret files are tracked.
**Dependencies:** T001.
**Completion Report Format:** Use the global completion report format.

### T003 Add Docker Compose for PostgreSQL and Redis

**Task ID:** T003
**Task Name:** Add Docker Compose for PostgreSQL and Redis
**Phase:** Phase 1: Project Scaffold
**Goal:** Add local infrastructure services for PostgreSQL and Redis.
**Input Documents:** `docs/engineering/DEVELOPMENT.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `docker/docker-compose.yml`, `.env.example`, `README.md`
**Forbidden Changes:** Do not containerize backend, frontend, worker, or beat in this task unless docs are first updated by a design decision.
**Implementation Notes:** Use development-only service definitions and local volumes. Keep service names aligned with docs: `postgres` and `redis`.
**Acceptance Criteria:** Compose file defines PostgreSQL and Redis services with env-file support and local persistent volumes.
**Test Requirements:** Run `docker compose -f docker/docker-compose.yml config` if Docker is available; otherwise report that Docker was unavailable.
**Dependencies:** T002.
**Completion Report Format:** Use the global completion report format.

### T004 Initialize FastAPI backend

**Task ID:** T004
**Task Name:** Initialize FastAPI backend
**Phase:** Phase 1: Project Scaffold
**Goal:** Create a minimal FastAPI backend shell with no business routes beyond health/startup checks.
**Input Documents:** `docs/engineering/DEVELOPMENT.md`, `docs/api/API_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/main.py`, `backend/app/__init__.py`, `backend/requirements.txt`, `backend/README.md`
**Forbidden Changes:** Do not implement Auth, Gmail OAuth, Digest, Email, Mailbox, Job, Action, or User APIs in this task.
**Implementation Notes:** Keep the app importable and ready for later routers.
**Acceptance Criteria:** Backend can start and expose only a minimal health endpoint if included.
**Test Requirements:** Run backend import/start command documented in the task result, or explain why dependencies are not installed.
**Dependencies:** T001, T002.
**Completion Report Format:** Use the global completion report format.

### T005 Initialize Next.js frontend

**Task ID:** T005
**Task Name:** Initialize Next.js frontend
**Phase:** Phase 1: Project Scaffold
**Goal:** Create the frontend shell for later MVP pages.
**Input Documents:** `docs/frontend/FRONTEND_DESIGN.md`, `docs/engineering/DEVELOPMENT.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `frontend/`, `frontend/package.json`, `frontend/src/`, `frontend/README.md`
**Forbidden Changes:** Do not implement Dashboard, login/register, Gmail settings, email list, or email detail workflows in this task.
**Implementation Notes:** Use the documented stack: Next.js, TypeScript, TailwindCSS, shadcn/ui conventions, and TanStack Query when dependencies are added.
**Acceptance Criteria:** Frontend shell is installable and has no product feature implementation beyond a placeholder page.
**Test Requirements:** Run package validation/typecheck if dependencies are installed; otherwise report bootstrap-only status.
**Dependencies:** T001, T002.
**Completion Report Format:** Use the global completion report format.

## Phase 2: Backend Foundation

### T006 Configure backend settings system

**Task ID:** T006
**Task Name:** Configure backend settings system
**Phase:** Phase 2: Backend Foundation
**Goal:** Centralize backend configuration loading from environment variables.
**Input Documents:** `docs/security/SECURITY.md`, `docs/engineering/DEVELOPMENT.md`, `docs/ai/AI_PIPELINE.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/core/config.py`, `backend/app/core/__init__.py`, `backend/tests/`, `.env.example`
**Forbidden Changes:** Do not hardcode secrets, create Gmail logic, create AI clients, or read credentials outside the settings layer.
**Implementation Notes:** Validate required config names without logging secret values.
**Acceptance Criteria:** Settings include database, Redis, session, encryption, Gmail OAuth, and MVP AI provider placeholders.
**Test Requirements:** Add tests for missing required config and secret redaction where applicable.
**Dependencies:** T004.
**Completion Report Format:** Use the global completion report format.

## Phase 3: Database & Migrations

### T007 Configure database connection and Alembic

**Task ID:** T007
**Task Name:** Configure database connection and Alembic
**Phase:** Phase 3: Database & Migrations
**Goal:** Add database session wiring and migration tooling without creating business tables yet.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/engineering/DEVELOPMENT.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/`, `backend/alembic.ini`, `backend/app/db/migrations/`, `backend/requirements.txt`, `backend/tests/`
**Forbidden Changes:** Do not define application models before their specific tasks. Do not alter database design from the docs.
**Implementation Notes:** Use PostgreSQL-compatible SQLAlchemy/Alembic setup and keep models import path ready.
**Acceptance Criteria:** Alembic can discover metadata and create empty revisions.
**Test Requirements:** Run an Alembic command or report why database dependencies are unavailable.
**Dependencies:** T006.
**Completion Report Format:** Use the global completion report format.

### T008 Implement users / auth_accounts / sessions models

**Task ID:** T008
**Task Name:** Implement users / auth_accounts / sessions models
**Phase:** Phase 3: Database & Migrations
**Goal:** Add identity tables exactly as defined by database design.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/schemas/user.py`, `backend/app/schemas/auth.py`, `backend/app/db/migrations/versions/`, `backend/tests/`
**Forbidden Changes:** Do not add mailbox, email, digest, AI, action, or job tables in this task.
**Implementation Notes:** Preserve `users.timezone` default behavior and `sessions.session_token_hash`.
**Acceptance Criteria:** Models and migration match `users`, `auth_accounts`, and `sessions` fields, constraints, and indexes.
**Test Requirements:** Add model/migration tests or schema introspection checks.
**Dependencies:** T007.
**Completion Report Format:** Use the global completion report format.

## Phase 4: Authentication & Sessions

### T009 Implement registration / login / logout / current user

**Task ID:** T009
**Task Name:** Implement registration / login / logout / current user
**Phase:** Phase 4: Authentication & Sessions
**Goal:** Implement system identity APIs independent of Gmail authorization.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/database/DATABASE_DESIGN.md`, `docs/security/SECURITY.md`, `docs/architecture/DATA_FLOWS.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/auth.py`, `backend/app/services/auth_service.py`, `backend/app/core/security.py`, `backend/app/schemas/auth.py`, `backend/tests/`
**Forbidden Changes:** Do not implement Google login as system login; do not bind Gmail OAuth identity to system identity automatically.
**Implementation Notes:** Keep password hashing and session creation separated from Gmail OAuth.
**Acceptance Criteria:** `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, and `/api/auth/me` match documented behavior.
**Test Requirements:** Add API tests for successful login, failed login, logout, and current-user access.
**Dependencies:** T008.
**Completion Report Format:** Use the global completion report format.

### T010 Implement HttpOnly cookie session flow

**Task ID:** T010
**Task Name:** Implement HttpOnly cookie session flow
**Phase:** Phase 4: Authentication & Sessions
**Goal:** Store and validate sessions through HttpOnly cookies and hashed tokens.
**Input Documents:** `docs/architecture/DATA_FLOWS.md`, `docs/database/DATABASE_DESIGN.md`, `docs/security/SECURITY.md`, `docs/api/API_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/core/session.py`, `backend/app/services/auth_service.py`, `backend/app/api/auth.py`, `backend/tests/`
**Forbidden Changes:** Do not store raw session tokens in PostgreSQL; do not expose session tokens in API JSON.
**Implementation Notes:** Use `sessions.session_token_hash`, expiration, revocation, and user ownership checks.
**Acceptance Criteria:** Cookie is HttpOnly; raw token is never persisted; revoked/expired sessions are rejected.
**Test Requirements:** Add tests for cookie attributes, expired session rejection, and revoked session rejection.
**Dependencies:** T009.
**Completion Report Format:** Use the global completion report format.

## Phase 5: Gmail OAuth & Mailbox Credentials

### T011 Implement mailbox and mailbox_credentials models

**Task ID:** T011
**Task Name:** Implement mailbox and mailbox_credentials models
**Phase:** Phase 5: Gmail OAuth & Mailbox Credentials
**Goal:** Add mailbox connection and encrypted credential tables.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/security/SECURITY.md`, `docs/architecture/SYSTEM_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/schemas/mailbox.py`, `backend/app/db/migrations/versions/`, `backend/tests/`
**Forbidden Changes:** Do not implement OAuth routes, Gmail Provider logic, Outlook/IMAP runtime support, or AI provider config table in MVP.
**Implementation Notes:** Include future enum values only where database design defines them; do not implement future providers.
**Acceptance Criteria:** `mailboxes` and `mailbox_credentials` fields, constraints, and indexes match docs.
**Test Requirements:** Add migration/model tests for uniqueness and credential type constraints.
**Dependencies:** T008.
**Completion Report Format:** Use the global completion report format.

### T012 Implement APP_ENCRYPTION_KEY encryption utility

**Task ID:** T012
**Task Name:** Implement APP_ENCRYPTION_KEY encryption utility
**Phase:** Phase 5: Gmail OAuth & Mailbox Credentials
**Goal:** Provide a reusable credential encryption/decryption utility.
**Input Documents:** `docs/security/SECURITY.md`, `docs/database/DATABASE_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/core/encryption.py`, `backend/app/core/config.py`, `backend/tests/`
**Forbidden Changes:** Do not log plaintext, ciphertext secrets, or `APP_ENCRYPTION_KEY`. Do not create separate encryption paths for Gmail and future AI keys.
**Implementation Notes:** Use a well-reviewed symmetric encryption primitive and support `encryption_key_version`.
**Acceptance Criteria:** Utility encrypts and decrypts round-trip; invalid key config fails fast without revealing secrets.
**Test Requirements:** Add tests for round-trip, wrong key failure, and no secret exposure in exception messages.
**Dependencies:** T006.
**Completion Report Format:** Use the global completion report format.

### T013 Implement Gmail OAuth login and callback

**Task ID:** T013
**Task Name:** Implement Gmail OAuth login and callback
**Phase:** Phase 5: Gmail OAuth & Mailbox Credentials
**Goal:** Implement Gmail OAuth connection flow for already logged-in system users.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/security/SECURITY.md`, `docs/database/DATABASE_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/gmail_auth.py`, `backend/app/services/mailbox_service.py`, `backend/app/services/token_service.py`, `backend/app/schemas/mailbox.py`, `backend/tests/`
**Forbidden Changes:** Do not request `gmail.send`; do not treat Gmail OAuth as system login; do not store access tokens long term in PostgreSQL.
**Implementation Notes:** Persist encrypted refresh token in `mailbox_credentials`; cache access token only through the token service when implemented.
**Acceptance Criteria:** `/api/auth/gmail/login` requires system login and returns an auth URL; `/api/auth/gmail/callback` creates or updates the user's Gmail mailbox and encrypted credentials.
**Test Requirements:** Add mocked OAuth tests for missing login, success callback, duplicate mailbox update, and scope capture.
**Dependencies:** T010, T011, T012.
**Completion Report Format:** Use the global completion report format.

### T014 Implement Gmail disconnect

**Task ID:** T014
**Task Name:** Implement Gmail disconnect
**Phase:** Phase 5: Gmail OAuth & Mailbox Credentials
**Goal:** Allow users to disconnect Gmail authorization and clear stored credentials.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/security/SECURITY.md`, `docs/database/DATABASE_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/gmail_auth.py`, `backend/app/services/mailbox_service.py`, `backend/app/services/token_service.py`, `backend/tests/`
**Forbidden Changes:** Do not delete unrelated user data; do not expose encrypted credentials; do not revoke another user's mailbox.
**Implementation Notes:** Follow the documented disconnect behavior: mailbox status can become `disconnected` and credentials must be cleared.
**Acceptance Criteria:** Authenticated user can disconnect own mailbox; other users cannot access it; credentials are removed or invalidated.
**Test Requirements:** Add tests for ownership, successful disconnect, and missing mailbox behavior.
**Dependencies:** T013.
**Completion Report Format:** Use the global completion report format.

### T015 Implement GmailProvider adapter

**Task ID:** T015
**Task Name:** Implement GmailProvider adapter
**Phase:** Phase 5: Gmail OAuth & Mailbox Credentials
**Goal:** Add the Gmail implementation behind the provider adapter contract.
**Input Documents:** `docs/architecture/SYSTEM_DESIGN.md`, `docs/security/SECURITY.md`, `docs/engineering/TIMEZONE_RULES.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/providers/base.py`, `backend/app/providers/gmail.py`, `backend/app/services/token_service.py`, `backend/tests/`
**Forbidden Changes:** Do not implement Outlook or IMAP runtime adapters; do not leak Gmail tokens into logs.
**Implementation Notes:** Map provider errors to stable internal categories; represent Gmail read/unread through the `UNREAD` label.
**Acceptance Criteria:** Adapter exposes `list_messages_for_window`, `get_message_detail`, `get_new_messages_after`, `mark_as_read`, and `mark_as_unread`.
**Test Requirements:** Add mocked provider tests for success, auth failure, rate limit, and read/unread label operations.
**Dependencies:** T012, T013.
**Completion Report Format:** Use the global completion report format.

## Phase 6: Email Synchronization

### T016 Implement list_messages_for_window

**Task ID:** T016
**Task Name:** Implement list_messages_for_window
**Phase:** Phase 6: Email Synchronization
**Goal:** Implement time-window Gmail listing with local secondary filtering.
**Input Documents:** `docs/architecture/SYSTEM_DESIGN.md`, `docs/engineering/TIMEZONE_RULES.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/providers/gmail.py`, `backend/app/providers/base.py`, `backend/tests/`
**Forbidden Changes:** Do not calculate business day windows inside provider code; do not rely only on Gmail search boundaries.
**Implementation Notes:** Business services pass UTC window bounds; provider returns normalized message metadata and details.
**Acceptance Criteria:** Candidate Gmail messages are locally filtered by `coverage_start <= received_at <= coverage_end` after parsing.
**Test Requirements:** Add tests for timezone boundary cases and candidate filtering.
**Dependencies:** T015.
**Completion Report Format:** Use the global completion report format.

### T017 Implement email synchronization

**Task ID:** T017
**Task Name:** Implement email synchronization
**Phase:** Phase 6: Email Synchronization
**Goal:** Sync today's Gmail messages into local email records.
**Input Documents:** `docs/architecture/DATA_FLOWS.md`, `docs/database/DATABASE_DESIGN.md`, `docs/engineering/TIMEZONE_RULES.md`, `docs/ai/AI_PIPELINE.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/services/email_service.py`, `backend/app/utils/email_parser.py`, `backend/app/ai/preprocessor.py`, `backend/app/schemas/email.py`, `backend/tests/`
**Forbidden Changes:** Do not store full MIME, attachments, tokens, or unbounded body text.
**Implementation Notes:** Clean HTML, strip quoted noise where practical, truncate body text, and preserve `body_text_truncated`.
**Acceptance Criteria:** Sync calculates user's local day window, fetches messages through provider, cleans body text, and prepares records for upsert.
**Test Requirements:** Add unit tests for window calculation, body cleaning, truncation flag, and provider failure handling.
**Dependencies:** T016.
**Completion Report Format:** Use the global completion report format.

### T018 Implement emails table write / update logic

**Task ID:** T018
**Task Name:** Implement emails table write / update logic
**Phase:** Phase 6: Email Synchronization
**Goal:** Upsert synchronized email records while preserving provider state.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/db/migrations/versions/`, `backend/app/services/email_service.py`, `backend/app/schemas/email.py`, `backend/tests/`
**Forbidden Changes:** Do not store AI priority or AI summary on `emails`; do not create duplicate email rows for the same `mailbox_id + external_id`.
**Implementation Notes:** `emails.is_read` reflects provider truth, not user handling state.
**Acceptance Criteria:** `emails` model/migration matches docs; sync upsert updates existing records and inserts new records.
**Test Requirements:** Add tests for uniqueness, idempotent sync, read-state update, and user/mailbox ownership consistency.
**Dependencies:** T011, T017.
**Completion Report Format:** Use the global completion report format.

## Phase 7: AI Pipeline MVP

### T019 Implement daily_digests version model

**Task ID:** T019
**Task Name:** Implement daily_digests version model
**Phase:** Phase 7: AI Pipeline MVP
**Goal:** Add versioned Daily Digest persistence.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/architecture/SYSTEM_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/db/migrations/versions/`, `backend/app/schemas/digest.py`, `backend/tests/`
**Forbidden Changes:** Do not remove versioning; do not allow more than one current digest per `mailbox_id + digest_date`.
**Implementation Notes:** Include partial unique index for current digest where supported.
**Acceptance Criteria:** `daily_digests` model/migration matches docs and enforces version/current constraints.
**Test Requirements:** Add tests for version uniqueness and current-version uniqueness.
**Dependencies:** T018.
**Completion Report Format:** Use the global completion report format.

### T020 Implement digest_items model

**Task ID:** T020
**Task Name:** Implement digest_items model
**Phase:** Phase 7: AI Pipeline MVP
**Goal:** Add unified dashboard item persistence.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/ai/AI_PIPELINE.md`, `docs/architecture/SYSTEM_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/db/migrations/versions/`, `backend/app/schemas/digest.py`, `backend/tests/`
**Forbidden Changes:** Do not create `ai_actions`, `todos`, or `risks` tables; do not change `suggested_action` enum.
**Implementation Notes:** Enforce item-type and section consistency as documented.
**Acceptance Criteria:** `digest_items` fields, checks, and indexes match docs; todos and risks are item types, not separate facts.
**Test Requirements:** Add tests for email item uniqueness, section/type checks, and confidence range.
**Dependencies:** T019.
**Completion Report Format:** Use the global completion report format.

### T021 Implement ai_runs model

**Task ID:** T021
**Task Name:** Implement ai_runs model
**Phase:** Phase 7: AI Pipeline MVP
**Goal:** Add AI run metadata and raw structured output tracking.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/ai/AI_PIPELINE.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/db/migrations/versions/`, `backend/app/schemas/job.py`, `backend/tests/`
**Forbidden Changes:** Do not store full prompts, full email bodies, tokens, or API keys in `ai_runs`.
**Implementation Notes:** `input_hash` and `input_summary_json` represent AI input without storing sensitive prompt/body content.
**Acceptance Criteria:** `ai_runs` model/migration matches docs and supports daily digest, single email, and new-mail preview run types.
**Test Requirements:** Add tests for status/output consistency and non-negative token counters.
**Dependencies:** T019.
**Completion Report Format:** Use the global completion report format.

### T022 Implement AI Pipeline MVP using .env provider

**Task ID:** T022
**Task Name:** Implement AI Pipeline MVP using .env provider
**Phase:** Phase 7: AI Pipeline MVP
**Goal:** Add MVP AI pipeline components using the `.env` default provider only.
**Input Documents:** `docs/ai/AI_PIPELINE.md`, `docs/product/PRD.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/ai/`, `backend/app/services/ai_service.py`, `backend/app/core/config.py`, `backend/tests/`
**Forbidden Changes:** Do not implement AI Provider UI, `ai_provider_configs` runtime table, model profiles, Codex/Claude Code provider types, or V1/V2 routing.
**Implementation Notes:** Implement interfaces for `EmailPreprocessor`, `DigestInputBuilder`, `LLMClient`, `StructuredOutputParser`, `DigestDecisionEngine`, and `SafetyFilter`.
**Acceptance Criteria:** Pipeline can run with a fake LLM client and produce a typed digest output.
**Test Requirements:** Add fake LLM tests for successful digest generation and provider misconfiguration.
**Dependencies:** T006, T021.
**Completion Report Format:** Use the global completion report format.

### T023 Implement AI JSON Schema validation

**Task ID:** T023
**Task Name:** Implement AI JSON Schema validation
**Phase:** Phase 7: AI Pipeline MVP
**Goal:** Validate AI output against the documented MVP JSON schema.
**Input Documents:** `docs/ai/AI_PIPELINE.md`, `docs/database/DATABASE_DESIGN.md`, `docs/product/PRD.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/ai/output_parser.py`, `backend/app/ai/schemas/`, `backend/tests/`
**Forbidden Changes:** Do not change `item_type`, `section`, `category`, `suggested_action`, or `priority` enums without design review.
**Implementation Notes:** Low-confidence business downgrades belong in the decision engine, not the raw schema.
**Acceptance Criteria:** Valid outputs pass; missing required fields, invalid enum values, invalid confidence, and malformed deadlines fail.
**Test Requirements:** Add parser tests for valid output, invalid enum, missing field, low confidence handling handoff, and malformed JSON.
**Dependencies:** T022.
**Completion Report Format:** Use the global completion report format.

## Phase 8: Daily Digest Generation

### T024 Implement generate_daily_digest task

**Task ID:** T024
**Task Name:** Implement generate_daily_digest task
**Phase:** Phase 8: Daily Digest Generation
**Goal:** Generate a Daily Digest version from synchronized emails through the AI pipeline.
**Input Documents:** `docs/architecture/DATA_FLOWS.md`, `docs/database/DATABASE_DESIGN.md`, `docs/ai/AI_PIPELINE.md`, `docs/engineering/ASYNC_TASKS.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/services/digest_service.py`, `backend/app/tasks/digest_tasks.py`, `backend/app/ai/decision_engine.py`, `backend/tests/`
**Forbidden Changes:** Do not switch current digest before digest items are written; do not overwrite old digest versions.
**Implementation Notes:** Create `daily_digests` row with `status = generating`, create `ai_runs`, call pipeline, parse output, map items, and mark failures without changing current version.
**Acceptance Criteria:** Successful run creates digest, ai_run, and items; failed run records failed statuses and preserves previous current digest.
**Test Requirements:** Add fake LLM tests for success, AI failure, parser failure, and no-email cases.
**Dependencies:** T019, T020, T021, T023.
**Completion Report Format:** Use the global completion report format.

### T025 Implement Digest current version transaction switch

**Task ID:** T025
**Task Name:** Implement Digest current version transaction switch
**Phase:** Phase 8: Daily Digest Generation
**Goal:** Switch current Daily Digest version atomically after successful item insertion.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/engineering/ASYNC_TASKS.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/services/digest_service.py`, `backend/tests/`
**Forbidden Changes:** Do not directly update old digest content; do not leave two current digests; do not expose half-built digests to reads.
**Implementation Notes:** Use transaction boundaries and locking strategy consistent with database design.
**Acceptance Criteria:** Old current digest remains current on rollback; exactly one current digest exists after success.
**Test Requirements:** Add transaction tests for success, insertion failure, and concurrent generation attempt.
**Dependencies:** T024.
**Completion Report Format:** Use the global completion report format.

### T026 Implement GET /api/digest/today

**Task ID:** T026
**Task Name:** Implement GET /api/digest/today
**Phase:** Phase 8: Daily Digest Generation
**Goal:** Return the current user's current Daily Digest for today.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/database/DATABASE_DESIGN.md`, `docs/frontend/FRONTEND_DESIGN.md`, `docs/engineering/INCREMENTAL_SYNC.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/digest.py`, `backend/app/services/digest_service.py`, `backend/app/schemas/digest.py`, `backend/tests/`
**Forbidden Changes:** Do not return another user's digest; do not return non-current versions by default.
**Implementation Notes:** Include digest metadata, overview, items grouped or sortable by section, and new-mail status if already known.
**Acceptance Criteria:** Endpoint returns only `is_current = true` digest for current user and local digest date.
**Test Requirements:** Add API tests for no digest, current digest, stale digest, and cross-user isolation.
**Dependencies:** T025.
**Completion Report Format:** Use the global completion report format.

### T027 Implement POST /api/digest/today/generate

**Task ID:** T027
**Task Name:** Implement POST /api/digest/today/generate
**Phase:** Phase 8: Daily Digest Generation
**Goal:** Trigger asynchronous generation of today's Daily Digest.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/engineering/ASYNC_TASKS.md`, `docs/database/DATABASE_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/digest.py`, `backend/app/services/digest_service.py`, `backend/app/tasks/digest_tasks.py`, `backend/tests/`
**Forbidden Changes:** Do not run long AI generation synchronously in the API request; do not bypass job de-duplication.
**Implementation Notes:** Return a `job_id` and rely on job polling.
**Acceptance Criteria:** Authenticated request creates or returns a queued/running generation job for current user's mailbox/date.
**Test Requirements:** Add API tests for unauthenticated access, missing mailbox, existing running job, and new job creation.
**Dependencies:** T024, T034.
**Completion Report Format:** Use the global completion report format.

### T028 Implement POST /api/digest/today/refresh

**Task ID:** T028
**Task Name:** Implement POST /api/digest/today/refresh
**Phase:** Phase 8: Daily Digest Generation
**Goal:** Trigger refresh flow that syncs new mail and generates a new digest version.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/engineering/ASYNC_TASKS.md`, `docs/engineering/INCREMENTAL_SYNC.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/digest.py`, `backend/app/services/digest_service.py`, `backend/app/tasks/digest_tasks.py`, `backend/tests/`
**Forbidden Changes:** Do not silently overwrite the current digest; do not skip new-mail sync before refresh.
**Implementation Notes:** Existing current digest may show `refreshing` while a new version is being generated.
**Acceptance Criteria:** Endpoint returns existing active refresh job or creates one; successful refresh creates a new version and switches current only after success.
**Test Requirements:** Add tests for no current digest, stale digest refresh, running refresh de-duplication, and failed refresh preserving old current version.
**Dependencies:** T025, T034, T035.
**Completion Report Format:** Use the global completion report format.

## Phase 9: User Actions & Gmail Read/Unread Sync

### T029 Implement GET /api/emails/today

**Task ID:** T029
**Task Name:** Implement GET /api/emails/today
**Phase:** Phase 9: User Actions & Gmail Read/Unread Sync
**Goal:** Return today's email list with optional digest-based priority filtering.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/database/DATABASE_DESIGN.md`, `docs/frontend/FRONTEND_DESIGN.md`, `docs/engineering/TIMEZONE_RULES.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/emails.py`, `backend/app/services/email_service.py`, `backend/app/schemas/email.py`, `backend/tests/`
**Forbidden Changes:** Do not store AI priority on `emails`; priority filtering must use current digest join when `source=current_digest`.
**Implementation Notes:** Support documented query params: `sort`, `is_read`, `priority`, and `source`.
**Acceptance Criteria:** `source=all` returns email facts only; `source=current_digest` joins `digest_items(item_type='email')`.
**Test Requirements:** Add tests for filters, sorting, current-digest priority join, and user isolation.
**Dependencies:** T018, T020.
**Completion Report Format:** Use the global completion report format.

### T030 Implement GET /api/emails/new

**Task ID:** T030
**Task Name:** Implement GET /api/emails/new
**Phase:** Phase 9: User Actions & Gmail Read/Unread Sync
**Goal:** Return emails received after the current digest coverage end.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/engineering/INCREMENTAL_SYNC.md`, `docs/frontend/FRONTEND_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/emails.py`, `backend/app/services/email_service.py`, `backend/app/services/digest_service.py`, `backend/tests/`
**Forbidden Changes:** Do not create a separate temporary new-mail page model; do not mutate digest items while only listing new mail.
**Implementation Notes:** Optional AI preview belongs to `new_mail_preview` and may fail without blocking the list.
**Acceptance Criteria:** Endpoint returns emails after current digest `coverage_end` for the authenticated user's mailbox.
**Test Requirements:** Add tests for no current digest, no new mail, new mail list, and AI preview failure fallback if implemented.
**Dependencies:** T026, T029.
**Completion Report Format:** Use the global completion report format.

### T031 Implement GET /api/emails/{id}

**Task ID:** T031
**Task Name:** Implement GET /api/emails/{id}
**Phase:** Phase 9: User Actions & Gmail Read/Unread Sync
**Goal:** Return email detail and any related current digest item analysis.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/frontend/FRONTEND_DESIGN.md`, `docs/database/DATABASE_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/emails.py`, `backend/app/services/email_service.py`, `backend/app/schemas/email.py`, `backend/tests/`
**Forbidden Changes:** Do not expose emails across users; do not fetch or store attachments.
**Implementation Notes:** Include body text as locally stored cleaned text and related digest item if present in current digest.
**Acceptance Criteria:** Authenticated owner can fetch detail; non-owner receives not found or forbidden per API convention.
**Test Requirements:** Add tests for owner access, cross-user denial, missing email, and related digest item inclusion.
**Dependencies:** T029.
**Completion Report Format:** Use the global completion report format.

### T032 Implement mark-read / mark-unread Gmail sync

**Task ID:** T032
**Task Name:** Implement mark-read / mark-unread Gmail sync
**Phase:** Phase 9: User Actions & Gmail Read/Unread Sync
**Goal:** Implement real Gmail read/unread state synchronization.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/security/SECURITY.md`, `docs/database/DATABASE_DESIGN.md`, `docs/architecture/SYSTEM_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/api/emails.py`, `backend/app/services/email_service.py`, `backend/app/providers/gmail.py`, `backend/app/services/action_service.py`, `backend/tests/`
**Forbidden Changes:** Do not update `emails.is_read` before provider success; do not let frontend or API fake success; do not skip scope and permission checks.
**Implementation Notes:** Check ownership, `write_enabled`, `gmail.modify`, then call provider. Write `user_actions` for both success and failure.
**Acceptance Criteria:** Successful provider call updates local read state and action record; failed provider call leaves local state unchanged and records failed action.
**Test Requirements:** Add tests for mark read, mark unread, readonly mailbox, missing scope, provider failure, and cross-user denial.
**Dependencies:** T015, T031, T033.
**Completion Report Format:** Use the global completion report format.

### T033 Implement user_actions model and service

**Task ID:** T033
**Task Name:** Implement user_actions model and service
**Phase:** Phase 9: User Actions & Gmail Read/Unread Sync
**Goal:** Record actual user behavior separately from AI suggestions.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/architecture/SYSTEM_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/db/migrations/versions/`, `backend/app/services/action_service.py`, `backend/app/api/actions.py`, `backend/app/schemas/action.py`, `backend/tests/`
**Forbidden Changes:** Do not modify `digest_items` to represent completed/dismissed state; do not treat AI suggestion as user action.
**Implementation Notes:** Use `before_state`, `after_state`, `provider_effect`, and `action_status` for auditability.
**Acceptance Criteria:** `user_actions` model/migration and APIs match docs; service enforces user/mailbox consistency.
**Test Requirements:** Add tests for action creation, digest item action lookup, failed action record, and cross-user isolation.
**Dependencies:** T020, T031.
**Completion Report Format:** Use the global completion report format.

## Phase 10: Frontend MVP

### T037 Implement Dashboard frontend page

**Task ID:** T037
**Task Name:** Implement Dashboard frontend page
**Phase:** Phase 10: Frontend MVP
**Goal:** Implement the Daily Digest-first dashboard.
**Input Documents:** `docs/frontend/FRONTEND_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/product/PRD.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `frontend/src/app/dashboard/`, `frontend/src/components/dashboard/`, `frontend/src/lib/api/`, `frontend/src/lib/query/`, `frontend/tests/`
**Forbidden Changes:** Do not make a traditional inbox the homepage; do not implement AI Provider UI; do not fake Gmail sync success.
**Implementation Notes:** Use `GET /api/digest/today` as the main data source and show freshness/new-mail status.
**Acceptance Criteria:** Dashboard shows status bar, overview, urgent, review, ignore, todo, risk, and new-mail prompt sections.
**Test Requirements:** Add frontend typecheck/lint and component or E2E tests for fresh, stale, generating, and failed states.
**Dependencies:** T005, T026, T027, T028.
**Completion Report Format:** Use the global completion report format.

### T038 Implement Email Detail frontend page

**Task ID:** T038
**Task Name:** Implement Email Detail frontend page
**Phase:** Phase 10: Frontend MVP
**Goal:** Implement email detail view linked from Dashboard and email list.
**Input Documents:** `docs/frontend/FRONTEND_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/product/PRD.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `frontend/src/app/emails/[id]/`, `frontend/src/components/email/`, `frontend/src/lib/api/`, `frontend/tests/`
**Forbidden Changes:** Do not add send/reply capability; do not hide provider sync failures.
**Implementation Notes:** Use `GET /api/emails/{id}` and mark-read/mark-unread endpoints.
**Acceptance Criteria:** Page shows subject, sender, recipients, received time, cleaned body, AI analysis, related items, and supported actions.
**Test Requirements:** Add tests for loaded state, missing email, mark-read success, and mark-read failure UI.
**Dependencies:** T031, T032.
**Completion Report Format:** Use the global completion report format.

### T039 Implement Gmail connection settings page

**Task ID:** T039
**Task Name:** Implement Gmail connection settings page
**Phase:** Phase 10: Frontend MVP
**Goal:** Implement mailbox connection management for Gmail.
**Input Documents:** `docs/frontend/FRONTEND_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `frontend/src/app/settings/mailboxes/`, `frontend/src/components/settings/`, `frontend/src/lib/api/`, `frontend/tests/`
**Forbidden Changes:** Do not add Outlook/IMAP UI; do not add AI Provider settings UI in MVP.
**Implementation Notes:** Support connect Gmail, mailbox status display, sync status display, and disconnect.
**Acceptance Criteria:** Page reflects connected, disconnected, reauth required, and error states.
**Test Requirements:** Add tests for connect action, disconnect action, and reauth state rendering.
**Dependencies:** T013, T014.
**Completion Report Format:** Use the global completion report format.

### T040 Implement login/register pages

**Task ID:** T040
**Task Name:** Implement login/register pages
**Phase:** Phase 10: Frontend MVP
**Goal:** Implement system login and registration UI.
**Input Documents:** `docs/frontend/FRONTEND_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `frontend/src/app/login/`, `frontend/src/app/register/`, `frontend/src/components/auth/`, `frontend/src/lib/api/`, `frontend/tests/`
**Forbidden Changes:** Do not conflate Google/Gmail OAuth with system login.
**Implementation Notes:** System identity is separate from mailbox authorization.
**Acceptance Criteria:** Users can register, login, logout, and fetch current user through documented APIs.
**Test Requirements:** Add tests for login success, login failure, register success, and redirect after authenticated access.
**Dependencies:** T009, T010.
**Completion Report Format:** Use the global completion report format.

### T041 Implement failure fallback UI

**Task ID:** T041
**Task Name:** Implement failure fallback UI
**Phase:** Phase 10: Frontend MVP
**Goal:** Show usable fallback states when AI digest generation fails or is unavailable.
**Input Documents:** `docs/product/PRD.md`, `docs/frontend/FRONTEND_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `frontend/src/app/dashboard/`, `frontend/src/app/emails/`, `frontend/src/components/dashboard/`, `frontend/src/components/email/`, `frontend/tests/`
**Forbidden Changes:** Do not show a blank dashboard on AI failure; do not overwrite old digest client-side.
**Implementation Notes:** Reuse `/emails` behavior for raw email fallback and show retry controls.
**Acceptance Criteria:** Failed digest state shows error, retry, and raw email fallback; previous successful digest can still be identified as historical.
**Test Requirements:** Add tests for digest failed with previous digest, failed without digest, and retry action.
**Dependencies:** T029, T037.
**Completion Report Format:** Use the global completion report format.

## Phase 11: Async Tasks & Redis

### T034 Implement sync_jobs model and job status API

**Task ID:** T034
**Task Name:** Implement sync_jobs model and job status API
**Phase:** Phase 11: Async Tasks & Redis
**Goal:** Track asynchronous job status and expose polling endpoint.
**Input Documents:** `docs/database/DATABASE_DESIGN.md`, `docs/api/API_DESIGN.md`, `docs/engineering/ASYNC_TASKS.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/db/models.py`, `backend/app/db/models/`, `backend/app/db/migrations/versions/`, `backend/app/api/jobs.py`, `backend/app/schemas/job.py`, `backend/app/services/job_service.py`, `backend/tests/`
**Forbidden Changes:** Do not rely only on Celery task state; do not skip job-key de-duplication.
**Implementation Notes:** Implement `job_key` uniqueness for active queued/running jobs.
**Acceptance Criteria:** `/api/jobs/{job_id}` returns status for user's own jobs only.
**Test Requirements:** Add tests for job creation, duplicate active job, status lookup, and cross-user denial.
**Dependencies:** T011.
**Completion Report Format:** Use the global completion report format.

### T035 Implement Redis cache for new-mail detection

**Task ID:** T035
**Task Name:** Implement Redis cache for new-mail detection
**Phase:** Phase 11: Async Tasks & Redis
**Goal:** Cache lightweight new-mail checks after current digest generation.
**Input Documents:** `docs/engineering/INCREMENTAL_SYNC.md`, `docs/api/API_DESIGN.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/services/digest_service.py`, `backend/app/services/email_service.py`, `backend/app/core/redis.py`, `backend/tests/`
**Forbidden Changes:** Do not treat Redis as the persistent source of truth; do not store email bodies or tokens in this cache.
**Implementation Notes:** Use key shape `new_mail_check:{mailbox_id}:{digest_id}` and TTL 60 or 120 seconds.
**Acceptance Criteria:** Cache hit avoids provider call; cache miss checks provider and updates digest stale status when new mail exists.
**Test Requirements:** Add tests for cache hit, miss, TTL write, and stale status update.
**Dependencies:** T026, T030.
**Completion Report Format:** Use the global completion report format.

### T036 Implement Celery worker and beat

**Task ID:** T036
**Task Name:** Implement Celery worker and beat
**Phase:** Phase 11: Async Tasks & Redis
**Goal:** Add Celery app, worker tasks, and scheduled digest generation hook.
**Input Documents:** `docs/engineering/ASYNC_TASKS.md`, `docs/engineering/DEVELOPMENT.md`, `docs/security/SECURITY.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/app/tasks/celery_app.py`, `backend/app/tasks/sync_tasks.py`, `backend/app/tasks/digest_tasks.py`, `backend/app/tasks/token_tasks.py`, `backend/app/core/config.py`, `backend/tests/`
**Forbidden Changes:** Do not auto-send email; do not bypass `sync_jobs`; do not add real-time Gmail Push in MVP.
**Implementation Notes:** Add tasks for `sync_today_emails`, `generate_daily_digest`, `refresh_daily_digest`, `check_new_emails_after_digest`, and `refresh_access_token`.
**Acceptance Criteria:** Tasks update `sync_jobs` status and obey de-duplication and retry rules.
**Test Requirements:** Add eager-mode task tests for success, retry, and failure status recording.
**Dependencies:** T017, T024, T034, T035.
**Completion Report Format:** Use the global completion report format.

## Phase 12: Error Handling & Fallback

### T042 Add backend tests

**Task ID:** T042
**Task Name:** Add backend tests
**Phase:** Phase 12: Error Handling & Fallback
**Goal:** Build the backend verification harness for MVP-critical behavior.
**Input Documents:** `docs/api/API_DESIGN.md`, `docs/database/DATABASE_DESIGN.md`, `docs/ai/AI_PIPELINE.md`, `docs/security/SECURITY.md`, `docs/engineering/REVIEW_CHECKLIST.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `backend/tests/`, `backend/pytest.ini`, `backend/pyproject.toml`, `backend/requirements.txt`
**Forbidden Changes:** Do not change production code except where needed to make already-planned tests pass within a specific task.
**Implementation Notes:** Add fixtures for database, Redis fake or test instance, fake Gmail provider, and fake LLM client.
**Acceptance Criteria:** Backend tests cover auth, ownership, digest switching, AI parser, Gmail sync, and sensitive logging boundaries.
**Test Requirements:** Run backend test suite and report pass/fail.
**Dependencies:** T032, T036.
**Completion Report Format:** Use the global completion report format.

## Phase 13: Security Hardening

### T043 Add frontend typecheck/lint

**Task ID:** T043
**Task Name:** Add frontend typecheck/lint
**Phase:** Phase 13: Security Hardening
**Goal:** Add frontend static verification commands.
**Input Documents:** `docs/frontend/FRONTEND_DESIGN.md`, `docs/engineering/DEVELOPMENT.md`, `docs/engineering/REVIEW_CHECKLIST.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `frontend/package.json`, `frontend/tsconfig.json`, `frontend/eslint.config.*`, `frontend/src/`, `frontend/tests/`
**Forbidden Changes:** Do not silence type errors by weakening API types; do not remove useful lint rules for convenience.
**Implementation Notes:** Ensure API response types line up with backend schemas where possible.
**Acceptance Criteria:** `typecheck` and `lint` scripts exist and run in local development.
**Test Requirements:** Run frontend typecheck and lint, or explain dependency/bootstrap blocker.
**Dependencies:** T037, T038, T039, T040, T041.
**Completion Report Format:** Use the global completion report format.

### T044 Add CI workflow

**Task ID:** T044
**Task Name:** Add CI workflow
**Phase:** Phase 13: Security Hardening
**Goal:** Add continuous integration for backend, frontend, and documentation safety checks.
**Input Documents:** `docs/engineering/DEVELOPMENT.md`, `docs/engineering/REVIEW_CHECKLIST.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `.github/workflows/ci.yml`, `README.md`
**Forbidden Changes:** Do not add deployment, production secrets, or cloud credentials.
**Implementation Notes:** CI should run backend tests, frontend lint/typecheck, and optionally docs link/check formatting.
**Acceptance Criteria:** Workflow is scoped to validation and does not deploy.
**Test Requirements:** Validate YAML syntax locally if tooling is available; otherwise report manual review.
**Dependencies:** T042, T043.
**Completion Report Format:** Use the global completion report format.

## Phase 14: MVP Acceptance

### T045 MVP end-to-end acceptance checklist

**Task ID:** T045
**Task Name:** MVP end-to-end acceptance checklist
**Phase:** Phase 14: MVP Acceptance
**Goal:** Verify the complete MVP path from registration through Gmail authorization, sync, digest generation, dashboard, detail, read/unread sync, and fallback behavior.
**Input Documents:** `docs/product/PRD.md`, `docs/architecture/SYSTEM_DESIGN.md`, `docs/architecture/DATA_FLOWS.md`, `docs/api/API_DESIGN.md`, `docs/frontend/FRONTEND_DESIGN.md`, `docs/security/SECURITY.md`, `docs/engineering/REVIEW_CHECKLIST.md`, `docs/engineering/AGENTS.md`
**Allowed Files:** `docs/engineering/MVP_ACCEPTANCE.md`, `README.md`, test fixtures under `backend/tests/` and `frontend/tests/`
**Forbidden Changes:** Do not expand MVP scope during acceptance; do not add Outlook, IMAP, send-mail, AI Provider UI, or automatic replies.
**Implementation Notes:** Use fake Gmail/fake LLM where real credentials are unavailable; real Gmail smoke testing must avoid committing secrets.
**Acceptance Criteria:** Checklist covers registration, login, Gmail connect/disconnect, sync, digest generate, refresh, new mail detection, email detail, read/unread sync, job polling, and failure fallback.
**Test Requirements:** Run all automated tests and record any manual smoke-test gaps.
**Dependencies:** T044.
**Completion Report Format:** Use the global completion report format.
