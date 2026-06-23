"use client";

import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { InlineFeedback } from "@/components/inline-feedback";
import { MailboxProviderBadge } from "@/components/mailbox-provider-badge";
import { SettingsSection } from "@/components/settings-section";
import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  MailboxSyncCard,
  type MailboxSyncStatusView,
} from "@/components/mailbox-sync-card";
import { useJobPolling } from "@/components/jobs/use-job-polling";
import { useRecentJobs } from "@/components/jobs/use-recent-jobs";
import { useAuth } from "@/lib/auth";
import {
  ApiRequestError,
  connectImapMailbox,
  disconnectGmail,
  getMailboxSyncStatus,
  listMailboxes,
  startGmailLogin,
  triggerMailboxSync,
  triggerMailboxSyncJob,
} from "@/lib/api-client";
import type { Job, Mailbox } from "@/lib/api-types";
import { isActiveJob } from "@/lib/jobs";
import {
  formatDateTimeWithRelative,
  mailboxStateMessage,
  requiresGmailReconnect,
  syncResultMessage,
} from "@/lib/mailboxes";
import { useI18n, type TranslationKey } from "@/i18n/provider";

type MailboxLoadState =
  | "loading"
  | "loaded"
  | "not_signed_in"
  | "backend_unavailable"
  | "error";

const GMAIL_PROVIDER = "gmail";
const IMAP_PROVIDER = "imap";
const SYSTEM_AUTH_ERROR_CODE = "UNAUTHORIZED";
const GMAIL_REAUTH_ERROR_CODE = "MAILBOX_REAUTH_REQUIRED";
const STALE_QUEUED_SYNC_JOB_MS = 5 * 60 * 1000;
const STALE_RUNNING_SYNC_JOB_MS = 20 * 60 * 1000;

interface ImapFormState {
  accountEmail: string;
  displayName: string;
  host: string;
  port: string;
  username: string;
  password: string;
  folder: string;
  useSsl: boolean;
}

const initialImapForm: ImapFormState = {
  accountEmail: "",
  displayName: "",
  host: "",
  port: "993",
  username: "",
  password: "",
  folder: "INBOX",
  useSsl: true,
};

function isSystemAuthError(error: ApiRequestError): boolean {
  return error.status === 401 && error.code === SYSTEM_AUTH_ERROR_CODE;
}

function isGmailReauthError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError && error.code === GMAIL_REAUTH_ERROR_CODE
  );
}

type TFunction = (key: TranslationKey) => string;

function toErrorMessage(error: unknown, t: TFunction): string {
  if (error instanceof ApiRequestError) {
    return error.status === 0 ? t("account.backendUnavailable") : error.message;
  }

  return t("digest.genericError");
}

function toMailboxLoadState(error: unknown, t: TFunction): {
  state: MailboxLoadState;
  message: string;
} {
  if (error instanceof ApiRequestError) {
    if (isSystemAuthError(error)) {
      return {
        state: "not_signed_in",
        message: t("mailboxes.signInBeforeGmail"),
      };
    }

    if (error.status === 0) {
      return {
        state: "backend_unavailable",
        message: t("digest.backendUnavailableMessage"),
      };
    }

    return { state: "error", message: error.message };
  }

  return {
    state: "error",
    message: t("digest.genericError"),
  };
}

function isGmailMailbox(mailbox: Mailbox): boolean {
  return mailbox.provider.toLowerCase() === GMAIL_PROVIDER;
}

function isImapMailbox(mailbox: Mailbox): boolean {
  return mailbox.provider.toLowerCase() === IMAP_PROVIDER;
}

function isStaleSyncJob(job: Job, nowMs = Date.now()): boolean {
  const reference =
    job.status === "running" && job.started_at ? job.started_at : job.created_at;
  const referenceMs = new Date(reference).getTime();
  if (Number.isNaN(referenceMs)) {
    return false;
  }
  const ageMs = nowMs - referenceMs;
  if (job.status === "queued") {
    return ageMs > STALE_QUEUED_SYNC_JOB_MS;
  }
  if (job.status === "running") {
    return ageMs > STALE_RUNNING_SYNC_JOB_MS;
  }
  return false;
}

function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

function mailboxStatusTone(status: string): BadgeTone {
  switch (status) {
    case "connected":
      return "ok";
    case "reauthorization_required":
    case "reauth_required":
      return "warn";
    case "error":
      return "danger";
    case "disconnected":
      return "neutral";
    default:
      return "info";
  }
}

function actionButtonStyle(disabled: boolean): React.CSSProperties {
  return { cursor: disabled ? "not-allowed" : "pointer" };
}

function gmailOverview(
  loadState: MailboxLoadState,
  gmailMailbox: Mailbox | null,
  t: TFunction,
): { text: string; tone: BadgeTone } {
  if (loadState === "loading") {
    return { text: t("mailboxes.checkingGmail"), tone: "neutral" };
  }

  if (loadState === "not_signed_in") {
    return { text: t("account.notSignedIn"), tone: "neutral" };
  }

  if (loadState === "backend_unavailable") {
    return { text: t("account.backendUnavailable"), tone: "danger" };
  }

  if (loadState === "error") {
    return { text: t("mailboxes.stateUnavailable"), tone: "danger" };
  }

  if (gmailMailbox === null) {
    return { text: t("mailboxes.notConnectedStatus"), tone: "neutral" };
  }

  return {
    text: `Gmail ${statusLabel(gmailMailbox.status)}`,
    tone: mailboxStatusTone(gmailMailbox.status),
  };
}

function imapFormFromMailbox(mailbox: Mailbox): ImapFormState {
  return {
    accountEmail: mailbox.account_email ?? mailbox.email_address,
    displayName: mailbox.display_name ?? "",
    host: mailbox.imap_config?.host ?? "",
    port: String(mailbox.imap_config?.port ?? 993),
    username: mailbox.imap_config?.username ?? mailbox.email_address,
    password: "",
    folder: mailbox.imap_config?.folder ?? "INBOX",
    useSsl: mailbox.imap_config?.use_ssl ?? true,
  };
}

function PolledMailboxSyncCard({
  mailbox,
  syncStatus,
  syncing,
  activeJob,
  onSync,
  onJobCompleted,
  onJobFailed,
  onJobRetried,
  onJobRetryError,
}: {
  mailbox: Mailbox;
  syncStatus?: MailboxSyncStatusView;
  syncing: boolean;
  activeJob: Job | null;
  onSync: (mailboxId: string) => void;
  onJobCompleted: (job: Job) => void;
  onJobFailed: (job: Job) => void;
  onJobRetried: (job: Job) => void;
  onJobRetryError: (message: string) => void;
}) {
  const polledSyncJob = useJobPolling({
    job: activeJob,
    enabled: activeJob !== null,
    onCompleted: onJobCompleted,
    onFailed: onJobFailed,
  });

  return (
    <MailboxSyncCard
      mailbox={mailbox}
      syncStatus={syncStatus}
      syncing={syncing}
      activeJob={polledSyncJob.job}
      onSync={onSync}
      onJobRetried={onJobRetried}
      onJobRetryError={onJobRetryError}
    />
  );
}

export default function MailboxSettingsPage() {
  const { t } = useI18n();
  const { status: authStatus, refresh: refreshAuth } = useAuth();
  const [loadState, setLoadState] = useState<MailboxLoadState>("loading");
  const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
  const [syncStatuses, setSyncStatuses] = useState<
    Record<string, MailboxSyncStatusView>
  >({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connectingImap, setConnectingImap] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [imapForm, setImapForm] = useState<ImapFormState>(initialImapForm);
  const [syncingMailboxId, setSyncingMailboxId] = useState<string | null>(null);
  const [activeSyncJobsByMailboxId, setActiveSyncJobsByMailboxId] = useState<
    Record<string, Job>
  >({});
  const recentSyncJobsQuery = useMemo(
    () => ({ limit: 20, job_type: "email_sync" as const }),
    [],
  );
  const recentSyncJobs = useRecentJobs({
    enabled: authStatus === "authenticated",
    query: recentSyncJobsQuery,
  });

  const refreshSyncStatuses = useCallback(async (nextMailboxes: Mailbox[]) => {
    if (nextMailboxes.length === 0) {
      setSyncStatuses({});
      return;
    }

    setSyncStatuses(
      Object.fromEntries(
        nextMailboxes.map((mailbox) => [mailbox.id, { state: "loading" }]),
      ),
    );

    const entries = await Promise.all(
      nextMailboxes.map(async (mailbox) => {
        try {
          const response = await getMailboxSyncStatus(mailbox.id);
          return [
            mailbox.id,
            { state: "loaded", data: response.data } satisfies MailboxSyncStatusView,
          ] as const;
        } catch (error) {
          return [
            mailbox.id,
            {
              state: "error",
              message: toErrorMessage(error, t),
            } satisfies MailboxSyncStatusView,
          ] as const;
        }
      }),
    );

    setSyncStatuses(Object.fromEntries(entries));
  }, [t]);

  const loadMailboxList = useCallback(async (): Promise<boolean> => {
    setLoadState("loading");
    setLoadError(null);

    try {
      const response = await listMailboxes();
      setMailboxes(response.data.mailboxes);
      setLoadState("loaded");
      void refreshSyncStatuses(response.data.mailboxes);
      return true;
    } catch (error) {
      const resolved = toMailboxLoadState(error, t);
      setMailboxes([]);
      setSyncStatuses({});
      setLoadState(resolved.state);
      setLoadError(resolved.message);
      return false;
    }
  }, [refreshSyncStatuses, t]);

  const onSyncJobCompleted = useCallback(
    async (job: Job) => {
      if (job.related_resource_id) {
        setActiveSyncJobsByMailboxId((current) => {
          const next = { ...current };
          delete next[job.related_resource_id as string];
          return next;
        });
      }
      setActionMessage(t("mailboxes.syncJobCompleted"));
      await loadMailboxList();
    },
    [loadMailboxList, t],
  );

  const onSyncJobFailed = useCallback(
    (job: Job) => {
      if (job.related_resource_id) {
        setActiveSyncJobsByMailboxId((current) => {
          const next = { ...current };
          delete next[job.related_resource_id as string];
          return next;
        });
      }
      setActionError(job.error_message ?? t("mailboxes.syncJobFailed"));
    },
    [t],
  );

  useEffect(() => {
    const mailboxIds = new Set(mailboxes.map((mailbox) => mailbox.id));
    setActiveSyncJobsByMailboxId((current) => {
      const next = { ...current };
      for (const job of recentSyncJobs.jobs) {
        const mailboxId =
          typeof job.related_resource_id === "string" ? job.related_resource_id : "";
        if (
          isActiveJob(job) &&
          !isStaleSyncJob(job) &&
          job.related_resource_type === "mailbox" &&
          mailboxIds.has(mailboxId) &&
          next[mailboxId] === undefined
        ) {
          next[mailboxId] = job;
        }
      }
      return next;
    });
  }, [mailboxes, recentSyncJobs.jobs]);

  useEffect(() => {
    if (authStatus === "loading") {
      setLoadState("loading");
      return;
    }

    if (authStatus === "unauthenticated") {
      setMailboxes([]);
      setSyncStatuses({});
      setLoadState("not_signed_in");
      setLoadError(null);
      return;
    }

    if (authStatus === "unavailable") {
      setMailboxes([]);
      setSyncStatuses({});
      setLoadState("backend_unavailable");
      setLoadError(t("digest.backendUnavailableMessage"));
      return;
    }

    void loadMailboxList();
  }, [authStatus, loadMailboxList, t]);

  const gmailMailbox = useMemo(
    () => mailboxes.find(isGmailMailbox) ?? null,
    [mailboxes],
  );
  const imapMailboxes = useMemo(
    () => mailboxes.filter(isImapMailbox),
    [mailboxes],
  );
  const primaryImapMailbox = imapMailboxes[0] ?? null;

  useEffect(() => {
    if (primaryImapMailbox === null) {
      return;
    }
    setImapForm((current) => ({
      ...imapFormFromMailbox(primaryImapMailbox),
      password: current.password,
    }));
  }, [primaryImapMailbox]);

  const gmailStatus = gmailMailbox?.status ?? "not_connected";
  const gmailSummary = gmailOverview(loadState, gmailMailbox, t);
  const canAct = authStatus === "authenticated";
  const showConnect =
    canAct &&
    (gmailMailbox === null ||
      gmailStatus === "disconnected" ||
      gmailStatus === "reauthorization_required" ||
      gmailStatus === "reauth_required" ||
      gmailStatus === "error");
  const showDisconnect =
    canAct && gmailMailbox !== null && gmailStatus !== "disconnected";

  async function onConnectGmail() {
    setActionError(null);
    setActionMessage(null);
    setConnecting(true);

    try {
      const response = await startGmailLogin();
      if (response.data.authorization_url.trim().length === 0) {
        throw new Error("Backend did not return an authorization URL.");
      }

      window.location.href = response.data.authorization_url;
    } catch (error) {
      const resolved = toMailboxLoadState(error, t);
      if (
        resolved.state === "not_signed_in" ||
        resolved.state === "backend_unavailable"
      ) {
        setLoadState(resolved.state);
        setLoadError(resolved.message);
      }
      setActionError(toErrorMessage(error, t));
      setConnecting(false);
    }
  }

  async function onDisconnectGmail() {
    const confirmed = window.confirm(t("mailboxes.disconnectConfirm"));
    if (!confirmed) {
      return;
    }

    setActionError(null);
    setActionMessage(null);
    setDisconnecting(true);

    try {
      await disconnectGmail();
      const refreshed = await loadMailboxList();
      if (refreshed) {
        setActionMessage(t("mailboxes.disconnectedMessage"));
      }
    } catch (error) {
      const resolved = toMailboxLoadState(error, t);
      if (
        resolved.state === "not_signed_in" ||
        resolved.state === "backend_unavailable"
      ) {
        setLoadState(resolved.state);
        setLoadError(resolved.message);
      }
      setActionError(toErrorMessage(error, t));
    } finally {
      setDisconnecting(false);
    }
  }

  function updateImapForm<K extends keyof ImapFormState>(
    key: K,
    value: ImapFormState[K],
  ) {
    setImapForm((current) => ({ ...current, [key]: value }));
  }

  async function onConnectImap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActionError(null);
    setActionMessage(null);
    setConnectingImap(true);

    try {
      await connectImapMailbox({
        account_email: imapForm.accountEmail,
        display_name: imapForm.displayName || undefined,
        host: imapForm.host,
        port: Number(imapForm.port),
        username: imapForm.username,
        password: imapForm.password,
        folder: imapForm.folder,
        use_ssl: imapForm.useSsl,
      });
      setImapForm((current) => ({ ...current, password: "" }));
      const refreshed = await loadMailboxList();
      if (refreshed) {
        setActionMessage(t("mailboxes.imapConnected"));
      }
    } catch (error) {
      const resolved = toMailboxLoadState(error, t);
      if (
        resolved.state === "not_signed_in" ||
        resolved.state === "backend_unavailable"
      ) {
        setLoadState(resolved.state);
        setLoadError(resolved.message);
      }
      setActionError(toErrorMessage(error, t));
    } finally {
      setConnectingImap(false);
    }
  }

  async function onSyncMailbox(mailboxId: string) {
    setActionError(null);
    setActionMessage(null);
    setSyncingMailboxId(mailboxId);
    setActiveSyncJobsByMailboxId((current) => {
      const next = { ...current };
      delete next[mailboxId];
      return next;
    });
    setSyncStatuses((current) => ({
      ...current,
      [mailboxId]: { state: "loading" },
    }));

    try {
      const response = await triggerMailboxSyncJob(mailboxId);
      setActiveSyncJobsByMailboxId((current) => ({
        ...current,
        [mailboxId]: response.data.job,
      }));
      setActionMessage(t("mailboxes.syncJobQueued"));
      await refreshSyncStatuses(mailboxes);
    } catch (error) {
      try {
        const fallbackResponse = await triggerMailboxSync(mailboxId);
        setActionMessage(syncResultMessage(fallbackResponse.data));
        await loadMailboxList();
      } catch (fallbackError) {
        const message = toErrorMessage(fallbackError, t);
        const resolved = toMailboxLoadState(fallbackError, t);
        if (
          resolved.state === "not_signed_in" ||
          resolved.state === "backend_unavailable"
        ) {
          setLoadState(resolved.state);
          setLoadError(resolved.message);
        }
        setSyncStatuses((current) => ({
          ...current,
          [mailboxId]: { state: "error", message },
        }));
        setActionError(
          `${toErrorMessage(error, t)} ${t("mailboxes.syncFallbackFailed")} ${message}`,
        );
        if (isGmailReauthError(fallbackError)) {
          await loadMailboxList();
        }
      }
    } finally {
      setSyncingMailboxId(null);
    }
  }

  async function onRetry() {
    setActionError(null);
    setActionMessage(null);

    if (authStatus === "authenticated") {
      await loadMailboxList();
      return;
    }

    await refreshAuth();
  }

  function renderMailboxList() {
    if (loadState === "loading") {
      return <Skeleton lines={4} widths={["42%", "80%", "65%", "52%"]} />;
    }

    if (loadState === "not_signed_in") {
      return (
        <EmptyState
          title={t("account.notSignedIn")}
          hint={t("mailboxes.signInHint")}
          action={<a href="/login">{t("account.signIn")}</a>}
        />
      );
    }

    if (loadState === "backend_unavailable") {
      return (
        <EmptyState
          title={t("account.backendUnavailable")}
          hint={loadError ?? t("mailboxes.unableToReachFallback")}
          action={
            <button
              type="button"
              className="mm-btn"
              onClick={onRetry}
              style={actionButtonStyle(false)}
            >
              {t("common.retry")}
            </button>
          }
        />
      );
    }

    if (loadState === "error") {
      return (
        <EmptyState
          title={t("mailboxes.errorTitle")}
          hint={loadError ?? t("mailboxes.backendErrorFallback")}
          action={
            <button
              type="button"
              className="mm-btn"
              onClick={onRetry}
              style={actionButtonStyle(false)}
            >
              {t("common.retry")}
            </button>
          }
        />
      );
    }

    if (mailboxes.length === 0) {
      return (
        <EmptyState
          title={t("mailboxes.notConnectedTitle")}
          hint={t("mailboxes.notConnectedHint")}
        />
      );
    }

    return (
      <div className="mm-stack" style={{ gap: 0 }}>
        {mailboxes.map((mailbox, index) => (
          <div
            key={mailbox.id}
            style={{
              borderTop: index === 0 ? 0 : "1px solid var(--mm-border)",
              padding: index === 0 ? "0 0 16px" : "16px 0",
            }}
          >
            <div className="mm-spread" style={{ alignItems: "flex-start" }}>
              <div>
                <h3 style={{ fontSize: 14 }}>{mailbox.email_address}</h3>
                <p className="mm-muted" style={{ fontSize: 12, marginTop: 2 }}>
                  <MailboxProviderBadge provider={mailbox.provider} />
                </p>
                <p className="mm-muted" style={{ fontSize: 12, marginTop: 6 }}>
                  {mailboxStateMessage(mailbox)}
                </p>
              </div>
              <Badge tone={mailboxStatusTone(mailbox.status)} dot>
                {statusLabel(mailbox.status)}
              </Badge>
            </div>

            <div style={{ marginTop: 14 }}>
              <PolledMailboxSyncCard
                mailbox={mailbox}
                syncStatus={syncStatuses[mailbox.id]}
                syncing={syncingMailboxId === mailbox.id}
                activeJob={activeSyncJobsByMailboxId[mailbox.id] ?? null}
                onSync={(mailboxId) => void onSyncMailbox(mailboxId)}
                onJobCompleted={(job) => void onSyncJobCompleted(job)}
                onJobFailed={onSyncJobFailed}
                onJobRetried={(job) => {
                  setActionError(null);
                  setActionMessage(t("mailboxes.syncJobQueued"));
                  if (job.related_resource_id) {
                    setActiveSyncJobsByMailboxId((current) => ({
                      ...current,
                      [job.related_resource_id as string]: job,
                    }));
                  }
                }}
                onJobRetryError={(message) => setActionError(message)}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const connectDisabled =
    !canAct ||
    connecting ||
    connectingImap ||
    disconnecting ||
    loadState === "loading" ||
    loadState === "backend_unavailable";
  const disconnectDisabled = !canAct || connecting || connectingImap || disconnecting;
  const imapConnectDisabled =
    !canAct ||
    connecting ||
    connectingImap ||
    disconnecting ||
    loadState === "loading" ||
    loadState === "backend_unavailable";

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title={t("mailboxes.pageTitle")}
        description={t("mailboxes.pageDescription")}
      >
        <SettingsSection
          title={t("mailboxes.title")}
          description={t("mailboxes.description")}
        >
          <div className="mm-spread" style={{ alignItems: "flex-start" }}>
            <div className="mm-stack" style={{ gap: 8 }}>
              <div>
                <Badge tone={gmailSummary.tone} dot>
                  {gmailSummary.text}
                </Badge>
              </div>
              {gmailMailbox ? (
                <div style={{ fontSize: 13 }}>
                  <div>{gmailMailbox.email_address}</div>
                  <div className="mm-muted" style={{ fontSize: 12, marginTop: 2 }}>
                    Updated {formatDateTimeWithRelative(gmailMailbox.updated_at)}
                  </div>
                  <p className="mm-muted" style={{ fontSize: 12, marginTop: 6 }}>
                    {mailboxStateMessage(gmailMailbox)}
                  </p>
                </div>
              ) : (
                <p className="mm-muted" style={{ fontSize: 13 }}>
                  {loadState === "not_signed_in"
                    ? t("mailboxes.signInBeforeGmail")
                    : loadState === "backend_unavailable"
                      ? t("mailboxes.stateBackendUnavailable")
                      : t("mailboxes.noGmailReturned")}
                </p>
              )}
            </div>

            <div className="mm-row" style={{ justifyContent: "flex-end" }}>
              {showConnect ? (
                <button
                  type="button"
                  className="mm-btn mm-btn--primary"
                  onClick={onConnectGmail}
                  disabled={connectDisabled}
                  aria-disabled={connectDisabled}
                  style={actionButtonStyle(connectDisabled)}
                >
                  {connecting
                    ? t("mailboxes.startingGmail")
                    : gmailMailbox && requiresGmailReconnect(gmailMailbox)
                      ? t("mailboxes.reconnectGmail")
                      : t("mailboxes.connectGmail")}
                </button>
              ) : null}

              {showDisconnect ? (
                <button
                  type="button"
                  className="mm-btn"
                  onClick={onDisconnectGmail}
                  disabled={disconnectDisabled}
                  aria-disabled={disconnectDisabled}
                  style={actionButtonStyle(disconnectDisabled)}
                >
                  {disconnecting ? t("mailboxes.disconnecting") : t("mailboxes.disconnectGmail")}
                </button>
              ) : null}
            </div>
          </div>

          {actionError ? (
            <div style={{ marginTop: 14 }}>
              <InlineFeedback tone="danger" title={t("mailboxes.actionError")}>
                {actionError}
              </InlineFeedback>
            </div>
          ) : null}

          {actionMessage ? (
            <div style={{ marginTop: 14 }}>
              <InlineFeedback tone="success" title={t("mailboxes.updated")}>
                {actionMessage}
              </InlineFeedback>
            </div>
          ) : null}
        </SettingsSection>

        <SettingsSection
          title={t("mailboxes.imapTitle")}
          description={t("mailboxes.imapDescription")}
        >
          <form className="mm-stack" style={{ gap: 14 }} onSubmit={onConnectImap}>
            <div className="mm-spread" style={{ alignItems: "center" }}>
              <div>
                <Badge tone={imapMailboxes.length > 0 ? "ok" : "neutral"} dot>
                  {imapMailboxes.length > 0
                    ? t("mailboxes.imapConnectedStatus")
                    : t("mailboxes.imapNotConnectedStatus")}
                </Badge>
              </div>
              <button
                type="submit"
                className="mm-btn mm-btn--primary"
                disabled={imapConnectDisabled}
                aria-disabled={imapConnectDisabled}
                style={actionButtonStyle(imapConnectDisabled)}
              >
                {connectingImap
                  ? t("mailboxes.connectingImap")
                  : primaryImapMailbox
                    ? t("mailboxes.updateImap")
                    : t("mailboxes.connectImap")}
              </button>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: 12,
              }}
            >
              <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                <span>{t("mailboxes.imapAccountEmail")}</span>
                <input
                  className="mm-input"
                  type="email"
                  value={imapForm.accountEmail}
                  onChange={(event) => updateImapForm("accountEmail", event.target.value)}
                  disabled={imapConnectDisabled}
                  required
                />
              </label>
              <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                <span>{t("mailboxes.imapDisplayName")}</span>
                <input
                  className="mm-input"
                  type="text"
                  value={imapForm.displayName}
                  onChange={(event) => updateImapForm("displayName", event.target.value)}
                  disabled={imapConnectDisabled}
                />
              </label>
              <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                <span>{t("mailboxes.imapHost")}</span>
                <input
                  className="mm-input"
                  type="text"
                  value={imapForm.host}
                  onChange={(event) => updateImapForm("host", event.target.value)}
                  disabled={imapConnectDisabled}
                  required
                />
              </label>
              <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                <span>{t("mailboxes.imapPort")}</span>
                <input
                  className="mm-input"
                  type="number"
                  min={1}
                  max={65535}
                  value={imapForm.port}
                  onChange={(event) => updateImapForm("port", event.target.value)}
                  disabled={imapConnectDisabled}
                  required
                />
              </label>
              <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                <span>{t("mailboxes.imapUsername")}</span>
                <input
                  className="mm-input"
                  type="text"
                  value={imapForm.username}
                  onChange={(event) => updateImapForm("username", event.target.value)}
                  disabled={imapConnectDisabled}
                  required
                />
              </label>
              <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                <span>{t("mailboxes.imapPassword")}</span>
                <input
                  className="mm-input"
                  type="password"
                  value={imapForm.password}
                  onChange={(event) => updateImapForm("password", event.target.value)}
                  disabled={imapConnectDisabled}
                  required
                />
              </label>
              <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                <span>{t("mailboxes.imapFolder")}</span>
                <input
                  className="mm-input"
                  type="text"
                  value={imapForm.folder}
                  onChange={(event) => updateImapForm("folder", event.target.value)}
                  disabled={imapConnectDisabled}
                  required
                />
              </label>
              <label
                className="mm-row"
                style={{ alignItems: "center", gap: 8, fontSize: 13, paddingTop: 24 }}
              >
                <input
                  type="checkbox"
                  checked={imapForm.useSsl}
                  onChange={(event) => updateImapForm("useSsl", event.target.checked)}
                  disabled={imapConnectDisabled}
                />
                <span>{t("mailboxes.imapUseSsl")}</span>
              </label>
            </div>
          </form>
        </SettingsSection>

        <SettingsSection
          title={t("mailboxes.listTitle")}
          description={
            mailboxes.length > 1
              ? t("mailboxes.listMultiDescription")
              : t("mailboxes.listDescription")
          }
        >
          {renderMailboxList()}
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
