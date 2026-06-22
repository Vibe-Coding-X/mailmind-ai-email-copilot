"use client";

import type { Job } from "@/lib/api-types";
import {
  formatJobDateTime,
  formatJobDuration,
  statusLabel,
} from "@/lib/jobs";
import { useI18n } from "@/i18n/provider";
import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { JobErrorPanel } from "./job-error-panel";
import { JobStatusBadge } from "./job-status-badge";

export interface JobActivityListProps {
  jobs: Job[];
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onRetried?: (job: Job) => void;
  onRetryError?: (message: string) => void;
}

export function JobActivityList({
  jobs,
  loading = false,
  error = null,
  onRefresh,
  onRetried,
  onRetryError,
}: JobActivityListProps) {
  const { t } = useI18n();

  if (loading) {
    return <Skeleton lines={5} widths={["42%", "90%", "76%", "68%", "50%"]} />;
  }

  if (error) {
    return (
      <EmptyState
        title={t("jobs.activityUnavailable")}
        hint={error}
        action={
          onRefresh ? (
            <button type="button" className="mm-btn" onClick={onRefresh}>
              {t("common.retry")}
            </button>
          ) : undefined
        }
      />
    );
  }

  if (jobs.length === 0) {
    return (
      <EmptyState
        title={t("jobs.noJobsTitle")}
        hint={t("jobs.noJobsHint")}
      />
    );
  }

  return (
    <div className="mm-stack" style={{ gap: 0 }}>
      {jobs.map((job, index) => (
        <article
          key={job.job_id}
          style={{
            borderTop: index === 0 ? 0 : "1px solid var(--color-border)",
            padding: index === 0 ? "0 0 14px" : "14px 0",
          }}
        >
          <div className="mm-spread" style={{ alignItems: "flex-start" }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 650, overflowWrap: "anywhere" }}>
                {statusLabel(job.job_type)}
              </div>
              <p className="mm-muted" style={{ fontSize: 12, marginTop: 4 }}>
                {t("jobs.created")} {formatJobDateTime(job.created_at)}
              </p>
            </div>
            <JobStatusBadge job={job} />
          </div>

          <div className="mm-row" style={{ marginTop: 10, fontSize: 12 }}>
            <span className="mm-muted">
              {t("jobs.finished")} {formatJobDateTime(job.finished_at)}
            </span>
            <span className="mm-muted">
              {t("jobs.duration")} {formatJobDuration(job) ?? "-"}
            </span>
            {job.related_resource_type ? (
              <span className="mm-muted">
                {statusLabel(job.related_resource_type)}
                {job.related_resource_id ? ` ${job.related_resource_id}` : ""}
              </span>
            ) : null}
          </div>

          <JobErrorPanel
            job={job}
            onRetried={onRetried}
            onError={onRetryError}
          />
        </article>
      ))}
    </div>
  );
}
