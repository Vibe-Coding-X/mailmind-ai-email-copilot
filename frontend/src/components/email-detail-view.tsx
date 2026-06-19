import { Badge } from "@/components/ui/badge";
import { EmailToolbar } from "@/components/email-toolbar";
import type { EmailDetail } from "@/lib/api-types";
import {
  displaySnippet,
  displaySubject,
  formatEmailDateTime,
  formatRecipients,
} from "@/lib/emails";

export function EmailDetailView({
  email,
  busy = false,
  actionError,
  onMarkRead,
  onMarkUnread,
}: {
  email: EmailDetail;
  busy?: boolean;
  actionError?: string | null;
  onMarkRead: () => void;
  onMarkUnread: () => void;
}) {
  const bodyText = email.body_text?.trim();

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
            {email.is_read ? "Read" : "Unread"}
          </Badge>
        </div>

        <div
          className="mm-grid mm-grid-2"
          style={{ marginTop: 18, fontSize: 13 }}
        >
          <Metadata label="Recipients" value={formatRecipients(email.recipients)} />
          <Metadata label="Received" value={formatEmailDateTime(email.received_at)} />
          <Metadata label="Provider" value={email.provider} />
          <Metadata label="Thread" value={email.thread_id} />
        </div>

        <div style={{ marginTop: 16 }}>
          <EmailToolbar
            isRead={email.is_read}
            busy={busy}
            onMarkRead={onMarkRead}
            onMarkUnread={onMarkUnread}
          />
        </div>

        {actionError ? (
          <div style={{ marginTop: 14 }}>
            <Badge tone="danger" dot>
              {actionError}
            </Badge>
          </div>
        ) : null}
      </section>

      <section className="mm-card">
        <div className="mm-card-title">Preview</div>
        <p className="mm-muted" style={{ fontSize: 14 }}>
          {displaySnippet(email.snippet)}
        </p>
      </section>

      <section className="mm-card">
        <div className="mm-card-title">Body</div>
        <div
          style={{
            fontSize: 14,
            lineHeight: 1.65,
            whiteSpace: "pre-wrap",
            color: bodyText ? "var(--color-text)" : "var(--color-text-muted)",
          }}
        >
          {bodyText || "No readable body text was stored for this email."}
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
