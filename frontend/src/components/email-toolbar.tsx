"use client";

import Link from "next/link";
import { useI18n } from "@/i18n/provider";

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
  const { t } = useI18n();

  return (
    <div className="mm-row">
      <Link className="mm-btn" href={backHref}>
        {t("emails.backToEmails")}
      </Link>
      <button
        type="button"
        className="mm-btn"
        disabled={busy || isRead}
        aria-disabled={busy || isRead}
        onClick={onMarkRead}
      >
        {busy && !isRead ? t("emails.marking") : t("emails.markAsRead")}
      </button>
      <button
        type="button"
        className="mm-btn"
        disabled={busy || !isRead}
        aria-disabled={busy || !isRead}
        onClick={onMarkUnread}
      >
        {busy && isRead ? t("emails.marking") : t("emails.markAsUnread")}
      </button>
    </div>
  );
}
