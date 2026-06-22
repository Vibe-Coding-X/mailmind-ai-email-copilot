"use client";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { AuthStatus } from "@/components/auth-status";
import { SettingsSection, SettingRow } from "@/components/settings-section";
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { InlineFeedback } from "@/components/inline-feedback";
import { useI18n } from "@/i18n/provider";

/**
 * /settings/profile — current system identity status. Profile editing remains
 * a design preview; auth state comes from GET /api/auth/me.
 */
export default function ProfileSettingsPage() {
  const { t } = useI18n();

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title={t("profile.title")}
        description={t("profile.description")}
      >
        <SettingsSection
          title={t("profile.account")}
          description={t("profile.accountDescription")}
        >
          <SettingRow
            label={t("profile.session")}
            value={<AuthStatus />}
          />
        </SettingsSection>

        <SettingsSection
          title={t("profile.preferences")}
          description={t("profile.preferencesDescription")}
        >
          <SettingRow
            label={t("profile.timezone")}
            value={<span className="mm-mono">Asia/Shanghai (default)</span>}
          />
          <div style={{ marginTop: 14, maxWidth: 320 }}>
            <Field
              label={t("profile.displayName")}
              placeholder={t("profile.displayNamePlaceholder")}
            />
            <Button
              variant="primary"
              disabled
              disabledReason={t("profile.disabledReason")}
            >
              {t("profile.save")}
            </Button>
          </div>
          <div style={{ marginTop: 12 }}>
            <InlineFeedback tone="info" title={t("profile.unavailable")}>
              {t("profile.disabledReason")}
            </InlineFeedback>
          </div>
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
