"use client";

import { Badge } from "@/components/ui/badge";
import type { Job } from "@/lib/api-types";
import { jobStatusTone, statusLabel } from "@/lib/jobs";

export function JobStatusBadge({ job }: { job: Job }) {
  return (
    <Badge tone={jobStatusTone(job)} dot>
      {statusLabel(job.status)}
    </Badge>
  );
}
