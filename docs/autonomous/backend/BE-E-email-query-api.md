# BE-E Email Query API Enhancement

Task ID: BE-E
Branch: feat/backend-v02-email-query-api
Parent branch: master
Goal: Add a general email query endpoint for future frontend views while
preserving existing `/api/emails/today` behavior.
Scope: `GET /api/emails`, query service filters, pagination metadata, API tests,
and v0.2 contract example.
Files changed:
- backend/app/api/emails.py
- backend/app/services/email_service.py
- backend/tests/test_email_api.py
- docs/contracts/v0.2/email-api.examples.json
- docs/autonomous/backend/BE-E-email-query-api.md
API contract changes: Added backward-compatible `GET /api/emails`.
Database changes: None.
Environment variables: None.
Tests added:
- Login required for `GET /api/emails`.
- Current-user isolation with read-state and mailbox filters.
- Date range and keyword filters.
- `received_at` descending pagination with `has_more`.
Validation commands:
- uv sync
- uv run alembic upgrade head
- uv run alembic current
- uv run pytest
- uv run python -m compileall app tests
- Secret scan over README, docs, backend, and .env.example
Validation result: Passed. `uv run pytest` reported 130 passed and 17 warnings.
Alembic current reported `20260619_0006 (head)`. Compileall completed with
exit code 0. Secret scan matches are documentation references and fake test
tokens only.
Security notes: The endpoint requires an authenticated user, filters by
`Email.user_id`, and validates mailbox filters against the current user's active
mailboxes. List responses use existing email summary payloads and do not include
`body_text`.
Known risks: Keyword search uses simple `ILIKE` predicates and is not tuned for
large mailboxes; a future indexed search path may be needed.
Next suggested tasks: BE-F Actions Query Enhancement.
