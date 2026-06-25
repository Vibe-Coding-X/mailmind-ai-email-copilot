"use client";

/**
 * AuthForm — sign-in / sign-up form with enhanced styling.
 */

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";
import { ApiRequestError } from "@/lib/api-client";
import { InlineFeedback } from "@/components/inline-feedback";
import { useI18n } from "@/i18n/provider";

type Mode = "login" | "register";

const DEFAULT_TIMEZONE = "Asia/Shanghai";

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const { login, register } = useAuth();
  const { t } = useI18n();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isRegister = mode === "register";

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (isRegister) {
        await register({
          email,
          password,
          timezone: timezone.trim() || DEFAULT_TIMEZONE,
        });
      } else {
        await login({ email, password });
      }
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.status === 0
            ? t("account.backendUnavailable")
            : err.message
          : t("digest.genericError"),
      );
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate>
      <div className="mm-field">
        <label className="mm-label" htmlFor="email">
          {t("auth.email")}
        </label>
        <input
          id="email"
          className="mm-input"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={submitting}
          required
          style={{ fontSize: 15 }}
        />
      </div>

      <div className="mm-field">
        <label className="mm-label" htmlFor="password">
          {t("auth.password")}
        </label>
        <input
          id="password"
          className="mm-input"
          type="password"
          autoComplete={isRegister ? "new-password" : "current-password"}
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={submitting}
          minLength={isRegister ? 8 : undefined}
          required
          style={{ fontSize: 15 }}
        />
      </div>

      {isRegister ? (
        <div className="mm-field">
          <label className="mm-label" htmlFor="timezone">
            {t("auth.timezone")}
          </label>
          <input
            id="timezone"
            className="mm-input"
            type="text"
            placeholder={DEFAULT_TIMEZONE}
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            disabled={submitting}
            style={{ fontSize: 15 }}
          />
        </div>
      ) : null}

      {error ? (
        <div style={{ marginBottom: 14 }}>
          <InlineFeedback tone="danger" title={t("auth.signInError")}>
            {error}
          </InlineFeedback>
        </div>
      ) : null}

      <button
        type="submit"
        className="mm-btn mm-btn--primary"
        disabled={submitting}
        aria-disabled={submitting}
        style={{
          cursor: submitting ? "wait" : "pointer",
          width: "100%",
          padding: "12px 20px",
          fontSize: 15,
          fontWeight: 600,
        }}
      >
        {submitting
          ? isRegister
            ? t("auth.creatingAccount")
            : t("auth.signingIn")
          : isRegister
            ? t("account.createAccount")
            : t("account.signIn")}
      </button>
    </form>
  );
}
