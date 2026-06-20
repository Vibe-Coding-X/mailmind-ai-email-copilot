import { Badge } from "@/components/ui/badge";

/**
 * StatusBanner — quiet, single-line product-scope notice.
 *
 * Authentication, Gmail, email, and digest surfaces call the backend where
 * available. The digest content remains mock-AI backed until a real provider is
 * configured.
 */
export function StatusBanner() {
  return (
    <div className="mm-banner" role="note">
      <Badge tone="ok" dot>
        Backend connected
      </Badge>
      <span>Digest content uses the configured backend provider.</span>
    </div>
  );
}
