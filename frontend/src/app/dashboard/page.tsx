"use client";

import { AppShell } from "@/components/app-shell";
import { PageFrame } from "@/components/page-frame";
import { DigestDashboard } from "@/components/digest-dashboard";
import { useI18n } from "@/i18n/provider";

/**
 * /dashboard — Daily Digest backed by the digest API.
 */
export default function DashboardPage() {
  const { t } = useI18n();

  return (
    <AppShell>
      <PageFrame
        title={t("digest.pageTitle")}
        description={t("digest.pageDescription")}
      >
        <DigestDashboard />
      </PageFrame>
    </AppShell>
  );
}
