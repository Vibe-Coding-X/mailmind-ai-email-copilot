"use client";

import { Badge } from "@/components/ui/badge";
import { InlineFeedback } from "@/components/inline-feedback";
import { EmailToolbar } from "@/components/email-toolbar";
import { useI18n } from "@/i18n/provider";
import type { EmailDetail } from "@/lib/api-types";
import {
  displayBodyText,
  displaySnippet,
  displaySubject,
  formatEmailDateTime,
  formatRecipients,
} from "@/lib/emails";

export function EmailDetailView({
  email,
  busy = false,
  actionError,
  backHref = "/emails",
  bodyBusy = false,
  onMarkRead,
  onMarkUnread,
  onFetchBody,
}: {
  email: EmailDetail;
  busy?: boolean;
  actionError?: string | null;
  backHref?: string;
  bodyBusy?: boolean;
  onMarkRead: () => void;
  onMarkUnread: () => void;
  onFetchBody: () => void;
}) {
  const { t } = useI18n();
  const cacheStatus = email.body_cache_status ?? "not_cached";
  const hasStoredBody = (email.body_text?.trim() ?? "").length > 0;
  const bodyText = hasStoredBody
    ? displayBodyText(email.body_text, null)
    : displayBodyText(null, cacheStatus === "cached" ? email.snippet : null);
  const labels = email.labels.length > 0 ? email.labels.join(", ") : t("emails.noLabels");
  const mailboxLabel =
    email.mailbox_display_name || email.mailbox_email || email.mailbox_id;
  const bodyStatus =
    cacheStatus === "cached"
      ? t("emails.bodyCached")
      : cacheStatus === "fetching"
        ? t("emails.bodyCacheFetching")
        : cacheStatus === "failed"
          ? t("emails.bodyCacheFailed")
          : t("emails.bodyNotCached");
  const canFetchBody = cacheStatus !== "cached" || !hasStoredBody;
  const fetchLabel =
    cacheStatus === "failed" ? t("emails.retryBodyCache") : t("emails.loadFullBody");

  return (
    <div className="mm-stack">
      <section className="mm-card">
        <div className="mm-spread" style={{ alignItems: "flex-start" }}>
          <div style={{ minWidth: 0 }}>
            <h2 style={{ fontSize: 20 }}>{displaySubject(email.subject)}</h2>
            <p className="mm-muted" style={{ fontSize: 13, marginTop: 6 }}>
              {email.sender}
            </p>
          </div>
          <Badge tone={email.is_read ? "neutral" : "info"} dot>
            {email.is_read ? t("emails.read") : t("emails.unread")}
          </Badge>
        </div>

        <div
          className="mm-grid mm-grid-2"
          style={{ marginTop: 18, fontSize: 13 }}
        >
          <Metadata label={t("emails.recipients")} value={formatRecipients(email.recipients)} />
          <Metadata label={t("emails.received")} value={formatEmailDateTime(email.received_at)} />
          <Metadata label={t("emails.mailbox")} value={mailboxLabel} />
          <Metadata label={t("emails.provider")} value={email.provider} />
          <Metadata label={t("emails.bodyCacheStatus")} value={bodyStatus} />
          <Metadata label={t("emails.labels")} value={labels} />
          <Metadata
            label={t("emails.attachments")}
            value={email.has_attachments ? t("common.yes") : t("common.no")}
          />
        </div>

        <div style={{ marginTop: 16 }}>
          <EmailToolbar
            isRead={email.is_read}
            busy={busy}
            backHref={backHref}
            onMarkRead={onMarkRead}
            onMarkUnread={onMarkUnread}
          />
        </div>

        {actionError ? (
          <div style={{ marginTop: 14 }}>
            <InlineFeedback tone="danger" title={t("emails.actionError")}>
              {actionError}
            </InlineFeedback>
          </div>
        ) : null}
      </section>

      <section className="mm-card">
        <div className="mm-card-title">{t("emails.preview")}</div>
        <p className="mm-muted" style={{ fontSize: 14 }}>
          {displaySnippet(email.snippet)}
        </p>
      </section>

      <section className="mm-card">
        <div className="mm-spread" style={{ alignItems: "flex-start", gap: 12 }}>
          <div>
            <div className="mm-card-title">{t("emails.body")}</div>
            {email.body_cached_at ? (
              <p className="mm-muted" style={{ fontSize: 12, marginTop: 4 }}>
                {t("emails.bodyCachedAt").replace(
                  "{{time}}",
                  formatEmailDateTime(email.body_cached_at),
                )}
              </p>
            ) : null}
          </div>
          <Badge tone={cacheStatus === "failed" ? "danger" : "neutral"} dot>
            {bodyStatus}
          </Badge>
        </div>
        {canFetchBody ? (
          <div style={{ marginTop: 14 }}>
            <button
              type="button"
              className="mm-btn"
              disabled={bodyBusy || cacheStatus === "fetching"}
              onClick={onFetchBody}
            >
              {bodyBusy || cacheStatus === "fetching"
                ? t("emails.bodyCacheFetching")
                : fetchLabel}
            </button>
            <p className="mm-muted" style={{ fontSize: 13, marginTop: 8 }}>
              {cacheStatus === "failed"
                ? t("emails.bodyCacheFailedHint")
                : t("emails.bodyCacheHint")}
            </p>
            {email.body_cache_error ? (
              <p className="mm-muted" style={{ fontSize: 13, marginTop: 6 }}>
                {t("emails.bodyCacheError").replace(
                  "{{error}}",
                  email.body_cache_error,
                )}
              </p>
            ) : null}
          </div>
        ) : null}
        <div
          style={{
            fontSize: 14,
            lineHeight: 1.65,
            maxWidth: 920,
            marginTop: 14,
            overflowWrap: "anywhere",
            whiteSpace: "pre-wrap",
            color: hasStoredBody ? "var(--color-text)" : "var(--color-text-muted)",
          }}
        >
          {bodyText}
        </div>
      </section>
    </div>
  );
}

function Metadata({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="mm-muted" style={{ fontSize: 12 }}>
        {label}
      </div>
      <div style={{ marginTop: 2, overflowWrap: "anywhere" }}>{value}</div>
    </div>
  );
}
