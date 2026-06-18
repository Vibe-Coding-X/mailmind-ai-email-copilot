import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { DashboardPreview } from "@/components/dashboard-preview";

/**
 * /dashboard (design preview).
 *
 * Daily Digest decision board. Static design preview only — does NOT call
 * GET /api/digest/today, does NOT generate a digest, and does NOT render real
 * or mock email content.
 */
export default function DashboardPage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Daily Digest"
        description="Today's AI email decision board. Future data source: GET /api/digest/today."
      >
        <DashboardPreview />
      </PageFrame>
    </AppShell>
  );
}
