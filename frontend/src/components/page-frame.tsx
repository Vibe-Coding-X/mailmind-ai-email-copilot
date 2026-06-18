import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";

/**
 * PageFrame — standard page header (title, description, optional preview badge).
 * Presentational only.
 */
export function PageFrame({
  title,
  description,
  badge = true,
  children,
}: {
  title: string;
  description?: string;
  badge?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className="mm-stack">
      <header>
        <div className="mm-row" style={{ marginBottom: 6 }}>
          <h1 style={{ fontSize: 24, letterSpacing: "-0.01em" }}>{title}</h1>
          {badge ? (
            <Badge tone="warn" dot>
              Design Preview
            </Badge>
          ) : null}
        </div>
        {description ? (
          <p className="mm-muted" style={{ fontSize: 14 }}>
            {description}
          </p>
        ) : null}
      </header>
      {children}
    </div>
  );
}
