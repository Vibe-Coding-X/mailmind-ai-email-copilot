"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { SettingsSection } from "@/components/settings-section";
import { EmptyState } from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  MailboxSyncCard,
  type MailboxSyncStatusView,
} from "@/components/mailbox-sync-card";
import { useAuth } from "@/lib/auth";
import {
  ApiRequestError,
  disconnectGmail,
  getMailboxSyncStatus,
  listMailboxes,
  startGmailLogin,
  triggerMailboxSync,
} from "@/lib/api-client";
import type { Mailbox } from "@/lib/api-types";
import {
  formatDateTimeWithRelative,
  mailboxStateMessage,
  requiresGmailReconnect,
  syncResultMessage,
} from "@/lib/mailboxes";

type MailboxLoadState =
  | "loading"
  | "loaded"
  | "not_signed_in"
  | "backend_unavailable"
  | "error";

const GMAIL_PROVIDER = "gmail";
const SYSTEM_AUTH_ERROR_CODE = "UNAUTHORIZED";
const GMAIL_REAUTH_ERROR_CODE = "MAILBOX_REAUTH_REQUIRED";

function isSystemAuthError(error: ApiRequestError): boolean {
  return error.status === 401 && error.code === SYSTEM_AUTH_ERROR_CODE;
}

function isGmailReauthError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError && error.code === GMAIL_REAUTH_ERROR_CODE
  );
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return error.status === 0 ? "Backend unavailable" : error.message;
  }

  return "Something went wrong. Please try again.";
}

function toMailboxLoadState(error: unknown): {
  state: MailboxLoadState;
  message: string;
} {
  if (error instanceof ApiRequestError) {
    if (isSystemAuthError(error)) {
      return {
        state: "not_signed_in",
        message: "Sign in before managing Gmail authorization.",
      };
    }

    if (error.status === 0) {
      return {
        state: "backend_unavailable",
        message: "Unable to reach the server. Check that the backend is running.",
      };
    }

    return { state: "error", message: error.message };
  }

  return {
    state: "error",
    message: "Something went wrong. Please try again.",
  };
}

function isGmailMailbox(mailbox: Mailbox): boolean {
  return mailbox.provider.toLowerCase() === GMAIL_PROVIDER;
}

function statusLabel(status: string): string {
  return status.replaceAll("_", " ");
}

function mailboxStatusTone(status: string): BadgeTone {
  switch (status) {
    case "connected":
      return "ok";
    case "reauthorization_required":
    case "reauth_required":
      return "warn";
    case "error":
      return "danger";
    case "disconnected":
      return "neutral";
    default:
      return "info";
  }
}

function actionButtonStyle(disabled: boolean): React.CSSProperties {
  return { cursor: disabled ? "not-allowed" : "pointer" };
}

function gmailOverview(
  loadState: MailboxLoadState,
  gmailMailbox: Mailbox | null,
): { text: string; tone: BadgeTone } {
  if (loadState === "loading") {
    return { text: "Checking Gmail", tone: "neutral" };
  }

  if (loadState === "not_signed_in") {
    return { text: "Not signed in", tone: "neutral" };
  }

  if (loadState === "backend_unavailable") {
    return { text: "Backend unavailable", tone: "danger" };
  }

  if (loadState === "error") {
    return { text: "Gmail state unavailable", tone: "danger" };
  }

  if (gmailMailbox === null) {
    return { text: "Gmail not connected", tone: "neutral" };
  }

  return {
    text: `Gmail ${statusLabel(gmailMailbox.status)}`,
    tone: mailboxStatusTone(gmailMailbox.status),
  };
}

export default function MailboxSettingsPage() {
  const { status: authStatus, refresh: refreshAuth } = useAuth();
  const [loadState, setLoadState] = useState<MailboxLoadState>("loading");
  const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
  const [syncStatuses, setSyncStatuses] = useState<
    Record<string, MailboxSyncStatusView>
  >({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [syncingMailboxId, setSyncingMailboxId] = useState<string | null>(null);

  const refreshSyncStatuses = useCallback(async (nextMailboxes: Mailbox[]) => {
    if (nextMailboxes.length === 0) {
      setSyncStatuses({});
      return;
    }

    setSyncStatuses(
      Object.fromEntries(
        nextMailboxes.map((mailbox) => [mailbox.id, { state: "loading" }]),
      ),
    );

    const entries = await Promise.all(
      nextMailboxes.map(async (mailbox) => {
        try {
          const response = await getMailboxSyncStatus(mailbox.id);
          return [
            mailbox.id,
            { state: "loaded", data: response.data } satisfies MailboxSyncStatusView,
          ] as const;
        } catch (error) {
          return [
            mailbox.id,
            {
              state: "error",
              message: toErrorMessage(error),
            } satisfies MailboxSyncStatusView,
          ] as const;
        }
      }),
    );

    setSyncStatuses(Object.fromEntries(entries));
  }, []);

  const loadMailboxList = useCallback(async (): Promise<boolean> => {
    setLoadState("loading");
    setLoadError(null);

    try {
      const response = await listMailboxes();
      setMailboxes(response.data.mailboxes);
      setLoadState("loaded");
      void refreshSyncStatuses(response.data.mailboxes);
      return true;
    } catch (error) {
      const resolved = toMailboxLoadState(error);
      setMailboxes([]);
      setSyncStatuses({});
      setLoadState(resolved.state);
      setLoadError(resolved.message);
      return false;
    }
  }, [refreshSyncStatuses]);

  useEffect(() => {
    if (authStatus === "loading") {
      setLoadState("loading");
      return;
    }

    if (authStatus === "unauthenticated") {
      setMailboxes([]);
      setSyncStatuses({});
      setLoadState("not_signed_in");
      setLoadError(null);
      return;
    }

    if (authStatus === "unavailable") {
      setMailboxes([]);
      setSyncStatuses({});
      setLoadState("backend_unavailable");
      setLoadError("Unable to reach the server. Check that the backend is running.");
      return;
    }

    void loadMailboxList();
  }, [authStatus, loadMailboxList]);

  const gmailMailbox = useMemo(
    () => mailboxes.find(isGmailMailbox) ?? null,
    [mailboxes],
  );

  const gmailStatus = gmailMailbox?.status ?? "not_connected";
  const gmailSummary = gmailOverview(loadState, gmailMailbox);
  const canAct = authStatus === "authenticated";
  const showConnect =
    canAct &&
    (gmailMailbox === null ||
      gmailStatus === "disconnected" ||
      gmailStatus === "reauthorization_required" ||
      gmailStatus === "reauth_required" ||
      gmailStatus === "error");
  const showDisconnect =
    canAct && gmailMailbox !== null && gmailStatus !== "disconnected";

  async function onConnectGmail() {
    setActionError(null);
    setActionMessage(null);
    setConnecting(true);

    try {
      const response = await startGmailLogin();
      if (response.data.authorization_url.trim().length === 0) {
        throw new Error("Backend did not return an authorization URL.");
      }

      window.location.href = response.data.authorization_url;
    } catch (error) {
      const resolved = toMailboxLoadState(error);
      if (
        resolved.state === "not_signed_in" ||
        resolved.state === "backend_unavailable"
      ) {
        setLoadState(resolved.state);
        setLoadError(resolved.message);
      }
      setActionError(toErrorMessage(error));
      setConnecting(false);
    }
  }

  async function onDisconnectGmail() {
    const confirmed = window.confirm(
      "Disconnect Gmail from MailMind? Email data already synced remains in MailMind, but new Gmail syncs will stop.",
    );
    if (!confirmed) {
      return;
    }

    setActionError(null);
    setActionMessage(null);
    setDisconnecting(true);

    try {
      await disconnectGmail();
      const refreshed = await loadMailboxList();
      if (refreshed) {
        setActionMessage("Gmail disconnected. Mailbox list refreshed.");
      }
    } catch (error) {
      const resolved = toMailboxLoadState(error);
      if (
        resolved.state === "not_signed_in" ||
        resolved.state === "backend_unavailable"
      ) {
        setLoadState(resolved.state);
        setLoadError(resolved.message);
      }
      setActionError(toErrorMessage(error));
    } finally {
      setDisconnecting(false);
    }
  }

  async function onSyncMailbox(mailboxId: string) {
    setActionError(null);
    setActionMessage(null);
    setSyncingMailboxId(mailboxId);
    setSyncStatuses((current) => ({
      ...current,
      [mailboxId]: { state: "loading" },
    }));

    try {
      const response = await triggerMailboxSync(mailboxId);
      setActionMessage(syncResultMessage(response.data));
      await loadMailboxList();
    } catch (error) {
      const message = toErrorMessage(error);
      const resolved = toMailboxLoadState(error);
      if (
        resolved.state === "not_signed_in" ||
        resolved.state === "backend_unavailable"
      ) {
        setLoadState(resolved.state);
        setLoadError(resolved.message);
      }
      setSyncStatuses((current) => ({
        ...current,
        [mailboxId]: { state: "error", message },
      }));
      setActionError(message);
      if (isGmailReauthError(error)) {
        await loadMailboxList();
      }
    } finally {
      setSyncingMailboxId(null);
    }
  }

  async function onRetry() {
    setActionError(null);
    setActionMessage(null);

    if (authStatus === "authenticated") {
      await loadMailboxList();
      return;
    }

    await refreshAuth();
  }

  function renderMailboxList() {
    if (loadState === "loading") {
      return <Skeleton lines={4} widths={["42%", "80%", "65%", "52%"]} />;
    }

    if (loadState === "not_signed_in") {
      return (
        <EmptyState
          title="Not signed in"
          hint="Sign in with your MailMind account before connecting Gmail."
          action={<a href="/login">Sign in</a>}
        />
      );
    }

    if (loadState === "backend_unavailable") {
      return (
        <EmptyState
          title="Backend unavailable"
          hint={loadError ?? "Unable to reach the server."}
          action={
            <button
              type="button"
              className="mm-btn"
              onClick={onRetry}
              style={actionButtonStyle(false)}
            >
              Retry
            </button>
          }
        />
      );
    }

    if (loadState === "error") {
      return (
        <EmptyState
          title="Mailbox error"
          hint={loadError ?? "The backend returned an error."}
          action={
            <button
              type="button"
              className="mm-btn"
              onClick={onRetry}
              style={actionButtonStyle(false)}
            >
              Retry
            </button>
          }
        />
      );
    }

    if (mailboxes.length === 0) {
      return (
        <EmptyState
          title="Not connected"
          hint="No mailboxes are connected."
        />
      );
    }

    return (
      <div className="mm-stack" style={{ gap: 0 }}>
        {mailboxes.map((mailbox, index) => (
          <div
            key={mailbox.id}
            style={{
              borderTop: index === 0 ? 0 : "1px solid var(--mm-border)",
              padding: index === 0 ? "0 0 16px" : "16px 0",
            }}
          >
            <div className="mm-spread" style={{ alignItems: "flex-start" }}>
              <div>
                <h3 style={{ fontSize: 14 }}>{mailbox.email_address}</h3>
                <p className="mm-muted" style={{ fontSize: 12, marginTop: 2 }}>
                  {mailbox.provider} account
                </p>
                <p className="mm-muted" style={{ fontSize: 12, marginTop: 6 }}>
                  {mailboxStateMessage(mailbox)}
                </p>
              </div>
              <Badge tone={mailboxStatusTone(mailbox.status)} dot>
                {statusLabel(mailbox.status)}
              </Badge>
            </div>

            <div style={{ marginTop: 14 }}>
              <MailboxSyncCard
                mailbox={mailbox}
                syncStatus={syncStatuses[mailbox.id]}
                syncing={syncingMailboxId === mailbox.id}
                onSync={(mailboxId) => void onSyncMailbox(mailboxId)}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const connectDisabled =
    !canAct ||
    connecting ||
    disconnecting ||
    loadState === "loading" ||
    loadState === "backend_unavailable";
  const disconnectDisabled = !canAct || connecting || disconnecting;

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Mailboxes"
        description="Connect and manage email accounts. System login is separate from Gmail authorization."
      >
        <SettingsSection
          title="Gmail"
          description="Manage the Gmail account authorized for MailMind."
        >
          <div className="mm-spread" style={{ alignItems: "flex-start" }}>
            <div className="mm-stack" style={{ gap: 8 }}>
              <div>
                <Badge tone={gmailSummary.tone} dot>
                  {gmailSummary.text}
                </Badge>
              </div>
              {gmailMailbox ? (
                <div style={{ fontSize: 13 }}>
                  <div>{gmailMailbox.email_address}</div>
                  <div className="mm-muted" style={{ fontSize: 12, marginTop: 2 }}>
                    Updated {formatDateTimeWithRelative(gmailMailbox.updated_at)}
                  </div>
                  <p className="mm-muted" style={{ fontSize: 12, marginTop: 6 }}>
                    {mailboxStateMessage(gmailMailbox)}
                  </p>
                </div>
              ) : (
                <p className="mm-muted" style={{ fontSize: 13 }}>
                  {loadState === "not_signed_in"
                    ? "Sign in before connecting Gmail."
                    : loadState === "backend_unavailable"
                      ? "Mailbox state cannot be loaded until the backend is reachable."
                      : "No Gmail mailbox was returned by the backend."}
                </p>
              )}
            </div>

            <div className="mm-row" style={{ justifyContent: "flex-end" }}>
              {showConnect ? (
                <button
                  type="button"
                  className="mm-btn mm-btn--primary"
                  onClick={onConnectGmail}
                  disabled={connectDisabled}
                  aria-disabled={connectDisabled}
                  style={actionButtonStyle(connectDisabled)}
                >
                  {connecting
                    ? "Starting Gmail..."
                    : gmailMailbox && requiresGmailReconnect(gmailMailbox)
                      ? "Reconnect Gmail"
                      : "Connect Gmail"}
                </button>
              ) : null}

              {showDisconnect ? (
                <button
                  type="button"
                  className="mm-btn"
                  onClick={onDisconnectGmail}
                  disabled={disconnectDisabled}
                  aria-disabled={disconnectDisabled}
                  style={actionButtonStyle(disconnectDisabled)}
                >
                  {disconnecting ? "Disconnecting..." : "Disconnect Gmail"}
                </button>
              ) : null}
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
        </SettingsSection>

        <SettingsSection
          title="Mailbox list"
          description={
            mailboxes.length > 1
              ? "Connected mailbox state and sync activity. Each mailbox syncs independently."
              : "Connected mailbox state and sync activity."
          }
        >
          {renderMailboxList()}
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
