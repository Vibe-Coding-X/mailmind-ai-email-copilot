# Review Checklist

Use this checklist to review Codex-generated changes and human PRs. Findings should reference the relevant files and the source document that defines the expected behavior.

## Architecture Review

- Daily Digest remains the homepage and primary product entry point.
- System login remains separate from Gmail mailbox authorization.
- Provider Adapter boundaries are preserved.
- Gmail is the only runtime MVP email provider.
- Outlook and IMAP are not implemented in MVP code paths.
- Daily Digest versioning is preserved.
- Old successful Digest versions are not overwritten by refresh attempts.
- AI suggestions, provider state, and user behavior remain separate.
- No undocumented architecture change is introduced.

## Database Review

- Tables match `docs/database/DATABASE_DESIGN.md`.
- No `ai_actions` table is added.
- No independent `todos` or `risks` fact tables are added.
- `digest_items` remains the single source for dashboard items.
- `emails` does not store AI priority, AI summary, or action state.
- `daily_digests` enforces one current version per mailbox/date.
- `ai_runs` records AI call metadata and raw structured output.
- `user_actions` records user behavior and provider sync outcomes.
- `mailbox_credentials` stores encrypted credentials separately from `mailboxes`.
- Migrations do not silently change documented enums or constraints.

## API Review

- Routes match `docs/api/API_DESIGN.md`.
- All user-owned resources are filtered by authenticated user.
- Missing or unauthorized resources do not leak cross-user existence.
- `GET /api/digest/today` returns only the current digest.
- Digest generate and refresh endpoints return job status handles rather than blocking on long work.
- Email priority filtering uses current digest join, not `emails` AI fields.
- Mark-read and mark-unread validate ownership, permission mode, and `gmail.modify`.
- New API routes are not added without design review.

## Security Review

- No token in logs.
- No API key in logs.
- No email body text in logs.
- No full AI prompt in logs.
- Refresh token encrypted before storage.
- Access token is not stored long term in PostgreSQL.
- AI API key encrypted when stored in future V1 features.
- User ownership checked before every mailbox, email, digest, job, and action operation.
- No `gmail.send` scope.
- Gmail write operations require `write_enabled`.
- Provider success happens before local Gmail read/unread state update.
- SSRF handled for future custom AI provider endpoint.
- `APP_ENCRYPTION_KEY` is never committed or logged.

## AI Pipeline Review

- LLM calls go through the AI pipeline, not scattered business code.
- AI output is validated against the documented JSON Schema.
- `suggested_action` enum matches PRD, AI Pipeline, and Database docs.
- Low-confidence handling follows documented downgrade behavior.
- `ai_runs` is created for AI calls.
- Full prompts and full email bodies are not logged.
- MVP uses `.env` AI provider configuration only.
- AI Provider UI and database-backed provider config are not added to MVP.
- Codex and Claude Code are not treated as LLM providers.

## Frontend Review

- Dashboard uses `GET /api/digest/today` as the main data source.
- The UI does not make the inbox the homepage.
- Gmail sync failures are visible and not faked as success.
- `/emails/new` is used for new-mail views.
- AI failure shows raw email fallback or previous digest, not a blank page.
- No email sending or auto-reply UI is added in MVP.
- No Outlook, IMAP, or AI Provider settings UI is added in MVP.

## Async Task Review

- Celery tasks update `sync_jobs`.
- Active job de-duplication uses `job_key`.
- Same mailbox/date does not run duplicate digest generation.
- Manual refresh priority does not bypass concurrency rules.
- Failed Digest generation preserves the previous current version.
- Redis new-mail cache does not store email bodies or secrets.
- Token refresh uses locking rules before refreshing shared credentials.
- Scheduled tasks do not compensate missed runs in MVP unless design changes.

## Testing Review

- Tests cover ownership checks.
- Tests cover Digest version switching and rollback behavior.
- Tests cover AI JSON parsing success and failure.
- Tests cover Gmail provider failure without local read-state mutation.
- Tests cover encrypted credential round-trip and no plaintext logging.
- Tests cover timezone window calculation.
- Tests cover frontend fallback states.
- Test failures are not hidden or weakened by changing product behavior.

## Harness Compliance Review

- Task ID exists.
- Task appears in `docs/engineering/TASK_BREAKDOWN.md`.
- Required input documents were consulted.
- Allowed files respected.
- Forbidden changes respected.
- Completion report provided.
- Tests or explanation included.
- No undocumented architecture change.
- New design questions are captured as design-review issues or unresolved questions.
