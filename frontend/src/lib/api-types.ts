/**
 * API response wrapper types for MailMind (T005 scaffold).
 *
 * These mirror the success/error envelope defined in docs/api/API_DESIGN.md
 * section 0. They are compile-time shapes only. Payload contents (`data`) are
 * intentionally left generic because per-page DTOs are not fully specified in
 * the API docs yet — see the T005 completion report Documentation Gaps.
 */

/** Success envelope: docs section 0.1 — { data, meta }. */
export interface ApiSuccess<TData = unknown, TMeta = Record<string, unknown>> {
  data: TData;
  meta: TMeta;
}

/**
 * Documented error codes (docs section 0). The V1-reserved AI Provider codes
 * from docs section 9 are intentionally excluded from the MVP frontend.
 */
export type ApiErrorCode =
  | "UNAUTHORIZED"
  | "FORBIDDEN"
  | "MAILBOX_REAUTH_REQUIRED"
  | "DIGEST_NOT_READY"
  | "DIGEST_GENERATION_FAILED"
  | "PROVIDER_RATE_LIMITED"
  | "PROVIDER_SYNC_FAILED"
  | "INVALID_REQUEST";

/** Error envelope: docs section 0.2 — { error: { code, message, retryable, details } }. */
export interface ApiError<TDetails = Record<string, unknown>> {
  error: {
    code: ApiErrorCode | string;
    message: string;
    retryable: boolean;
    details: TDetails;
  };
}

export type ApiResult<TData = unknown, TMeta = Record<string, unknown>> =
  | ApiSuccess<TData, TMeta>
  | ApiError;

export function isApiError(value: unknown): value is ApiError {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ApiError).error === "object"
  );
}

/**
 * Auth DTOs — derived strictly from the backend contract:
 * - app/schemas/user.py (UserRead)
 * - app/api/auth.py (register/login/me return { data: { user }, meta })
 * No fields are invented beyond what the backend returns.
 */
export interface AuthUser {
  id: string;
  email: string;
  timezone: string;
  status: string;
  created_at: string;
  updated_at: string;
}

/** Payload shape of register/login/me success responses. */
export interface AuthUserData {
  user: AuthUser;
}

export type AuthUserResponse = ApiSuccess<AuthUserData>;

export type MailboxProvider = "gmail" | string;

export type MailboxStatus =
  | "connected"
  | "disconnected"
  | "error"
  | "reauthorization_required"
  | string;

export interface Mailbox {
  id: string;
  provider: MailboxProvider;
  email_address: string;
  provider_account_id: string;
  status: MailboxStatus;
  last_successful_sync_at: string | null;
  sync_cursor: string | null;
  created_at: string;
  updated_at: string;
}

export interface MailboxesData {
  mailboxes: Mailbox[];
}

export type MailboxesResponse = ApiSuccess<MailboxesData>;

export interface MailboxData {
  mailbox: Mailbox;
}

export type MailboxResponse = ApiSuccess<MailboxData>;

export interface MailboxSyncStatusData {
  mailbox_id: string;
  status: string;
  last_successful_sync_at: string | null;
  message?: string;
}

export type MailboxSyncStatusResponse = ApiSuccess<MailboxSyncStatusData>;

export type MailboxSyncResponse = ApiSuccess<MailboxSyncStatusData>;

export interface GmailLoginData {
  authorization_url: string;
  provider: "gmail" | string;
}

export type GmailLoginResponse = ApiSuccess<GmailLoginData>;
