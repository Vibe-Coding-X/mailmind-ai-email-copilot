import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * /emails (T005 scaffold). Today's email list placeholder.
 *
 * This is NOT the product homepage — MailMind is dashboard-first. No email data
 * is loaded. Documented data source is GET /api/emails/today with sort/is_read/
 * priority/source query params (API_DESIGN.md section 4).
 */
export default function EmailsTodayPage() {
  return (
    <AppShell>
      <RouteHeading
        title="Today's Emails"
        description="Raw email list view. The product entry point is the Daily Digest dashboard."
      />
      <div style={{ marginBottom: 16 }}>
        <StatusPlaceholder feature="Today's email list" />
      </div>
      <PlaceholderPanel title="Email list">
        Placeholder. No emails are loaded and no sync state is implied.
      </PlaceholderPanel>
    </AppShell>
  );
}
