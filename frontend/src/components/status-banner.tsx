import { Badge } from "@/components/ui/badge";

/**
 * StatusBanner — quiet, single-line product-scope notice.
 *
 * Authentication is connected to the backend. Gmail, Digest, and AI surfaces
 * remain design previews until their dedicated tasks are implemented. Kept
 * deliberately low-weight so it informs without dominating the page.
 */
export function StatusBanner() {
  return (
    <div className="mm-banner" role="note">
      <Badge tone="ok" dot>
        Auth connected
      </Badge>
      <span>
        Daily Digest, Gmail, and AI are still preview-only.
      </span>
    </div>
  );
}
