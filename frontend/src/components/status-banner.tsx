import { Badge } from "@/components/ui/badge";

/**
 * StatusBanner — global "design preview / not connected" notice.
 *
 * Makes it unmistakable that the frontend is a static design preview with no
 * backend, Gmail, or AI connected. Used in the app shell and on key pages so
 * no screen can be mistaken for a working product.
 */
export function StatusBanner() {
  return (
    <div className="mm-banner" role="note">
      <Badge tone="warn" dot>
        Design Preview
      </Badge>
      <span>
        This is a static UI design preview. No data is loaded and nothing is
        connected.
      </span>
      <span className="mm-row" style={{ marginLeft: "auto" }}>
        <Badge tone="neutral" dot>
          Backend not connected
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
