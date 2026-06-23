import { Badge } from "@/components/ui/badge";

export function MailboxProviderBadge({ provider }: { provider: string }) {
  const normalized = provider.toLowerCase();
  const label =
    normalized === "gmail"
      ? "Gmail"
      : normalized === "imap"
        ? "IMAP"
        : normalized === "outlook"
          ? "Outlook"
          : provider.toUpperCase();

  return <Badge tone="neutral">{label}</Badge>;
}
