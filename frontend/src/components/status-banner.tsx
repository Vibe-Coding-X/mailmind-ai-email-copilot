import { Badge } from "@/components/ui/badge";

/**
 * StatusBanner — quiet, single-line product-scope notice.
 *
 * Authentication, Gmail, email, digest, and action surfaces call the backend
 * where available. AI output remains provider-dependent.
 */
export function StatusBanner() {
  return (
    <div className="mm-banner" role="note">
      <Badge tone="ok" dot>
        Backend connected
      </Badge>
      <span>MailMind data is loaded from the local backend when available.</span>
    </div>
  );
}
