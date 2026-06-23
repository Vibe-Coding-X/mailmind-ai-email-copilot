/**
 * Typed API client for MailMind.
 *
 * Auth and mailbox settings routes are wired to the real backend. All requests
 * send `credentials: "include"` so the browser carries the HttpOnly session
 * cookie; the frontend never reads or stores it.
 *
 * Routes outside the current integration scope remain safe placeholders that
 * throw `Not implemented`. Do NOT add email/digest/AI behavior here outside a
 * dedicated task, and wire any new route strictly per docs/api/API_DESIGN.md.
 */

import { API_BASE_URL } from "./config";
import { API_ROUTES } from "./api-routes";
import {
  isApiError,
  type ApiError,
  type ApiResult,
  type AuthUserResponse,
  type DigestItemActionResponse,
  type DigestResponse,
  type EmailMutationResponse,
  type EmailResponse,
  type GmailLoginResponse,
  type ImapConnectRequest,
  type ImapConnectResponse,
  type JobListQuery,
  type JobResponse,
  type JobsResponse,
  type MailboxResponse,
  type MailboxSyncJobResponse,
  type MailboxSyncResponse,
  type MailboxSyncStatusResponse,
  type MailboxesResponse,
  type TodayEmailsResponse,
  type UserActionResponse,
  type UserActionsResponse,
} from "./api-types";

function notImplemented(operation: string): never {
  throw new Error(
    `Not implemented: ${operation} is a placeholder. Real API wiring lands in a later task.`,
  );
}

/**
 * Error thrown for any non-success auth response. Carries the backend error
 * envelope (code/message/retryable) when available, plus the HTTP status.
 * For network/CORS failures, `code` is "NETWORK_ERROR" and status is 0.
 */
export class ApiRequestError extends Error {
  code: string;
  status: number;
  retryable: boolean;

  constructor(message: string, code: string, status: number, retryable = false) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
    this.retryable = retryable;
  }
}

interface RequestOptions {
  method: "GET" | "POST";
  body?: unknown;
}

function withQuery(
  path: string,
  query?: object,
): string {
  if (!query) {
    return path;
  }

  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) {
      params.set(key, String(value));
    }
  }

  const queryString = params.toString();
  return queryString.length > 0 ? `${path}?${queryString}` : path;
}

/**
 * Low-level JSON request against the backend. Always credentialed. Parses the
 * documented { data, meta } / { error } envelope and throws ApiRequestError on
 * any error response or transport failure. Never fabricates a success result.
 */
async function request<T extends ApiResult>(
  path: string,
  { method, body }: RequestOptions,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      credentials: "include",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    // fetch rejects on network failure, DNS failure, or CORS rejection.
    throw new ApiRequestError(
      "Unable to reach the server. Check that the backend is running.",
      "NETWORK_ERROR",
      0,
      true,
    );
  }

  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok || isApiError(payload)) {
    const err = payload as ApiError | null;
    throw new ApiRequestError(
      err?.error?.message ?? `Request failed (${response.status}).`,
      err?.error?.code ?? "INVALID_REQUEST",
      response.status,
      err?.error?.retryable ?? false,
    );
  }

  return payload as T;
}

export function listMailboxes(): Promise<MailboxesResponse> {
  return request<MailboxesResponse>(API_ROUTES.mailboxes.list, {
    method: "GET",
  });
}

export function getMailbox(mailboxId: string): Promise<MailboxResponse> {
  return request<MailboxResponse>(API_ROUTES.mailboxes.byId(mailboxId), {
    method: "GET",
  });
}

export function getMailboxSyncStatus(
  mailboxId: string,
): Promise<MailboxSyncStatusResponse> {
  return request<MailboxSyncStatusResponse>(
    API_ROUTES.mailboxes.syncStatus(mailboxId),
    { method: "GET" },
  );
}

export function triggerMailboxSync(
  mailboxId: string,
): Promise<MailboxSyncResponse> {
  return request<MailboxSyncResponse>(API_ROUTES.mailboxes.sync(mailboxId), {
    method: "POST",
  });
}

export function triggerMailboxSyncJob(
  mailboxId: string,
): Promise<MailboxSyncJobResponse> {
  return request<MailboxSyncJobResponse>(
    API_ROUTES.mailboxes.syncJobs(mailboxId),
    {
      method: "POST",
    },
  );
}

export function startGmailLogin(): Promise<GmailLoginResponse> {
  return request<GmailLoginResponse>(API_ROUTES.gmailAuth.login, {
    method: "GET",
  });
}

export function disconnectGmail(): Promise<ApiResult> {
  return request<ApiResult>(API_ROUTES.gmailAuth.disconnect, {
    method: "POST",
  });
}

export function connectImapMailbox(
  payload: ImapConnectRequest,
): Promise<ImapConnectResponse> {
  return request<ImapConnectResponse>(API_ROUTES.imapAuth.connect, {
    method: "POST",
    body: payload,
  });
}

export function getTodayDigest(): Promise<DigestResponse> {
  return request<DigestResponse>(API_ROUTES.digest.today, {
    method: "GET",
  });
}

export function generateTodayDigest(): Promise<DigestResponse> {
  return request<DigestResponse>(API_ROUTES.digest.todayGenerate, {
    method: "POST",
  });
}

export function generateTodayDigestJob(): Promise<JobResponse> {
  return request<JobResponse>(API_ROUTES.digest.todayGenerateJobs, {
    method: "POST",
  });
}

export function refreshTodayDigest(): Promise<DigestResponse> {
  return request<DigestResponse>(API_ROUTES.digest.todayRefresh, {
    method: "POST",
  });
}

export function refreshTodayDigestJob(): Promise<JobResponse> {
  return request<JobResponse>(API_ROUTES.digest.todayRefreshJobs, {
    method: "POST",
  });
}

export function getDigest(digestId: string): Promise<DigestResponse> {
  return request<DigestResponse>(API_ROUTES.digest.byId(digestId), {
    method: "GET",
  });
}

export function markDigestItemDone(
  itemId: string,
): Promise<DigestItemActionResponse> {
  return request<DigestItemActionResponse>(
    API_ROUTES.digest.itemMarkDone(itemId),
    {
      method: "POST",
    },
  );
}

export function dismissDigestItem(
  itemId: string,
): Promise<DigestItemActionResponse> {
  return request<DigestItemActionResponse>(
    API_ROUTES.digest.itemDismiss(itemId),
    {
      method: "POST",
    },
  );
}

export function snoozeDigestItem(
  itemId: string,
  input: { snoozed_until: string },
): Promise<DigestItemActionResponse> {
  return request<DigestItemActionResponse>(
    API_ROUTES.digest.itemSnooze(itemId),
    {
      method: "POST",
      body: input,
    },
  );
}

export function listTodayEmails(): Promise<TodayEmailsResponse> {
  return request<TodayEmailsResponse>(API_ROUTES.emails.today, {
    method: "GET",
  });
}

export function getEmail(emailId: string): Promise<EmailResponse> {
  return request<EmailResponse>(API_ROUTES.emails.byId(emailId), {
    method: "GET",
  });
}

export function markEmailRead(emailId: string): Promise<EmailMutationResponse> {
  return request<EmailMutationResponse>(API_ROUTES.emails.markRead(emailId), {
    method: "POST",
  });
}

export function markEmailUnread(
  emailId: string,
): Promise<EmailMutationResponse> {
  return request<EmailMutationResponse>(API_ROUTES.emails.markUnread(emailId), {
    method: "POST",
  });
}

export function listActions(): Promise<UserActionsResponse> {
  return request<UserActionsResponse>(API_ROUTES.actions.list, {
    method: "GET",
  });
}

export function getAction(actionId: string): Promise<UserActionResponse> {
  return request<UserActionResponse>(API_ROUTES.actions.byId(actionId), {
    method: "GET",
  });
}

export function listJobs(query?: JobListQuery): Promise<JobsResponse> {
  return request<JobsResponse>(withQuery(API_ROUTES.jobs.list, query), {
    method: "GET",
  });
}

export function getJob(jobId: string): Promise<JobResponse> {
  return request<JobResponse>(API_ROUTES.jobs.byId(jobId), {
    method: "GET",
  });
}

export function retryJob(jobId: string): Promise<JobResponse> {
  return request<JobResponse>(API_ROUTES.jobs.retry(jobId), {
    method: "POST",
  });
}

export const apiClient = {
  auth: {
    /** POST /api/auth/register — returns the created+authenticated user. */
    register(input: {
      email: string;
      password: string;
      timezone?: string;
    }): Promise<AuthUserResponse> {
      return request<AuthUserResponse>(API_ROUTES.auth.register, {
        method: "POST",
        body: input,
      });
    },
    /** POST /api/auth/login — returns the authenticated user. */
    login(input: { email: string; password: string }): Promise<AuthUserResponse> {
      return request<AuthUserResponse>(API_ROUTES.auth.login, {
        method: "POST",
        body: input,
      });
    },
    /** POST /api/auth/logout — clears the server session + cookie. */
    logout(): Promise<ApiResult> {
      return request<ApiResult>(API_ROUTES.auth.logout, { method: "POST" });
    },
    /** GET /api/auth/me — current user; throws ApiRequestError(401) if signed out. */
    me(): Promise<AuthUserResponse> {
      return request<AuthUserResponse>(API_ROUTES.auth.me, { method: "GET" });
    },
  },

  digest: {
    today: getTodayDigest,
    generateToday: generateTodayDigest,
    generateTodayJob: generateTodayDigestJob,
    refreshToday: refreshTodayDigest,
    refreshTodayJob: refreshTodayDigestJob,
    byId: getDigest,
    markItemDone: markDigestItemDone,
    dismissItem: dismissDigestItem,
    snoozeItem: snoozeDigestItem,
  },

  emails: {
    today: listTodayEmails,
    new(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.emails.new}`);
    },
    byId: getEmail,
    markRead: markEmailRead,
    markUnread: markEmailUnread,
  },

  mailboxes: {
    list: listMailboxes,
    byId: getMailbox,
    syncStatus: getMailboxSyncStatus,
    sync: triggerMailboxSync,
    syncJob: triggerMailboxSyncJob,
  },

  gmailAuth: {
    startLogin: startGmailLogin,
    disconnect: disconnectGmail,
  },

  imapAuth: {
    connect: connectImapMailbox,
  },

  jobs: {
    list: listJobs,
    byId: getJob,
    retry: retryJob,
  },

  actions: {
    list: listActions,
    create(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.actions.create}`);
    },
    byId: getAction,
    forDigestItem(digestItemId: string): Promise<ApiResult> {
      return notImplemented(
        `GET ${API_ROUTES.actions.forDigestItem(digestItemId)}`,
      );
    },
  },

  users: {
    me(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.users.me}`);
    },
    updateMe(): Promise<ApiResult> {
      return notImplemented(`PATCH ${API_ROUTES.users.me}`);
    },
    updatePassword(): Promise<ApiResult> {
      return notImplemented(`PATCH ${API_ROUTES.users.mePassword}`);
    },
  },
} as const;
