import type { BadgeTone } from "@/components/ui/badge";
import type { Job } from "./api-types";

const ACTIVE_JOB_STATUSES = new Set(["pending_dispatch", "queued", "running"]);
const TERMINAL_JOB_STATUSES = new Set([
  "completed",
  "failed",
  "dispatch_failed",
  "cancelled",
]);

export function isActiveJob(job: Job): boolean {
  return ACTIVE_JOB_STATUSES.has(job.status);
}

export function isTerminalJob(job: Job): boolean {
  return TERMINAL_JOB_STATUSES.has(job.status);
}

export function jobStatusTone(job: Job): BadgeTone {
  switch (job.status) {
    case "pending_dispatch":
      return "neutral";
    case "queued":
      return "neutral";
    case "running":
      return "info";
    case "completed":
      return "ok";
    case "failed":
    case "dispatch_failed":
      return "danger";
    case "cancelled":
      return "warn";
    default:
      return "neutral";
  }
}

export function statusLabel(value: string): string {
  return value.replaceAll("_", " ");
}

export function safeProgress(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }

  return Math.max(0, Math.min(100, Math.round(value)));
}

export function formatJobDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

export function formatJobDuration(job: Job): string | null {
  if (!job.started_at || !job.finished_at) {
    return null;
  }

  const started = new Date(job.started_at).getTime();
  const finished = new Date(job.finished_at).getTime();
  if (Number.isNaN(started) || Number.isNaN(finished) || finished < started) {
    return null;
  }

  const seconds = Math.round((finished - started) / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
}

export function canRetryJob(job: Job): boolean {
  return (
    (job.status === "failed" || job.status === "dispatch_failed") &&
    job.retry_count < job.max_retries
  );
}

export function digestIdFromJob(job: Job): string | null {
  const resultDigestId = job.result.digest_id;
  if (typeof resultDigestId === "string" && resultDigestId.trim().length > 0) {
    return resultDigestId;
  }

  if (job.related_resource_type === "digest" && job.related_resource_id) {
    return job.related_resource_id;
  }

  return null;
}
