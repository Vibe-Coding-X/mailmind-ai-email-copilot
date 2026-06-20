Task ID: BE-bugfix-real-ai-digest-output-stability
Branch: fix/backend-v02-real-ai-digest-output-stability
Parent branch: integration/v0.2-digest-ai
Goal: Stabilize real OpenAI-compatible Daily Digest output parsing without exposing provider secrets or raw model output.
Scope:
- Strengthened the digest prompt with the digest.v1 JSON shape, enum values, email_id rules, and a minimal safe example.
- Accepted low-risk real-model field aliases such as emailId, type, action, and priority_level.
- Kept unknown email_id references as hard failures.
- Stored short, redacted internal failure categories while keeping the public API error generic.
Files changed:
- backend/app/ai/prompts/digest.py
- backend/app/ai/parsers/digest_parser.py
- backend/app/ai/openai_compatible_provider.py
- backend/app/services/digest_service.py
- backend/tests/test_digest_prompt.py
- backend/tests/test_digest_parser.py
- backend/tests/test_digest_service.py
- backend/tests/test_digest_api.py
- backend/tests/test_ai_run_service.py
- docs/autonomous/backend/BE-bugfix-real-ai-digest-output-stability.md
API contract changes: None.
Database changes: None.
Environment variables: None.
Tests added:
- Prompt schema and enum contract coverage.
- Parser coverage for prose-wrapped JSON, missing/null items, aliases, malformed JSON, unknown email_id, and non-object items.
- Service coverage for real-provider-like output, provider failures, parse diagnostics, metadata recording, and public error secrecy.
Validation commands:
- uv sync
- uv run alembic upgrade head
- uv run alembic current
- uv run pytest
- uv run python -m compileall app tests
Validation result: 163 backend tests passed; Alembic current is 20260620_0007 (head); compileall passed.
Security notes:
- No real API keys, Gmail tokens, Google secrets, or APP_ENCRYPTION_KEY values were added.
- Stored diagnostics are constant, redacted messages and do not include raw prompts or full model output.
Known risks:
- Parser tolerance remains intentionally conservative. It will still fail unknown email_id references and non-object items.
Next suggested tasks:
- Optional manual smoke with real provider env vars only if explicitly requested.
