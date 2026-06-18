import { Badge } from "@/components/ui/badge";

/**
 * StatusBanner — global product-scope notice.
 *
 * Authentication is connected to the backend. Gmail, Digest, and AI surfaces
 * remain design previews until their dedicated tasks are implemented.
 */
export function StatusBanner() {
  return (
    <div className="mm-banner" role="note">
      <Badge tone="warn" dot>
        Partial Integration
      </Badge>
      <span>
        System authentication is connected. Daily Digest, Gmail, and AI data are
        still preview-only.
      </span>
      <span className="mm-row" style={{ marginLeft: "auto" }}>
        <Badge tone="ok" dot>
          Auth API connected
        </Badge>
        <Badge tone="neutral" dot>
          Gmail not connected
        </Badge>
        <Badge tone="neutral" dot>
          AI not connected
        </Badge>
      </span>
    </div>
  );
}
