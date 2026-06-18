/**
 * Frontend runtime config (auth integration round).
 *
 * Only non-sensitive, public config lives here. The API base URL points at the
 * local FastAPI backend by default and can be overridden via the public env var
 * NEXT_PUBLIC_API_BASE_URL. No secrets, tokens, or server-side config are read.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
