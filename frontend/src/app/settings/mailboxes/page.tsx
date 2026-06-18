import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { SettingsSection } from "@/components/settings-section";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";

/**
 * /settings/mailboxes (design preview).
 *
 * Mailbox connection management skeleton. Static only — does NOT implement
 * Gmail OAuth, does NOT manage real mailboxes, and does NOT claim any mailbox
 * is connected. System login is separate from Gmail authorization.
 */
export default function MailboxSettingsPage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Mailboxes"
        description="Connect and manage email accounts. System login is separate from Gmail authorization."
      >
        <SettingsSection
          title="Gmail"
          description="MVP supports Gmail only. OAuth is not implemented in this design preview."
        >
          <div className="mm-spread">
            <div className="mm-row">
              <Badge tone="neutral" dot>
                Gmail not connected
              </Badge>
            </div>
            <Button variant="primary" disabled>
              Connect Gmail
            </Button>
          </div>
          <p className="mm-muted" style={{ fontSize: 12, marginTop: 12 }}>
            The Connect button is disabled. No OAuth flow runs and no credentials
            are stored.
          </p>
        </SettingsSection>

        <SettingsSection title="Connected mailboxes">
          <EmptyState
            title="No mailboxes connected"
            hint="Connected accounts will appear here. Nothing is connected in this design preview."
          />
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
