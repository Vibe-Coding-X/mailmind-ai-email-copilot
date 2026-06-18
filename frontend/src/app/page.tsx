import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { DashboardPreview } from "@/components/dashboard-preview";

/**
 * Root page (design preview).
 *
 * MailMind is dashboard-first, so the landing page renders the Daily Digest
 * dashboard preview directly. This is a static design preview: no digest is
 * generated, no api-client is called, and no data is loaded.
 */
export default function HomePage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Daily Digest"
        description="Your action-oriented inbox summary. MailMind shows what needs attention today instead of a raw inbox."
      >
        <DashboardPreview />
      </PageFrame>
    </AppShell>
  );
}
