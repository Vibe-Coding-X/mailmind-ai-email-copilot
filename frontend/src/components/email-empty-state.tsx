import type { ReactNode } from "react";

import { EmptyState } from "@/components/empty-state";

export function EmailEmptyState({
  title = "No emails",
  hint,
  action,
}: {
  title?: string;
  hint: string;
  action?: ReactNode;
}) {
  return <EmptyState title={title} hint={hint} action={action} />;
}
