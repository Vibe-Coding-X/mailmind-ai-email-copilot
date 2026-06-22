"use client";

import type { ReactNode } from "react";

import { EmptyState } from "@/components/empty-state";
import { useI18n } from "@/i18n/provider";

export function EmailEmptyState({
  title,
  hint,
  action,
}: {
  title?: string;
  hint: string;
  action?: ReactNode;
}) {
  const { t } = useI18n();

  return <EmptyState title={title ?? t("emails.emptyDefault")} hint={hint} action={action} />;
}
