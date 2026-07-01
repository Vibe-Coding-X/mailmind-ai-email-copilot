# MailMind v0.6.0 Local Mail Archive PRD

## Goal

MailMind v0.6.0 turns the product into a local email archive plus today's AI digest workspace.

Dashboard remains the daily digest surface. Emails becomes a local PostgreSQL archive browser. Settings / Mailboxes owns provider connections and full-history archive backfill.

## User Outcomes

- A user can connect multiple Gmail and IMAP mailboxes.
- A user can start a full-history archive backfill for each mailbox.
- MailMind stores message metadata and snippets locally.
- The Emails page can filter locally stored messages by Today, Last 7 Days, Last 30 Days, Custom Range, or All Synced.
- A user can open an email detail view for metadata, snippet, labels, source mailbox, and body cache status.
- A user can load full body text on demand from the connected Gmail or IMAP mailbox; MailMind then stores that body locally for later opens.
- A user can see whether the local archive has not started, is running, is partial, is complete, or failed.

## Scope

In scope:

- Full-history archive backfill for Gmail and IMAP.
- Batched provider reads with cursor/checkpoint persistence.
- Local PostgreSQL email index and snippet storage.
- Mailbox archive state.
- Local email query API and UI filters.
- On-demand full body cache from email detail.
- Settings / Mailboxes archive controls.
- Job Activity visibility for archive jobs.

Out of scope:

- Sync Last 7 Days or Sync Last 30 Days jobs.
- Dashboard historical digest.
- Single-email AI summary.
- Reply drafting.
- Outlook connection.
- AI settings.
- Attachment download or attachment summaries.
- Full body sync by default.

## Product Semantics

There is only one archive sync mode: full history.

Today, Last 7 Days, Last 30 Days, Custom Range, and All Synced are query filters over the local database. They do not create provider sync jobs and they do not call Gmail or IMAP.

Dashboard daily digest behavior is unchanged and remains scoped to today's digest workflow.

Full-history archive does not download full body text or HTML. Body caching is an explicit detail-page action. Once cached, later detail opens read the stored body from PostgreSQL without calling Gmail or IMAP. If provider body fetch fails, the email stores `body_cache_status=failed` and an error code so the user can retry.
