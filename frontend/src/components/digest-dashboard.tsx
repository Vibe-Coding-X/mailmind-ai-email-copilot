"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge, type BadgeTone } from "@/components/ui/badge";
import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth";
import {
  ApiRequestError,
  dismissDigestItem,
  generateTodayDigest,
  getTodayDigest,
  markDigestItemDone,
  refreshTodayDigest,
  snoozeDigestItem,
} from "@/lib/api-client";
import type { Digest, DigestItem } from "@/lib/api-types";
import { useI18n, type TranslationKey } from "@/i18n/provider";

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

type DigestItemActionKind = "mark_done" | "dismiss" | "snooze";

interface ItemFeedback {
  tone: BadgeTone;
  message: string;
}

interface SnoozeOption {
  label: string;
  value: string;
}

type TFunction = (key: TranslationKey) => string;

function digestErrorView(error: unknown, t: TFunction): DigestErrorView {
  if (error instanceof ApiRequestError) {
    if (error.status === 401 || error.code === "UNAUTHORIZED") {
      return {
        state: "unauthorized",
        title: t("account.notSignedIn"),
        message: t("digest.notSignedInMessage"),
      };
    }

    if (
      error.status === 404 ||
      error.code === "DIGEST_NOT_READY" ||
      error.code === "NOT_FOUND"
    ) {
      return {
        state: "empty",
        title: t("digest.noDigestTitle"),
        message: t("digest.noDigestMessage"),
      };
    }

    if (
      error.status === 0 ||
      error.code === "NETWORK_ERROR" ||
      error.code === "BACKEND_UNAVAILABLE"
    ) {
      return {
        state: "backend_unavailable",
        title: t("account.backendUnavailable"),
        message: t("digest.backendUnavailableMessage"),
      };
    }

    return {
      state: "error",
      title: t("digest.errorTitle"),
      message: error.message,
    };
  }

  return {
    state: "error",
    title: t("digest.errorTitle"),
    message: t("digest.genericError"),
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

function formatConfidence(value: number, t: TFunction): string {
  if (!Number.isFinite(value)) {
    return t("common.unknownConfidence");
  }

  return t("digest.confidence").replace("{{value}}", String(Math.round(value * 100)));
}

function digestSummary(digest: Digest, t: TFunction): string {
  if (digest.summary && digest.summary.trim().length > 0) {
    return digest.summary;
  }

  const overviewSummary = digest.overview.summary;
  if (typeof overviewSummary === "string" && overviewSummary.trim().length > 0) {
    return overviewSummary;
  }

  return t("digest.noSummary");
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

function buildSnoozeOptions(t: TFunction): SnoozeOption[] {
  return [
    { label: t("digest.snoozeTomorrow"), value: futureIsoDate(1) },
    { label: t("digest.snooze3Days"), value: futureIsoDate(3) },
    { label: t("digest.snoozeNextWeek"), value: futureIsoDate(7) },
  ];
}

function futureIsoDate(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString();
}

export function DigestDashboard() {
  const { t } = useI18n();
  const { status: authStatus, refresh: refreshAuth } = useAuth();
  const [pageState, setPageState] = useState<DigestPageState>("loading");
  const [digest, setDigest] = useState<Digest | null>(null);
  const [pageError, setPageError] = useState<DigestErrorView | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"generate" | "refresh" | null>(
    null,
  );
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
  const [itemFeedback, setItemFeedback] = useState<Record<string, ItemFeedback>>(
    {},
  );
  const [snoozeValues, setSnoozeValues] = useState<Record<string, string>>({});

  const groupedItems = useMemo(
    () => groupDigestItems(digest?.items ?? []),
    [digest],
  );
  const snoozeOptions = useMemo(() => buildSnoozeOptions(t), [t]);

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
      const view = digestErrorView(error, t);
      setDigest(null);
      setPageError(view);
      setPageState(view.state);
      return false;
    }
  }, [t]);

  useEffect(() => {
    if (authStatus === "loading") {
      setPageState("loading");
      return;
    }

    if (authStatus === "unauthenticated") {
      setDigest(null);
      setPageError({
        state: "unauthorized",
        title: t("account.notSignedIn"),
        message: t("digest.notSignedInMessage"),
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setDigest(null);
      setPageError({
        state: "backend_unavailable",
        title: t("account.backendUnavailable"),
        message: t("digest.backendUnavailableMessage"),
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadDigest();
  }, [authStatus, loadDigest, t]);

  async function onGenerate() {
    setActionError(null);
    setActionMessage(null);
    setBusyAction("generate");

    try {
      const response = await generateTodayDigest();
      setDigest(response.data.digest);
      setPageState("loaded");
      setPageError(null);
      setActionMessage(t("digest.generatedMessage"));
    } catch (error) {
      const view = digestErrorView(error, t);
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
      setActionMessage(t("digest.refreshedMessage"));
    } catch (error) {
      const view = digestErrorView(error, t);
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

  async function onDigestItemAction(
    itemId: string,
    action: DigestItemActionKind,
  ) {
    setBusyItemId(itemId);
    setItemFeedback((current) => ({
      ...current,
      [itemId]: {
        tone: "neutral",
        message: t("digest.recordingAction"),
      },
    }));

    try {
      const response =
        action === "mark_done"
          ? await markDigestItemDone(itemId)
          : action === "dismiss"
            ? await dismissDigestItem(itemId)
            : await snoozeDigestItem(itemId, {
                snoozed_until:
                  snoozeValues[itemId] ??
                  snoozeOptions[0]?.value ??
                  futureIsoDate(1),
              });

      setItemFeedback((current) => ({
        ...current,
        [itemId]: {
          tone: "ok",
          message: t("digest.actionStatus").replace(
            "{{status}}",
            statusLabel(response.data.action.action_status),
          ),
        },
      }));
      await loadDigest();
    } catch (error) {
      setItemFeedback((current) => ({
        ...current,
        [itemId]: {
          tone: "danger",
          message: digestErrorView(error, t).message,
        },
      }));
    } finally {
      setBusyItemId(null);
    }
  }

  function onSnoozeValueChange(itemId: string, value: string) {
    setSnoozeValues((current) => ({
      ...current,
      [itemId]: value,
    }));
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
                {digest ? statusLabel(digest.status) : t("digest.noDigestLoaded")}
              </Badge>
              {digest ? (
                <Badge tone="neutral">
                  {t("digest.version")} {digest.version}
                </Badge>
              ) : null}
            </div>
            <p className="mm-muted" style={{ fontSize: 13 }}>
              {digest
                ? `${t("digest.generated")} ${formatDateTime(digest.generated_at)}`
                : t("digest.loadedFromBackend")}
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
              {busyAction === "generate" ? t("digest.generating") : t("digest.generate")}
            </button>
            <button
              type="button"
              className="mm-btn"
              onClick={() => void onRefreshDigest()}
              disabled={!canRefresh || busy}
              aria-disabled={!canRefresh || busy}
            >
              {busyAction === "refresh" ? t("digest.refreshing") : t("digest.refresh")}
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
        busyItemId,
        itemFeedback,
        snoozeOptions,
        onGenerate,
        onRetry,
        onDigestItemAction,
        onSnoozeValueChange,
        busy,
        t,
      })}
    </div>
  );
}

function renderDigestContent({
  pageState,
  digest,
  groupedItems,
  pageError,
  busyItemId,
  itemFeedback,
  snoozeOptions,
  onGenerate,
  onRetry,
  onDigestItemAction,
  onSnoozeValueChange,
  busy,
  t,
}: {
  pageState: DigestPageState;
  digest: Digest | null;
  groupedItems: Array<{ section: string; items: DigestItem[] }>;
  pageError: DigestErrorView | null;
  busyItemId: string | null;
  itemFeedback: Record<string, ItemFeedback>;
  snoozeOptions: SnoozeOption[];
  onGenerate: () => Promise<void>;
  onRetry: () => Promise<void>;
  onDigestItemAction: (
    itemId: string,
    action: DigestItemActionKind,
  ) => Promise<void>;
  onSnoozeValueChange: (itemId: string, value: string) => void;
  busy: boolean;
  t: TFunction;
}) {
  if (pageState === "loading") {
    return <DigestLoadingState />;
  }

  if (pageState === "empty") {
    return (
      <EmptyState
        title={pageError?.title ?? t("digest.noDigestTitle")}
        hint={pageError?.message ?? t("digest.noDigestMessage")}
        action={
          <button
            type="button"
            className="mm-btn mm-btn--primary"
            onClick={() => void onGenerate()}
            disabled={busy}
            aria-disabled={busy}
          >
            {busy ? t("digest.generating") : t("digest.generate")}
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
        title: t("digest.errorTitle"),
        message: t("digest.genericError"),
      } satisfies DigestErrorView);

    return (
      <EmptyState
        title={error.title}
        hint={error.message}
        action={
          error.state === "unauthorized" ? (
            <a href="/login">{t("account.signIn")}</a>
          ) : (
            <button
              type="button"
              className="mm-btn"
              onClick={() => void onRetry()}
            >
              {t("common.retry")}
            </button>
          )
        }
      />
    );
  }

  return (
    <DigestLoadedView
      digest={digest}
      groupedItems={groupedItems}
      busyItemId={busyItemId}
      itemFeedback={itemFeedback}
      snoozeOptions={snoozeOptions}
      onDigestItemAction={onDigestItemAction}
      onSnoozeValueChange={onSnoozeValueChange}
      t={t}
    />
  );
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
  busyItemId,
  itemFeedback,
  snoozeOptions,
  onDigestItemAction,
  onSnoozeValueChange,
  t,
}: {
  digest: Digest;
  groupedItems: Array<{ section: string; items: DigestItem[] }>;
  busyItemId: string | null;
  itemFeedback: Record<string, ItemFeedback>;
  snoozeOptions: SnoozeOption[];
  onDigestItemAction: (
    itemId: string,
    action: DigestItemActionKind,
  ) => Promise<void>;
  onSnoozeValueChange: (itemId: string, value: string) => void;
  t: TFunction;
}) {
  return (
    <div className="mm-stack">
      <div className="mm-grid mm-grid-3">
        <MetricCard label={t("digest.emailsAnalyzed")} value={String(digest.mail_count)} />
        <MetricCard
          label={t("digest.newSinceDigest")}
          value={String(digest.new_mail_count_after_digest)}
        />
        <MetricCard
          label={t("digest.digestWindow")}
          value={digest.digest_date}
          detail={`${formatDateTime(digest.coverage_start)} to ${formatDateTime(
            digest.coverage_end,
          )}`}
        />
      </div>

      <section className="mm-card mm-card--summary">
        <div className="mm-spread" style={{ alignItems: "flex-start" }}>
          <div>
            <div className="mm-card-title">{t("digest.summary")}</div>
            <p
              style={{
                maxWidth: 900,
                overflowWrap: "anywhere",
                whiteSpace: "pre-wrap",
              }}
            >
              {digestSummary(digest, t)}
            </p>
          </div>
          <Badge tone={digest.is_current ? "ok" : "warn"} dot>
            {digest.is_current ? t("common.current") : t("common.previousVersion")}
          </Badge>
        </div>
      </section>

      {digest.items.length === 0 ? (
        <EmptyState
          title={t("digest.noItemsTitle")}
          hint={t("digest.noItemsMessage")}
        />
      ) : (
        groupedItems.map((group) => (
          <section className="mm-card" key={group.section}>
            <div className="mm-spread" style={{ alignItems: "flex-start" }}>
              <div>
                <div className="mm-card-title">{statusLabel(group.section)}</div>
                <p className="mm-muted" style={{ fontSize: 13 }}>
                  {group.items.length} {group.items.length === 1 ? t("digest.item") : t("digest.items")}
                </p>
              </div>
            </div>

            <div className="mm-stack" style={{ gap: 0 }}>
              {group.items.map((item, index) => (
                <DigestItemRow
                  key={item.id}
                  item={item}
                  showTopBorder={index > 0}
                  busy={busyItemId === item.id}
                  feedback={itemFeedback[item.id]}
                  snoozeOptions={snoozeOptions}
                  onAction={onDigestItemAction}
                  onSnoozeValueChange={onSnoozeValueChange}
                  t={t}
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
    <section className="mm-card mm-card--metric">
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
  busy,
  feedback,
  snoozeOptions,
  onAction,
  onSnoozeValueChange,
  t,
}: {
  item: DigestItem;
  showTopBorder: boolean;
  busy: boolean;
  feedback: ItemFeedback | undefined;
  snoozeOptions: SnoozeOption[];
  onAction: (itemId: string, action: DigestItemActionKind) => Promise<void>;
  onSnoozeValueChange: (itemId: string, value: string) => void;
  t: TFunction;
}) {
  const defaultSnoozeValue = snoozeOptions[0]?.value ?? futureIsoDate(1);

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
            {item.title.trim().length > 0 ? item.title : t("digest.untitledItem")}
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
        <Badge tone="neutral">{formatConfidence(item.confidence, t)}</Badge>
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

      <div
        className="mm-row"
        style={{
          marginTop: 14,
          alignItems: "center",
        }}
      >
        <button
          type="button"
          className="mm-btn"
          onClick={() => void onAction(item.id, "mark_done")}
          disabled={busy}
          aria-disabled={busy}
        >
          {busy ? t("common.working") : t("digest.markDone")}
        </button>
        <button
          type="button"
          className="mm-btn"
          onClick={() => void onAction(item.id, "dismiss")}
          disabled={busy}
          aria-disabled={busy}
        >
          {t("digest.dismiss")}
        </button>
        <select
          className="mm-input"
          aria-label={`Snooze ${item.title}`}
          defaultValue={defaultSnoozeValue}
          disabled={busy}
          onChange={(event) => onSnoozeValueChange(item.id, event.target.value)}
          style={{
            minWidth: 132,
            maxWidth: "100%",
          }}
        >
          {snoozeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="mm-btn"
          onClick={() => void onAction(item.id, "snooze")}
          disabled={busy}
          aria-disabled={busy}
        >
          {t("digest.snooze")}
        </button>
      </div>

      {feedback ? (
        <div style={{ marginTop: 10 }}>
          <Badge tone={feedback.tone} dot>
            {feedback.message}
          </Badge>
        </div>
      ) : null}
    </article>
  );
}
