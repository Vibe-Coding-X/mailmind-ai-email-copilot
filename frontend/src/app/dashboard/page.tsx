import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * /dashboard (T005 scaffold). Daily Digest decision board placeholder.
 *
 * Outlines the documented dashboard regions (FRONTEND_DESIGN.md section 3) as
 * empty panels. It does NOT call GET /api/digest/today, does NOT generate a
 * digest, and does NOT claim any digest exists or that data has synced.
 */
const DIGEST_REGIONS = [
  "Digest freshness status",
  "Today's email overview",
  "Must handle",
  "Recommended to review",
  "Can ignore",
  "Today's to-dos",
  "Risk reminders",
  "New email notice",
];

export default function DashboardPage() {
  return (
    <AppShell>
      <RouteHeading
        title="Daily Digest"
        description="Today's AI email decision board. Primary data source will be GET /api/digest/today."
      />

      <div style={{ marginBottom: 16 }}>
        <StatusPlaceholder feature="Daily Digest" />
      </div>

      {DIGEST_REGIONS.map((region) => (
        <PlaceholderPanel key={region} title={region}>
          Placeholder region. No digest data is loaded in this scaffold.
        </PlaceholderPanel>
      ))}
    </AppShell>
  );
}
