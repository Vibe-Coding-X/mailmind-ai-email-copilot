"use client";

import type { Job } from "@/lib/api-types";
import {
  formatJobDateTime,
  formatJobDuration,
  safeProgress,
  statusLabel,
} from "@/lib/jobs";
import { useI18n } from "@/i18n/provider";
import { JobErrorPanel } from "./job-error-panel";
import { JobStatusBadge } from "./job-status-badge";

export interface JobProgressCardProps {
  job: Job;
  title?: string;
  onRetried?: (job: Job) => void;
  onError?: (message: string) => void;
}

export function JobProgressCard({
  job,
  title,
  onRetried,
  onError,
}: JobProgressCardProps) {
  const { t } = useI18n();
  const progress = safeProgress(job.progress);
  const duration = formatJobDuration(job);

  return (
    <section className="mm-card">
      <div className="mm-spread" style={{ alignItems: "flex-start" }}>
        <div style={{ minWidth: 0 }}>
          <div className="mm-card-title" style={{ marginBottom: 4 }}>
            {title ?? statusLabel(job.job_type)}
          </div>
          <p className="mm-muted" style={{ fontSize: 13 }}>
            {t("jobs.created")} {formatJobDateTime(job.created_at)}
          </p>
        </div>
        <JobStatusBadge job={job} />
      </div>

      <div
        aria-label={t("jobs.progress")}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progress}
        role="progressbar"
        style={{
          height: 8,
          marginTop: 14,
          overflow: "hidden",
          borderRadius: "var(--radius-pill)",
          background: "var(--color-surface-muted)",
          border: "var(--border-w) solid var(--color-border)",
        }}
      >
        <div
          style={{
            width: `${progress}%`,
            height: "100%",
            background:
              job.status === "failed"
                ? "var(--color-danger)"
                : "var(--color-primary)",
            transition: "width var(--mm-transition)",
          }}
        />
      </div>

      <div className="mm-grid mm-grid-3" style={{ marginTop: 14, fontSize: 13 }}>
        <JobDatum label={t("jobs.started")} value={formatJobDateTime(job.started_at)} />
        <JobDatum label={t("jobs.finished")} value={formatJobDateTime(job.finished_at)} />
        <JobDatum label={t("jobs.duration")} value={duration ?? "-"} />
      </div>

      <JobErrorPanel job={job} onRetried={onRetried} onError={onError} />
    </section>
  );
}

function JobDatum({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mm-muted" style={{ fontSize: 12 }}>
        {label}
      </div>
      <div style={{ marginTop: 2, overflowWrap: "anywhere" }}>{value}</div>
    </div>
  );
}
