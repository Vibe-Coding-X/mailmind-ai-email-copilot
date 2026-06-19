import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import type { EmailErrorView } from "@/lib/emails";

export function EmailErrorState({
  error,
  action,
}: {
  error: EmailErrorView;
  action?: ReactNode;
}) {
  return (
    <section className="mm-card">
      <div className="mm-stack" style={{ gap: 12, alignItems: "flex-start" }}>
        <Badge
          tone={error.kind === "backend_unavailable" ? "danger" : "warn"}
          dot
        >
          {error.title}
        </Badge>
        <p className="mm-muted" style={{ fontSize: 14 }}>
          {error.message}
        </p>
        {action ?? null}
      </div>
    </section>
  );
}
