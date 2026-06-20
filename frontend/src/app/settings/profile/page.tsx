import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { AuthStatus } from "@/components/auth-status";
import { SettingsSection, SettingRow } from "@/components/settings-section";
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { InlineFeedback } from "@/components/inline-feedback";

/**
 * /settings/profile — current system identity status. Profile editing remains
 * a design preview; auth state comes from GET /api/auth/me.
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
          description="Current system login state from the auth session."
        >
          <SettingRow
            label="Session"
            value={<AuthStatus />}
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
            <Button
              variant="primary"
              disabled
              disabledReason="Profile editing is not available until the profile update API is enabled."
            >
              Save changes
            </Button>
          </div>
          <div style={{ marginTop: 12 }}>
            <InlineFeedback tone="info" title="Unavailable">
              Profile editing is not available until the profile update API is
              enabled.
            </InlineFeedback>
          </div>
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
