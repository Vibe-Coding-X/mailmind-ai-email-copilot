import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { PreviewCard } from "@/components/preview-card";
import { ActionChip } from "@/components/action-chip";

/**
 * DashboardPreview — static composition of the documented Daily Digest regions
 * (docs/frontend/FRONTEND_DESIGN.md section 3).
 *
 * Everything here is a DESIGN PREVIEW: skeleton bars and generic placeholder
 * labels only. It does NOT call GET /api/digest/today, does NOT render real or
 * mock email/sender/subject text, and does NOT imply a digest has been
 * generated or that data synced.
 */

function DigestItemSkeleton({ actions }: { actions?: string[] }) {
  return (
    <div
      style={{
        padding: "12px 0",
        borderTop: "1px solid var(--mm-border)",
      }}
    >
      <Skeleton lines={2} widths={["72%", "48%"]} />
      {actions && actions.length > 0 ? (
        <div className="mm-row" style={{ marginTop: 10 }}>
          {actions.map((a) => (
            <ActionChip key={a}>{a}</ActionChip>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function DashboardPreview() {
  return (
    <div className="mm-stack">
      {/* 1. Digest freshness status (FRONTEND_DESIGN §3) */}
      <div className="mm-banner" role="note">
        <Badge tone="warn" dot>
          Digest status
        </Badge>
        <span>
          Daily Digest freshness will appear here once the backend and AI are
          connected. No digest has been generated.
        </span>
      </div>

      {/* 2. Today overview */}
      <div className="mm-grid mm-grid-3">
        {["Today overview", "Analyzed", "New since digest"].map((label) => (
          <div className="mm-card" key={label}>
            <div className="mm-muted" style={{ fontSize: 12 }}>
              {label}
            </div>
            <div
              className="mm-skel"
              style={{ height: 26, width: "40%", marginTop: 10 }}
            />
            <p className="mm-muted" style={{ fontSize: 11, marginTop: 10 }}>
              Placeholder · not connected
            </p>
          </div>
        ))}
      </div>

      {/* 3. Daily Digest preview */}
      <PreviewCard
        title="Daily Digest preview"
        badgeLabel="Not connected"
        badgeTone="neutral"
        note="Source (future): GET /api/digest/today. No content is loaded."
        skeletonLines={4}
      />

      {/* 4–6. Needs attention / Review later / Low priority */}
      <div className="mm-grid mm-grid-3">
        <PreviewCard
          title="Needs attention"
          badgeLabel="Urgent"
          badgeTone="danger"
          note="Placeholder region"
        >
          <DigestItemSkeleton actions={["Reply today", "Open"]} />
          <DigestItemSkeleton actions={["Reply today"]} />
        </PreviewCard>

        <PreviewCard
          title="Review later"
          badgeLabel="Review"
          badgeTone="info"
          note="Placeholder region"
        >
          <DigestItemSkeleton actions={["Review", "Snooze"]} />
          <DigestItemSkeleton actions={["Review"]} />
        </PreviewCard>

        <PreviewCard
          title="Low priority / Ignore"
          badgeLabel="Ignore"
          badgeTone="neutral"
          note="Placeholder region"
        >
          <DigestItemSkeleton actions={["Ignore"]} />
          <DigestItemSkeleton actions={["Ignore"]} />
        </PreviewCard>
      </div>

      {/* 7. Tasks & Risks */}
      <div className="mm-grid mm-grid-2">
        <PreviewCard
          title="Tasks"
          badgeLabel="To-do"
          badgeTone="ok"
          note="Extracted action items (placeholder)"
          skeletonLines={3}
        />
        <PreviewCard
          title="Risks"
          badgeLabel="Risk"
          badgeTone="warn"
          note="Risk reminders (placeholder)"
          skeletonLines={3}
        />
      </div>

      {/* System status */}
      <div className="mm-card">
        <div className="mm-card-title">System status</div>
        <div className="mm-row">
          <Badge tone="neutral" dot>
            Backend not connected
          </Badge>
          <Badge tone="neutral" dot>
            Gmail not connected
          </Badge>
          <Badge tone="neutral" dot>
            AI not connected
          </Badge>
          <Badge tone="warn" dot>
            Frontend scaffold
          </Badge>
        </div>
      </div>
    </div>
  );
}
