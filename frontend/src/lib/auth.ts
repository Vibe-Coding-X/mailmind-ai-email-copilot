"use client";

/**
 * Auth state (auth integration round).
 *
 * Minimal in-memory auth context backed entirely by the backend session
 * cookie. There is NO localStorage, NO cookie parsing, and NO fabricated state:
 * the current user is derived solely from GET /api/auth/me, which the browser
 * authenticates via the HttpOnly cookie (credentials: "include").
 *
 * On mount (and after register/login/logout) we (re)fetch /me, so a page
 * refresh restores the session if the cookie is still valid.
 */

import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { ApiRequestError, apiClient } from "./api-client";
import type { AuthUser } from "./api-types";

type AuthStatus =
  | "loading"
  | "authenticated"
  | "unauthenticated"
  | "unavailable";

interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  /** Re-derive auth state from GET /api/auth/me. */
  refresh: () => Promise<void>;
  register: (input: {
    email: string;
    password: string;
    timezone?: string;
  }) => Promise<void>;
  login: (input: { email: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await apiClient.auth.me();
      setUser(res.data.user);
      setStatus("authenticated");
    } catch (error) {
      // A 401 simply means "not signed in". Network/CORS/backend failures are
      // a different user-facing state so the UI can show Backend unavailable.
      setUser(null);
      setStatus(
        error instanceof ApiRequestError && error.status !== 401
          ? "unavailable"
          : "unauthenticated",
      );
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const register = useCallback(
    async (input: { email: string; password: string; timezone?: string }) => {
      const res = await apiClient.auth.register(input);
      setUser(res.data.user);
      setStatus("authenticated");
    },
    [],
  );

  const login = useCallback(
    async (input: { email: string; password: string }) => {
      const res = await apiClient.auth.login(input);
      setUser(res.data.user);
      setStatus("authenticated");
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      await apiClient.auth.logout();
    } finally {
      // Clear in-memory state regardless; the cookie is cleared server-side.
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  return createElement(
    AuthContext.Provider,
    { value: { status, user, refresh, register, login, logout } },
    children,
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
