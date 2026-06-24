import type { BadgeTone } from "@/components/ui/badge";
import type {
  Mailbox,
  MailboxSyncData,
  MailboxSyncStatusData,
  MailboxSyncState,
} from "./api-types";

export function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

export function mailboxStatusTone(status: string): BadgeTone {
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

export function isConnectedMailbox(mailbox: Mailbox): boolean {
  return mailbox.status === "connected";
}

export function requiresGmailReconnect(mailbox: Mailbox): boolean {
  return (
    mailbox.status === "reauth_required" ||
    mailbox.status === "reauthorization_required"
  );
}

function providerLabel(mailbox: Mailbox): string {
  return mailbox.provider.toLowerCase() === "gmail"
    ? "Gmail"
    : mailbox.provider.toUpperCase();
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Never";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export function formatDateTimeWithRelative(
  value: string | null | undefined,
): string {
  if (!value) {
    return "Never";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.max(0, Math.round(diffMs / 60000));
  const relative =
    diffMinutes < 1
      ? "just now"
      : diffMinutes < 60
        ? `${diffMinutes} min ago`
        : diffMinutes < 1440
          ? `${Math.round(diffMinutes / 60)} hr ago`
          : `${Math.round(diffMinutes / 1440)} day ago`;

  return `${date.toLocaleString()} (${relative})`;
}

export function mailboxStateMessage(mailbox: Mailbox): string {
  if (requiresGmailReconnect(mailbox)) {
    return `${providerLabel(mailbox)} authorization has expired. Reconnect before syncing.`;
  }

  if (mailbox.status === "connected") {
    return `${providerLabel(mailbox)} is connected and ready for manual sync.`;
  }

  if (mailbox.status === "disconnected") {
    return "This mailbox is disconnected.";
  }

  if (mailbox.status === "error") {
    return `${providerLabel(mailbox)} connection needs attention.`;
  }

  return `Mailbox status: ${statusLabel(mailbox.status)}.`;
}

export function syncStatusTone(status: MailboxSyncState | undefined): BadgeTone {
  switch (status) {
    case "completed":
      return "ok";
    case "running":
      return "info";
    case "failed":
      return "danger";
    case "not_started":
      return "neutral";
    default:
      return "neutral";
  }
}

export function syncStatusSummary(
  syncStatus: MailboxSyncStatusData | undefined,
): string {
  if (!syncStatus) {
    return "Sync status has not been loaded.";
  }

  if (syncStatus.message && syncStatus.message.trim().length > 0) {
    return syncStatus.message;
  }

  return `Sync status: ${statusLabel(syncStatus.status)}`;
}

export function syncStatusDetail(
  syncStatus: MailboxSyncStatusData | undefined,
): string {
  if (!syncStatus) {
    return "Sync status will appear after the backend responds.";
  }

  if (syncStatus.status === "completed") {
    return "The last sync completed successfully.";
  }

  if (syncStatus.status === "running") {
    return "A sync job is currently running.";
  }

  if (syncStatus.status === "failed") {
    return syncStatus.last_job?.error_message ?? "The last sync job failed.";
  }

  if (syncStatus.status === "not_started") {
    return "No sync job has been started for this mailbox.";
  }

  return `Current sync state is ${statusLabel(syncStatus.status)}.`;
}

export function syncResultMessage(result: MailboxSyncData): string {
  const status = statusLabel(result.status);
  const count =
    typeof result.synced_count === "number"
      ? ` Synced emails: ${result.synced_count}.`
      : "";
  const job = result.job_id ? ` Job: ${result.job_id}.` : "";

  return `Sync ${status}.${count}${job}`;
}
