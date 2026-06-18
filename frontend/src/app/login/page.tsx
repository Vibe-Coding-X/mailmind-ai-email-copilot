import { RouteHeading, StatusPlaceholder } from "@/components/placeholders";

/**
 * /login (T005 scaffold). System login page placeholder.
 * Login/register workflow is explicitly out of scope for T005.
 */
export default function LoginPage() {
  return (
    <main style={{ padding: "48px 40px", maxWidth: 480, margin: "0 auto" }}>
      <RouteHeading
        title="Sign in to MailMind"
        description="System login is separate from Gmail authorization."
      />
      <StatusPlaceholder feature="Login workflow" />
    </main>
  );
}
