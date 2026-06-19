import { API_ROUTES } from "./api-routes";
import {
  disconnectGmail,
  getMailbox,
  getMailboxSyncStatus,
  listMailboxes,
  startGmailLogin,
  triggerMailboxSync,
} from "./api-client";
import type {
  ApiResult,
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

type GmailRoutesMatchResolvedContract = Assert<
  Equal<GmailAuthRouteKeys, "login" | "disconnect">
>;
type MailboxRoutesMatchResolvedContract = Assert<
  Equal<MailboxRouteKeys, "list" | "byId" | "syncStatus" | "sync">
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

type ContractAssertions = [
  GmailRoutesMatchResolvedContract,
  MailboxRoutesMatchResolvedContract,
  ListMailboxesSignature,
  GetMailboxParameters,
  GetMailboxSignature,
  GetMailboxSyncStatusParameters,
  GetMailboxSyncStatusSignature,
  TriggerMailboxSyncParameters,
  TriggerMailboxSyncSignature,
  StartGmailLoginSignature,
  DisconnectGmailSignature,
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
];

void contractAssertions;
void gmailLoginPath;
void gmailDisconnectPath;
void mailboxesPath;
void mailboxDetailPath;
void mailboxSyncStatusPath;
void mailboxSyncPath;
