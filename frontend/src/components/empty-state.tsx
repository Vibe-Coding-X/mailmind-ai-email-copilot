import type { ReactNode } from "react";

/**
 * EmptyState — neutral "nothing to show / not connected" panel (design preview).
 * Never implies that data exists or that a sync/connection succeeded.
 */
export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
}) {
  return (
    <div
      style={{
        border: "1px dashed var(--mm-border-strong)",
        borderRadius: "var(--mm-radius)",
        padding: "32px 24px",
        textAlign: "center",
        color: "var(--mm-muted)",
      }}
    >
      <div style={{ fontSize: 14, color: "var(--mm-text-soft)", marginBottom: 6 }}>
        {title}
      </div>
      {hint ? (
        <div style={{ fontSize: 13, marginBottom: action ? 14 : 0 }}>{hint}</div>
      ) : null}
      {action ?? null}
    </div>
  );
}
