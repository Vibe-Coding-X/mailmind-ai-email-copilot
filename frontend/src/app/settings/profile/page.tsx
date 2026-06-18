import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { SettingsSection, SettingRow } from "@/components/settings-section";
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";

/**
 * /settings/profile (design preview).
 *
 * User profile & preferences skeleton. Static only — no user data is loaded or
 * persisted. Future routes: GET/PATCH /api/users/me (API_DESIGN.md §8).
 */
export default function ProfileSettingsPage() {
  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title="Profile"
        description="Account info and display preferences."
      >
        <SettingsSection
          title="Account"
          description="Read-only preview. No account data is loaded."
        >
          <SettingRow
            label="Email"
            value={<span className="mm-muted">not connected</span>}
          />
          <SettingRow
            label="Account status"
            value={
              <Badge tone="neutral" dot>
                Unknown · not connected
              </Badge>
            }
          />
        </SettingsSection>

        <SettingsSection
          title="Preferences"
          description="Timezone affects how Daily Digest windows are calculated (future)."
        >
          <SettingRow
            label="Timezone"
            value={<span className="mm-mono">Asia/Shanghai (default)</span>}
          />
          <div style={{ marginTop: 14, maxWidth: 320 }}>
            <Field label="Display name" placeholder="Your name" />
            <Button variant="primary" disabled>
              Save changes
            </Button>
          </div>
          <p className="mm-muted" style={{ fontSize: 12, marginTop: 12 }}>
            Saving is disabled in this design preview.
          </p>
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
