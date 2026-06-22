import type { Job } from "@/lib/api-types";
import {
  formatJobDuration,
  isActiveJob,
  isTerminalJob,
  jobStatusTone,
} from "@/lib/jobs";
import {
  JobActivityList,
  type JobActivityListProps,
} from "./job-activity-list";
import { JobErrorPanel, type JobErrorPanelProps } from "./job-error-panel";
import {
  JobProgressCard,
  type JobProgressCardProps,
} from "./job-progress-card";
import { JobStatusBadge } from "./job-status-badge";
import { RetryJobButton, type RetryJobButtonProps } from "./retry-job-button";
import { useJobPolling, type UseJobPollingOptions } from "./use-job-polling";
import { useRecentJobs, type UseRecentJobsOptions } from "./use-recent-jobs";

type Equal<A, B> = (<T>() => T extends A ? 1 : 2) extends <
  T,
>() => T extends B ? 1 : 2
  ? true
  : false;

type Assert<T extends true> = T;

type JobStatusToneSignature = Assert<
  Equal<ReturnType<typeof jobStatusTone>, "neutral" | "info" | "ok" | "warn" | "danger">
>;
type IsActiveJobParameters = Assert<Equal<Parameters<typeof isActiveJob>, [Job]>>;
type IsActiveJobSignature = Assert<Equal<ReturnType<typeof isActiveJob>, boolean>>;
type IsTerminalJobParameters = Assert<Equal<Parameters<typeof isTerminalJob>, [Job]>>;
type IsTerminalJobSignature = Assert<Equal<ReturnType<typeof isTerminalJob>, boolean>>;
type FormatJobDurationParameters = Assert<
  Equal<Parameters<typeof formatJobDuration>, [Job]>
>;
type FormatJobDurationSignature = Assert<
  Equal<ReturnType<typeof formatJobDuration>, string | null>
>;

type StatusBadgeProps = Assert<
  Equal<Parameters<typeof JobStatusBadge>, [{ job: Job }]>
>;
type ProgressCardProps = Assert<
  Equal<Parameters<typeof JobProgressCard>, [JobProgressCardProps]>
>;
type ErrorPanelProps = Assert<
  Equal<Parameters<typeof JobErrorPanel>, [JobErrorPanelProps]>
>;
type RetryButtonProps = Assert<
  Equal<Parameters<typeof RetryJobButton>, [RetryJobButtonProps]>
>;
type ActivityListProps = Assert<
  Equal<Parameters<typeof JobActivityList>, [JobActivityListProps]>
>;
type UseJobPollingProps = Assert<
  Equal<Parameters<typeof useJobPolling>, [UseJobPollingOptions]>
>;
type UseRecentJobsProps = Assert<
  Equal<Parameters<typeof useRecentJobs>, [UseRecentJobsOptions?]>
>;

type ComponentReturn = Assert<
  Equal<ReturnType<typeof JobProgressCard>, React.JSX.Element>
>;

type JobComponentAssertions = [
  JobStatusToneSignature,
  IsActiveJobParameters,
  IsActiveJobSignature,
  IsTerminalJobParameters,
  IsTerminalJobSignature,
  FormatJobDurationParameters,
  FormatJobDurationSignature,
  StatusBadgeProps,
  ProgressCardProps,
  ErrorPanelProps,
  RetryButtonProps,
  ActivityListProps,
  UseJobPollingProps,
  UseRecentJobsProps,
  ComponentReturn,
];

const jobComponentAssertions: JobComponentAssertions = [
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
  true,
];

void jobComponentAssertions;
