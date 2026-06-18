import type { ReactNode } from "react";

/**
 * Badge — small status/label pill (design preview).
 * Presentational only. No data, no fetch, no backend awareness.
 */
export type BadgeTone = "neutral" | "info" | "warn" | "danger" | "ok";

const TONE_CLASS: Record<BadgeTone, string> = {
  neutral: "mm-badge",
  info: "mm-badge mm-badge--info",
  warn: "mm-badge mm-badge--warn",
  danger: "mm-badge mm-badge--danger",
  ok: "mm-badge mm-badge--ok",
};

export function Badge({
  children,
  tone = "neutral",
  dot = false,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  dot?: boolean;
}) {
  return (
    <span className={TONE_CLASS[tone]}>
      {dot ? <span className="mm-badge-dot" /> : null}
      {children}
    </span>
  );
}
