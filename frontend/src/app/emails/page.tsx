"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
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
  listEmails,
  markEmailRead,
  markEmailUnread,
} from "@/lib/api-client";
import type { EmailRange, EmailSummary, Mailbox, MailboxArchiveState } from "@/lib/api-types";
import {
  EMAIL_RANGE_FILTERS,
  EMAIL_READ_FILTERS,
  buildEmailListHref,
  emailErrorView,
  filterEmails,
  filterEmailsByMailbox,
  filterEmailsByQuery,
  mergeEmailMutation,
  parseEmailRangeFilter,
  parseEmailReadFilter,
  type EmailErrorView,
  type EmailRangeFilter,
  type EmailReadFilter,
} from "@/lib/emails";
import { useI18n, type TranslationKey } from "@/i18n/provider";
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
  const [rangeFilter, setRangeFilter] = useState<EmailRangeFilter>("today");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");
  const [mailboxFilter, setMailboxFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [pagination, setPagination] = useState({ total: 0, hasMore: false });
  const [archiveState, setArchiveState] = useState<MailboxArchiveState | null>(null);
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
    () =>
      buildEmailListHref({
        filter,
        mailboxId: mailboxFilter,
        query: searchQuery,
        range: rangeFilter,
        from: customFrom,
        to: customTo,
      }),
    [customFrom, customTo, filter, mailboxFilter, rangeFilter, searchQuery],
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setFilter(parseEmailReadFilter(params.get("filter")));
    setRangeFilter(parseEmailRangeFilter(params.get("range")));
    setCustomFrom(params.get("from") ?? "");
    setCustomTo(params.get("to") ?? "");
    setMailboxFilter(params.get("mailbox") ?? "");
    setSearchQuery(params.get("q") ?? "");
    setUrlStateLoaded(true);
  }, []);

  useEffect(() => {
    if (!urlStateLoaded) {
      return;
    }

    window.history.replaceState(null, "", listHref);
  }, [listHref, urlStateLoaded]);

  useEffect(() => {
    if (!urlStateLoaded) {
      return;
    }

    setOffset(0);
  }, [customFrom, customTo, filter, mailboxFilter, rangeFilter, searchQuery, urlStateLoaded]);

  const loadEmails = useCallback(async (): Promise<boolean> => {
    setPageState("loading");
    setPageError(null);
    setActionError(null);

    try {
      const readFilter =
        filter === "read" ? true : filter === "unread" ? false : undefined;
      const [emailResponse, mailboxResponse] = await Promise.all([
        listEmails({
          limit: 25,
          offset,
          is_read: readFilter,
          mailbox_id: mailboxFilter || undefined,
          range: rangeFilter as EmailRange,
          from: rangeFilter === "custom" ? customFrom || undefined : undefined,
          to: rangeFilter === "custom" ? customTo || undefined : undefined,
          q: searchQuery.trim() || undefined,
          sort: "received_at_desc",
        }),
        listMailboxes(),
      ]);
      setEmails(emailResponse.data.emails);
      setMailboxes(mailboxResponse.data.mailboxes);
      setPagination({
        total: emailResponse.data.pagination.total,
        hasMore: emailResponse.data.pagination.has_more,
      });
      setArchiveState(emailResponse.data.archive_state);
      setPageState("loaded");
      return true;
    } catch (error) {
      const view = emailErrorView(error);
      setEmails([]);
      setMailboxes([]);
      setArchiveState(null);
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
  }, [customFrom, customTo, filter, mailboxFilter, offset, rangeFilter, searchQuery]);

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

  function renderArchiveBanner() {
    if (pageState !== "loaded" || mailboxes.length === 0 || !archiveState) {
      return null;
    }
    if (archiveState.status === "complete") {
      return null;
    }

    return (
      <div style={{ marginTop: 12 }}>
        <InlineFeedback
          tone={archiveStateTone(archiveState)}
          title={t("emails.localArchive")}
        >
          {archiveStateMessage(archiveState, t)}
        </InlineFeedback>
      </div>
    );
  }

  function renderPagination() {
    if (pageState !== "loaded" || pagination.total <= 25) {
      return null;
    }

    const start = pagination.total === 0 ? 0 : offset + 1;
    const end = Math.min(offset + filteredEmails.length, pagination.total);

    return (
      <div
        className="mm-spread"
        style={{
          borderTop: "1px solid var(--mm-border)",
          marginTop: 16,
          paddingTop: 14,
        }}
      >
        <span className="mm-muted" style={{ fontSize: 13 }}>
          {t("emails.paginationSummary")
            .replace("{{start}}", String(start))
            .replace("{{end}}", String(end))
            .replace("{{total}}", String(pagination.total))}
        </span>
        <div className="mm-row">
          <button
            type="button"
            className="mm-btn"
            onClick={() => setOffset((current) => Math.max(0, current - 25))}
            disabled={offset === 0}
            aria-disabled={offset === 0}
          >
            {t("emails.previousPage")}
          </button>
          <button
            type="button"
            className="mm-btn"
            onClick={() => setOffset((current) => current + 25)}
            disabled={!pagination.hasMore}
            aria-disabled={!pagination.hasMore}
          >
            {t("emails.nextPage")}
          </button>
        </div>
      </div>
    );
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
      const emptyCopy = emptyArchiveCopy(archiveState, t);
      return (
        <EmailEmptyState
          title={emptyCopy.title}
          hint={emptyCopy.hint}
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
      <PageFrame
        title={t("emails.title")}
        description={t("emails.description")}
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
              <label className="mm-field" style={{ marginBottom: 0 }}>
                <span className="mm-label">{t("emails.timeRange")}</span>
                <select
                  className="mm-input"
                  value={rangeFilter}
                  onChange={(event) =>
                    setRangeFilter(event.target.value as EmailRangeFilter)
                  }
                  style={{ minWidth: 180 }}
                >
                  {EMAIL_RANGE_FILTERS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {rangeLabel(option.value, t)}
                    </option>
                  ))}
                </select>
              </label>
              <Badge tone="neutral" dot>
                {t("emails.shown")
                  .replace("{{count}}", String(filteredEmails.length))
                  .replace("{{total}}", String(pagination.total))}
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

          {rangeFilter === "custom" ? (
            <div className="mm-row" style={{ marginTop: 14, gap: 12 }}>
              <label className="mm-field" style={{ marginBottom: 0 }}>
                <span className="mm-label">{t("emails.rangeFrom")}</span>
                <input
                  className="mm-input"
                  type="date"
                  value={customFrom}
                  onChange={(event) => setCustomFrom(event.target.value)}
                />
              </label>
              <label className="mm-field" style={{ marginBottom: 0 }}>
                <span className="mm-label">{t("emails.rangeTo")}</span>
                <input
                  className="mm-input"
                  type="date"
                  value={customTo}
                  onChange={(event) => setCustomTo(event.target.value)}
                />
              </label>
            </div>
          ) : null}

          {selectedMailbox ? (
            <div className="mm-row" style={{ marginTop: 12, gap: 8 }}>
              <MailboxProviderBadge provider={selectedMailbox.provider} />
              <span className="mm-muted" style={{ fontSize: 13 }}>
                {selectedMailbox.display_name || selectedMailbox.email_address}
              </span>
            </div>
          ) : null}

          {renderArchiveBanner()}

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
            <div>
              {renderContent()}
              {renderPagination()}
            </div>
          </div>
        ) : (
          <>
            {renderContent()}
            {renderPagination()}
          </>
        )}
      </PageFrame>
    </AppShell>
  );
}

type TFunction = (key: TranslationKey) => string;

function rangeLabel(value: EmailRangeFilter, t: TFunction): string {
  switch (value) {
    case "today":
      return t("emails.rangeToday");
    case "last_7_days":
      return t("emails.rangeLast7");
    case "last_30_days":
      return t("emails.rangeLast30");
    case "custom":
      return t("emails.rangeCustom");
    case "all_synced":
      return t("emails.rangeAllSynced");
  }
}

function archiveStateTone(state: MailboxArchiveState): "info" | "success" | "warning" | "danger" {
  switch (state.status) {
    case "complete":
      return "success";
    case "failed":
      return "danger";
    case "not_started":
      return "warning";
    case "running":
    case "partial":
      return "info";
    default:
      return "info";
  }
}

function archiveStateMessage(
  state: MailboxArchiveState,
  t: TFunction,
): string {
  const base =
    state.message ??
    (state.status === "not_started"
      ? t("emails.archiveNotStarted")
      : state.status === "running"
        ? t("emails.archiveRunning")
        : state.status === "partial"
          ? t("emails.archivePartial")
          : state.status === "failed"
            ? t("emails.archiveFailed")
            : state.status === "complete"
              ? t("emails.archiveComplete")
              : t("emails.archiveUnknown"));
  if (state.status === "not_started") {
    return base;
  }

  const synced = t("emails.archiveSynced")
    .replace("{{count}}", String(state.total_synced_count ?? 0))
    .replace("{{batches}}", String(state.batch_count ?? 0));
  const range =
    state.oldest_synced_at || state.newest_synced_at
      ? ` ${t("emails.archiveRange")
          .replace("{{oldest}}", formatArchiveDate(state.oldest_synced_at))
          .replace("{{newest}}", formatArchiveDate(state.newest_synced_at))}`
      : "";
  const error = state.last_error_message ? ` ${state.last_error_message}` : "";

  return `${base} ${synced}${range}${error}`;
}

function emptyArchiveCopy(
  state: MailboxArchiveState | null,
  t: TFunction,
): { title: string; hint: string } {
  if (state?.status === "not_started") {
    return {
      title: t("emails.archiveNotStartedTitle"),
      hint: t("emails.archiveNotStartedHint"),
    };
  }

  if (state?.status === "running" || state?.status === "partial") {
    return {
      title: t("emails.archiveIncompleteTitle"),
      hint: t("emails.archiveIncompleteHint"),
    };
  }

  if (state?.status === "failed") {
    return {
      title: t("emails.archiveFailedTitle"),
      hint: state.last_error_message ?? t("emails.archiveFailedHint"),
    };
  }

  return {
    title: t("emails.noRangeTitle"),
    hint: t("emails.noRangeHint"),
  };
}

function formatArchiveDate(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString();
}
