import { API_ROUTES } from "./api-routes";
import {
  connectImapMailbox,
  disconnectGmail,
  dismissDigestItem,
  generateTodayDigest,
  generateTodayDigestJob,
  getAction,
  getDigest,
  getEmail,
  getJob,
  getMailbox,
  getMailboxSyncStatus,
  getTodayDigest,
  listJobs,
  listActions,
  listMailboxes,
  listTodayEmails,
  markEmailRead,
  markEmailUnread,
  markDigestItemDone,
  refreshTodayDigest,
  refreshTodayDigestJob,
  retryJob,
  snoozeDigestItem,
  startGmailLogin,
  triggerMailboxSync,
  triggerMailboxSyncJob,
} from "./api-client";
import type {
  ApiResult,
  DigestItemActionResponse,
  DigestMailboxRequest,
  DigestResponse,
  EmailMutationResponse,
  EmailResponse,
  TodayEmailsResponse,
  GmailLoginResponse,
  ImapConnectRequest,
  ImapConnectResponse,
  JobResponse,
  JobListQuery,
  JobsResponse,
  MailboxResponse,
  MailboxSyncJobResponse,
  MailboxSyncResponse,
  MailboxSyncStatusResponse,
  MailboxesResponse,
  UserActionResponse,
  UserActionsResponse,
} from "./api-types";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type GmailAuthRouteKeys = keyof typeof API_ROUTES.gmailAuth;
type ImapAuthRouteKeys = keyof typeof API_ROUTES.imapAuth;
type MailboxRouteKeys = keyof typeof API_ROUTES.mailboxes;
type DigestRouteKeys = keyof typeof API_ROUTES.digest;
type JobRouteKeys = keyof typeof API_ROUTES.jobs;
type ActionsRouteKeys = keyof typeof API_ROUTES.actions;

type GmailRoutesMatchResolvedContract = Assert<
  Equal<GmailAuthRouteKeys, "login" | "disconnect">
>;
type ImapRoutesMatchResolvedContract = Assert<
  Equal<ImapAuthRouteKeys, "connect">
>;
type MailboxRoutesMatchResolvedContract = Assert<
  Equal<MailboxRouteKeys, "list" | "byId" | "syncStatus" | "sync" | "syncJobs">
>;
type DigestRoutesMatchResolvedContract = Assert<
  Equal<
    DigestRouteKeys,
    | "today"
    | "todayGenerate"
    | "todayGenerateJobs"
    | "todayRefresh"
    | "todayRefreshJobs"
    | "byId"
    | "itemMarkDone"
    | "itemDismiss"
    | "itemSnooze"
  >
>;
type JobRoutesMatchResolvedContract = Assert<
  Equal<JobRouteKeys, "list" | "byId" | "retry">
>;
type ActionsRoutesMatchResolvedContract = Assert<
  Equal<ActionsRouteKeys, "list" | "create" | "byId" | "forDigestItem">
>;

const gmailLoginPath: "/api/auth/gmail/login" = API_ROUTES.gmailAuth.login;
const gmailDisconnectPath: "/api/auth/gmail/disconnect" =
  API_ROUTES.gmailAuth.disconnect;
const imapConnectPath: "/api/auth/imap/connect" = API_ROUTES.imapAuth.connect;
const mailboxesPath: "/api/mailboxes" = API_ROUTES.mailboxes.list;
const mailboxDetailPath: "/api/mailboxes/mailbox-id" =
  API_ROUTES.mailboxes.byId("mailbox-id");
const mailboxSyncStatusPath: "/api/mailboxes/mailbox-id/sync-status" =
  API_ROUTES.mailboxes.syncStatus("mailbox-id");
const mailboxSyncPath: "/api/mailboxes/mailbox-id/sync" =
  API_ROUTES.mailboxes.sync("mailbox-id");
const mailboxSyncJobsPath: "/api/mailboxes/mailbox-id/sync-jobs" =
  API_ROUTES.mailboxes.syncJobs("mailbox-id");
const todayDigestPath: "/api/digest/today" = API_ROUTES.digest.today;
const generateTodayDigestPath: "/api/digest/today/generate" =
  API_ROUTES.digest.todayGenerate;
const generateTodayDigestJobPath: "/api/digest/today/generate-jobs" =
  API_ROUTES.digest.todayGenerateJobs;
const refreshTodayDigestPath: "/api/digest/today/refresh" =
  API_ROUTES.digest.todayRefresh;
const refreshTodayDigestJobPath: "/api/digest/today/refresh-jobs" =
  API_ROUTES.digest.todayRefreshJobs;
const digestDetailPath: "/api/digest/digest-id" =
  API_ROUTES.digest.byId("digest-id");
const digestItemMarkDonePath: "/api/digest/items/item-id/mark-done" =
  API_ROUTES.digest.itemMarkDone("item-id");
const digestItemDismissPath: "/api/digest/items/item-id/dismiss" =
  API_ROUTES.digest.itemDismiss("item-id");
const digestItemSnoozePath: "/api/digest/items/item-id/snooze" =
  API_ROUTES.digest.itemSnooze("item-id");
const todayEmailsPath: "/api/emails/today" = API_ROUTES.emails.today;
const emailDetailPath: "/api/emails/email-id" =
  API_ROUTES.emails.byId("email-id");
const emailMarkReadPath: "/api/emails/email-id/mark-read" =
  API_ROUTES.emails.markRead("email-id");
const emailMarkUnreadPath: "/api/emails/email-id/mark-unread" =
  API_ROUTES.emails.markUnread("email-id");
const actionsPath: "/api/actions" = API_ROUTES.actions.list;
const actionCreatePath: "/api/actions" = API_ROUTES.actions.create;
const actionDetailPath: "/api/actions/action-id" =
  API_ROUTES.actions.byId("action-id");
const actionDigestItemPath: "/api/actions/digest-items/item-id" =
  API_ROUTES.actions.forDigestItem("item-id");
const jobsPath: "/api/jobs" = API_ROUTES.jobs.list;
const jobDetailPath: "/api/jobs/job-id" = API_ROUTES.jobs.byId("job-id");
const jobRetryPath: "/api/jobs/job-id/retry" = API_ROUTES.jobs.retry("job-id");

type ListMailboxesSignature = Assert<
  Equal<ReturnType<typeof listMailboxes>, Promise<MailboxesResponse>>
>;
type GetMailboxParameters = Assert<
  Equal<Parameters<typeof getMailbox>, [mailboxId: string]>
>;
type GetMailboxSignature = Assert<
  Equal<ReturnType<typeof getMailbox>, Promise<MailboxResponse>>
>;
type GetMailboxSyncStatusParameters = Assert<
  Equal<Parameters<typeof getMailboxSyncStatus>, [mailboxId: string]>
>;
type GetMailboxSyncStatusSignature = Assert<
  Equal<
    ReturnType<typeof getMailboxSyncStatus>,
    Promise<MailboxSyncStatusResponse>
  >
>;
type TriggerMailboxSyncParameters = Assert<
  Equal<Parameters<typeof triggerMailboxSync>, [mailboxId: string]>
>;
type TriggerMailboxSyncSignature = Assert<
  Equal<ReturnType<typeof triggerMailboxSync>, Promise<MailboxSyncResponse>>
>;
type TriggerMailboxSyncJobParameters = Assert<
  Equal<Parameters<typeof triggerMailboxSyncJob>, [mailboxId: string]>
>;
type TriggerMailboxSyncJobSignature = Assert<
  Equal<ReturnType<typeof triggerMailboxSyncJob>, Promise<MailboxSyncJobResponse>>
>;
type StartGmailLoginSignature = Assert<
  Equal<ReturnType<typeof startGmailLogin>, Promise<GmailLoginResponse>>
>;
type DisconnectGmailSignature = Assert<
  Equal<ReturnType<typeof disconnectGmail>, Promise<ApiResult>>
>;
type ConnectImapParameters = Assert<
  Equal<Parameters<typeof connectImapMailbox>, [payload: ImapConnectRequest]>
>;
type ConnectImapSignature = Assert<
  Equal<ReturnType<typeof connectImapMailbox>, Promise<ImapConnectResponse>>
>;
type GetTodayDigestParameters = Assert<
  Equal<Parameters<typeof getTodayDigest>, [mailboxId: string]>
>;
type GetTodayDigestSignature = Assert<
  Equal<ReturnType<typeof getTodayDigest>, Promise<DigestResponse>>
>;
type GenerateTodayDigestParameters = Assert<
  Equal<Parameters<typeof generateTodayDigest>, [payload: DigestMailboxRequest]>
>;
type GenerateTodayDigestSignature = Assert<
  Equal<ReturnType<typeof generateTodayDigest>, Promise<DigestResponse>>
>;
type GenerateTodayDigestJobParameters = Assert<
  Equal<Parameters<typeof generateTodayDigestJob>, [payload: DigestMailboxRequest]>
>;
type GenerateTodayDigestJobSignature = Assert<
  Equal<ReturnType<typeof generateTodayDigestJob>, Promise<JobResponse>>
>;
type RefreshTodayDigestParameters = Assert<
  Equal<Parameters<typeof refreshTodayDigest>, [payload: DigestMailboxRequest]>
>;
type RefreshTodayDigestSignature = Assert<
  Equal<ReturnType<typeof refreshTodayDigest>, Promise<DigestResponse>>
>;
type RefreshTodayDigestJobParameters = Assert<
  Equal<Parameters<typeof refreshTodayDigestJob>, [payload: DigestMailboxRequest]>
>;
type RefreshTodayDigestJobSignature = Assert<
  Equal<ReturnType<typeof refreshTodayDigestJob>, Promise<JobResponse>>
>;
type GetDigestParameters = Assert<
  Equal<Parameters<typeof getDigest>, [digestId: string]>
>;
type GetDigestSignature = Assert<
  Equal<ReturnType<typeof getDigest>, Promise<DigestResponse>>
>;
type MarkDigestItemDoneParameters = Assert<
  Equal<Parameters<typeof markDigestItemDone>, [itemId: string]>
>;
type MarkDigestItemDoneSignature = Assert<
  Equal<ReturnType<typeof markDigestItemDone>, Promise<DigestItemActionResponse>>
>;
type DismissDigestItemParameters = Assert<
  Equal<Parameters<typeof dismissDigestItem>, [itemId: string]>
>;
type DismissDigestItemSignature = Assert<
  Equal<ReturnType<typeof dismissDigestItem>, Promise<DigestItemActionResponse>>
>;
type SnoozeDigestItemParameters = Assert<
  Equal<
    Parameters<typeof snoozeDigestItem>,
    [itemId: string, input: { snoozed_until: string }]
  >
>;
type SnoozeDigestItemSignature = Assert<
  Equal<ReturnType<typeof snoozeDigestItem>, Promise<DigestItemActionResponse>>
>;
type ListTodayEmailsSignature = Assert<
  Equal<ReturnType<typeof listTodayEmails>, Promise<TodayEmailsResponse>>
>;
type GetEmailParameters = Assert<Equal<Parameters<typeof getEmail>, [emailId: string]>>;
type GetEmailSignature = Assert<
  Equal<ReturnType<typeof getEmail>, Promise<EmailResponse>>
>;
type MarkEmailReadParameters = Assert<
  Equal<Parameters<typeof markEmailRead>, [emailId: string]>
>;
type MarkEmailReadSignature = Assert<
  Equal<ReturnType<typeof markEmailRead>, Promise<EmailMutationResponse>>
>;
type MarkEmailUnreadParameters = Assert<
  Equal<Parameters<typeof markEmailUnread>, [emailId: string]>
>;
type MarkEmailUnreadSignature = Assert<
  Equal<ReturnType<typeof markEmailUnread>, Promise<EmailMutationResponse>>
>;
type ListActionsSignature = Assert<
  Equal<ReturnType<typeof listActions>, Promise<UserActionsResponse>>
>;
type GetActionParameters = Assert<
  Equal<Parameters<typeof getAction>, [actionId: string]>
>;
type GetActionSignature = Assert<
  Equal<ReturnType<typeof getAction>, Promise<UserActionResponse>>
>;
type ListJobsSignature = Assert<
  Equal<Parameters<typeof listJobs>, [query?: JobListQuery]>
>;
type ListJobsReturn = Assert<
  Equal<ReturnType<typeof listJobs>, Promise<JobsResponse>>
>;
type GetJobParameters = Assert<Equal<Parameters<typeof getJob>, [jobId: string]>>;
type GetJobSignature = Assert<
  Equal<ReturnType<typeof getJob>, Promise<JobResponse>>
>;
type RetryJobParameters = Assert<Equal<Parameters<typeof retryJob>, [jobId: string]>>;
type RetryJobSignature = Assert<
  Equal<ReturnType<typeof retryJob>, Promise<JobResponse>>
>;

type ContractAssertions = [
  GmailRoutesMatchResolvedContract,
  ImapRoutesMatchResolvedContract,
  MailboxRoutesMatchResolvedContract,
  DigestRoutesMatchResolvedContract,
  JobRoutesMatchResolvedContract,
  ActionsRoutesMatchResolvedContract,
  ListMailboxesSignature,
  GetMailboxParameters,
  GetMailboxSignature,
  GetMailboxSyncStatusParameters,
  GetMailboxSyncStatusSignature,
  TriggerMailboxSyncParameters,
  TriggerMailboxSyncSignature,
  TriggerMailboxSyncJobParameters,
  TriggerMailboxSyncJobSignature,
  StartGmailLoginSignature,
  DisconnectGmailSignature,
  ConnectImapParameters,
  ConnectImapSignature,
  GetTodayDigestParameters,
  GetTodayDigestSignature,
  GenerateTodayDigestParameters,
  GenerateTodayDigestSignature,
  GenerateTodayDigestJobParameters,
  GenerateTodayDigestJobSignature,
  RefreshTodayDigestParameters,
  RefreshTodayDigestSignature,
  RefreshTodayDigestJobParameters,
  RefreshTodayDigestJobSignature,
  GetDigestParameters,
  GetDigestSignature,
  MarkDigestItemDoneParameters,
  MarkDigestItemDoneSignature,
  DismissDigestItemParameters,
  DismissDigestItemSignature,
  SnoozeDigestItemParameters,
  SnoozeDigestItemSignature,
  ListTodayEmailsSignature,
  GetEmailParameters,
  GetEmailSignature,
  MarkEmailReadParameters,
  MarkEmailReadSignature,
  MarkEmailUnreadParameters,
  MarkEmailUnreadSignature,
  ListActionsSignature,
  GetActionParameters,
  GetActionSignature,
  ListJobsSignature,
  ListJobsReturn,
  GetJobParameters,
  GetJobSignature,
  RetryJobParameters,
  RetryJobSignature,
];

const contractAssertions: ContractAssertions = [
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
];

void contractAssertions;
void gmailLoginPath;
void gmailDisconnectPath;
void imapConnectPath;
void mailboxesPath;
void mailboxDetailPath;
void mailboxSyncStatusPath;
void mailboxSyncPath;
void mailboxSyncJobsPath;
void todayDigestPath;
void generateTodayDigestPath;
void generateTodayDigestJobPath;
void refreshTodayDigestPath;
void refreshTodayDigestJobPath;
void digestDetailPath;
void digestItemMarkDonePath;
void digestItemDismissPath;
void digestItemSnoozePath;
void todayEmailsPath;
void emailDetailPath;
void emailMarkReadPath;
void emailMarkUnreadPath;
void actionsPath;
void actionCreatePath;
void actionDetailPath;
void actionDigestItemPath;
void jobsPath;
void jobDetailPath;
void jobRetryPath;
