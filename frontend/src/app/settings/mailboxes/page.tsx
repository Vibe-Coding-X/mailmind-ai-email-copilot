"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";

import { AppShell } from "@/components/app-shell";
import { EmptyState } from "@/components/empty-state";
import { InlineFeedback } from "@/components/inline-feedback";
import { useJobPolling } from "@/components/jobs/use-job-polling";
import { useRecentJobs } from "@/components/jobs/use-recent-jobs";
import {
  MailboxSyncCard,
  type MailboxSyncStatusView,
} from "@/components/mailbox-sync-card";
import { MailboxProviderBadge } from "@/components/mailbox-provider-badge";
import { PageFrame } from "@/components/page-frame";
import { SettingsSection } from "@/components/settings-section";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useI18n, type TranslationKey } from "@/i18n/provider";
import {
  ApiRequestError,
  connectImapMailbox,
  getMailboxSyncStatus,
  listMailboxes,
  startGmailLogin,
  triggerMailboxArchiveJob,
  triggerMailboxSync,
  triggerMailboxSyncJob,
} from "@/lib/api-client";
import type { Job, Mailbox, MailboxArchiveState } from "@/lib/api-types";
import { isActiveJob } from "@/lib/jobs";
import {
  formatDateTimeWithRelative,
  mailboxStateMessage,
  requiresGmailReconnect,
  syncResultMessage,
} from "@/lib/mailboxes";

type MailboxLoadState =
  | "loading"
  | "loaded"
  | "not_signed_in"
  | "backend_unavailable"
  | "error";

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

const GMAIL_PROVIDER = "gmail";
const IMAP_PROVIDER = "imap";
const SYSTEM_AUTH_ERROR_CODE = "UNAUTHORIZED";
const GMAIL_REAUTH_ERROR_CODE = "MAILBOX_REAUTH_REQUIRED";
const STALE_QUEUED_SYNC_JOB_MS = 5 * 60 * 1000;
const STALE_RUNNING_SYNC_JOB_MS = 20 * 60 * 1000;

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

const imapPresets = [
  { key: "qq", label: "QQ Mail", host: "imap.qq.com" },
  { key: "163", label: "163 Mail", host: "imap.163.com" },
  { key: "gmail_imap", label: "Gmail IMAP", host: "imap.gmail.com" },
  { key: "custom", label: "Custom", host: "" },
] as const;

type TFunction = (key: TranslationKey) => string;
type ModuleFeedback = {
  tone: "info" | "success" | "warning" | "danger";
  title: string;
  message: string;
};

function isSystemAuthError(error: ApiRequestError): boolean {
  return error.status === 401 && error.code === SYSTEM_AUTH_ERROR_CODE;
}

function isGmailReauthError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError && error.code === GMAIL_REAUTH_ERROR_CODE
  );
}

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

  return { state: "error", message: t("digest.genericError") };
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

function archiveStatusTone(status: string): BadgeTone {
  switch (status) {
    case "complete":
      return "ok";
    case "failed":
      return "danger";
    case "not_started":
      return "neutral";
    case "running":
    case "partial":
      return "info";
    case "canceled":
      return "warn";
    default:
      return "neutral";
  }
}

function archiveButtonLabel(
  state: MailboxArchiveState | undefined,
  t: TFunction,
): string {
  switch (state?.status) {
    case "partial":
      return t("mailboxes.resumeArchive");
    case "failed":
      return t("mailboxes.retryArchive");
    case "running":
      return t("mailboxes.archiveRunningButton");
    case "complete":
      return t("mailboxes.archiveCompleteButton");
    default:
      return t("mailboxes.startFullArchive");
  }
}

function archiveStateOrDefault(mailbox: Mailbox): MailboxArchiveState {
  return (
    mailbox.archive_state ?? {
      mailbox_id: mailbox.id,
      status: "not_started",
      is_complete: false,
      total_synced_count: 0,
      batch_count: 0,
      newest_synced_at: null,
      oldest_synced_at: null,
      message: undefined,
    }
  );
}

function actionButtonStyle(disabled: boolean): CSSProperties {
  return { cursor: disabled ? "not-allowed" : "pointer" };
}

function isGmailMailbox(mailbox: Mailbox): boolean {
  return mailbox.provider.toLowerCase() === GMAIL_PROVIDER;
}

function isImapMailbox(mailbox: Mailbox): boolean {
  return mailbox.provider.toLowerCase() === IMAP_PROVIDER;
}

function mailboxTitle(mailbox: Mailbox): string {
  return mailbox.display_name || mailbox.account_email || mailbox.email_address;
}

function imapCredentialText(mailbox: Mailbox): string {
  return mailbox.credential_status === "present" ? "Credential: saved" : "Credential: missing";
}

function imapConnectionText(mailbox: Mailbox): string | null {
  const config = mailbox.provider_config ?? mailbox.imap_config;
  if (!config?.host) {
    return null;
  }
  const port = config.port ?? 993;
  const useSsl = config.use_ssl ? " SSL" : "";
  return `Host: ${config.host}:${port}${useSsl}`;
}

function syncStatusViewFromJob(
  job: Job,
  current: MailboxSyncStatusView | undefined,
): MailboxSyncStatusView {
  const previousLoaded = current?.state === "loaded" ? current.data : null;
  const mailboxId =
    typeof job.related_resource_id === "string"
      ? job.related_resource_id
      : previousLoaded?.mailbox_id ?? "";
  const lastSuccessfulSyncAt =
    job.status === "completed"
      ? job.finished_at ?? previousLoaded?.last_successful_sync_at ?? new Date().toISOString()
      : previousLoaded?.last_successful_sync_at ?? null;

  return {
    state: "loaded",
    data: {
      mailbox_id: mailboxId,
      status: job.status,
      last_successful_sync_at: lastSuccessfulSyncAt,
      last_job: {
        id: job.job_id,
        job_type: job.job_type,
        status: job.status,
        started_at: job.started_at,
        finished_at: job.finished_at,
        error_message: job.error_message,
      },
    },
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
  const [loadState, setLoadState] = useState<MailboxLoadState>("loading");
  const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
  const [syncStatuses, setSyncStatuses] = useState<
    Record<string, MailboxSyncStatusView>
  >({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [addFeedback, setAddFeedback] = useState<ModuleFeedback | null>(null);
  const [mailboxFeedbackById, setMailboxFeedbackById] = useState<
    Record<string, ModuleFeedback | undefined>
  >({});
  const [connectingGmail, setConnectingGmail] = useState(false);
  const [connectingImap, setConnectingImap] = useState(false);
  const [showImapForm, setShowImapForm] = useState(false);
  const [showImapPassword, setShowImapPassword] = useState(false);
  const [imapForm, setImapForm] = useState<ImapFormState>(initialImapForm);
  const [syncingMailboxId, setSyncingMailboxId] = useState<string | null>(null);
  const [archivingMailboxId, setArchivingMailboxId] = useState<string | null>(null);
  const [activeSyncJobsByMailboxId, setActiveSyncJobsByMailboxId] = useState<
    Record<string, Job>
  >({});
  const recentSyncJobsQuery = useMemo(
    () => ({ limit: 20, job_type: "email_sync" as const }),
    [],
  );
  const recentSyncJobs = useRecentJobs({
    enabled: loadState === "loaded",
    query: recentSyncJobsQuery,
  });

  const canAct = loadState === "loaded";
  const busy = connectingGmail || connectingImap;

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

  useEffect(() => {
    void loadMailboxList();
  }, [loadMailboxList]);

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

  const onSyncJobCompleted = useCallback(
    async (job: Job) => {
      if (job.related_resource_id) {
        setActiveSyncJobsByMailboxId((current) => {
          const next = { ...current };
          delete next[job.related_resource_id as string];
          return next;
        });
        setSyncStatuses((current) => ({
          ...current,
          [job.related_resource_id as string]: syncStatusViewFromJob(
            job,
            current[job.related_resource_id as string],
          ),
        }));
      }
      if (job.related_resource_id) {
        setMailboxFeedbackById((current) => ({
          ...current,
          [job.related_resource_id as string]: {
            tone: "success",
            title: t("mailboxes.syncJobTitle"),
            message: t("mailboxes.syncJobCompleted"),
          },
        }));
      }
      await Promise.all([loadMailboxList(), recentSyncJobs.refresh()]);
    },
    [loadMailboxList, recentSyncJobs, t],
  );

  const onSyncJobFailed = useCallback(
    async (job: Job) => {
      if (job.related_resource_id) {
        setActiveSyncJobsByMailboxId((current) => {
          const next = { ...current };
          delete next[job.related_resource_id as string];
          return next;
        });
        setSyncStatuses((current) => ({
          ...current,
          [job.related_resource_id as string]: syncStatusViewFromJob(
            job,
            current[job.related_resource_id as string],
          ),
        }));
      }
      if (job.related_resource_id) {
        setMailboxFeedbackById((current) => ({
          ...current,
          [job.related_resource_id as string]: {
            tone: "danger",
            title: t("mailboxes.syncJobTitle"),
            message: job.error_message ?? t("mailboxes.syncJobFailed"),
          },
        }));
      }
      await recentSyncJobs.refresh();
    },
    [recentSyncJobs, t],
  );

  async function onStartGmail() {
    setAddFeedback(null);
    setConnectingGmail(true);

    try {
      const response = await startGmailLogin();
      if (response.data.authorization_url.trim().length === 0) {
        throw new Error("Backend did not return an authorization URL.");
      }

      window.location.href = response.data.authorization_url;
    } catch (error) {
      setAddFeedback({
        tone: "danger",
        title: t("mailboxes.actionError"),
        message: toErrorMessage(error, t),
      });
      setConnectingGmail(false);
    }
  }

  function updateImapForm<K extends keyof ImapFormState>(
    key: K,
    value: ImapFormState[K],
  ) {
    setImapForm((current) => ({ ...current, [key]: value }));
  }

  function applyPreset(host: string) {
    setImapForm((current) => ({
      ...current,
      host,
      port: "993",
      useSsl: true,
      folder: current.folder || "INBOX",
    }));
  }

  async function onConnectImap(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAddFeedback(null);
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
      setImapForm(initialImapForm);
      const refreshed = await loadMailboxList();
      if (refreshed) {
        setAddFeedback({
          tone: "success",
          title: t("mailboxes.updated"),
          message: t("mailboxes.imapConnected"),
        });
      }
    } catch (error) {
      setAddFeedback({
        tone: "danger",
        title: t("mailboxes.actionError"),
        message: toErrorMessage(error, t),
      });
    } finally {
      setConnectingImap(false);
    }
  }

  async function onSyncMailbox(mailboxId: string) {
    setMailboxFeedbackById((current) => ({ ...current, [mailboxId]: undefined }));
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
      setMailboxFeedbackById((current) => ({
        ...current,
        [mailboxId]: {
          tone: "info",
          title: t("mailboxes.syncJobTitle"),
          message: t("mailboxes.syncJobQueued"),
        },
      }));
      await refreshSyncStatuses(mailboxes);
    } catch (error) {
      try {
        const fallbackResponse = await triggerMailboxSync(mailboxId);
        setMailboxFeedbackById((current) => ({
          ...current,
          [mailboxId]: {
            tone: "success",
            title: t("mailboxes.syncJobTitle"),
            message: syncResultMessage(fallbackResponse.data),
          },
        }));
        await loadMailboxList();
      } catch (fallbackError) {
        const message = toErrorMessage(fallbackError, t);
        setSyncStatuses((current) => ({
          ...current,
          [mailboxId]: { state: "error", message },
        }));
        setMailboxFeedbackById((current) => ({
          ...current,
          [mailboxId]: {
            tone: "danger",
            title: t("mailboxes.syncJobTitle"),
            message: `${toErrorMessage(error, t)} ${t("mailboxes.syncFallbackFailed")} ${message}`,
          },
        }));
        if (isGmailReauthError(fallbackError)) {
          await loadMailboxList();
        }
      }
    } finally {
      setSyncingMailboxId(null);
    }
  }

  async function onArchiveMailbox(mailbox: Mailbox) {
    const confirmed = window.confirm(t("mailboxes.archiveConfirm"));
    if (!confirmed) {
      return;
    }

    setMailboxFeedbackById((current) => ({ ...current, [mailbox.id]: undefined }));
    setArchivingMailboxId(mailbox.id);

    try {
      await triggerMailboxArchiveJob(mailbox.id);
      setMailboxFeedbackById((current) => ({
        ...current,
        [mailbox.id]: {
          tone: "info",
          title: t("mailboxes.localArchive"),
          message: t("mailboxes.archiveJobQueued"),
        },
      }));
      await Promise.all([loadMailboxList(), recentSyncJobs.refresh()]);
    } catch (error) {
      setMailboxFeedbackById((current) => ({
        ...current,
        [mailbox.id]: {
          tone: "danger",
          title: t("mailboxes.localArchive"),
          message: toErrorMessage(error, t),
        },
      }));
    } finally {
      setArchivingMailboxId(null);
    }
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

    if (loadState === "backend_unavailable" || loadState === "error") {
      return (
        <EmptyState
          title={
            loadState === "backend_unavailable"
              ? t("account.backendUnavailable")
              : t("mailboxes.errorTitle")
          }
          hint={loadError ?? t("mailboxes.backendErrorFallback")}
          action={
            <button
              type="button"
              className="mm-btn"
              onClick={() => void loadMailboxList()}
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
        {mailboxes.map((mailbox, index) => {
          const imapText = isImapMailbox(mailbox) ? imapConnectionText(mailbox) : null;
          const archiveState = archiveStateOrDefault(mailbox);
          const archiveDisabled =
            !canAct ||
            busy ||
            archivingMailboxId === mailbox.id ||
            archiveState.status === "running" ||
            archiveState.status === "complete";
          const mailboxFeedback = mailboxFeedbackById[mailbox.id];
          return (
            <div
              key={mailbox.id}
              style={{
                borderTop: index === 0 ? 0 : "1px solid var(--mm-border)",
                padding: index === 0 ? "0 0 16px" : "16px 0",
              }}
            >
              <div className="mm-spread" style={{ alignItems: "flex-start" }}>
                <div>
                  <h3 style={{ fontSize: 14 }}>{mailboxTitle(mailbox)}</h3>
                  <div className="mm-row" style={{ gap: 8, marginTop: 6 }}>
                    <MailboxProviderBadge provider={mailbox.provider} />
                    <Badge tone={mailboxStatusTone(mailbox.status)} dot>
                      {statusLabel(mailbox.status)}
                    </Badge>
                  </div>
                  <p className="mm-muted" style={{ fontSize: 12, marginTop: 8 }}>
                    {mailbox.email_address}
                  </p>
                  {imapText ? (
                    <p className="mm-muted" style={{ fontSize: 12, marginTop: 4 }}>
                      {imapText}
                    </p>
                  ) : null}
                  {isImapMailbox(mailbox) ? (
                    <p className="mm-muted" style={{ fontSize: 12, marginTop: 4 }}>
                      {imapCredentialText(mailbox)}
                    </p>
                  ) : null}
                  <p className="mm-muted" style={{ fontSize: 12, marginTop: 6 }}>
                    {mailboxStateMessage(mailbox)}
                  </p>
                  <p className="mm-muted" style={{ fontSize: 12, marginTop: 4 }}>
                    Updated {formatDateTimeWithRelative(mailbox.updated_at)}
                  </p>
                </div>

                <div className="mm-row" style={{ justifyContent: "flex-end" }}>
                  {isGmailMailbox(mailbox) ? (
                    <button
                      type="button"
                      className="mm-btn"
                      onClick={() => void onStartGmail()}
                      disabled={!canAct || busy}
                      aria-disabled={!canAct || busy}
                      style={actionButtonStyle(!canAct || busy)}
                    >
                      {requiresGmailReconnect(mailbox)
                        ? t("mailboxes.reconnectGmail")
                        : t("mailboxes.reconnect")}
                    </button>
                  ) : null}
                  {isImapMailbox(mailbox) ? (
                    <>
                      <button
                        type="button"
                        className="mm-btn"
                        disabled
                        aria-disabled
                        title={t("mailboxes.editUnavailable")}
                        style={actionButtonStyle(true)}
                      >
                        {t("mailboxes.editSettings")}
                      </button>
                      <button
                        type="button"
                        className="mm-btn"
                        disabled
                        aria-disabled
                        title={t("mailboxes.updatePasswordUnavailable")}
                        style={actionButtonStyle(true)}
                      >
                        {t("mailboxes.updatePassword")}
                      </button>
                    </>
                  ) : null}
                </div>
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
                    if (job.related_resource_id) {
                      setActiveSyncJobsByMailboxId((current) => ({
                        ...current,
                        [job.related_resource_id as string]: job,
                      }));
                      setMailboxFeedbackById((current) => ({
                        ...current,
                        [job.related_resource_id as string]: {
                          tone: "info",
                          title: t("mailboxes.syncJobTitle"),
                          message: t("mailboxes.syncJobQueued"),
                        },
                      }));
                    }
                  }}
                  onJobRetryError={(message) =>
                    setMailboxFeedbackById((current) => ({
                      ...current,
                      [mailbox.id]: {
                        tone: "danger",
                        title: t("mailboxes.syncJobTitle"),
                        message,
                      },
                    }))
                  }
                />
              </div>

              {mailboxFeedback ? (
                <div style={{ marginTop: 10 }}>
                  <InlineFeedback
                    tone={mailboxFeedback.tone}
                    title={mailboxFeedback.title}
                  >
                    {mailboxFeedback.message}
                  </InlineFeedback>
                </div>
              ) : null}

              <div
                style={{
                  border: "1px solid var(--mm-border)",
                  borderRadius: 8,
                  marginTop: 14,
                  padding: 14,
                }}
              >
                <div className="mm-spread" style={{ alignItems: "flex-start" }}>
                  <div>
                    <div className="mm-card-title" style={{ marginBottom: 6 }}>
                      {t("mailboxes.localArchive")}
                    </div>
                    <div className="mm-row" style={{ gap: 8 }}>
                      <Badge tone={archiveStatusTone(archiveState.status)} dot>
                        {statusLabel(archiveState.status)}
                      </Badge>
                      <span className="mm-muted" style={{ fontSize: 12 }}>
                        {t("mailboxes.archiveSynced")
                          .replace(
                            "{{count}}",
                            String(archiveState.total_synced_count ?? 0),
                          )
                          .replace("{{batches}}", String(archiveState.batch_count ?? 0))}
                      </span>
                    </div>
                    <div
                      className="mm-grid mm-grid-3"
                      style={{ marginTop: 12, fontSize: 13 }}
                    >
                      <ArchiveDatum
                        label={t("mailboxes.archiveNewest")}
                        value={formatArchiveValue(archiveState.newest_synced_at)}
                      />
                      <ArchiveDatum
                        label={t("mailboxes.archiveOldest")}
                        value={formatArchiveValue(archiveState.oldest_synced_at)}
                      />
                      <ArchiveDatum
                        label={t("mailboxes.archiveUpdated")}
                        value={formatArchiveValue(
                          archiveState.completed_at ??
                            archiveState.last_batch_completed_at ??
                            archiveState.started_at ??
                            null,
                        )}
                      />
                    </div>
                    <p className="mm-muted" style={{ fontSize: 12, marginTop: 10 }}>
                      {archiveHint(archiveState, t)}
                    </p>
                  </div>
                  <button
                    type="button"
                    className="mm-btn"
                    onClick={() => void onArchiveMailbox(mailbox)}
                    disabled={archiveDisabled}
                    aria-disabled={archiveDisabled}
                    style={actionButtonStyle(archiveDisabled)}
                  >
                    {archivingMailboxId === mailbox.id
                      ? t("common.working")
                      : archiveButtonLabel(archiveState, t)}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  const addDisabled =
    busy || loadState === "loading" || loadState === "backend_unavailable";

  return (
    <AppShell>
      <PageFrame
        title={t("mailboxes.pageTitle")}
        description={t("mailboxes.pageDescription")}
      >
        <SettingsSection
          title={t("mailboxes.connectedTitle")}
          description={t("mailboxes.connectedDescription")}
        >
          {renderMailboxList()}
        </SettingsSection>

        <SettingsSection
          title={t("mailboxes.addTitle")}
          description={t("mailboxes.addDescription")}
        >
          {addFeedback ? (
            <div style={{ marginBottom: 12 }}>
              <InlineFeedback tone={addFeedback.tone} title={addFeedback.title}>
                {addFeedback.message}
              </InlineFeedback>
            </div>
          ) : null}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 12,
            }}
          >
            <div
              style={{
                border: "1px solid var(--mm-border)",
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div className="mm-spread" style={{ alignItems: "flex-start" }}>
                <div>
                  <MailboxProviderBadge provider="gmail" />
                  <p className="mm-muted" style={{ fontSize: 13, marginTop: 8 }}>
                    {t("mailboxes.addGmailHint")}
                  </p>
                </div>
                <button
                  type="button"
                  className="mm-btn mm-btn--primary"
                  onClick={() => void onStartGmail()}
                  disabled={addDisabled}
                  aria-disabled={addDisabled}
                  style={actionButtonStyle(addDisabled)}
                >
                  {connectingGmail ? t("mailboxes.startingGmail") : t("mailboxes.addGmail")}
                </button>
              </div>
            </div>

            <div
              style={{
                border: "1px solid var(--mm-border)",
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div className="mm-spread" style={{ alignItems: "flex-start" }}>
                <div>
                  <MailboxProviderBadge provider="imap" />
                  <p className="mm-muted" style={{ fontSize: 13, marginTop: 8 }}>
                    {t("mailboxes.addImapHint")}
                  </p>
                </div>
                <button
                  type="button"
                  className="mm-btn mm-btn--primary"
                  onClick={() => setShowImapForm((current) => !current)}
                  disabled={addDisabled}
                  aria-disabled={addDisabled}
                  style={actionButtonStyle(addDisabled)}
                >
                  {t("mailboxes.addImap")}
                </button>
              </div>
            </div>

            <div
              style={{
                border: "1px solid var(--mm-border)",
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div className="mm-spread" style={{ alignItems: "flex-start" }}>
                <div>
                  <MailboxProviderBadge provider="outlook" />
                  <p className="mm-muted" style={{ fontSize: 13, marginTop: 8 }}>
                    {t("mailboxes.outlookComingSoon")}
                  </p>
                </div>
                <button
                  type="button"
                  className="mm-btn"
                  disabled
                  aria-disabled
                  style={actionButtonStyle(true)}
                >
                  {t("mailboxes.unavailable")}
                </button>
              </div>
            </div>
          </div>

          {showImapForm ? (
            <form
              className="mm-stack"
              style={{ gap: 14, marginTop: 16 }}
              onSubmit={onConnectImap}
            >
              <div className="mm-row" style={{ gap: 8 }}>
                {imapPresets.map((preset) => (
                  <button
                    key={preset.key}
                    type="button"
                    className="mm-btn"
                    onClick={() => applyPreset(preset.host)}
                    disabled={connectingImap}
                    aria-disabled={connectingImap}
                    style={{ fontSize: 12, padding: "6px 12px" }}
                  >
                    {preset.label}
                  </button>
                ))}
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
                    disabled={connectingImap}
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
                    disabled={connectingImap}
                  />
                </label>
                <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                  <span>{t("mailboxes.imapHost")}</span>
                  <input
                    className="mm-input"
                    type="text"
                    value={imapForm.host}
                    onChange={(event) => updateImapForm("host", event.target.value)}
                    disabled={connectingImap}
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
                    disabled={connectingImap}
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
                    disabled={connectingImap}
                    required
                  />
                </label>
                <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                  <span>{t("mailboxes.imapPassword")}</span>
                  <div className="mm-row" style={{ gap: 8, alignItems: "center" }}>
                    <input
                      className="mm-input"
                      type={showImapPassword ? "text" : "password"}
                      value={imapForm.password}
                      onChange={(event) => updateImapForm("password", event.target.value)}
                      disabled={connectingImap}
                      required
                      style={{ flex: 1, minWidth: 0 }}
                    />
                    <button
                      type="button"
                      className="mm-btn"
                      onClick={() => setShowImapPassword((current) => !current)}
                      disabled={connectingImap}
                      aria-disabled={connectingImap}
                      aria-pressed={showImapPassword}
                      style={{ fontSize: 12, padding: "8px 12px", flexShrink: 0 }}
                    >
                      {showImapPassword
                        ? t("mailboxes.hidePassword")
                        : t("mailboxes.showPassword")}
                    </button>
                  </div>
                </label>
                <label className="mm-stack" style={{ gap: 6, fontSize: 13 }}>
                  <span>{t("mailboxes.imapFolder")}</span>
                  <input
                    className="mm-input"
                    type="text"
                    value={imapForm.folder}
                    onChange={(event) => updateImapForm("folder", event.target.value)}
                    disabled={connectingImap}
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
                    disabled={connectingImap}
                  />
                  <span>{t("mailboxes.imapUseSsl")}</span>
                </label>
              </div>

              <div className="mm-row" style={{ justifyContent: "flex-end" }}>
                <button
                  type="submit"
                  className="mm-btn mm-btn--primary"
                  disabled={connectingImap}
                  aria-disabled={connectingImap}
                  style={actionButtonStyle(connectingImap)}
                >
                  {connectingImap ? t("mailboxes.connectingImap") : t("mailboxes.addImap")}
                </button>
              </div>
            </form>
          ) : null}
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}

function ArchiveDatum({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mm-muted" style={{ fontSize: 12 }}>
        {label}
      </div>
      <div style={{ marginTop: 2, overflowWrap: "anywhere" }}>{value}</div>
    </div>
  );
}

function archiveHint(state: MailboxArchiveState, t: TFunction): string {
  if (state.last_error_message) {
    return state.last_error_message;
  }

  switch (state.status) {
    case "not_started":
      return t("mailboxes.archiveNotStartedHint");
    case "running":
      return t("mailboxes.archiveRunningHint");
    case "partial":
      return t("mailboxes.archivePartialHint");
    case "complete":
      return t("mailboxes.archiveCompleteHint");
    case "failed":
      return t("mailboxes.archiveFailedHint");
    default:
      return t("mailboxes.archiveUnknownHint");
  }
}

function formatArchiveValue(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}
