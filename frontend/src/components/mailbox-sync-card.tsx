"use client";

import { Badge } from "@/components/ui/badge";
import { JobProgressCard } from "@/components/jobs/job-progress-card";
import { useI18n } from "@/i18n/provider";
import type { Job, Mailbox, MailboxSyncStatusData } from "@/lib/api-types";
import { isActiveJob } from "@/lib/jobs";
import {
  formatDateTimeWithRelative,
  isConnectedMailbox,
  mailboxStateMessage,
  requiresGmailReconnect,
  statusLabel,
  syncStatusDetail,
  syncStatusSummary,
  syncStatusTone,
} from "@/lib/mailboxes";

export type MailboxSyncStatusView =
  | { state: "loading" }
  | { state: "loaded"; data: MailboxSyncStatusData }
  | { state: "error"; message: string };

export function MailboxSyncCard({
  mailbox,
  syncStatus,
  syncing = false,
  activeJob = null,
  onSync,
  onJobRetried,
  onJobRetryError,
}: {
  mailbox: Mailbox;
  syncStatus?: MailboxSyncStatusView;
  syncing?: boolean;
  activeJob?: Job | null;
  onSync: (mailboxId: string) => void;
  onJobRetried?: (job: Job) => void;
  onJobRetryError?: (message: string) => void;
}) {
  const { t } = useI18n();
  const loaded = syncStatus?.state === "loaded" ? syncStatus.data : undefined;
  const hasActiveJob = activeJob !== null && isActiveJob(activeJob);
  const disabled = !isConnectedMailbox(mailbox) || syncing || hasActiveJob;
  const lastJob = loaded?.last_job ?? null;
  const needsReconnect = requiresGmailReconnect(mailbox);
  const syncError =
    syncStatus?.state === "error"
      ? syncStatus.message
      : lastJob?.error_message ?? null;

  return (
    <div
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: 14,
        background: "var(--color-surface-muted)",
      }}
    >
      <div className="mm-spread" style={{ alignItems: "flex-start" }}>
        <div>
          <div className="mm-card-title" style={{ marginBottom: 4 }}>
            {t("mailboxes.syncToday")}
          </div>
          <p className="mm-muted" style={{ fontSize: 13 }}>
            {syncStatus?.state === "loading"
              ? t("mailboxes.checkingSync")
              : syncStatusSummary(loaded)}
          </p>
          {syncStatus?.state !== "loading" ? (
            <p className="mm-muted" style={{ fontSize: 12, marginTop: 4 }}>
              {loaded ? syncStatusDetail(loaded) : mailboxStateMessage(mailbox)}
            </p>
          ) : null}
        </div>
        <Badge tone={syncStatusTone(loaded?.status)} dot>
          {loaded ? statusLabel(loaded.status) : syncStatus?.state ?? "unknown"}
        </Badge>
      </div>

      <div
        className="mm-grid mm-grid-2"
        style={{ marginTop: 14, fontSize: 13 }}
      >
        <SyncDatum
          label={t("mailboxes.lastSuccessfulSync")}
          value={formatDateTimeWithRelative(loaded?.last_successful_sync_at)}
        />
        <SyncDatum
          label={t("mailboxes.lastJob")}
          value={
            lastJob
              ? `${statusLabel(lastJob.status)} (${lastJob.job_type})`
              : t("mailboxes.noJob")
          }
        />
      </div>

      {syncError ? (
        <div style={{ marginTop: 12 }}>
          <Badge tone="danger" dot>
            {syncError}
          </Badge>
        </div>
      ) : null}

      {activeJob ? (
        <div style={{ marginTop: 14 }}>
          <JobProgressCard
            job={activeJob}
            title={t("mailboxes.syncJobTitle")}
            onRetried={onJobRetried}
            onError={onJobRetryError}
          />
        </div>
      ) : null}

      <div className="mm-row" style={{ marginTop: 14 }}>
        <button
          type="button"
          className="mm-btn"
          disabled={disabled}
          aria-disabled={disabled}
          onClick={() => onSync(mailbox.id)}
          style={{ cursor: disabled ? "not-allowed" : "pointer" }}
        >
          {syncing || hasActiveJob
            ? t("mailboxes.syncing")
            : t("mailboxes.syncToday")}
        </button>
        {!isConnectedMailbox(mailbox) ? (
          <span className="mm-muted" style={{ fontSize: 12 }}>
            {needsReconnect
              ? t("mailboxes.reconnectBeforeSync")
              : t("mailboxes.connectBeforeSync")}
          </span>
        ) : null}
      </div>
    </div>
  );
}

function SyncDatum({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mm-muted" style={{ fontSize: 12 }}>
        {label}
      </div>
      <div style={{ marginTop: 2 }}>{value}</div>
    </div>
  );
}
