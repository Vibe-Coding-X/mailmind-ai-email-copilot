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

function actionErrorView(error: unknown): ActionErrorView {
  if (error instanceof ApiRequestError) {
    if (error.status === 401 || error.code === "UNAUTHORIZED") {
      return {
        state: "unauthorized",
        title: "Not signed in",
        message: "Sign in with your MailMind account to view action history.",
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
      title: "Actions error",
      message: error.message,
    };
  }

  return {
    state: "error",
    title: "Actions error",
    message: "Something went wrong. Please try again.",
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

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Not executed";
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
      const view = actionErrorView(error);
      setActions([]);
      setSelectedActionId(null);
      setSelectedAction(null);
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
      setActions([]);
      setPageError({
        state: "unauthorized",
        title: "Not signed in",
        message: "Sign in with your MailMind account to view action history.",
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setActions([]);
      setPageError({
        state: "backend_unavailable",
        title: "Backend unavailable",
        message: "Unable to reach the server. Check that the backend is running.",
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadActions();
  }, [authStatus, loadActions]);

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
      setDetailError(actionErrorView(error).message);
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
          title: "Actions error",
          message: "Something went wrong. Please try again.",
        } satisfies ActionErrorView);

      return (
        <EmptyState
          title={error.title}
          hint={error.message}
          action={
            error.state === "unauthorized" ? (
              <a href="/login">Sign in</a>
            ) : (
              <button type="button" className="mm-btn" onClick={onRetry}>
                Retry
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
              <div className="mm-card-title">Action history</div>
              <p className="mm-muted" style={{ fontSize: 13 }}>
                {filteredActions.length} shown from {actions.length} recorded actions.
              </p>
            </div>
            <button type="button" className="mm-btn" onClick={() => void loadActions()}>
              Refresh
            </button>
          </div>

          <div className="mm-row" style={{ marginTop: 14 }}>
            <label className="mm-field" style={{ marginBottom: 0 }}>
              <span className="mm-label">Action type</span>
              <select
                className="mm-input"
                value={actionTypeFilter}
                onChange={(event) => setActionTypeFilter(event.target.value)}
              >
                <option value="all">All</option>
                {actionTypes.map((type) => (
                  <option key={type} value={type}>
                    {statusLabel(type)}
                  </option>
                ))}
              </select>
            </label>

            <label className="mm-field" style={{ marginBottom: 0 }}>
              <span className="mm-label">Status</span>
              <select
                className="mm-input"
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option value="all">All</option>
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
                title={actions.length === 0 ? "No actions recorded" : "No matching actions"}
                hint={
                  actions.length === 0
                    ? "User actions will appear here after email or digest operations."
                    : "Adjust the filters to view more action history."
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
                />
              ))}
            </div>
          )}
        </section>

        <ActionDetailPanel
          action={selectedAction}
          loading={detailLoading}
          error={detailError}
        />
      </div>
    );
  }

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Actions"
        description="Recent MailMind actions and provider effects."
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
}: {
  action: UserAction;
  selected: boolean;
  showTopBorder: boolean;
  onSelect: (actionId: string) => Promise<void>;
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
            {formatDateTime(action.created_at)}
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
}: {
  action: UserAction | null;
  loading: boolean;
  error: string | null;
}) {
  return (
    <section className="mm-card">
      <div className="mm-card-title">Action detail</div>

      {loading ? (
        <Skeleton lines={5} widths={["40%", "82%", "70%", "62%", "52%"]} />
      ) : error ? (
        <EmptyState title="Action detail unavailable" hint={error} />
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

          <DetailLine label="Action type" value={statusLabel(action.action_type)} />
          <DetailLine label="Source" value={statusLabel(action.source)} />
          <DetailLine label="Created" value={formatDateTime(action.created_at)} />
          <DetailLine label="Executed" value={formatDateTime(action.executed_at)} />

          {action.error_message ? (
            <div>
              <div className="mm-label">Error</div>
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
          title="Select an action"
          hint="Choose an action from the list to view status and provider effect."
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
