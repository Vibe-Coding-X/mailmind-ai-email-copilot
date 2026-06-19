/**
 * Theme model for MailMind (frontend theme system).
 *
 * A theme is two orthogonal axes:
 *   - preset: the visual personality (shape language, density, elevation)
 *   - mode:   light / dark
 *
 * This module is pure data + helpers — NO React, NO DOM side effects beyond the
 * small reader/writer helpers, and it persists ONLY the theme preference. It
 * never reads or writes any user, session, token, or mailbox data, and never
 * touches cookies. The persisted value is a plain string key in localStorage.
 */

export type ThemeMode = "light" | "dark";

export type ThemePreset = "capsule" | "clean" | "minimal" | "soft";

export interface ThemeChoice {
  preset: ThemePreset;
  mode: ThemeMode;
}

/** Capsule (card-pill) is the product's default personality. */
export const DEFAULT_THEME: ThemeChoice = { preset: "capsule", mode: "light" };

export const THEME_PRESETS: ThemePreset[] = [
  "capsule",
  "clean",
  "minimal",
  "soft",
];

export const THEME_MODES: ThemeMode[] = ["light", "dark"];

/** Human-facing labels + one-line descriptions for the switcher UI. */
export const PRESET_META: Record<
  ThemePreset,
  { label: string; hint: string }
> = {
  capsule: { label: "Capsule", hint: "Rounded cards, pill controls, soft depth" },
  clean: { label: "Clean", hint: "Crisp surfaces, high contrast" },
  minimal: { label: "Minimal", hint: "Hairline borders, flat and quiet" },
  soft: { label: "Soft", hint: "Gentle tints, low contrast" },
};

export const MODE_META: Record<ThemeMode, { label: string }> = {
  light: { label: "Light" },
  dark: { label: "Dark" },
};

/** localStorage key — theme preference only. */
export const THEME_STORAGE_KEY = "mailmind-theme";

function isThemePreset(value: unknown): value is ThemePreset {
  return (
    typeof value === "string" &&
    (THEME_PRESETS as string[]).includes(value)
  );
}

function isThemeMode(value: unknown): value is ThemeMode {
  return typeof value === "string" && (THEME_MODES as string[]).includes(value);
}

/** Parse a stored "preset:mode" string into a validated choice (or null). */
export function parseThemeChoice(raw: string | null): ThemeChoice | null {
  if (!raw) {
    return null;
  }

  const [preset, mode] = raw.split(":");
  if (isThemePreset(preset) && isThemeMode(mode)) {
    return { preset, mode };
  }

  return null;
}

/** Serialize a choice for storage / data attributes. */
export function serializeThemeChoice(choice: ThemeChoice): string {
  return `${choice.preset}:${choice.mode}`;
}

/**
 * Resolve the initial theme without throwing in any environment:
 *   stored preference > prefers-color-scheme (mode only) > DEFAULT_THEME.
 * The preset always falls back to the default; only the mode follows the OS.
 */
export function resolveInitialTheme(): ThemeChoice {
  if (typeof window === "undefined") {
    return DEFAULT_THEME;
  }

  try {
    const stored = parseThemeChoice(
      window.localStorage.getItem(THEME_STORAGE_KEY),
    );
    if (stored) {
      return stored;
    }
  } catch {
    // localStorage may be unavailable (privacy mode / SSR mismatch) — ignore.
  }

  const prefersDark =
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;

  return { preset: DEFAULT_THEME.preset, mode: prefersDark ? "dark" : "light" };
}

/** Persist the preference (best-effort; never throws). */
export function persistThemeChoice(choice: ThemeChoice): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, serializeThemeChoice(choice));
  } catch {
    // Ignore storage failures — theme still applies for the session.
  }
}

/** Apply the choice to <html> data attributes (the CSS theming hook). */
export function applyThemeToDocument(choice: ThemeChoice): void {
  if (typeof document === "undefined") {
    return;
  }
  const root = document.documentElement;
  root.dataset.themePreset = choice.preset;
  root.dataset.themeMode = choice.mode;
}
