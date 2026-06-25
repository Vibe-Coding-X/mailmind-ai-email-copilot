import type { ReactNode } from "react";

/**
 * EmptyState — neutral "nothing to show / not connected" panel.
 * Enhanced with glow effects for the new theme system.
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
        border: `1px dashed var(--color-border-strong)`,
        borderRadius: "var(--radius-lg)",
        padding: "40px 28px",
        textAlign: "center",
        color: "var(--color-text-muted)",
        animation: "fadeSlideUp 0.4s ease-out",
      }}
    >
      <div
        style={{
          fontSize: 16,
          fontWeight: 600,
          color: "var(--color-text-muted)",
          marginBottom: 8,
        }}
      >
        {title}
      </div>
      {hint ? (
        <div style={{ fontSize: 14, marginBottom: action ? 18 : 0, lineHeight: 1.6 }}>
          {hint}
        </div>
      ) : null}
      {action ?? null}
    </div>
  );
}
