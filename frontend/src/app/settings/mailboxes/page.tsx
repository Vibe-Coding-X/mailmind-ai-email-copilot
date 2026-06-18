import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * /settings/mailboxes (T005 scaffold). Mailbox connection management placeholder.
 *
 * Documented related routes: /api/mailboxes (section 5) and /api/auth/gmail
 * (section 2). T005 must NOT implement Gmail OAuth or real mailbox management,
 * and must NOT claim a mailbox is connected.
 */
export default function MailboxSettingsPage() {
  return (
    <AppShell>
      <RouteHeading
        title="Mailboxes"
        description="Connect and manage email accounts. System login is separate from Gmail authorization."
      />
      <div style={{ marginBottom: 16 }}>
        <StatusPlaceholder feature="Mailbox connection management" />
      </div>
      <PlaceholderPanel title="Connected mailboxes">
        Placeholder. No mailbox is connected and no connection state is implied.
      </PlaceholderPanel>
    </AppShell>
  );
}
