/**
 * API route constants for MailMind (T005 scaffold).
 *
 * Every entry here is derived directly from docs/api/API_DESIGN.md. Do not add
 * routes, query params, or response fields that are not documented there. If a
 * future page needs something undocumented, record it as a Documentation Gap
 * rather than inventing it here.
 *
 * The MVP frontend MUST NOT surface the AI Provider API (docs section 9), which
 * is V1-reserved. It is intentionally omitted from these constants.
 */

export const API_BASE = "/api";

export const API_ROUTES = {
  // Section 1 — Auth API (/api/auth)
  auth: {
    register: "/api/auth/register",
    login: "/api/auth/login",
    logout: "/api/auth/logout",
    me: "/api/auth/me",
  },

  // Section 2 — Gmail OAuth API (/api/auth/gmail)
  // The backend owns the callback route. The frontend only starts login and
  // requests disconnect.
  gmailAuth: {
    login: "/api/auth/gmail/login",
    disconnect: "/api/auth/gmail/disconnect",
  },

  // Section 3 — Digest API (/api/digest)
  digest: {
    today: "/api/digest/today",
    todayGenerate: "/api/digest/today/generate",
    todayRefresh: "/api/digest/today/refresh",
    byId: <TDigestId extends string>(digestId: TDigestId) =>
      `/api/digest/${digestId}` as const,
    itemMarkDone: <TItemId extends string>(itemId: TItemId) =>
      `/api/digest/items/${itemId}/mark-done` as const,
    itemDismiss: <TItemId extends string>(itemId: TItemId) =>
      `/api/digest/items/${itemId}/dismiss` as const,
    itemSnooze: <TItemId extends string>(itemId: TItemId) =>
      `/api/digest/items/${itemId}/snooze` as const,
  },

  // Section 4 — Email API (/api/emails)
  emails: {
    today: "/api/emails/today",
    new: "/api/emails/new",
    byId: <TEmailId extends string>(emailId: TEmailId) =>
      `/api/emails/${emailId}` as const,
    markRead: <TEmailId extends string>(emailId: TEmailId) =>
      `/api/emails/${emailId}/mark-read` as const,
    markUnread: <TEmailId extends string>(emailId: TEmailId) =>
      `/api/emails/${emailId}/mark-unread` as const,
  },

  // Section 5 — Mailbox API (/api/mailboxes)
  mailboxes: {
    list: "/api/mailboxes",
    byId: <TMailboxId extends string>(mailboxId: TMailboxId) =>
      `/api/mailboxes/${mailboxId}` as const,
    syncStatus: <TMailboxId extends string>(mailboxId: TMailboxId) =>
      `/api/mailboxes/${mailboxId}/sync-status` as const,
    sync: <TMailboxId extends string>(mailboxId: TMailboxId) =>
      `/api/mailboxes/${mailboxId}/sync` as const,
  },

  // Section 6 — Job API (/api/jobs)
  jobs: {
    byId: (jobId: string) => `/api/jobs/${jobId}`,
  },

  // Section 7 — User Action API (/api/actions)
  actions: {
    list: "/api/actions",
    create: "/api/actions",
    byId: <TActionId extends string>(actionId: TActionId) =>
      `/api/actions/${actionId}` as const,
    forDigestItem: <TDigestItemId extends string>(digestItemId: TDigestItemId) =>
      `/api/actions/digest-items/${digestItemId}` as const,
  },

  // Section 8 — Users API (/api/users)
  users: {
    me: "/api/users/me",
    mePassword: "/api/users/me/password",
  },
} as const;

/**
 * Documented query params for GET /api/emails/today (docs section 4).
 * `priority` is only valid when `source=current_digest`.
 */
export const EMAILS_TODAY_QUERY = {
  sort: ["received_at_desc"] as const,
  isRead: ["true", "false"] as const,
  priority: ["high", "medium", "low"] as const,
  source: ["current_digest", "all"] as const,
} as const;
