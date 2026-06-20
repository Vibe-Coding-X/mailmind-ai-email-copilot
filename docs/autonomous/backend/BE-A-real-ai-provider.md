# BE-A Real AI Provider Core

Task ID: BE-A
Branch: feat/backend-v02-real-ai-provider
Parent branch: master
Goal: Extend the Daily Digest AI pipeline from a mock-only provider to
OpenAI-compatible provider profiles with fallback.
Scope: Backend AI provider abstraction, provider profile configuration, AI run
provider metadata, migration, tests, environment placeholders, and v0.2 contract
configuration notes.
Files changed:
- backend/app/ai/base.py
- backend/app/ai/mock_provider.py
- backend/app/ai/llm_client.py
- backend/app/ai/openai_compatible_provider.py
- backend/app/core/config.py
- backend/app/db/models/ai_run.py
- backend/app/services/ai_run_service.py
- backend/app/services/digest_service.py
- backend/alembic/versions/20260620_0007_add_ai_run_provider_metadata.py
- backend/tests/test_llm_provider.py
- backend/tests/test_ai_run_service.py
- backend/tests/test_digest_service.py
- backend/tests/test_digest_models.py
- backend/tests/test_digest_migration.py
- .env.example
- docs/contracts/v0.2/ai-provider-config.md
API contract changes: No Digest API path or response shape changes.
Database changes: Added nullable `ai_runs.provider_id` and
`ai_runs.provider_type`.
Environment variables:
- AI_PROVIDER_MODE
- AI_DEFAULT_PROVIDER
- AI_PROVIDER_ORDER
- AI_PROVIDER_<ID>_TYPE
- AI_PROVIDER_<ID>_BASE_URL
- AI_PROVIDER_<ID>_API_KEY
- AI_PROVIDER_<ID>_MODEL
- AI_PROVIDER_<ID>_TIMEOUT_SECONDS
- AI_PROVIDER_<ID>_MAX_RETRIES
- LLM_BASE_URL
- LLM_TIMEOUT_SECONDS
- LLM_MAX_RETRIES
Tests added:
- OpenAI-compatible provider request/response parsing.
- Provider fallback for timeout and HTTP error.
- Sanitized all-provider failure.
- Missing API key fail-fast behavior.
- AI run provider metadata persistence.
Validation commands:
- uv sync
- uv run alembic upgrade head
- uv run alembic current
- uv run pytest
- uv run python -m compileall app tests
- Secret scan over README, docs, backend, and .env.example
Validation result: Passed. `uv run pytest` reported 134 passed and 17 warnings.
Alembic current reported `20260620_0007 (head)`. Compileall completed with exit
code 0. Secret scan returned documentation keyword references and fake test
tokens only; no real API key or token was added.
Security notes: `F:\WorkSpace\model.txt` was inspected only for configuration
shape. No real provider key or model value was copied into code, docs, tests, or
examples. Provider failures redact configured keys and OpenAI-style key strings.
Known risks: Provider profile ids are environment-driven; production deployment
must supply real values outside Git. BE-C should centralize broader secret
redaction across logs and stored error fields.
Next suggested tasks: BE-B AI Output Robustness, then BE-C Security / Secret
Redaction.
