import { Badge } from "@/components/ui/badge";
import { AuthForm } from "@/components/auth-form";
import { AuthStatus } from "@/components/auth-status";

/**
 * /login — system authentication. System login is separate from Gmail
 * authorization; the form only calls POST /api/auth/login.
 */
export default function LoginPage() {
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
            <h1 style={{ fontSize: 18 }}>Sign in</h1>
            <Badge tone="ok" dot>
              Auth API
            </Badge>
          </div>

          <AuthForm mode="login" />

          <div style={{ marginTop: 16 }}>
            <AuthStatus />
          </div>

          <hr className="mm-divider" style={{ margin: "16px 0" }} />

          <p className="mm-muted" style={{ fontSize: 13 }}>
            No account yet? <a href="/register">Create one</a>
          </p>
        </section>
      </div>
    </main>
  );
}
