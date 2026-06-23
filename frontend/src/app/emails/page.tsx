"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { InlineFeedback } from "@/components/inline-feedback";
import { SegmentedControl } from "@/components/ui/segmented-control";
import { EmailList } from "@/components/email-list";
import { EmailLoadingState } from "@/components/email-loading-state";
import { EmailErrorState } from "@/components/email-error-state";
import { EmailEmptyState } from "@/components/email-empty-state";
import { useAuth } from "@/lib/auth";
import {
  listMailboxes,
  listTodayEmails,
  markEmailRead,
  markEmailUnread,
} from "@/lib/api-client";
import type { EmailSummary, Mailbox } from "@/lib/api-types";
import {
  EMAIL_READ_FILTERS,
  buildEmailListHref,
  emailErrorView,
  filterEmails,
  filterEmailsByMailbox,
  filterEmailsByQuery,
  mergeEmailMutation,
  parseEmailReadFilter,
  type EmailErrorView,
  type EmailReadFilter,
} from "@/lib/emails";
import { useI18n } from "@/i18n/provider";
import { MailboxProviderBadge } from "@/components/mailbox-provider-badge";

type EmailsPageState =
  | "loading"
  | "loaded"
  | "unauthorized"
  | "backend_unavailable"
  | "error";

export default function EmailsTodayPage() {
  const { t } = useI18n();
  const { status: authStatus, refresh: refreshAuth } = useAuth();
  const [pageState, setPageState] = useState<EmailsPageState>("loading");
  const [emails, setEmails] = useState<EmailSummary[]>([]);
  const [mailboxes, setMailboxes] = useState<Mailbox[]>([]);
  const [filter, setFilter] = useState<EmailReadFilter>("all");
  const [mailboxFilter, setMailboxFilter] = useState("");
  const [mailboxParamProvided, setMailboxParamProvided] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [urlStateLoaded, setUrlStateLoaded] = useState(false);
  const [pageError, setPageError] = useState<EmailErrorView | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyEmailId, setBusyEmailId] = useState<string | null>(null);

  const filteredEmails = useMemo(
    () =>
      filterEmailsByQuery(
        filterEmailsByMailbox(filterEmails(emails, filter), mailboxFilter),
        searchQuery,
      ),
    [emails, filter, mailboxFilter, searchQuery],
  );
  const mailboxesById = useMemo(
    () => Object.fromEntries(mailboxes.map((mailbox) => [mailbox.id, mailbox])),
    [mailboxes],
  );
  const actionSupportByEmailId = useMemo(
    () =>
      Object.fromEntries(
        filteredEmails.map((email) => {
          const capabilities = mailboxesById[email.mailbox_id]?.capabilities;
          const canMarkRead = capabilities?.can_mark_read ?? true;
          const canMarkUnread = capabilities?.can_mark_unread ?? true;
          return [
            email.id,
            {
              canMarkRead,
              canMarkUnread,
              disabledReason:
                !canMarkRead || !canMarkUnread
                  ? t("emails.unsupportedProviderAction")
                  : undefined,
            },
          ];
        }),
      ),
    [filteredEmails, mailboxesById, t],
  );
  const selectedMailbox = mailboxFilter ? mailboxesById[mailboxFilter] : null;
  const sourceLabelByEmailId = useMemo(
    () =>
      Object.fromEntries(
        filteredEmails.map((email) => {
          const mailbox = mailboxesById[email.mailbox_id];
          if (!mailbox || mailboxFilter) {
            return [email.id, ""];
          }
          return [
            email.id,
            `${mailbox.display_name || mailbox.email_address} · ${mailbox.provider.toUpperCase()}`,
          ];
        }),
      ),
    [filteredEmails, mailboxFilter, mailboxesById],
  );
  const listHref = useMemo(
    () => buildEmailListHref({ filter, mailboxId: mailboxFilter, query: searchQuery }),
    [filter, mailboxFilter, searchQuery],
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setFilter(parseEmailReadFilter(params.get("filter")));
    const mailboxParam = params.get("mailbox");
    setMailboxFilter(mailboxParam ?? "");
    setMailboxParamProvided(mailboxParam !== null);
    setSearchQuery(params.get("q") ?? "");
    setUrlStateLoaded(true);
  }, []);

  useEffect(() => {
    if (pageState !== "loaded" || mailboxParamProvided || mailboxFilter) {
      return;
    }

    const defaultMailbox = [...mailboxes].sort((left, right) => {
      const leftTime = new Date(left.last_successful_sync_at ?? left.updated_at).getTime();
      const rightTime = new Date(right.last_successful_sync_at ?? right.updated_at).getTime();
      return rightTime - leftTime;
    })[0];

    if (defaultMailbox) {
      setMailboxFilter(defaultMailbox.id);
    }
  }, [mailboxFilter, mailboxParamProvided, mailboxes, pageState]);

  useEffect(() => {
    if (!urlStateLoaded) {
      return;
    }

    window.history.replaceState(null, "", listHref);
  }, [listHref, urlStateLoaded]);

  const loadEmails = useCallback(async (): Promise<boolean> => {
    setPageState("loading");
    setPageError(null);
    setActionError(null);

    try {
      const [emailResponse, mailboxResponse] = await Promise.all([
        listTodayEmails(),
        listMailboxes(),
      ]);
      setEmails(emailResponse.data.emails);
      setMailboxes(mailboxResponse.data.mailboxes);
      setPageState("loaded");
      return true;
    } catch (error) {
      const view = emailErrorView(error);
      setEmails([]);
      setMailboxes([]);
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
      setMailboxes([]);
      setPageError({
        kind: "unauthorized",
        title: t("account.notSignedIn"),
        message: t("emails.notSignedInMessage"),
      });
      setPageState("unauthorized");
      return;
    }

    if (authStatus === "unavailable") {
      setEmails([]);
      setMailboxes([]);
      setPageError({
        kind: "backend_unavailable",
        title: t("account.backendUnavailable"),
        message: t("digest.backendUnavailableMessage"),
      });
      setPageState("backend_unavailable");
      return;
    }

    void loadEmails();
  }, [authStatus, loadEmails, t]);

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
              <button type="button" className="mm-btn" onClick={onRefresh}>
                {t("common.retry")}
              </button>
            )
          }
        />
      );
    }

    if (mailboxes.length === 0) {
      return (
        <EmailEmptyState
          title={t("emails.noMailboxTitle")}
          hint={t("emails.noMailboxHint")}
          action={<a href="/settings/mailboxes">{t("mailboxes.addTitle")}</a>}
        />
      );
    }

    if (emails.length === 0) {
      return (
        <EmailEmptyState
          title={t("emails.noTodayTitle")}
          hint={t("emails.noTodayHint")}
          action={
            <button type="button" className="mm-btn" onClick={onRefresh}>
              {t("common.refresh")}
            </button>
          }
        />
      );
    }

    if (filteredEmails.length === 0) {
      return (
        <EmailEmptyState
          title={t("emails.noMatchingTitle")}
          hint={
            searchQuery.trim().length > 0
              ? t("emails.noMatchingSearchHint")
              : t("emails.noMatchingFilterHint")
          }
        />
      );
    }

    return (
      <EmailList
        emails={filteredEmails}
        busyEmailId={busyEmailId}
        listHref={listHref}
        actionSupportByEmailId={actionSupportByEmailId}
        sourceLabelByEmailId={sourceLabelByEmailId}
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
        title={t("emails.title")}
        description={t("emails.description")}
        badge={false}
      >
        <section className="mm-card">
          <div className="mm-spread" style={{ alignItems: "flex-start" }}>
            <div className="mm-row">
              <SegmentedControl
                label={t("emails.readFilter")}
                value={filter}
                options={EMAIL_READ_FILTERS}
                onChange={setFilter}
              />
              <label className="mm-field" style={{ marginBottom: 0 }}>
                <span className="mm-label">{t("common.search")}</span>
                <input
                  className="mm-input"
                  type="search"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder={t("emails.searchPlaceholder")}
                  style={{ minWidth: 220 }}
                />
              </label>
              <label className="mm-field" style={{ marginBottom: 0 }}>
                <span className="mm-label">{t("emails.mailboxFilter")}</span>
                <select
                  className="mm-input"
                  value={mailboxFilter}
                  onChange={(event) => {
                    setMailboxParamProvided(true);
                    setMailboxFilter(event.target.value);
                  }}
                  style={{ minWidth: 220 }}
                >
                  <option value="">{t("emails.allMailboxes")}</option>
                  {mailboxes.map((mailbox) => (
                    <option key={mailbox.id} value={mailbox.id}>
                      {mailbox.display_name || mailbox.email_address} ·{" "}
                      {mailbox.provider.toUpperCase()}
                    </option>
                  ))}
                </select>
              </label>
              <Badge tone="neutral" dot>
                {t("emails.shown").replace("{{count}}", String(filteredEmails.length))}
              </Badge>
            </div>
            <button
              type="button"
              className="mm-btn"
              onClick={onRefresh}
              disabled={pageState === "loading"}
              aria-disabled={pageState === "loading"}
            >
              {t("common.refresh")}
            </button>
          </div>

          {selectedMailbox ? (
            <div className="mm-row" style={{ marginTop: 12, gap: 8 }}>
              <MailboxProviderBadge provider={selectedMailbox.provider} />
              <span className="mm-muted" style={{ fontSize: 13 }}>
                {selectedMailbox.display_name || selectedMailbox.email_address}
              </span>
            </div>
          ) : mailboxFilter === "" ? (
            <p className="mm-muted" style={{ fontSize: 13, marginTop: 12 }}>
              {t("emails.allSourceHint")}
            </p>
          ) : null}

          {actionError ? (
            <div style={{ marginTop: 14 }}>
              <InlineFeedback tone="danger" title={t("emails.actionError")}>
                {actionError}
              </InlineFeedback>
            </div>
          ) : null}
        </section>

        {pageState === "loaded" && mailboxes.length > 0 ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(180px, 240px) minmax(0, 1fr)",
              gap: 16,
              alignItems: "start",
            }}
          >
            <section className="mm-card">
              <div className="mm-card-title">{t("emails.mailboxesTitle")}</div>
              <div className="mm-stack" style={{ gap: 8 }}>
                {mailboxes.map((mailbox) => {
                  const selected = mailboxFilter === mailbox.id;
                  return (
                    <button
                      key={mailbox.id}
                      type="button"
                      className="mm-btn"
                      onClick={() => {
                        setMailboxParamProvided(true);
                        setMailboxFilter(mailbox.id);
                      }}
                      style={{
                        justifyContent: "flex-start",
                        borderColor: selected
                          ? "var(--color-primary)"
                          : "var(--mm-border)",
                        width: "100%",
                      }}
                    >
                      {mailbox.display_name || mailbox.email_address}
                    </button>
                  );
                })}
                <button
                  type="button"
                  className="mm-btn"
                  onClick={() => {
                    setMailboxParamProvided(true);
                    setMailboxFilter("");
                  }}
                  style={{
                    justifyContent: "flex-start",
                    borderColor:
                      mailboxFilter === "" ? "var(--color-primary)" : "var(--mm-border)",
                    width: "100%",
                  }}
                >
                  {t("emails.allMailboxes")}
                </button>
              </div>
            </section>
            <div>{renderContent()}</div>
          </div>
        ) : (
          renderContent()
        )}
      </PageFrame>
    </AppShell>
  );
}
