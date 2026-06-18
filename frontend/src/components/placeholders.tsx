import type { ReactNode } from "react";

/**
 * RouteHeading — generic page title block (T005 scaffold).
 */
export function RouteHeading({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <header style={{ marginBottom: 24 }}>
      <h1 style={{ fontSize: 24, margin: "0 0 6px" }}>{title}</h1>
      {description ? (
        <p style={{ color: "var(--mm-muted)", margin: 0 }}>{description}</p>
      ) : null}
    </header>
  );
}

/**
 * PlaceholderPanel — generic bordered panel used to outline future content
 * regions without implementing them (T005 scaffold).
 */
export function PlaceholderPanel({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <section
      style={{
        border: "1px solid var(--mm-border)",
        borderRadius: 10,
        background: "var(--mm-surface)",
        padding: 20,
        marginBottom: 16,
      }}
    >
      <h2 style={{ fontSize: 15, margin: "0 0 8px" }}>{title}</h2>
      <div style={{ color: "var(--mm-muted)", fontSize: 14 }}>{children}</div>
    </section>
  );
}

/**
 * StatusPlaceholder — explicit "not implemented" marker so scaffold pages can
 * never be mistaken for working product features. It must not claim that data
 * synced, a digest generated, Gmail connected, or any action succeeded.
 */
export function StatusPlaceholder({ feature }: { feature: string }) {
  return (
    <p
      style={{
        display: "inline-block",
        border: "1px dashed var(--mm-border)",
        borderRadius: 6,
        padding: "4px 10px",
        color: "var(--mm-muted)",
        fontSize: 12,
      }}
    >
      Placeholder · {feature} is not implemented yet (T005 scaffold).
    </p>
  );
}
