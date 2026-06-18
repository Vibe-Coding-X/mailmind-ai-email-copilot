import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * /emails/new (T005 scaffold). New-since-digest email list placeholder.
 *
 * Documented data source is GET /api/emails/new (emails after coverage_end).
 * No data is loaded and no new-mail count is fabricated.
 */
export default function EmailsNewPage() {
  return (
    <AppShell>
      <RouteHeading
        title="New Emails"
        description="Emails received after the current digest's coverage window."
      />
      <div style={{ marginBottom: 16 }}>
        <StatusPlaceholder feature="New email list" />
      </div>
      <PlaceholderPanel title="New email list">
        Placeholder. No new emails are loaded and no AI judgement is shown.
      </PlaceholderPanel>
    </AppShell>
  );
}
