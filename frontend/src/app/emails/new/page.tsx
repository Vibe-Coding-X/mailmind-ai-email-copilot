import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ActionChip } from "@/components/action-chip";
import { EmptyState } from "@/components/empty-state";

/**
 * /emails/new (design preview).
 *
 * Emails received after the current digest's coverage window. Static design
 * preview only. Future data source: GET /api/emails/new. No new-mail count is
 * fabricated and no sync success is implied.
 */

function NewEmailRowSkeleton() {
  return (
    <div style={{ padding: "14px 0", borderTop: "1px solid var(--mm-border)" }}>
      <div className="mm-spread" style={{ marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Skeleton lines={2} widths={["58%", "36%"]} />
        </div>
        <Badge tone="info" dot>
          New
        </Badge>
      </div>
      <div className="mm-row">
        <ActionChip>Open</ActionChip>
        <ActionChip>Preview</ActionChip>
      </div>
    </div>
  );
}

export default function EmailsNewPage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="New Emails"
        description="Emails that arrived after the current digest's coverage window. Future data source: GET /api/emails/new."
      >
        <div className="mm-banner" role="note">
          <Badge tone="info" dot>
            After digest
          </Badge>
          <span>
            New emails since the last digest will be listed here. The count and
            AI preview are not generated in this design preview.
          </span>
        </div>

        <section className="mm-card">
          <div className="mm-card-title">New since last digest</div>
          <NewEmailRowSkeleton />
          <NewEmailRowSkeleton />
          <p className="mm-muted" style={{ fontSize: 12, marginTop: 12 }}>
            Layout preview only. No new emails are loaded.
          </p>
        </section>

        <EmptyState
          title="Nothing to show"
          hint="New-mail detection runs after a digest is generated. Backend is not connected."
        />
      </PageFrame>
    </AppShell>
  );
}
