import Link from "next/link";

export function EmailToolbar({
  isRead,
  busy = false,
  backHref = "/emails",
  onMarkRead,
  onMarkUnread,
}: {
  isRead: boolean;
  busy?: boolean;
  backHref?: string;
  onMarkRead: () => void;
  onMarkUnread: () => void;
}) {
  return (
    <div className="mm-row">
      <Link className="mm-btn" href={backHref}>
        Back to emails
      </Link>
      <button
        type="button"
        className="mm-btn"
        disabled={busy || isRead}
        aria-disabled={busy || isRead}
        onClick={onMarkRead}
      >
        {busy && !isRead ? "Marking..." : "Mark as read"}
      </button>
      <button
        type="button"
        className="mm-btn"
        disabled={busy || !isRead}
        aria-disabled={busy || !isRead}
        onClick={onMarkUnread}
      >
        {busy && isRead ? "Marking..." : "Mark as unread"}
      </button>
    </div>
  );
}
