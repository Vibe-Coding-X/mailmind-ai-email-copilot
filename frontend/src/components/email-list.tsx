import { EmailListItem } from "@/components/email-list-item";
import type { EmailSummary } from "@/lib/api-types";

export interface EmailActionSupport {
  canMarkRead: boolean;
  canMarkUnread: boolean;
  disabledReason?: string;
}

export function EmailList({
  emails,
  busyEmailId,
  listHref,
  actionSupportByEmailId = {},
  onMarkRead,
  onMarkUnread,
}: {
  emails: EmailSummary[];
  busyEmailId?: string | null;
  listHref?: string;
  actionSupportByEmailId?: Record<string, EmailActionSupport>;
  onMarkRead: (emailId: string) => void;
  onMarkUnread: (emailId: string) => void;
}) {
  return (
    <section className="mm-card">
      <div className="mm-card-title">Today&apos;s emails</div>
      {emails.map((email) => (
        <EmailListItem
          key={email.id}
          email={email}
          busy={busyEmailId === email.id}
          listHref={listHref}
          canMarkRead={actionSupportByEmailId[email.id]?.canMarkRead ?? true}
          canMarkUnread={actionSupportByEmailId[email.id]?.canMarkUnread ?? true}
          disabledReason={actionSupportByEmailId[email.id]?.disabledReason}
          onMarkRead={onMarkRead}
          onMarkUnread={onMarkUnread}
        />
      ))}
    </section>
  );
}
