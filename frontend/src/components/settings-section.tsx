import type { ReactNode } from "react";

/**
 * SettingsSection — titled block for settings pages (design preview).
 * Presentational only; no settings are read or persisted.
 */
export function SettingsSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="mm-card" style={{ padding: "20px 22px" }}>
      <h2 style={{ fontSize: 15, marginBottom: 4 }}>{title}</h2>
      {description ? (
        <p className="mm-muted" style={{ fontSize: 13, marginBottom: 16 }}>
          {description}
        </p>
      ) : (
        <div style={{ height: 16 }} />
      )}
      {children}
    </section>
  );
}

/**
 * SettingRow — label/value row for read-only settings preview.
 */
export function SettingRow({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div
      className="mm-spread"
      style={{ padding: "10px 0", borderTop: "1px solid var(--mm-border)" }}
    >
      <span className="mm-muted" style={{ fontSize: 13 }}>
        {label}
      </span>
      <span style={{ fontSize: 13.5 }}>{value}</span>
    </div>
  );
}
