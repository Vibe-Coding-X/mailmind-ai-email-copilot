# BE-B AI Output Robustness

Task ID: BE-B
Branch: feat/backend-v02-ai-output-robustness
Parent branch: master
Goal: Make Daily Digest structured output parsing resilient to common LLM output
variance without changing Digest API contracts.
Scope: Digest parser hardening, parser regression tests, and refresh-failure
safety coverage.
Files changed:
- backend/app/ai/parsers/digest_parser.py
- backend/tests/test_digest_parser.py
- backend/tests/test_digest_service.py
API contract changes: None.
Database changes: None.
Environment variables: None.
Tests added:
- Markdown fenced JSON parsing.
- Empty output fallback.
- Missing overview and item-field fallback.
- Priority and suggested-action normalization.
- Confidence defaulting and clamping.
- Invalid AI output during refresh preserves the previous current digest.
Validation commands:
- uv sync
- uv run alembic stamp head --purge
- uv run alembic upgrade head
- uv run alembic current
- uv run pytest
- uv run python -m compileall app tests
- Secret scan over README, docs, backend, and .env.example
Validation result: Passed. `uv run pytest` reported 131 passed and 17 warnings.
Alembic current reported `20260619_0006 (head)`. Compileall completed with
exit code 0. The local Alembic stamp was purged and restamped because the
shared development database had been left at BE-A's independent `20260620_0007`
revision, which is not present on this branch.
Security notes: Parser changes do not log or persist raw prompts, tokens, API
keys, cookies, or credentials. Secret scan matches are documentation references
and fake test tokens only.
Known risks: Fallback parsing intentionally accepts more malformed AI output;
unknown `email_id` values still fail hard to prevent cross-input item creation.
Next suggested tasks: BE-C Security / Secret Redaction, then BE-D Gmail Sync
Robustness.
