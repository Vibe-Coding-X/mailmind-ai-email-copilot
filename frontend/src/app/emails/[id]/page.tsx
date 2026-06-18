import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * /emails/[id] (T005 scaffold). Email detail placeholder.
 *
 * Documented data source is GET /api/emails/{email_id} (FRONTEND_DESIGN.md
 * section 4). This scaffold does NOT load the email, and does NOT implement
 * mark-read / mark-unread behavior. The route param is shown only to confirm
 * routing works.
 */
export default async function EmailDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <AppShell>
      <RouteHeading
        title="Email detail"
        description={`Route param email_id: ${id}`}
      />
      <div style={{ marginBottom: 16 }}>
        <StatusPlaceholder feature="Email detail and read-state sync" />
      </div>
      <PlaceholderPanel title="Email content">
        Placeholder. No email content is loaded. Mark-read / mark-unread are not
        implemented and no Gmail sync success is implied.
      </PlaceholderPanel>
    </AppShell>
  );
}
