/**
 * Typed API client for MailMind.
 *
 * Auth routes (register/login/logout/me) are wired to the real backend in this
 * integration round. All requests send `credentials: "include"` so the browser
 * carries the HttpOnly session cookie; the frontend never reads or stores it.
 *
 * Every other route remains a safe placeholder that throws `Not implemented`.
 * Do NOT add Gmail/email/digest/AI behavior here outside a dedicated, in-scope
 * task — and wire any new route strictly per docs/api/API_DESIGN.md.
 */

import { API_BASE_URL } from "./config";
import { API_ROUTES } from "./api-routes";
import {
  isApiError,
  type ApiError,
  type ApiResult,
  type AuthUserResponse,
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
    today(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.digest.today}`);
    },
    generateToday(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.digest.todayGenerate}`);
    },
    refreshToday(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.digest.todayRefresh}`);
    },
    byId(digestId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.digest.byId(digestId)}`);
    },
  },

  emails: {
    today(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.emails.today}`);
    },
    new(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.emails.new}`);
    },
    byId(emailId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.emails.byId(emailId)}`);
    },
    markRead(emailId: string): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.emails.markRead(emailId)}`);
    },
    markUnread(emailId: string): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.emails.markUnread(emailId)}`);
    },
  },

  mailboxes: {
    list(): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.mailboxes.list}`);
    },
    byId(mailboxId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.mailboxes.byId(mailboxId)}`);
    },
    syncStatus(mailboxId: string): Promise<ApiResult> {
      return notImplemented(
        `GET ${API_ROUTES.mailboxes.syncStatus(mailboxId)}`,
      );
    },
    sync(mailboxId: string): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.mailboxes.sync(mailboxId)}`);
    },
  },

  jobs: {
    byId(jobId: string): Promise<ApiResult> {
      return notImplemented(`GET ${API_ROUTES.jobs.byId(jobId)}`);
    },
  },

  actions: {
    create(): Promise<ApiResult> {
      return notImplemented(`POST ${API_ROUTES.actions.create}`);
    },
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
