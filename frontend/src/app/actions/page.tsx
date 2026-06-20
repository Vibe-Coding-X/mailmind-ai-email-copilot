"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { PageFrame } from "@/components/page-frame";
import { StatusBanner } from "@/components/status-banner";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth";
import { ApiRequestError, getAction, listActions } from "@/lib/api-client";
import type { UserAction } from "@/lib/api-types";
import { useI18n, type TranslationKey } from "@/i18n/provider";

type PageState =
  | "loading"
  | "loaded"
  | "unauthorized"
  | "backend_unavailable"
  | "error";

interface ActionErrorView {
  state: Exclude<PageState, "loading" | "loaded">;
  title: string;
  message: string;
}

type TFunction = (key: TranslationKey) => string;

function actionErrorView(error: unknown, t: TFunction): ActionErrorView {
  if (error instanceof ApiRequestError) {
    if (error.status === 401 || error.code === "UNAUTHORIZED") {
      return {
        state: "unauthorized",
        title: t("account.notSignedIn"),
        message: t("actions.notSignedInMessage"),
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
      title: t("actions.errorTitle"),
      message: error.message,
    };
  }

  return {
    state: "error",
    title: t("actions.errorTitle"),
    message: t("digest.genericError"),
  };
}

function statusLabel(value: string): string {
  return value.replaceAll("_", " ");
}

function actionTone(status: string): BadgeTone {
  switch (status) {
    case "executed":
    case "completed":
      return "ok";
    case "failed":
      return "danger";
    case "pending":
      return "warn";
    default:
      return "neutral";
  }
}

function providerTone(effect: string): BadgeTone {
  switch (effect) {
    case "gmail_synced":
      return "ok";
    case "failed":
      return "danger";
    case "none":
      return "neutral";
    default:
      return "info";
  }
}

function formatDateTime(value: string | null, t: TFunction): string {
  if (!value) {
    return t("actions.notExecuted");
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function uniqueValues(actions: UserAction[], key: keyof UserAction): string[] {
  return Array.from(
    new Set(
      actions
        .map((action) => action[key])
        .filter((value): value is string => typeof value === "string"),
    ),
  ).sort();
}

export default function ActionsPage() {
  const { t } = useI18n();
  const { status: authStatus, refresh: refreshAuth } = useAuth();
  const [pageState, setPageState] = useState<PageState>("loading");
  const [actions, setActions] = useState<UserAction[]>([]);
  const [pageError, setPageError] = useState<ActionErrorView | null>(null);
  const [actionTypeFilter, setActionTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [selectedAction, setSelectedAction] = useState<UserAction | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const actionTypes = useMemo(
    () => uniqueValues(actions, "action_type"),
    [actions],
  );
  const statuses = useMemo(
    () => uniqueValues(actions, "action_status"),
    [actions],
  );
  const filteredActions = useMemo(
    () =>
      actions.filter((action) => {
        const typeMatches =
          actionTypeFilter === "all" || action.action_type === actionTypeFilter;
        const statusMatches =
          statusFilter === "all" || action.action_status === statusFilter;
        return typeMatches && statusMatches;
      }),
    [actions, actionTypeFilter, statusFilter],
  );

  const loadActions = useCallback(async (): Promise<boolean> => {
    setPageState("loading");
    setPageError(null);
    setDetailError(null);

    try {
      const response = await listActions();
      setActions(response.data.actions);
      setSelectedActionId(null);
      setSelectedAction(null);
      setPageState("loaded");
      return true;
    } catch (error) {
      const view = actionErrorView(error, t);
      setActions([]);
      setSelectedActionId(null);
      setSelectedAction(null);
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
      setActions([]);
      setPageError({
        state: "unauthorized",
        title: t("account.notSignedIn"),
        message: t("actions.notSignedInMessage"),
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setActions([]);
      setPageError({
        state: "backend_unavailable",
        title: t("account.backendUnavailable"),
        message: t("digest.backendUnavailableMessage"),
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadActions();
  }, [authStatus, loadActions, t]);

  async function onRetry() {
    if (authStatus === "authenticated") {
      await loadActions();
      return;
    }

    await refreshAuth();
  }

  async function onSelectAction(actionId: string) {
    setSelectedActionId(actionId);
    setSelectedAction(null);
    setDetailLoading(true);
    setDetailError(null);

    try {
      const response = await getAction(actionId);
      setSelectedAction(response.data.action);
    } catch (error) {
      setDetailError(actionErrorView(error, t).message);
    } finally {
      setDetailLoading(false);
    }
  }

  function renderContent() {
    if (pageState === "loading") {
      return (
        <div className="mm-grid mm-grid-2">
          <section className="mm-card">
            <Skeleton lines={6} widths={["42%", "90%", "84%", "78%", "72%", "64%"]} />
          </section>
          <section className="mm-card">
            <Skeleton lines={5} widths={["30%", "80%", "72%", "62%", "48%"]} />
          </section>
        </div>
      );
    }

    if (pageState !== "loaded") {
      const error =
        pageError ??
        ({
          state: "error",
          title: t("actions.errorTitle"),
          message: t("digest.genericError"),
        } satisfies ActionErrorView);

      return (
        <EmptyState
          title={error.title}
          hint={error.message}
          action={
            error.state === "unauthorized" ? (
              <a href="/login">{t("account.signIn")}</a>
            ) : (
              <button type="button" className="mm-btn" onClick={onRetry}>
                {t("common.retry")}
              </button>
            )
          }
        />
      );
    }

    return (
      <div className="mm-grid mm-grid-2">
        <section className="mm-card">
          <div className="mm-spread" style={{ alignItems: "flex-start" }}>
            <div>
              <div className="mm-card-title">{t("actions.history")}</div>
              <p className="mm-muted" style={{ fontSize: 13 }}>
                {t("actions.shown")
                  .replace("{{filtered}}", String(filteredActions.length))
                  .replace("{{total}}", String(actions.length))}
              </p>
            </div>
            <button type="button" className="mm-btn" onClick={() => void loadActions()}>
              {t("common.refresh")}
            </button>
          </div>

          <div className="mm-row" style={{ marginTop: 14 }}>
            <label className="mm-field" style={{ marginBottom: 0 }}>
              <span className="mm-label">{t("actions.actionType")}</span>
              <select
                className="mm-input"
                value={actionTypeFilter}
                onChange={(event) => setActionTypeFilter(event.target.value)}
              >
                <option value="all">{t("actions.all")}</option>
                {actionTypes.map((type) => (
                  <option key={type} value={type}>
                    {statusLabel(type)}
                  </option>
                ))}
              </select>
            </label>

            <label className="mm-field" style={{ marginBottom: 0 }}>
              <span className="mm-label">{t("actions.status")}</span>
              <select
                className="mm-input"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="all">{t("actions.all")}</option>
                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {statusLabel(status)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {filteredActions.length === 0 ? (
            <div style={{ marginTop: 18 }}>
              <EmptyState
                title={actions.length === 0 ? t("actions.noActionsTitle") : t("actions.noMatchingTitle")}
                hint={
                  actions.length === 0
                    ? t("actions.noActionsHint")
                    : t("actions.noMatchingHint")
                }
              />
            </div>
          ) : (
            <div className="mm-stack" style={{ gap: 0, marginTop: 16 }}>
              {filteredActions.map((action, index) => (
                <ActionListRow
                  key={action.id}
                  action={action}
                  selected={selectedActionId === action.id}
                  showTopBorder={index > 0}
                  onSelect={onSelectAction}
                  t={t}
                />
              ))}
            </div>
          )}
        </section>

        <ActionDetailPanel
          action={selectedAction}
          loading={detailLoading}
          error={detailError}
          t={t}
        />
      </div>
    );
  }

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title={t("actions.title")}
        description={t("actions.pageDescription")}
        badge={false}
      >
        {renderContent()}
      </PageFrame>
    </AppShell>
  );
}

function ActionListRow({
  action,
  selected,
  showTopBorder,
  onSelect,
  t,
}: {
  action: UserAction;
  selected: boolean;
  showTopBorder: boolean;
  onSelect: (actionId: string) => Promise<void>;
  t: TFunction;
}) {
  return (
    <button
      type="button"
      onClick={() => void onSelect(action.id)}
      className="mm-card"
      style={{
        width: "100%",
        textAlign: "left",
        boxShadow: "none",
        marginTop: showTopBorder ? 12 : 0,
        borderColor: selected ? "var(--color-primary)" : "var(--color-border)",
        cursor: "pointer",
      }}
    >
      <div className="mm-spread" style={{ alignItems: "flex-start" }}>
        <div style={{ minWidth: 0 }}>
          <div
            style={{
              fontWeight: 650,
              overflowWrap: "anywhere",
            }}
          >
            {statusLabel(action.action_type)}
          </div>
          <p className="mm-muted" style={{ fontSize: 12, marginTop: 4 }}>
            {formatDateTime(action.created_at, t)}
          </p>
        </div>
        <Badge tone={actionTone(action.action_status)} dot>
          {statusLabel(action.action_status)}
        </Badge>
      </div>
      <div className="mm-row" style={{ marginTop: 10 }}>
        <Badge tone={providerTone(action.provider_effect)}>
          {statusLabel(action.provider_effect)}
        </Badge>
        <Badge tone="neutral">{statusLabel(action.source)}</Badge>
      </div>
    </button>
  );
}

function ActionDetailPanel({
  action,
  loading,
  error,
  t,
}: {
  action: UserAction | null;
  loading: boolean;
  error: string | null;
  t: TFunction;
}) {
  return (
    <section className="mm-card">
      <div className="mm-card-title">{t("actions.detail")}</div>

      {loading ? (
        <Skeleton lines={5} widths={["40%", "82%", "70%", "62%", "52%"]} />
      ) : error ? (
        <EmptyState title={t("actions.detailUnavailable")} hint={error} />
      ) : action ? (
        <div className="mm-stack">
          <div className="mm-row">
            <Badge tone={actionTone(action.action_status)} dot>
              {statusLabel(action.action_status)}
            </Badge>
            <Badge tone={providerTone(action.provider_effect)}>
              {statusLabel(action.provider_effect)}
            </Badge>
          </div>

          <DetailLine label={t("actions.actionType")} value={statusLabel(action.action_type)} />
          <DetailLine label={t("actions.source")} value={statusLabel(action.source)} />
          <DetailLine label={t("actions.created")} value={formatDateTime(action.created_at, t)} />
          <DetailLine label={t("actions.executed")} value={formatDateTime(action.executed_at, t)} />

          {action.error_message ? (
            <div>
              <div className="mm-label">{t("actions.error")}</div>
              <p
                style={{
                  color: "var(--color-danger)",
                  overflowWrap: "anywhere",
                }}
              >
                {action.error_message}
              </p>
            </div>
          ) : null}
        </div>
      ) : (
        <EmptyState
          title={t("actions.selectTitle")}
          hint={t("actions.selectHint")}
        />
      )}
    </section>
  );
}

function DetailLine({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mm-label">{label}</div>
      <div style={{ overflowWrap: "anywhere" }}>{value}</div>
    </div>
  );
}
