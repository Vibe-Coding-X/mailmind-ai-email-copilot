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

export function syncStatusTone(status: MailboxSyncState | undefined): BadgeTone {
  switch (status) {
    case "completed":
      return "ok";
    case "running":
      return "info";
    case "failed":
      return "danger";
    case "not_implemented":
      return "warn";
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

export function syncResultMessage(result: MailboxSyncData): string {
  const status = statusLabel(result.status);
  const count =
    typeof result.synced_count === "number"
      ? ` Synced emails: ${result.synced_count}.`
      : "";
  const job = result.job_id ? ` Job: ${result.job_id}.` : "";

  return `Sync ${status}.${count}${job}`;
}
