"use client";

import { useCallback, useEffect, useState } from "react";

import { listJobs } from "@/lib/api-client";
import type { Job, JobListQuery, JobsPagination } from "@/lib/api-types";

const DEFAULT_RECENT_JOBS_QUERY: JobListQuery = { limit: 8 };

export interface UseRecentJobsOptions {
  enabled?: boolean;
  query?: JobListQuery;
}

export function useRecentJobs(options: UseRecentJobsOptions = {}) {
  const { enabled = true, query = DEFAULT_RECENT_JOBS_QUERY } = options;
  const [jobs, setJobs] = useState<Job[]>([]);
  const [pagination, setPagination] = useState<JobsPagination | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (): Promise<boolean> => {
    if (!enabled) {
      setLoading(false);
      return false;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await listJobs(query);
      setJobs(response.data.jobs);
      setPagination(response.data.pagination);
      return true;
    } catch (err) {
      setJobs([]);
      setPagination(null);
      setError(err instanceof Error ? err.message : "Jobs unavailable.");
      return false;
    } finally {
      setLoading(false);
    }
  }, [enabled, query]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { jobs, pagination, loading, error, refresh };
}
