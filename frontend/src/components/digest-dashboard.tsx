"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge, type BadgeTone } from "@/components/ui/badge";
import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth";
import {
  ApiRequestError,
  generateTodayDigest,
  getTodayDigest,
  refreshTodayDigest,
} from "@/lib/api-client";
import type { Digest, DigestItem } from "@/lib/api-types";

type DigestPageState =
  | "loading"
  | "loaded"
  | "empty"
  | "unauthorized"
  | "backend_unavailable"
  | "error";

interface DigestErrorView {
  state: Exclude<DigestPageState, "loading" | "loaded">;
  title: string;
  message: string;
}

function digestErrorView(error: unknown): DigestErrorView {
  if (error instanceof ApiRequestError) {
    if (error.status === 401 || error.code === "UNAUTHORIZED") {
      return {
        state: "unauthorized",
        title: "Not signed in",
        message: "Sign in with your MailMind account to load the digest.",
      };
    }

    if (
      error.status === 404 ||
      error.code === "DIGEST_NOT_READY" ||
      error.code === "NOT_FOUND"
    ) {
      return {
        state: "empty",
        title: "No digest yet",
        message: "Generate today's digest after syncing email.",
      };
    }

    if (
      error.status === 0 ||
      error.code === "NETWORK_ERROR" ||
      error.code === "BACKEND_UNAVAILABLE"
    ) {
      return {
        state: "backend_unavailable",
        title: "Backend unavailable",
        message: "Unable to reach the server. Check that the backend is running.",
      };
    }

    return {
      state: "error",
      title: "Digest error",
      message: error.message,
    };
  }

  return {
    state: "error",
    title: "Digest error",
    message: "Something went wrong. Please try again.",
  };
}

function digestStatusTone(status: string): BadgeTone {
  switch (status) {
    case "fresh":
      return "ok";
    case "stale":
      return "warn";
    case "failed":
      return "danger";
    default:
      return "info";
  }
}

function priorityTone(priority: string): BadgeTone {
  switch (priority) {
    case "high":
      return "danger";
    case "medium":
      return "warn";
    case "low":
      return "neutral";
    default:
      return "info";
  }
}

function statusLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function formatConfidence(value: number): string {
  if (!Number.isFinite(value)) {
    return "Unknown confidence";
  }

  return `${Math.round(value * 100)}% confidence`;
}

function digestSummary(digest: Digest): string {
  if (digest.summary && digest.summary.trim().length > 0) {
    return digest.summary;
  }

  const overviewSummary = digest.overview.summary;
  if (typeof overviewSummary === "string" && overviewSummary.trim().length > 0) {
    return overviewSummary;
  }

  return "Digest generated without a summary.";
}

function groupDigestItems(items: DigestItem[]): Array<{
  section: string;
  items: DigestItem[];
}> {
  const grouped = new Map<string, DigestItem[]>();

  for (const item of items) {
    const section = item.section.trim().length > 0 ? item.section : "review";
    grouped.set(section, [...(grouped.get(section) ?? []), item]);
  }

  return Array.from(grouped.entries()).map(([section, sectionItems]) => ({
    section,
    items: sectionItems,
  }));
}

export function DigestDashboard() {
  const { status: authStatus, refresh: refreshAuth } = useAuth();
  const [pageState, setPageState] = useState<DigestPageState>("loading");
  const [digest, setDigest] = useState<Digest | null>(null);
  const [pageError, setPageError] = useState<DigestErrorView | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"generate" | "refresh" | null>(
    null,
  );

  const groupedItems = useMemo(
    () => groupDigestItems(digest?.items ?? []),
    [digest],
  );

  const loadDigest = useCallback(async (): Promise<boolean> => {
    setPageState("loading");
    setPageError(null);
    setActionError(null);

    try {
      const response = await getTodayDigest();
      setDigest(response.data.digest);
      setPageState("loaded");
      return true;
    } catch (error) {
      const view = digestErrorView(error);
      setDigest(null);
      setPageError(view);
      setPageState(view.state);
      return false;
    }
  }, []);

  useEffect(() => {
    if (authStatus === "loading") {
      setPageState("loading");
      return;
    }

    if (authStatus === "unauthenticated") {
      setDigest(null);
      setPageError({
        state: "unauthorized",
        title: "Not signed in",
        message: "Sign in with your MailMind account to load the digest.",
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setDigest(null);
      setPageError({
        state: "backend_unavailable",
        title: "Backend unavailable",
        message: "Unable to reach the server. Check that the backend is running.",
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadDigest();
  }, [authStatus, loadDigest]);

  async function onGenerate() {
    setActionError(null);
    setActionMessage(null);
    setBusyAction("generate");

    try {
      const response = await generateTodayDigest();
      setDigest(response.data.digest);
      setPageState("loaded");
      setPageError(null);
      setActionMessage("Digest generated.");
    } catch (error) {
      const view = digestErrorView(error);
      setActionError(view.message);
      if (view.state === "unauthorized" || view.state === "backend_unavailable") {
        setPageError(view);
        setPageState(view.state);
      }
    } finally {
      setBusyAction(null);
    }
  }

  async function onRefreshDigest() {
    setActionError(null);
    setActionMessage(null);
    setBusyAction("refresh");

    try {
      const response = await refreshTodayDigest();
      setDigest(response.data.digest);
      setPageState("loaded");
      setPageError(null);
      setActionMessage("Digest refreshed.");
    } catch (error) {
      const view = digestErrorView(error);
      setActionError(view.message);
      if (view.state === "unauthorized" || view.state === "backend_unavailable") {
        setPageError(view);
        setPageState(view.state);
      }
    } finally {
      setBusyAction(null);
    }
  }

  async function onRetry() {
    setActionError(null);
    setActionMessage(null);

    if (authStatus === "authenticated") {
      await loadDigest();
      return;
    }

    await refreshAuth();
  }

  const busy = busyAction !== null;
  const canGenerate =
    authStatus === "authenticated" &&
    (pageState === "empty" || pageState === "error" || pageState === "loaded");
  const canRefresh = authStatus === "authenticated" && pageState === "loaded";

  return (
    <div className="mm-stack">
      <section className="mm-card">
        <div className="mm-spread" style={{ alignItems: "flex-start" }}>
          <div className="mm-stack" style={{ gap: 8 }}>
            <div className="mm-row">
              <Badge
                tone={digest ? digestStatusTone(digest.status) : "neutral"}
                dot
              >
                {digest ? statusLabel(digest.status) : "No digest loaded"}
              </Badge>
              {digest ? (
                <Badge tone="neutral">Version {digest.version}</Badge>
              ) : null}
            </div>
            <p className="mm-muted" style={{ fontSize: 13 }}>
              {digest
                ? `Generated ${formatDateTime(digest.generated_at)}`
                : "Today's digest is loaded from the backend when available."}
            </p>
          </div>

          <div className="mm-row" style={{ justifyContent: "flex-end" }}>
            <button
              type="button"
              className="mm-btn mm-btn--primary"
              onClick={() => void onGenerate()}
              disabled={!canGenerate || busy}
              aria-disabled={!canGenerate || busy}
            >
              {busyAction === "generate" ? "Generating..." : "Generate Digest"}
            </button>
            <button
              type="button"
              className="mm-btn"
              onClick={() => void onRefreshDigest()}
              disabled={!canRefresh || busy}
              aria-disabled={!canRefresh || busy}
            >
              {busyAction === "refresh" ? "Refreshing..." : "Refresh Digest"}
            </button>
          </div>
        </div>

        {actionError ? (
          <div style={{ marginTop: 14 }}>
            <Badge tone="danger" dot>
              {actionError}
            </Badge>
          </div>
        ) : null}

        {actionMessage ? (
          <div style={{ marginTop: 14 }}>
            <Badge tone="ok" dot>
              {actionMessage}
            </Badge>
          </div>
        ) : null}
      </section>

      {renderDigestContent({
        pageState,
        digest,
        groupedItems,
        pageError,
        onGenerate,
        onRetry,
        busy,
      })}
    </div>
  );
}

function renderDigestContent({
  pageState,
  digest,
  groupedItems,
  pageError,
  onGenerate,
  onRetry,
  busy,
}: {
  pageState: DigestPageState;
  digest: Digest | null;
  groupedItems: Array<{ section: string; items: DigestItem[] }>;
  pageError: DigestErrorView | null;
  onGenerate: () => Promise<void>;
  onRetry: () => Promise<void>;
  busy: boolean;
}) {
  if (pageState === "loading") {
    return <DigestLoadingState />;
  }

  if (pageState === "empty") {
    return (
      <EmptyState
        title={pageError?.title ?? "No digest yet"}
        hint={pageError?.message ?? "Generate today's digest after syncing email."}
        action={
          <button
            type="button"
            className="mm-btn mm-btn--primary"
            onClick={() => void onGenerate()}
            disabled={busy}
            aria-disabled={busy}
          >
            {busy ? "Generating..." : "Generate Digest"}
          </button>
        }
      />
    );
  }

  if (pageState !== "loaded" || digest === null) {
    const error =
      pageError ??
      ({
        state: "error",
        title: "Digest error",
        message: "Something went wrong. Please try again.",
      } satisfies DigestErrorView);

    return (
      <EmptyState
        title={error.title}
        hint={error.message}
        action={
          error.state === "unauthorized" ? (
            <a href="/login">Sign in</a>
          ) : (
            <button
              type="button"
              className="mm-btn"
              onClick={() => void onRetry()}
            >
              Retry
            </button>
          )
        }
      />
    );
  }

  return <DigestLoadedView digest={digest} groupedItems={groupedItems} />;
}

function DigestLoadingState() {
  return (
    <div className="mm-stack">
      <div className="mm-grid mm-grid-3">
        <MetricSkeleton />
        <MetricSkeleton />
        <MetricSkeleton />
      </div>
      <section className="mm-card">
        <Skeleton lines={5} widths={["35%", "90%", "84%", "72%", "50%"]} />
      </section>
    </div>
  );
}

function MetricSkeleton() {
  return (
    <section className="mm-card">
      <Skeleton lines={3} widths={["42%", "34%", "58%"]} />
    </section>
  );
}

function DigestLoadedView({
  digest,
  groupedItems,
}: {
  digest: Digest;
  groupedItems: Array<{ section: string; items: DigestItem[] }>;
}) {
  return (
    <div className="mm-stack">
      <div className="mm-grid mm-grid-3">
        <MetricCard label="Emails analyzed" value={String(digest.mail_count)} />
        <MetricCard
          label="New since digest"
          value={String(digest.new_mail_count_after_digest)}
        />
        <MetricCard
          label="Digest window"
          value={digest.digest_date}
          detail={`${formatDateTime(digest.coverage_start)} to ${formatDateTime(
            digest.coverage_end,
          )}`}
        />
      </div>

      <section className="mm-card">
        <div className="mm-spread" style={{ alignItems: "flex-start" }}>
          <div>
            <div className="mm-card-title">Summary</div>
            <p
              style={{
                maxWidth: 900,
                overflowWrap: "anywhere",
                whiteSpace: "pre-wrap",
              }}
            >
              {digestSummary(digest)}
            </p>
          </div>
          <Badge tone={digest.is_current ? "ok" : "warn"} dot>
            {digest.is_current ? "Current" : "Previous version"}
          </Badge>
        </div>
      </section>

      {digest.items.length === 0 ? (
        <EmptyState
          title="No digest items"
          hint="The backend returned a digest without item-level recommendations."
        />
      ) : (
        groupedItems.map((group) => (
          <section className="mm-card" key={group.section}>
            <div className="mm-spread" style={{ alignItems: "flex-start" }}>
              <div>
                <div className="mm-card-title">{statusLabel(group.section)}</div>
                <p className="mm-muted" style={{ fontSize: 13 }}>
                  {group.items.length} item{group.items.length === 1 ? "" : "s"}
                </p>
              </div>
            </div>

            <div className="mm-stack" style={{ gap: 0 }}>
              {group.items.map((item, index) => (
                <DigestItemRow
                  key={item.id}
                  item={item}
                  showTopBorder={index > 0}
                />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <section className="mm-card">
      <div className="mm-muted" style={{ fontSize: 12 }}>
        {label}
      </div>
      <div
        style={{
          fontSize: 26,
          fontWeight: 700,
          marginTop: 8,
          overflowWrap: "anywhere",
        }}
      >
        {value}
      </div>
      {detail ? (
        <p className="mm-muted" style={{ fontSize: 11, marginTop: 8 }}>
          {detail}
        </p>
      ) : null}
    </section>
  );
}

function DigestItemRow({
  item,
  showTopBorder,
}: {
  item: DigestItem;
  showTopBorder: boolean;
}) {
  return (
    <article
      style={{
        padding: showTopBorder ? "16px 0 0" : "16px 0 0",
        marginTop: showTopBorder ? 16 : 0,
        borderTop: showTopBorder ? "1px solid var(--mm-border)" : undefined,
      }}
    >
      <div className="mm-spread" style={{ alignItems: "flex-start" }}>
        <div style={{ minWidth: 0 }}>
          <h3
            style={{
              fontSize: 15,
              overflowWrap: "anywhere",
            }}
          >
            {item.title.trim().length > 0 ? item.title : "Untitled item"}
          </h3>
          <p
            className="mm-muted"
            style={{
              fontSize: 13,
              marginTop: 6,
              overflowWrap: "anywhere",
              whiteSpace: "pre-wrap",
            }}
          >
            {item.summary}
          </p>
        </div>
        <Badge tone={priorityTone(item.priority)} dot>
          {statusLabel(item.priority)}
        </Badge>
      </div>

      <div className="mm-row" style={{ marginTop: 12 }}>
        <Badge tone="neutral">{statusLabel(item.category)}</Badge>
        <Badge tone="info">{statusLabel(item.suggested_action)}</Badge>
        <Badge tone="neutral">{formatConfidence(item.confidence)}</Badge>
      </div>

      {item.reason ? (
        <p
          className="mm-muted"
          style={{
            fontSize: 12,
            marginTop: 10,
            overflowWrap: "anywhere",
          }}
        >
          {item.reason}
        </p>
      ) : null}
    </article>
  );
}
