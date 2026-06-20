"use client";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { Badge } from "@/components/ui/badge";
import { SettingsSection, SettingRow } from "@/components/settings-section";
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { InlineFeedback } from "@/components/inline-feedback";
import { useI18n } from "@/i18n/provider";

/**
 * /settings/security (design preview).
 *
 * Security settings skeleton. Static only. Does NOT display real keys, generate
 * any security config, or implement password change. Future route:
 * PATCH /api/users/me/password (API_DESIGN.md §8).
 */
export default function SecuritySettingsPage() {
  const { t } = useI18n();

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title={t("security.title")}
        description={t("security.description")}
      >
        <SettingsSection
          title={t("profile.session")}
          description={t("security.sessionDescription")}
        >
          <SettingRow
            label={t("security.sessionCookie")}
            value={
              <Badge tone="neutral" dot>
                {t("security.httpOnlyPlanned")}
              </Badge>
            }
          />
          <SettingRow
            label={t("security.tokenEncryption")}
            value={
              <Badge tone="neutral" dot>
                {t("security.encryptionPlanned")}
              </Badge>
            }
          />
          <p className="mm-muted" style={{ fontSize: 12, marginTop: 12 }}>
            {t("security.noSecrets")}
          </p>
        </SettingsSection>

        <SettingsSection
          title={t("security.changePassword")}
          description={t("security.changePasswordDescription")}
        >
          <div style={{ maxWidth: 320 }}>
            <Field
              label={t("security.currentPassword")}
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
            />
            <Field
              label={t("security.newPassword")}
              type="password"
              placeholder="••••••••"
              autoComplete="new-password"
            />
            <Button
              variant="primary"
              disabled
              disabledReason={t("security.disabledReason")}
            >
              {t("security.updatePassword")}
            </Button>
          </div>
          <div style={{ marginTop: 12 }}>
            <InlineFeedback tone="info" title={t("profile.unavailable")}>
              {t("security.disabledReason")}
            </InlineFeedback>
          </div>
        </SettingsSection>
      </PageFrame>
    </AppShell>
  );
}
