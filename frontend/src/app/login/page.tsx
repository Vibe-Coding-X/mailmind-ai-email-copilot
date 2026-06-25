"use client";

import { Badge } from "@/components/ui/badge";
import { AuthForm } from "@/components/auth-form";
import { AuthStatus } from "@/components/auth-status";
import { ThemeSwitcher } from "@/components/theme-switcher";
import { useI18n } from "@/i18n/provider";

/**
 * /login — system authentication.
 * Styled for dramatic visual impact with the new theme system.
 */
export default function LoginPage() {
  const { t } = useI18n();

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "40px 20px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Animated background gradient */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `
            radial-gradient(ellipse at 20% 20%, rgba(0, 255, 255, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(255, 0, 255, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 50% 50%, rgba(0, 255, 136, 0.04) 0%, transparent 60%)
          `,
          pointerEvents: "none",
          animation: "pulseGlow 8s ease-in-out infinite",
        }}
      />

      <div style={{ width: "100%", maxWidth: 400, position: "relative", zIndex: 1 }}>
        {/* Brand header with glow */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div
            className="mm-brand-name"
            style={{
              fontSize: 32,
              fontWeight: 900,
              letterSpacing: "-0.02em",
            }}
          >
            MailMind
          </div>
          <div
            className="mm-brand-sub"
            style={{
              fontSize: 13,
              marginTop: 8,
              letterSpacing: "0.04em",
            }}
          >
            {t("app.subtitle")}
          </div>
        </div>

        {/* Auth card */}
        <section
          className="mm-card"
          style={{
            padding: "28px 28px 26px",
            position: "relative",
          }}
        >
          <div className="mm-spread" style={{ marginBottom: 20 }}>
            <h1 style={{ fontSize: 20, fontWeight: 700 }}>{t("login.title")}</h1>
            <Badge tone="ok" dot>
              Auth API
            </Badge>
          </div>

          <AuthForm mode="login" />

          <div style={{ marginTop: 18 }}>
            <AuthStatus />
          </div>

          <hr className="mm-divider" style={{ margin: "20px 0" }} />

          <div className="mm-spread">
            <p className="mm-muted" style={{ fontSize: 13 }}>
              {t("login.noAccount")}{" "}
              <a href="/register" style={{ fontWeight: 500 }}>
                {t("login.createOne")}
              </a>
            </p>
            <ThemeSwitcher compact />
          </div>
        </section>

        {/* Footer hint */}
        <div style={{ textAlign: "center", marginTop: 20 }}>
          <p className="mm-muted" style={{ fontSize: 11 }}>
            {t("login.secureConnection")}
          </p>
        </div>
      </div>
    </main>
  );
}
