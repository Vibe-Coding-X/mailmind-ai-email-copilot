"use client";

/**
 * ThemeProvider — applies and persists the UI theme preference.
 *
 * The theme has two axes (preset × mode). State is initialized from
 * localStorage (preference only — never any user/session/token data) and
 * applied to <html> via data-theme-preset / data-theme-mode attributes, which
 * the stylesheet reads. An inline script in layout.tsx applies the same
 * attributes BEFORE hydration, so the initial paint already matches the stored
 * choice and there is no theme flash or hydration mismatch.
 *
 * This provider does no data fetching and has no backend awareness.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  DEFAULT_THEME,
  applyThemeToDocument,
  persistThemeChoice,
  resolveInitialTheme,
  type ThemeChoice,
  type ThemeMode,
  type ThemePreset,
} from "@/lib/theme";

interface ThemeContextValue {
  preset: ThemePreset;
  mode: ThemeMode;
  setPreset: (preset: ThemePreset) => void;
  setMode: (mode: ThemeMode) => void;
  setTheme: (choice: ThemeChoice) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function persistAndApply(next: ThemeChoice): ThemeChoice {
  applyThemeToDocument(next);
  persistThemeChoice(next);
  return next;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  // SSR + first client render use the default so markup matches the server.
  // The pre-hydration inline script has already set the real attributes on
  // <html>; the effect below syncs React state to the resolved choice.
  const [choice, setChoice] = useState<ThemeChoice>(DEFAULT_THEME);

  useEffect(() => {
    const resolved = resolveInitialTheme();
    setChoice(resolved);
    applyThemeToDocument(resolved);
  }, []);

  const setPreset = useCallback((preset: ThemePreset) => {
    setChoice((prev) => persistAndApply({ ...prev, preset }));
  }, []);

  const setMode = useCallback((mode: ThemeMode) => {
    setChoice((prev) => persistAndApply({ ...prev, mode }));
  }, []);

  const setTheme = useCallback((next: ThemeChoice) => {
    setChoice(() => persistAndApply(next));
  }, []);

  return (
    <ThemeContext.Provider
      value={{
        preset: choice.preset,
        mode: choice.mode,
        setPreset,
        setMode,
        setTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (ctx === null) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}
