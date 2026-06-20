"use client";

import { Badge } from "@/components/ui/badge";
import { AuthForm } from "@/components/auth-form";
import { AuthStatus } from "@/components/auth-status";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { useI18n } from "@/i18n/provider";

/**
 * /register — system account registration. Registration creates a system
 * account, not a Gmail connection, and only calls POST /api/auth/register.
 */
export default function RegisterPage() {
  const { t } = useI18n();

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
          <div className="mm-brand-sub">{t("app.subtitle")}</div>
        </div>

        <section className="mm-card" style={{ padding: "24px 24px 22px" }}>
          <div className="mm-spread" style={{ marginBottom: 16 }}>
            <h1 style={{ fontSize: 18 }}>{t("register.title")}</h1>
            <Badge tone="ok" dot>
              Auth API
            </Badge>
          </div>

          <AuthForm mode="register" />

          <div style={{ marginTop: 16 }}>
            <AuthStatus />
          </div>

          <hr className="mm-divider" style={{ margin: "16px 0" }} />

          <div className="mm-spread">
            <p className="mm-muted" style={{ fontSize: 13 }}>
              {t("register.hasAccount")} <a href="/login">{t("account.signIn")}</a>
            </p>
            <ThemeSwitcher compact />
          </div>
        </section>
      </div>
    </main>
  );
}
