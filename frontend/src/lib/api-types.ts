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
  | "NOT_FOUND"
  | "MAILBOX_REAUTH_REQUIRED"
  | "DIGEST_NOT_READY"
  | "DIGEST_GENERATION_FAILED"
  | "PROVIDER_RATE_LIMITED"
  | "PROVIDER_SYNC_FAILED"
  | "INVALID_REQUEST"
  | "INTERNAL_ERROR"
  | "NETWORK_ERROR"
  | "BACKEND_UNAVAILABLE";

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

export type MailboxProvider = "gmail" | "imap" | "outlook" | string;

export interface MailboxCapabilities {
  can_mark_read: boolean;
  can_mark_unread: boolean;
  can_fetch_body: boolean;
  can_fetch_thread: boolean;
  can_archive: boolean;
  can_label: boolean;
  supports_oauth: boolean;
  supports_password_auth: boolean;
  supports_folders: boolean;
}

export interface ImapMailboxConfig {
  host: string;
  port: number;
  username: string;
  folder: string;
  use_ssl: boolean;
}

export interface MailboxProviderConfig {
  host?: string;
  port?: number;
  username?: string;
  default_folder?: string;
  use_ssl?: boolean;
}

export interface MailboxArchiveState {
  mailbox_id?: string | null;
  status: "not_started" | "running" | "partial" | "complete" | "failed" | "canceled" | string;
  is_complete: boolean;
  total_synced_count: number;
  batch_count: number;
  newest_synced_at: string | null;
  oldest_synced_at: string | null;
  last_error_code?: string | null;
  last_error_message?: string | null;
  started_at?: string | null;
  last_batch_started_at?: string | null;
  last_batch_completed_at?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  message?: string;
}

export type MailboxStatus =
  | "connected"
  | "disconnected"
  | "error"
  | "reauth_required"
  | "reauthorization_required"
  | string;

export interface Mailbox {
  id: string;
  provider: MailboxProvider;
  provider_preset?: string;
  email_address: string;
  account_email?: string;
  display_name?: string | null;
  provider_account_id: string;
  status: MailboxStatus;
  last_successful_sync_at: string | null;
  last_error_code?: string | null;
  last_error_message?: string | null;
  credential_status?: "present" | "missing" | string;
  provider_config?: MailboxProviderConfig;
  capabilities?: MailboxCapabilities;
  imap_config?: ImapMailboxConfig;
  sync_cursor: string | null;
  archive_state?: MailboxArchiveState;
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

export interface ImapConnectRequest {
  account_email: string;
  host: string;
  port: number;
  username: string;
  password: string;
  folder: string;
  use_ssl: boolean;
  display_name?: string;
}

export type ImapConnectResponse = ApiSuccess<{
  provider: "imap" | string;
  mailbox: Mailbox;
}>;

export type MailboxSyncState =
  | "not_started"
  | "pending_dispatch"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "dispatch_failed"
  | "unknown"
  | string;

export interface MailboxSyncJob {
  id: string;
  job_type: string;
  status: MailboxSyncState;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
}

export interface MailboxSyncStatusData {
  mailbox_id: string;
  status: MailboxSyncState;
  last_successful_sync_at: string | null;
  last_job?: MailboxSyncJob | null;
  message?: string;
}

export type MailboxSyncStatusResponse = ApiSuccess<MailboxSyncStatusData>;

export interface MailboxSyncData {
  mailbox_id: string;
  status: MailboxSyncState;
  synced_count?: number;
  job_id?: string;
  message?: string;
}

export type MailboxSyncResponse = ApiSuccess<MailboxSyncData>;

export type JobStatus =
  | "pending_dispatch"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "dispatch_failed"
  | "cancelled";

export type JobType =
  | "email_sync"
  | "email_archive_backfill"
  | "digest_generate"
  | "digest_refresh"
  | "scheduled_email_sync"
  | "scheduled_digest";

export interface Job {
  job_id: string;
  job_type: JobType | string;
  scope_type: "all" | "mailbox" | string | null;
  status: JobStatus | string;
  progress: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  mailbox_id: string | null;
  digest_id: string | null;
  celery_task_id: string | null;
  error_code: string | null;
  error_message: string | null;
  retry_count: number;
  max_retries: number;
  retry_of_job_id: string | null;
  related_resource_type: "mailbox" | "digest" | "email" | string | null;
  related_resource_id: string | null;
  result: Record<string, unknown>;
}

export interface JobData {
  job: Job;
}

export type JobResponse = ApiSuccess<JobData>;
export type MailboxSyncJobResponse = JobResponse;
export type MailboxArchiveJobResponse = ApiSuccess<{
  job: Job;
  archive_state: MailboxArchiveState;
}>;
export type MailboxArchiveStateResponse = ApiSuccess<{
  archive_state: MailboxArchiveState;
}>;

export interface JobsPagination {
  limit: number;
  offset: number;
  count: number;
  has_more: boolean;
}

export interface JobsData {
  jobs: Job[];
  pagination: JobsPagination;
}

export interface JobListQuery {
  limit?: number;
  offset?: number;
  job_type?: JobType | string;
  status?: JobStatus | string;
  created_from?: string;
  created_to?: string;
}

export type JobsResponse = ApiSuccess<JobsData, { limit?: number; offset?: number }>;

export interface GmailLoginData {
  authorization_url: string;
  provider: "gmail" | string;
}

export type GmailLoginResponse = ApiSuccess<GmailLoginData>;

export interface EmailBase {
  id: string;
  mailbox_id: string;
  provider: string;
  mailbox_email?: string | null;
  mailbox_display_name?: string | null;
  external_id: string;
  thread_id: string;
  subject: string | null;
  sender_name?: string | null;
  sender: string;
  sender_email?: string | null;
  recipients: string[];
  cc?: string[];
  snippet: string | null;
  received_at: string;
  sent_at?: string | null;
  is_read: boolean;
  is_starred?: boolean;
  has_attachments?: boolean;
  labels: string[];
  body_cache_status?: string;
  body_cache_error?: string | null;
}

export type EmailSummary = EmailBase;

export interface EmailDetail extends EmailBase {
  body_text: string | null;
  body_html?: string | null;
  body_cached_at?: string | null;
  body_cache_source?: string | null;
}

export type EmailMutation = Partial<EmailDetail> & { id: string };

export interface TodayEmailsData {
  emails: EmailSummary[];
}

export type TodayEmailsResponse = ApiSuccess<TodayEmailsData>;

export type EmailRange =
  | "today"
  | "last_7_days"
  | "last_30_days"
  | "custom"
  | "all_synced";

export interface EmailListQuery {
  limit?: number;
  offset?: number;
  is_read?: boolean;
  mailbox_id?: string;
  range?: EmailRange;
  from?: string;
  to?: string;
  q?: string;
  sort?: "received_at_desc" | "received_at_asc";
}

export interface EmailsPagination {
  limit: number;
  offset: number;
  count: number;
  total: number;
  has_more: boolean;
}

export interface EmailsData {
  emails: EmailSummary[];
  pagination: EmailsPagination;
  range: EmailRange | string;
  archive_state: MailboxArchiveState;
}

export type EmailsResponse = ApiSuccess<EmailsData>;

export interface EmailData {
  email: EmailDetail;
}

export type EmailResponse = ApiSuccess<EmailData>;
export type EmailBodyCacheResponse = EmailResponse;

export interface EmailMutationData {
  email: EmailMutation;
}

export type EmailMutationResponse = ApiSuccess<EmailMutationData>;

export type DigestStatus = "fresh" | "stale" | "failed" | string;
export type DigestTriggerSource = "manual" | "refresh" | "scheduled" | string;
export type DigestItemPriority = "high" | "medium" | "low" | string;
export type DigestScopeType = "all" | "mailbox";

export interface DigestSourceMailbox {
  id: string;
  provider: string;
  account_email: string;
  display_name: string | null;
  title: string;
}

export interface DigestMailboxSummary {
  mailbox_id: string;
  provider: string | null;
  account_email: string | null;
  title: string | null;
  summary: string;
  highlights: string[];
}

export interface DigestItem {
  id: string;
  digest_id: string;
  mailbox_id: string;
  email_id: string | null;
  item_type: string;
  section: string | null;
  title: string | null;
  summary: string | null;
  category: string;
  suggested_action: string;
  priority: DigestItemPriority;
  reason: string | null;
  deadline: string | null;
  confidence: number;
  display_order: number;
  source_mailbox: DigestSourceMailbox | null;
}

export interface Digest {
  id: string;
  scope_type: DigestScopeType;
  mailbox_id: string | null;
  digest_date: string;
  version: number;
  is_current: boolean;
  status: DigestStatus;
  trigger_source: DigestTriggerSource;
  coverage_start: string;
  coverage_end: string;
  generated_at: string;
  mail_count: number;
  new_mail_count_after_digest: number;
  overview: Record<string, unknown>;
  summary: string | null;
  mailbox_summaries: DigestMailboxSummary[];
  items: DigestItem[];
}

export interface DigestData {
  digest: Digest;
}

export type DigestResponse = ApiSuccess<DigestData>;

export interface DigestScopeRequest {
  scope_type?: DigestScopeType;
  mailbox_id?: string;
}

export interface UserAction {
  id: string;
  user_id: string;
  mailbox_id: string | null;
  digest_id: string | null;
  digest_item_id: string | null;
  email_id: string | null;
  action_type: string;
  action_status: string;
  source: string;
  provider_effect: string;
  created_at: string;
  executed_at: string | null;
  before_state?: Record<string, unknown> | null;
  after_state?: Record<string, unknown> | null;
  error_code?: string | null;
  error_message?: string | null;
}

export interface DigestItemActionData {
  action: UserAction;
}

export type DigestItemActionResponse = ApiSuccess<DigestItemActionData>;

export interface UserActionsData {
  actions: UserAction[];
}

export type UserActionsResponse = ApiSuccess<UserActionsData>;

export interface UserActionData {
  action: UserAction;
}

export type UserActionResponse = ApiSuccess<UserActionData>;
