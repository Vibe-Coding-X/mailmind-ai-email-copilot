import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";

/**
 * PageFrame — standard page header with visual impact.
 * Styled for the new dramatic theme system.
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
      <header style={{ animation: "fadeSlideUp 0.5s ease-out" }}>
        <div className="mm-row" style={{ marginBottom: 8, alignItems: "center" }}>
          <h1
            style={{
              fontSize: 34,
              fontWeight: 800,
              letterSpacing: "-0.02em",
            }}
          >
            {title}
          </h1>
          {badge ? (
            <Badge tone="info" dot>
              Preview
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
