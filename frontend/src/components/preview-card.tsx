import type { ReactNode } from "react";
import { Badge, type BadgeTone } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * PreviewCard — a labeled section that outlines a future content region using
 * neutral skeletons (design preview).
 *
 * Shows ONLY skeleton bars and generic placeholder copy. It must never render
 * real or mock email content, sender names, subjects, or AI conclusions.
 */
export function PreviewCard({
  title,
  badgeLabel,
  badgeTone = "neutral",
  note,
  skeletonLines = 3,
  children,
}: {
  title: string;
  badgeLabel?: string;
  badgeTone?: BadgeTone;
  note?: string;
  skeletonLines?: number;
  children?: ReactNode;
}) {
  return (
    <section className="mm-card">
      <div className="mm-spread" style={{ marginBottom: 12 }}>
        <div className="mm-card-title" style={{ marginBottom: 0 }}>
          {title}
        </div>
        {badgeLabel ? (
          <Badge tone={badgeTone} dot>
            {badgeLabel}
          </Badge>
        ) : null}
      </div>

      {children ?? <Skeleton lines={skeletonLines} />}

      {note ? (
        <p className="mm-muted" style={{ fontSize: 12, marginTop: 12 }}>
          {note}
        </p>
      ) : null}
    </section>
  );
}
