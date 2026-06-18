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
