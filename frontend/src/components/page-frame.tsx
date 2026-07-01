import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";

/**
 * PageFrame — standard page header for primary app views.
 */
export function PageFrame({
  title,
  description,
  badgeLabel,
  children,
}: {
  title: string;
  description?: string;
  badgeLabel?: string;
  children?: ReactNode;
}) {
  return (
    <div className="mm-stack">
      <header className="mm-page-header">
        <div className="mm-row" style={{ marginBottom: 8, alignItems: "center" }}>
          <h1
            style={{
              fontSize: 30,
              fontWeight: 760,
            }}
          >
            {title}
          </h1>
          {badgeLabel ? (
            <Badge tone="info" dot>
              {badgeLabel}
            </Badge>
          ) : null}
        </div>
        {description ? (
          <p
            className="mm-muted"
            style={{
              fontSize: 15,
              lineHeight: 1.6,
              maxWidth: 720,
            }}
          >
            {description}
          </p>
        ) : null}
      </header>
      {children}
    </div>
  );
}
