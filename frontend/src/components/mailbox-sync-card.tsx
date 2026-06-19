import { Badge } from "@/components/ui/badge";
import type { Mailbox, MailboxSyncStatusData } from "@/lib/api-types";
import {
  formatDateTime,
  isConnectedMailbox,
  requiresGmailReconnect,
  statusLabel,
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
  onSync,
}: {
  mailbox: Mailbox;
  syncStatus?: MailboxSyncStatusView;
  syncing?: boolean;
  onSync: (mailboxId: string) => void;
}) {
  const loaded = syncStatus?.state === "loaded" ? syncStatus.data : undefined;
  const disabled = !isConnectedMailbox(mailbox) || syncing;
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
            Sync Today
          </div>
          <p className="mm-muted" style={{ fontSize: 13 }}>
            {syncStatus?.state === "loading"
              ? "Checking sync status..."
              : syncStatusSummary(loaded)}
          </p>
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
          label="Last successful sync"
          value={formatDateTime(loaded?.last_successful_sync_at)}
        />
        <SyncDatum
          label="Last job"
          value={
            lastJob
              ? `${statusLabel(lastJob.status)} (${lastJob.job_type})`
              : "No job"
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

      <div className="mm-row" style={{ marginTop: 14 }}>
        <button
          type="button"
          className="mm-btn"
          disabled={disabled}
          aria-disabled={disabled}
          onClick={() => onSync(mailbox.id)}
          style={{ cursor: disabled ? "not-allowed" : "pointer" }}
        >
          {syncing ? "Syncing..." : "Sync Today"}
        </button>
        {!isConnectedMailbox(mailbox) ? (
          <span className="mm-muted" style={{ fontSize: 12 }}>
            {needsReconnect
              ? "Reconnect Gmail before syncing."
              : "Connect Gmail before syncing."}
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
