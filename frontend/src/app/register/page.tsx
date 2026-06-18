import { Badge } from "@/components/ui/badge";
import { AuthForm } from "@/components/auth-form";
import { AuthStatus } from "@/components/auth-status";

/**
 * /register — system account registration. Registration creates a system
 * account, not a Gmail connection, and only calls POST /api/auth/register.
 */
export default function RegisterPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "40px 20px",
      }}
    >
      <div style={{ width: "100%", maxWidth: 380 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div className="mm-brand-name" style={{ fontSize: 22 }}>
            MailMind
          </div>
          <div className="mm-brand-sub">AI Email Copilot</div>
        </div>

        <section className="mm-card" style={{ padding: "24px 24px 22px" }}>
          <div className="mm-spread" style={{ marginBottom: 16 }}>
            <h1 style={{ fontSize: 18 }}>Create account</h1>
            <Badge tone="ok" dot>
              Auth API
            </Badge>
          </div>

          <AuthForm mode="register" />

          <div style={{ marginTop: 16 }}>
            <AuthStatus />
          </div>

          <hr className="mm-divider" style={{ margin: "16px 0" }} />

          <p className="mm-muted" style={{ fontSize: 13 }}>
            Already have an account? <a href="/login">Sign in</a>
          </p>
        </section>
      </div>
    </main>
  );
}
