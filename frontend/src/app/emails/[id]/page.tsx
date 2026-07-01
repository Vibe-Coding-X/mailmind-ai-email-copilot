"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { PageFrame } from "@/components/page-frame";
import { EmailDetailView } from "@/components/email-detail-view";
import { EmailLoadingState } from "@/components/email-loading-state";
import { EmailErrorState } from "@/components/email-error-state";
import { useAuth } from "@/lib/auth";
import {
  cacheEmailBody,
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
import { useI18n } from "@/i18n/provider";

type EmailDetailState =
  | "loading"
  | "loaded"
  | "unauthorized"
  | "not_found"
  | "backend_unavailable"
  | "error";

export default function EmailDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const emailId = Array.isArray(params.id) ? params.id[0] : params.id;
  const { status: authStatus, refresh: refreshAuth } = useAuth();

  const [pageState, setPageState] = useState<EmailDetailState>("loading");
  const [email, setEmail] = useState<EmailDetail | null>(null);
  const [pageError, setPageError] = useState<EmailErrorView | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [marking, setMarking] = useState(false);
  const [bodyBusy, setBodyBusy] = useState(false);
  const [backHref, setBackHref] = useState("/emails");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setBackHref(
      buildEmailListHref({
        filter: params.get("filter"),
        mailboxId: params.get("mailbox"),
        query: params.get("q"),
        range: params.get("range"),
        from: params.get("from"),
        to: params.get("to"),
      }),
    );
  }, []);

  const loadEmail = useCallback(async (): Promise<boolean> => {
    if (!emailId) {
      setEmail(null);
      setPageError({
        kind: "not_found",
        title: t("emails.notFoundTitle"),
        message: t("emails.missingId"),
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
  }, [emailId, t]);

  useEffect(() => {
    if (authStatus === "loading") {
      setPageState("loading");
      return;
    }

    if (authStatus === "unauthenticated") {
      setEmail(null);
      setPageError({
        kind: "unauthorized",
        title: t("account.notSignedIn"),
        message: t("emails.detailNotSignedIn"),
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setEmail(null);
      setPageError({
        kind: "backend_unavailable",
        title: t("account.backendUnavailable"),
        message: t("digest.backendUnavailableMessage"),
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadEmail();
  }, [authStatus, loadEmail, t]);

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

  async function fetchBody() {
    if (!email) {
      return;
    }

    setActionError(null);
    setBodyBusy(true);

    try {
      const response = await cacheEmailBody(email.id);
      setEmail(response.data.email);
    } catch (error) {
      setActionError(emailErrorView(error).message);
    } finally {
      setBodyBusy(false);
    }
  }

  function renderContent() {
    if (pageState === "loading") {
      return <EmailLoadingState title={t("emails.loadingDetail")} />;
    }

    if (pageState !== "loaded" || email === null) {
      const error =
        pageError ??
        ({
          kind: "error",
          title: t("emails.errorTitle"),
          message: t("digest.genericError"),
        } satisfies EmailErrorView);

      return (
        <EmailErrorState
          error={error}
          action={
            error.kind === "unauthorized" ? (
              <a href="/login">{t("account.signIn")}</a>
            ) : (
              <div className="mm-row">
                <Link className="mm-btn" href={backHref}>
                  {t("emails.backToEmails")}
                </Link>
                <button type="button" className="mm-btn" onClick={onRetry}>
                  {t("common.retry")}
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
        bodyBusy={bodyBusy}
        actionError={actionError}
        backHref={backHref}
        onMarkRead={() => void updateReadState(true)}
        onMarkUnread={() => void updateReadState(false)}
        onFetchBody={() => void fetchBody()}
      />
    );
  }

  return (
    <AppShell>
      <PageFrame
        title={email ? displaySubject(email.subject) : t("emails.detailTitle")}
        description={t("emails.detailDescription")}
      >
        {renderContent()}
      </PageFrame>
    </AppShell>
  );
}
