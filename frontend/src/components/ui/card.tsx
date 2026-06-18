import type { ReactNode } from "react";

/**
 * Card — generic bordered surface (design preview).
 * Presentational only.
 */
export function Card({
  title,
  action,
  children,
}: {
  title?: ReactNode;
  action?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <section className="mm-card">
      {title || action ? (
        <div className="mm-spread" style={{ marginBottom: 10 }}>
          {title ? <div className="mm-card-title">{title}</div> : <span />}
          {action ?? null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
