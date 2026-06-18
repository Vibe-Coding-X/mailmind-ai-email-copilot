import { RouteHeading, StatusPlaceholder } from "@/components/placeholders";

/**
 * /register (T005 scaffold). System registration page placeholder.
 * Register workflow is explicitly out of scope for T005.
 */
export default function RegisterPage() {
  return (
    <main style={{ padding: "48px 40px", maxWidth: 480, margin: "0 auto" }}>
      <RouteHeading
        title="Create a MailMind account"
        description="Registration creates a system account, not a Gmail connection."
      />
      <StatusPlaceholder feature="Registration workflow" />
    </main>
  );
}
