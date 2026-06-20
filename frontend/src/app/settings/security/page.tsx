import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { SettingsSection, SettingRow } from "@/components/settings-section";
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { InlineFeedback } from "@/components/inline-feedback";

/**
 * /settings/security (design preview).
 *
 * Security settings skeleton. Static only. Does NOT display real keys, generate
 * any security config, or implement password change. Future route:
 * PATCH /api/users/me/password (API_DESIGN.md §8).
 */
export default function SecuritySettingsPage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Security"
        description="System login security. Session, cookie, and encryption status are described here."
      >
        <SettingsSection
          title="Session"
          description="MVP uses HttpOnly cookie sessions (per design docs). Status is descriptive only."
        >
          <SettingRow
            label="Session cookie"
            value={
              <Badge tone="neutral" dot>
                HttpOnly (planned) · not connected
              </Badge>
            }
          />
          <SettingRow
            label="Token encryption"
            value={
              <Badge tone="neutral" dot>
                At-rest encryption (planned)
              </Badge>
            }
          />
          <p className="mm-muted" style={{ fontSize: 12, marginTop: 12 }}>
            No real keys, tokens, or secrets are displayed or generated here.
          </p>
        </SettingsSection>

        <SettingsSection
          title="Change password"
          description="Password change requires the current password (future)."
        >
          <div style={{ maxWidth: 320 }}>
            <Field
              label="Current password"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
            />
            <Field
              label="New password"
              type="password"
              placeholder="••••••••"
              autoComplete="new-password"
            />
            <Button
              variant="primary"
              disabled
              disabledReason="Password change is not available until the password update API is enabled."
            >
              Update password
            </Button>
          </div>
          <div style={{ marginTop: 12 }}>
            <InlineFeedback tone="info" title="Unavailable">
              Password change is not available until the password update API is
              enabled.
            </InlineFeedback>
          </div>
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
