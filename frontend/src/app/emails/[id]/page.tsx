"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { EmailDetailView } from "@/components/email-detail-view";
import { EmailLoadingState } from "@/components/email-loading-state";
import { EmailErrorState } from "@/components/email-error-state";
import { useAuth } from "@/lib/auth";
import {
  getEmail,
  markEmailRead,
  markEmailUnread,
} from "@/lib/api-client";
import type { EmailDetail } from "@/lib/api-types";
import {
  buildEmailListHref,
  displaySubject,
  emailErrorView,
  mergeEmailMutation,
  type EmailErrorView,
} from "@/lib/emails";

type EmailDetailState =
  | "loading"
  | "loaded"
  | "unauthorized"
  | "not_found"
  | "backend_unavailable"
  | "error";

export default function EmailDetailPage() {
  const params = useParams<{ id: string }>();
  const emailId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { status: authStatus, refresh: refreshAuth } = useAuth();

  const [pageState, setPageState] = useState<EmailDetailState>("loading");
  const [email, setEmail] = useState<EmailDetail | null>(null);
  const [pageError, setPageError] = useState<EmailErrorView | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [marking, setMarking] = useState(false);
  const [backHref, setBackHref] = useState("/emails");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setBackHref(
      buildEmailListHref({
        filter: params.get("filter"),
        query: params.get("q"),
      }),
    );
  }, []);

  const loadEmail = useCallback(async (): Promise<boolean> => {
    if (!emailId) {
      setEmail(null);
      setPageError({
        kind: "not_found",
        title: "Email not found",
        message: "The route did not include an email id.",
      });
      setPageState("not_found");
      return false;
    }

    setPageState("loading");
    setPageError(null);
    setActionError(null);

    try {
      const response = await getEmail(emailId);
      setEmail(response.data.email);
      setPageState("loaded");
      return true;
    } catch (error) {
      const view = emailErrorView(error);
      setEmail(null);
      setPageError(view);
      setPageState(
        view.kind === "unauthorized"
          ? "unauthorized"
          : view.kind === "not_found"
            ? "not_found"
            : view.kind === "backend_unavailable"
              ? "backend_unavailable"
              : "error",
      );
      return false;
    }
  }, [emailId]);

  useEffect(() => {
    if (authStatus === "loading") {
      setPageState("loading");
      return;
    }

    if (authStatus === "unauthenticated") {
      setEmail(null);
      setPageError({
        kind: "unauthorized",
        title: "Not signed in",
        message: "Sign in with your MailMind account to load this email.",
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setEmail(null);
      setPageError({
        kind: "backend_unavailable",
        title: "Backend unavailable",
        message: "Unable to reach the server. Check that the backend is running.",
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadEmail();
  }, [authStatus, loadEmail]);

  async function onRetry() {
    if (authStatus === "authenticated") {
      await loadEmail();
      return;
    }

    await refreshAuth();
  }

  async function updateReadState(nextReadState: boolean) {
    if (!email) {
      return;
    }

    setActionError(null);
    setMarking(true);

    try {
      const response = nextReadState
        ? await markEmailRead(email.id)
        : await markEmailUnread(email.id);
      const mutation = response.data.email;

      if (typeof mutation.is_read === "boolean") {
        setEmail((current) =>
          current ? mergeEmailMutation(current, mutation) : current,
        );
      } else {
        await loadEmail();
      }
    } catch (error) {
      setActionError(emailErrorView(error).message);
    } finally {
      setMarking(false);
    }
  }

  function renderContent() {
    if (pageState === "loading") {
      return <EmailLoadingState title="Loading email" />;
    }

    if (pageState !== "loaded" || email === null) {
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
              <div className="mm-row">
                <Link className="mm-btn" href={backHref}>
                  Back to emails
                </Link>
                <button type="button" className="mm-btn" onClick={onRetry}>
                  Retry
                </button>
              </div>
            )
          }
        />
      );
    }

    return (
      <EmailDetailView
        email={email}
        busy={marking}
        actionError={actionError}
        backHref={backHref}
        onMarkRead={() => void updateReadState(true)}
        onMarkUnread={() => void updateReadState(false)}
      />
    );
  }

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title={email ? displaySubject(email.subject) : "Email detail"}
        description="Message content and read state from the connected mailbox."
        badge={false}
      >
        {renderContent()}
      </PageFrame>
    </AppShell>
  );
}
