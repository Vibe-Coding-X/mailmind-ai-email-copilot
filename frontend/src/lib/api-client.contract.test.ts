import { API_ROUTES } from "./api-routes";
import {
  disconnectGmail,
  generateTodayDigest,
  getDigest,
  getEmail,
  getMailbox,
  getMailboxSyncStatus,
  getTodayDigest,
  listMailboxes,
  listTodayEmails,
  markEmailRead,
  markEmailUnread,
  refreshTodayDigest,
  startGmailLogin,
  triggerMailboxSync,
} from "./api-client";
import type {
  ApiResult,
  DigestResponse,
  EmailMutationResponse,
  EmailResponse,
  TodayEmailsResponse,
  GmailLoginResponse,
  MailboxResponse,
  MailboxSyncResponse,
  MailboxSyncStatusResponse,
  MailboxesResponse,
} from "./api-types";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type GmailAuthRouteKeys = keyof typeof API_ROUTES.gmailAuth;
type MailboxRouteKeys = keyof typeof API_ROUTES.mailboxes;
type DigestRouteKeys = keyof typeof API_ROUTES.digest;

type GmailRoutesMatchResolvedContract = Assert<
  Equal<GmailAuthRouteKeys, "login" | "disconnect">
>;
type MailboxRoutesMatchResolvedContract = Assert<
  Equal<MailboxRouteKeys, "list" | "byId" | "syncStatus" | "sync">
>;
type DigestRoutesMatchResolvedContract = Assert<
  Equal<DigestRouteKeys, "today" | "todayGenerate" | "todayRefresh" | "byId">
>;

const gmailLoginPath: "/api/auth/gmail/login" = API_ROUTES.gmailAuth.login;
const gmailDisconnectPath: "/api/auth/gmail/disconnect" =
  API_ROUTES.gmailAuth.disconnect;
const mailboxesPath: "/api/mailboxes" = API_ROUTES.mailboxes.list;
const mailboxDetailPath: "/api/mailboxes/mailbox-id" =
  API_ROUTES.mailboxes.byId("mailbox-id");
const mailboxSyncStatusPath: "/api/mailboxes/mailbox-id/sync-status" =
  API_ROUTES.mailboxes.syncStatus("mailbox-id");
const mailboxSyncPath: "/api/mailboxes/mailbox-id/sync" =
  API_ROUTES.mailboxes.sync("mailbox-id");
const todayDigestPath: "/api/digest/today" = API_ROUTES.digest.today;
const generateTodayDigestPath: "/api/digest/today/generate" =
  API_ROUTES.digest.todayGenerate;
const refreshTodayDigestPath: "/api/digest/today/refresh" =
  API_ROUTES.digest.todayRefresh;
const digestDetailPath: "/api/digest/digest-id" =
  API_ROUTES.digest.byId("digest-id");
const todayEmailsPath: "/api/emails/today" = API_ROUTES.emails.today;
const emailDetailPath: "/api/emails/email-id" =
  API_ROUTES.emails.byId("email-id");
const emailMarkReadPath: "/api/emails/email-id/mark-read" =
  API_ROUTES.emails.markRead("email-id");
const emailMarkUnreadPath: "/api/emails/email-id/mark-unread" =
  API_ROUTES.emails.markUnread("email-id");

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
type StartGmailLoginSignature = Assert<
  Equal<ReturnType<typeof startGmailLogin>, Promise<GmailLoginResponse>>
>;
type DisconnectGmailSignature = Assert<
  Equal<ReturnType<typeof disconnectGmail>, Promise<ApiResult>>
>;
type GetTodayDigestSignature = Assert<
  Equal<ReturnType<typeof getTodayDigest>, Promise<DigestResponse>>
>;
type GenerateTodayDigestSignature = Assert<
  Equal<ReturnType<typeof generateTodayDigest>, Promise<DigestResponse>>
>;
type RefreshTodayDigestSignature = Assert<
  Equal<ReturnType<typeof refreshTodayDigest>, Promise<DigestResponse>>
>;
type GetDigestParameters = Assert<
  Equal<Parameters<typeof getDigest>, [digestId: string]>
>;
type GetDigestSignature = Assert<
  Equal<ReturnType<typeof getDigest>, Promise<DigestResponse>>
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

type ContractAssertions = [
  GmailRoutesMatchResolvedContract,
  MailboxRoutesMatchResolvedContract,
  DigestRoutesMatchResolvedContract,
  ListMailboxesSignature,
  GetMailboxParameters,
  GetMailboxSignature,
  GetMailboxSyncStatusParameters,
  GetMailboxSyncStatusSignature,
  TriggerMailboxSyncParameters,
  TriggerMailboxSyncSignature,
  StartGmailLoginSignature,
  DisconnectGmailSignature,
  GetTodayDigestSignature,
  GenerateTodayDigestSignature,
  RefreshTodayDigestSignature,
  GetDigestParameters,
  GetDigestSignature,
  ListTodayEmailsSignature,
  GetEmailParameters,
  GetEmailSignature,
  MarkEmailReadParameters,
  MarkEmailReadSignature,
  MarkEmailUnreadParameters,
  MarkEmailUnreadSignature,
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
];

void contractAssertions;
void gmailLoginPath;
void gmailDisconnectPath;
void mailboxesPath;
void mailboxDetailPath;
void mailboxSyncStatusPath;
void mailboxSyncPath;
void todayDigestPath;
void generateTodayDigestPath;
void refreshTodayDigestPath;
void digestDetailPath;
void todayEmailsPath;
void emailDetailPath;
void emailMarkReadPath;
void emailMarkUnreadPath;
