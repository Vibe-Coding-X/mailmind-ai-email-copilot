/**
 * Theme model for MailMind (frontend theme system v2).
 *
 * A theme is two orthogonal axes:
 *   - preset: the visual personality (color language, density, elevation)
 *   - mode:   light / dark
 *
 * v2 keeps a small set of optional presets, while the default stays a calm
 * dense-minimal workspace suited to email and archive workflows.
 *
 * This module is pure data + helpers — NO React, NO DOM side effects beyond the
 * small reader/writer helpers, and it persists ONLY the theme preference.
 */

export type ThemeMode = "light" | "dark";

export type ThemePreset =
  | "neon-cyber"
  | "glass-aurora"
  | "gradient-flow"
  | "soft-clay"
  | "noir-pulse"
  | "dense-minimal";

export interface ThemeChoice {
  preset: ThemePreset;
  mode: ThemeMode;
}

export const DEFAULT_THEME = {
  preset: "dense-minimal",
  mode: "light",
} as const satisfies ThemeChoice;

export const THEME_PRESETS: ThemePreset[] = [
  "neon-cyber",
  "glass-aurora",
  "gradient-flow",
  "soft-clay",
  "noir-pulse",
  "dense-minimal",
];

export const THEME_MODES: ThemeMode[] = ["light", "dark"];

/** Human-facing labels + one-line descriptions for the switcher UI. */
export const PRESET_META: Record<
  ThemePreset,
  { label: string; hint: string }
> = {
  "neon-cyber": {
    label: "Neon Cyber",
    hint: "High contrast dark theme with bright cyan accents",
  },
  "glass-aurora": {
    label: "Glass Aurora",
    hint: "Soft translucent surfaces with a light blue accent",
  },
  "gradient-flow": {
    label: "Gradient Flow",
    hint: "Brighter accent styling for marketing-style demos",
  },
  "soft-clay": {
    label: "Soft Clay",
    hint: "Warm surfaces with softer elevation",
  },
  "noir-pulse": {
    label: "Noir Pulse",
    hint: "Dark mode with amber status color",
  },
  "dense-minimal": {
    label: "Dense Minimal",
    hint: "Compact, quiet workspace for daily use",
  },
};

export const MODE_META: Record<ThemeMode, { label: string }> = {
  light: { label: "Light" },
  dark: { label: "Dark" },
};

/** localStorage key — theme preference only. */
export const THEME_STORAGE_KEY = "mailmind-theme";
export const THEME_STORAGE_VERSION_KEY = "mailmind-theme-version";
export const THEME_STORAGE_VERSION = "2026-07-ui-polish";
const LEGACY_DEFAULT_THEME_STORAGE_VALUES = new Set(["neon-cyber:dark"]);

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

  // Legacy preset migration
  const legacyMap: Record<string, ThemePreset> = {
    "amber-focus": "neon-cyber",
    "paper-calm": "glass-aurora",
  };
  if (preset && legacyMap[preset]) {
    return { preset: legacyMap[preset], mode: isThemeMode(mode) ? mode : "dark" };
  }

  return null;
}

function shouldMigrateLegacyDefaultTheme(
  raw: string | null,
  version: string | null,
): boolean {
  return (
    version !== THEME_STORAGE_VERSION &&
    raw !== null &&
    LEGACY_DEFAULT_THEME_STORAGE_VALUES.has(raw)
  );
}

/** Serialize a choice for storage / data attributes. */
export function serializeThemeChoice(choice: ThemeChoice): string {
  return `${choice.preset}:${choice.mode}`;
}

/**
 * Resolve the initial theme without throwing in any environment:
 *   stored preference > prefers-color-scheme (mode only) > DEFAULT_THEME.
 */
export function resolveInitialTheme(): ThemeChoice {
  if (typeof window === "undefined") {
    return DEFAULT_THEME;
  }

  try {
    const raw = window.localStorage.getItem(THEME_STORAGE_KEY);
    const version = window.localStorage.getItem(THEME_STORAGE_VERSION_KEY);
    if (shouldMigrateLegacyDefaultTheme(raw, version)) {
      persistThemeChoice(DEFAULT_THEME);
      return DEFAULT_THEME;
    }

    const stored = parseThemeChoice(raw);
    if (stored) {
      return stored;
    }
  } catch {
    // localStorage may be unavailable — ignore.
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
    window.localStorage.setItem(THEME_STORAGE_VERSION_KEY, THEME_STORAGE_VERSION);
  } catch {
    // Ignore storage failures.
  }
}

/** Apply the choice to <html> data attributes. */
export function applyThemeToDocument(choice: ThemeChoice): void {
  if (typeof document === "undefined") {
    return;
  }
  const root = document.documentElement;
  root.dataset.themePreset = choice.preset;
  root.dataset.themeMode = choice.mode;
}
