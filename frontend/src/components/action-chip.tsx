import type { ReactNode } from "react";

/**
 * ActionChip — STATIC, non-interactive chip representing a possible AI-suggested
 * action (e.g. "Reply today", "Review", "Ignore") for layout preview only.
 *
 * Has no click behavior. It does not trigger mark-read/unread, does not call any
 * API, and does not represent a real AI suggestion — it is a visual placeholder.
 */
export function ActionChip({ children }: { children: ReactNode }) {
  return (
    <span className="mm-chip" aria-disabled="true">
      {children}
    </span>
  );
}
