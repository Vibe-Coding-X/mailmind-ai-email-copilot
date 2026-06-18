import { Badge } from "@/components/ui/badge";
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";

/**
 * /register (design preview).
 *
 * Static visual skeleton only. No submit logic, no API call, no cookie, no
 * localStorage. Inputs are disabled/read-only and the button is non-functional.
 * Registration creates a system account, not a Gmail connection.
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
            <Badge tone="warn" dot>
              Design Preview
            </Badge>
          </div>

          <Field
            label="Email"
            type="email"
            placeholder="you@example.com"
            autoComplete="email"
          />
          <Field
            label="Password"
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
          />
          <Field
            label="Confirm password"
            type="password"
            placeholder="••••••••"
            autoComplete="new-password"
          />

          <Button type="button" variant="primary" disabled>
            Create account
          </Button>

          <p className="mm-muted" style={{ fontSize: 12, marginTop: 14 }}>
            Authentication backend is not connected. This form is a static design
            preview and does not submit, store, or create anything.
          </p>

          <hr className="mm-divider" style={{ margin: "16px 0" }} />

          <p className="mm-muted" style={{ fontSize: 13 }}>
            Already have an account? <a href="/login">Sign in</a>
          </p>
        </section>
      </div>
    </main>
  );
}
