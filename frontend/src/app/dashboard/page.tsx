"use client";

import { AppShell } from "@/components/app-shell";
import { StatusBanner } from "@/components/status-banner";
import { PageFrame } from "@/components/page-frame";
import { DigestDashboard } from "@/components/digest-dashboard";
import { useI18n } from "@/i18n/provider";

/**
 * /dashboard — Daily Digest decision board backed by the digest API.
 */
export default function DashboardPage() {
  const { t } = useI18n();

  return (
    <AppShell>
      <StatusBanner />
      <div style={{ height: 20 }} />
      <PageFrame
        title={t("digest.pageTitle")}
        description={t("digest.pageDescription")}
        badge={false}
      >
        <DigestDashboard />
      </PageFrame>
    </AppShell>
  );
}
