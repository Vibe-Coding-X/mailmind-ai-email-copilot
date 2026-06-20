# BE-C Security / Secret Redaction

Task ID: BE-C
Branch: fix/backend-v02-secret-redaction
Parent branch: feat/backend-v02-real-ai-provider
Goal: Centralize backend secret redaction for AI provider failures, AI run error
storage, and action audit payloads.
Scope: Shared redaction helper, provider error redaction, AI run failed-message
redaction, action audit sanitization, and security regression tests.
Files changed:
- backend/app/utils/redaction.py
- backend/app/ai/openai_compatible_provider.py
- backend/app/services/ai_run_service.py
- backend/app/services/user_action_service.py
- backend/tests/test_redaction.py
- backend/tests/test_ai_run_service.py
- backend/tests/test_llm_provider.py
- backend/tests/test_user_action_service.py
- docs/autonomous/backend/BE-C-secret-redaction.md
API contract changes: None.
Database changes: None.
Environment variables: None.
Tests added:
- Common text redaction for API keys, bearer headers, cookies, OAuth tokens, and
OpenAI-style keys.
- Recursive audit-state sanitization for sensitive keys.
- `ai_runs.error_message` redaction.
- OpenAI-compatible provider error redaction for headers, cookies, and tokens.
- Nested user action audit sanitization.
Validation commands:
- uv sync
- uv run alembic upgrade head
- uv run alembic current
- uv run pytest
- uv run python -m compileall app tests
- Secret scan over README, docs, backend, and .env.example
Validation result: Passed. `uv run pytest` reported 140 passed and 17 warnings.
Alembic current reported `20260620_0007 (head)`. Compileall completed with
exit code 0. Secret scan matches are documentation references and fake test
tokens only.
Security notes: Redaction removes configured provider keys, OpenAI-style keys,
authorization bearer values, cookie values, OAuth token assignments, API key
assignments, and sensitive audit keys. Raw prompt text and full email body text
are not stored by this change.
Known risks: The helper uses pattern-based redaction; unusual secret formats may
need additional patterns as new providers are added.
Next suggested tasks: BE-D Gmail Sync Robustness or BE-E Email Query API
Enhancement.
