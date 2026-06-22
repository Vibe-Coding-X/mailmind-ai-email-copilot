"use client";

import { useEffect, useRef, useState } from "react";

import { getJob } from "@/lib/api-client";
import type { Job } from "@/lib/api-types";
import { isTerminalJob } from "@/lib/jobs";

export interface UseJobPollingOptions {
  job: Job | null;
  enabled?: boolean;
  intervalMs?: number;
  maxDurationMs?: number;
  onCompleted?: (job: Job) => void;
  onFailed?: (job: Job) => void;
  onStopped?: (job: Job) => void;
}

export function useJobPolling({
  job,
  enabled = true,
  intervalMs = 2500,
  maxDurationMs = 120000,
  onCompleted,
  onFailed,
  onStopped,
}: UseJobPollingOptions) {
  const [currentJob, setCurrentJob] = useState<Job | null>(job);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const notifiedJobIdRef = useRef<string | null>(null);

  useEffect(() => {
    setCurrentJob(job);
    setError(null);
    notifiedJobIdRef.current = null;
  }, [job]);

  useEffect(() => {
    if (!enabled || job === null || isTerminalJob(job)) {
      setPolling(false);
      return;
    }

    let cancelled = false;
    const startedAt = Date.now();
    const jobToPoll = job;
    setPolling(true);

    async function poll() {
      try {
        const response = await getJob(jobToPoll.job_id);
        if (cancelled) {
          return;
        }

        const nextJob = response.data.job;
        setCurrentJob(nextJob);
        setError(null);

        if (isTerminalJob(nextJob)) {
          setPolling(false);
          if (notifiedJobIdRef.current !== nextJob.job_id) {
            notifiedJobIdRef.current = nextJob.job_id;
            if (nextJob.status === "completed") {
              onCompleted?.(nextJob);
            } else if (nextJob.status === "failed") {
              onFailed?.(nextJob);
            }
            onStopped?.(nextJob);
          }
          return;
        }

        if (Date.now() - startedAt >= maxDurationMs) {
          setPolling(false);
          onStopped?.(nextJob);
        }
      } catch (err) {
        if (!cancelled) {
          setPolling(false);
          setError(err instanceof Error ? err.message : "Job status unavailable.");
        }
      }
    }

    const interval = window.setInterval(() => {
      void poll();
    }, intervalMs);
    void poll();

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [
    enabled,
    intervalMs,
    job,
    maxDurationMs,
    onCompleted,
    onFailed,
    onStopped,
  ]);

  return { job: currentJob, polling, error };
}
