"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { useI18n } from "@/i18n/provider";

export function EmailLoadingState({
  title,
}: {
  title?: string;
}) {
  const { t } = useI18n();

  return (
    <section className="mm-card">
      <div className="mm-card-title">{title ?? t("emails.loading")}</div>
      <Skeleton lines={5} widths={["50%", "90%", "74%", "84%", "42%"]} />
    </section>
  );
}
