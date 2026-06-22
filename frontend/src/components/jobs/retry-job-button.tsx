"use client";

import { useState } from "react";

import { retryJob } from "@/lib/api-client";
import type { Job } from "@/lib/api-types";
import { canRetryJob } from "@/lib/jobs";
import { useI18n } from "@/i18n/provider";

export interface RetryJobButtonProps {
  job: Job;
  onRetried?: (job: Job) => void;
  onError?: (message: string) => void;
}

export function RetryJobButton({ job, onRetried, onError }: RetryJobButtonProps) {
  const { t } = useI18n();
  const [retrying, setRetrying] = useState(false);
  const disabled = !canRetryJob(job) || retrying;

  async function onRetry() {
    if (disabled) {
      return;
    }

    setRetrying(true);
    try {
      const response = await retryJob(job.job_id);
      onRetried?.(response.data.job);
    } catch (error) {
      onError?.(error instanceof Error ? error.message : t("jobs.retryFailed"));
    } finally {
      setRetrying(false);
    }
  }

  return (
    <button
      type="button"
      className="mm-btn"
      disabled={disabled}
      aria-disabled={disabled}
      onClick={() => void onRetry()}
    >
      {retrying ? t("jobs.retrying") : t("jobs.retry")}
    </button>
  );
}
