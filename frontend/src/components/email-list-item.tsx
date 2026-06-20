import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import type { EmailSummary } from "@/lib/api-types";
import {
  displaySnippet,
  displaySubject,
  formatEmailDateTime,
} from "@/lib/emails";

export function EmailListItem({
  email,
  busy = false,
  listHref = "/emails",
  onMarkRead,
  onMarkUnread,
}: {
  email: EmailSummary;
  busy?: boolean;
  listHref?: string;
  onMarkRead: (emailId: string) => void;
  onMarkUnread: (emailId: string) => void;
}) {
  const statusLabel = email.is_read ? "Read" : "Unread";
  const detailHref = listHref.includes("?")
    ? `/emails/${email.id}?${listHref.split("?")[1]}`
    : `/emails/${email.id}`;

  return (
    <article
      style={{
        borderTop: "1px solid var(--mm-border)",
        borderLeft: email.is_read
          ? "3px solid transparent"
          : "3px solid var(--color-primary)",
        padding: "16px 0 16px 14px",
      }}
    >
      <div className="mm-spread" style={{ alignItems: "flex-start" }}>
        <div style={{ minWidth: 0 }}>
          <Link
            href={detailHref}
            style={{
              color: "var(--color-text)",
              fontSize: 15,
              fontWeight: email.is_read ? 560 : 700,
              textDecoration: "none",
              overflowWrap: "anywhere",
            }}
          >
            {displaySubject(email.subject)}
          </Link>
          <div
            className="mm-muted"
            style={{ fontSize: 13, marginTop: 3, overflowWrap: "anywhere" }}
          >
            {email.sender}
          </div>
        </div>
        <div
          className="mm-stack"
          style={{ gap: 6, alignItems: "flex-end", flexShrink: 0 }}
        >
          <Badge tone={email.is_read ? "neutral" : "info"} dot>
            {statusLabel}
          </Badge>
          <span className="mm-muted" style={{ fontSize: 12 }}>
            {formatEmailDateTime(email.received_at)}
          </span>
        </div>
      </div>

      <p
        className="mm-muted"
        style={{ fontSize: 13, marginTop: 10, overflowWrap: "anywhere" }}
      >
        {displaySnippet(email.snippet)}
      </p>

      <div className="mm-row" style={{ marginTop: 12 }}>
        {email.labels.slice(0, 4).map((label) => (
          <span className="mm-chip" key={label}>
            {label}
          </span>
        ))}
        <button
          type="button"
          className="mm-btn"
          disabled={busy || email.is_read}
          aria-disabled={busy || email.is_read}
          onClick={() => onMarkRead(email.id)}
          style={{ fontSize: 12, padding: "6px 12px" }}
        >
          Mark read
        </button>
        <button
          type="button"
          className="mm-btn"
          disabled={busy || !email.is_read}
          aria-disabled={busy || !email.is_read}
          onClick={() => onMarkUnread(email.id)}
          style={{ fontSize: 12, padding: "6px 12px" }}
        >
          Mark unread
        </button>
      </div>
    </article>
  );
}
