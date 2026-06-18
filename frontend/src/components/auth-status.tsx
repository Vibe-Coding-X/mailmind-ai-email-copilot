"use client";

/**
 * AuthStatus — shows the current auth state derived from GET /api/auth/me.
 *
 * Reads only from the auth context (cookie-backed). No localStorage, no cookie
 * parsing. Renders "Not signed in" when unauthenticated and a logout control
 * when authenticated.
 */

import { useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";

export function AuthStatus({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const { status, user, logout } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);

  async function onLogout() {
    setLoggingOut(true);
    try {
      await logout();
      router.push("/login");
    } finally {
      setLoggingOut(false);
    }
  }

  if (status === "loading") {
    return (
      <Badge tone="neutral" dot>
        Checking session…
      </Badge>
    );
  }

  if (status === "unavailable") {
    return (
      <Badge tone="danger" dot>
        Backend unavailable
      </Badge>
    );
  }

  if (status === "unauthenticated" || user === null) {
    return (
      <div className="mm-stack" style={{ gap: 8, alignItems: "flex-start" }}>
        <Badge tone="neutral" dot>
          Not signed in
        </Badge>
        {!compact ? (
          <span className="mm-row" style={{ fontSize: 13 }}>
            <a href="/login">Sign in</a>
            <span className="mm-muted">·</span>
            <a href="/register">Create account</a>
          </span>
        ) : null}
      </div>
    );
  }

  return (
    <div className="mm-stack" style={{ gap: 8, alignItems: "flex-start" }}>
      <Badge tone="ok" dot>
        Signed in
      </Badge>
      <div style={{ fontSize: 13 }}>
        <div>{user.email}</div>
        {!compact ? (
          <div className="mm-muted" style={{ fontSize: 12, marginTop: 2 }}>
            {user.timezone} · {user.status}
          </div>
        ) : null}
      </div>
      <button
        type="button"
        className="mm-btn"
        onClick={onLogout}
        disabled={loggingOut}
        aria-disabled={loggingOut}
        style={{
          cursor: loggingOut ? "wait" : "pointer",
          fontSize: 13,
          padding: "6px 12px",
        }}
      >
        {loggingOut ? "Signing out…" : "Sign out"}
      </button>
    </div>
  );
}
