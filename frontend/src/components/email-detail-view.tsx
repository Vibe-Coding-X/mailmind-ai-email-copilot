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
  onMarkRead,
  onMarkUnread,
}: {
  email: EmailDetail;
  busy?: boolean;
  actionError?: string | null;
  backHref?: string;
  onMarkRead: () => void;
  onMarkUnread: () => void;
}) {
  const { t } = useI18n();
  const bodyText = displayBodyText(email.body_text, email.snippet);
  const hasStoredBody = (email.body_text?.trim() ?? "").length > 0;
  const labels = email.labels.length > 0 ? email.labels.join(", ") : t("emails.noLabels");

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
          <Metadata label={t("emails.provider")} value={email.provider} />
          <Metadata label={t("emails.labels")} value={labels} />
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
        <div className="mm-card-title">{t("emails.body")}</div>
        <div
          style={{
            fontSize: 14,
            lineHeight: 1.65,
            maxWidth: 920,
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
