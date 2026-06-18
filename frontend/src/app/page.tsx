import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * Root page (T005 scaffold).
 *
 * Reflects MailMind's dashboard-first positioning as an AI Email Copilot
 * without implementing the actual Daily Digest workflow. It points users at
 * the documented /dashboard entry point. No data is loaded here.
 */
export default function HomePage() {
  return (
    <AppShell>
      <RouteHeading
        title="MailMind"
        description="AI Email Copilot — a dashboard-first decision layer on top of your email."
      />

      <PlaceholderPanel title="Dashboard-first product direction">
        MailMind&apos;s primary entry point is the Daily Digest dashboard, not a
        raw inbox list. The dashboard will surface what needs attention today.
        This scaffold does not generate or display any digest data.
        <div style={{ marginTop: 12 }}>
          <a href="/dashboard">Go to Daily Digest →</a>
        </div>
      </PlaceholderPanel>

      <PlaceholderPanel title="Build status">
        <StatusPlaceholder feature="Product UI" />
      </PlaceholderPanel>
    </AppShell>
  );
}
