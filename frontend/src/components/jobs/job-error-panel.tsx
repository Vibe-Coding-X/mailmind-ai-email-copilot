"use client";

import type { Job } from "@/lib/api-types";
import { useI18n } from "@/i18n/provider";
import { RetryJobButton } from "./retry-job-button";

export interface JobErrorPanelProps {
  job: Job;
  onRetried?: (job: Job) => void;
  onError?: (message: string) => void;
}

export function JobErrorPanel({ job, onRetried, onError }: JobErrorPanelProps) {
  const { t } = useI18n();

  if (job.status !== "failed") {
    return null;
  }

  return (
    <div className="mm-feedback mm-feedback--danger" style={{ marginTop: 12 }}>
      <div className="mm-feedback-main">
        <span>{t("jobs.failed")}</span>
        <span>
          {job.error_message ?? job.error_code ?? t("jobs.noErrorMessage")}
        </span>
      </div>
      <div className="mm-feedback-action">
        <RetryJobButton job={job} onRetried={onRetried} onError={onError} />
      </div>
    </div>
  );
}
