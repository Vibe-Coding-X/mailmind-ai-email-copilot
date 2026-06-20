"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { ThemeSwitcher } from "@/components/theme-switcher";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

function initials(email: string | undefined): string {
  if (!email) {
    return "MM";
  }

  const name = email.split("@")[0] ?? email;
  const parts = name.split(/[._-]+/).filter(Boolean);
  const letters = parts.length >= 2 ? parts[0][0] + parts[1][0] : name.slice(0, 2);
  return letters.toUpperCase();
}

export function AccountMenu({ compact = false }: { compact?: boolean }) {
  const router = useRouter();
  const { status, user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const menuId = useId();

  useEffect(() => {
    function onPointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, []);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      setOpen(false);
    }
  }

  async function onLogout() {
    setLoggingOut(true);
    try {
      await logout();
      setOpen(false);
      router.push("/login");
    } finally {
      setLoggingOut(false);
    }
  }

  const signedIn = status === "authenticated" && user !== null;
  const avatarLabel = signedIn ? user.email : "Account";

  return (
    <div
      ref={rootRef}
      className={compact ? "mm-account mm-account--compact" : "mm-account"}
      onKeyDown={onKeyDown}
    >
      <button
        type="button"
        className="mm-account-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="mm-avatar" aria-hidden="true">
          {initials(user?.email)}
        </span>
        <span className="mm-account-copy">
          <span className="mm-account-name">
            {signedIn ? user.email : status === "loading" ? "Checking session" : "Not signed in"}
          </span>
          <span className="mm-account-sub">
            {signedIn ? user.timezone : "Open account menu"}
          </span>
        </span>
      </button>

      {open ? (
        <div id={menuId} className="mm-account-menu" role="menu" aria-label={avatarLabel}>
          <div className="mm-account-menu-head">
            <Badge tone={signedIn ? "ok" : status === "unavailable" ? "danger" : "neutral"} dot>
              {signedIn
                ? "Signed in"
                : status === "unavailable"
                  ? "Backend unavailable"
                  : "Not signed in"}
            </Badge>
            {signedIn ? (
              <div className="mm-account-email">{user.email}</div>
            ) : null}
          </div>

          <div className="mm-account-menu-section">
            <Link role="menuitem" className="mm-menu-link" href="/settings/profile" onClick={() => setOpen(false)}>
              Profile
            </Link>
            <Link role="menuitem" className="mm-menu-link" href="/settings/security" onClick={() => setOpen(false)}>
              Security
            </Link>
            <button
              type="button"
              role="menuitem"
              className="mm-menu-link"
              disabled
              aria-disabled="true"
              title="Language switching is wired in FE-R5."
            >
              Language
            </button>
          </div>

          <div className="mm-account-menu-section">
            <div className="mm-nav-label" style={{ marginBottom: 8 }}>
              Theme
            </div>
            <ThemeSwitcher />
          </div>

          <div className="mm-account-menu-section">
            {signedIn ? (
              <Button
                variant="ghost"
                disabled={loggingOut}
                disabledReason="Sign out is already in progress."
                onClick={() => void onLogout()}
              >
                {loggingOut ? "Signing out..." : "Sign out"}
              </Button>
            ) : (
              <div className="mm-row">
                <Link className="mm-btn mm-btn--primary" href="/login" onClick={() => setOpen(false)}>
                  Sign in
                </Link>
                <Link className="mm-btn" href="/register" onClick={() => setOpen(false)}>
                  Create account
                </Link>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
