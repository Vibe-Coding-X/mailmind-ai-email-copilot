import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { DigestDashboard } from "@/components/digest-dashboard";

/**
 * /dashboard — Daily Digest decision board backed by the digest API.
 */
export default function DashboardPage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Daily Digest"
        description="Today's email summary and recommended review items."
        badge={false}
      >
        <DigestDashboard />
      </PageFrame>
    </AppShell>
  );
}
