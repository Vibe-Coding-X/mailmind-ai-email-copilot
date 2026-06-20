# MailMind v0.2 AI Provider Configuration

MailMind v0.2 keeps the existing Digest API contract unchanged and adds
environment-driven AI provider profiles for the backend digest pipeline.

## Provider Selection

```env
AI_PROVIDER_MODE=env
AI_DEFAULT_PROVIDER=primary
AI_PROVIDER_ORDER=primary,backup
```

`AI_PROVIDER_ORDER` controls fallback order. The backend tries each profile in
order until one returns a valid OpenAI-compatible chat completion response.

## Provider Profile

Each provider id is uppercased in environment variable names.

```env
AI_PROVIDER_PRIMARY_TYPE=openai_compatible
AI_PROVIDER_PRIMARY_BASE_URL=https://api.example.com/v1
AI_PROVIDER_PRIMARY_API_KEY=replace-with-your-key
AI_PROVIDER_PRIMARY_MODEL=replace-with-model
AI_PROVIDER_PRIMARY_TIMEOUT_SECONDS=60
AI_PROVIDER_PRIMARY_MAX_RETRIES=2
```

Supported provider types:

- `openai_compatible`: sends `POST /chat/completions`.
- `mock`: uses the local deterministic test provider.

Legacy `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`,
`LLM_TIMEOUT_SECONDS`, and `LLM_MAX_RETRIES` remain accepted for local
compatibility.

## Security

Do not commit real API keys. Contract examples use placeholders only. Provider
errors stored in `ai_runs` and surfaced through digest generation are sanitized
and must not include API keys, authorization headers, refresh tokens, access
tokens, cookies, or raw prompt content.
