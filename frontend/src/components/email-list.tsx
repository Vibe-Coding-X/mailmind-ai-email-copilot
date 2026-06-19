import { EmailListItem } from "@/components/email-list-item";
import type { EmailSummary } from "@/lib/api-types";

export function EmailList({
  emails,
  busyEmailId,
  onMarkRead,
  onMarkUnread,
}: {
  emails: EmailSummary[];
  busyEmailId?: string | null;
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
          onMarkRead={onMarkRead}
          onMarkUnread={onMarkUnread}
        />
      ))}
    </section>
  );
}
