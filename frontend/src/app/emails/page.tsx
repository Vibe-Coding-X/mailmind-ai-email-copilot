import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ActionChip } from "@/components/action-chip";
import { EmptyState } from "@/components/empty-state";

/**
 * /emails (design preview).
 *
 * Auxiliary email list view — NOT the product homepage (MailMind is
 * dashboard-first). Static design preview: no Gmail messages, no real senders
 * or subjects, no sync state. Future data source: GET /api/emails/today with
 * documented sort/is_read/priority/source query params (API_DESIGN.md §4).
 */

// Documented filter dimensions (visual placeholders only — not wired).
const FILTERS = [
  "Sort: newest",
  "Status: all",
  "Priority: any",
  "Source: current digest",
];

function EmailRowSkeleton() {
  return (
    <div
      style={{
        padding: "14px 0",
        borderTop: "1px solid var(--mm-border)",
      }}
    >
      <div className="mm-spread" style={{ marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Skeleton lines={2} widths={["64%", "40%"]} />
        </div>
        <Badge tone="neutral" dot>
          Unread
        </Badge>
      </div>
      <div className="mm-row">
        <ActionChip>Open</ActionChip>
        <ActionChip>Mark read</ActionChip>
      </div>
    </div>
  );
}

export default function EmailsTodayPage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Emails"
        description="Auxiliary list view of today's emails. The primary entry point is the Daily Digest dashboard."
      >
        {/* Filter bar (static) */}
        <div className="mm-row" role="group" aria-label="Filters (preview)">
          {FILTERS.map((f) => (
            <span className="mm-chip" key={f} aria-disabled="true">
              {f}
            </span>
          ))}
        </div>

        {/* List skeleton */}
        <section className="mm-card">
          <div className="mm-card-title">Today&apos;s emails</div>
          <EmailRowSkeleton />
          <EmailRowSkeleton />
          <EmailRowSkeleton />
          <p className="mm-muted" style={{ fontSize: 12, marginTop: 12 }}>
            Layout preview only. No emails are loaded and no Gmail sync is
            implied.
          </p>
        </section>

        {/* Not-connected empty state */}
        <EmptyState
          title="No mailbox connected"
          hint="Connect Gmail in Settings → Mailboxes to load today's emails. Nothing is synced yet."
        />
      </PageFrame>
    </AppShell>
  );
}
