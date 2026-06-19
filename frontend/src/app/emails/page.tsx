"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { EmailList } from "@/components/email-list";
import { EmailLoadingState } from "@/components/email-loading-state";
import { EmailErrorState } from "@/components/email-error-state";
import { EmailEmptyState } from "@/components/email-empty-state";
import { useAuth } from "@/lib/auth";
import {
  listTodayEmails,
  markEmailRead,
  markEmailUnread,
} from "@/lib/api-client";
import type { EmailSummary } from "@/lib/api-types";
import {
  EMAIL_READ_FILTERS,
  emailErrorView,
  filterEmails,
  mergeEmailMutation,
  type EmailErrorView,
  type EmailReadFilter,
} from "@/lib/emails";

type EmailsPageState =
  | "loading"
  | "loaded"
  | "unauthorized"
  | "backend_unavailable"
  | "error";

export default function EmailsTodayPage() {
  const { status: authStatus, refresh: refreshAuth } = useAuth();
  const [pageState, setPageState] = useState<EmailsPageState>("loading");
  const [emails, setEmails] = useState<EmailSummary[]>([]);
  const [filter, setFilter] = useState<EmailReadFilter>("all");
  const [pageError, setPageError] = useState<EmailErrorView | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyEmailId, setBusyEmailId] = useState<string | null>(null);

  const filteredEmails = useMemo(
    () => filterEmails(emails, filter),
    [emails, filter],
  );

  const loadEmails = useCallback(async (): Promise<boolean> => {
    setPageState("loading");
    setPageError(null);
    setActionError(null);

    try {
      const response = await listTodayEmails();
      setEmails(response.data.emails);
      setPageState("loaded");
      return true;
    } catch (error) {
      const view = emailErrorView(error);
      setEmails([]);
      setPageError(view);
      setPageState(
        view.kind === "unauthorized"
          ? "unauthorized"
          : view.kind === "backend_unavailable"
            ? "backend_unavailable"
            : "error",
      );
      return false;
    }
  }, []);

  useEffect(() => {
    if (authStatus === "loading") {
      setPageState("loading");
      return;
    }

    if (authStatus === "unauthenticated") {
      setEmails([]);
      setPageError({
        kind: "unauthorized",
        title: "Not signed in",
        message: "Sign in with your MailMind account to load emails.",
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setEmails([]);
      setPageError({
        kind: "backend_unavailable",
        title: "Backend unavailable",
        message: "Unable to reach the server. Check that the backend is running.",
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadEmails();
  }, [authStatus, loadEmails]);

  async function onRefresh() {
    if (authStatus === "authenticated") {
      await loadEmails();
      return;
    }

    await refreshAuth();
  }

  async function updateReadState(emailId: string, nextReadState: boolean) {
    setActionError(null);
    setBusyEmailId(emailId);

    try {
      const response = nextReadState
        ? await markEmailRead(emailId)
        : await markEmailUnread(emailId);
      const mutation = response.data.email;

      if (typeof mutation.is_read === "boolean") {
        setEmails((current) =>
          current.map((email) => mergeEmailMutation(email, mutation)),
        );
      } else {
        await loadEmails();
      }
    } catch (error) {
      setActionError(emailErrorView(error).message);
    } finally {
      setBusyEmailId(null);
    }
  }

  function renderContent() {
    if (pageState === "loading") {
      return <EmailLoadingState />;
    }

    if (pageState !== "loaded") {
      const error =
        pageError ??
        ({
          kind: "error",
          title: "Email error",
          message: "Something went wrong. Please try again.",
        } satisfies EmailErrorView);

      return (
        <EmailErrorState
          error={error}
          action={
            error.kind === "unauthorized" ? (
              <a href="/login">Sign in</a>
            ) : (
              <button type="button" className="mm-btn" onClick={onRefresh}>
                Retry
              </button>
            )
          }
        />
      );
    }

    if (emails.length === 0) {
      return (
        <EmailEmptyState
          title="No emails today"
          hint="No messages were returned for today."
          action={
            <button type="button" className="mm-btn" onClick={onRefresh}>
              Refresh
            </button>
          }
        />
      );
    }

    if (filteredEmails.length === 0) {
      return (
        <EmailEmptyState
          title="No matching emails"
          hint="The current read filter has no matching messages."
        />
      );
    }

    return (
      <EmailList
        emails={filteredEmails}
        busyEmailId={busyEmailId}
        onMarkRead={(emailId) => void updateReadState(emailId, true)}
        onMarkUnread={(emailId) => void updateReadState(emailId, false)}
      />
    );
  }

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Emails"
        description="Messages received today from connected mailboxes."
        badge={false}
      >
        <section className="mm-card">
          <div className="mm-spread" style={{ alignItems: "flex-start" }}>
            <div className="mm-row">
              <SegmentedControl
                label="Read filter"
                value={filter}
                options={EMAIL_READ_FILTERS}
                onChange={setFilter}
              />
              <Badge tone="neutral" dot>
                {filteredEmails.length} shown
              </Badge>
            </div>
            <button
              type="button"
              className="mm-btn"
              onClick={onRefresh}
              disabled={pageState === "loading"}
              aria-disabled={pageState === "loading"}
            >
              Refresh
            </button>
          </div>

          {actionError ? (
            <div style={{ marginTop: 14 }}>
              <Badge tone="danger" dot>
                {actionError}
              </Badge>
            </div>
          ) : null}
        </section>

        {renderContent()}
      </PageFrame>
    </AppShell>
  );
}
