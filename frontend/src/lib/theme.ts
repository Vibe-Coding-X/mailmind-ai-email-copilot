/**
 * Theme model for MailMind (frontend theme system v2).
 *
 * A theme is two orthogonal axes:
 *   - preset: the visual personality (color language, density, elevation)
 *   - mode:   light / dark
 *
 * v2 brings dramatic visual effects: neon-cyber as default, glass-aurora,
 * gradient-flow, soft-clay, plus preserved noir-pulse and dense-minimal.
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

/** Neon Cyber is now the DEFAULT theme for maximum visual impact. */
export const DEFAULT_THEME: ThemeChoice = {
  preset: "neon-cyber",
  mode: "dark",
};

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
    hint: "Cyberpunk neon glow, deep black, cyan/magenta accents",
  },
  "glass-aurora": {
    label: "Glass Aurora",
    hint: "Frosted glass, soft gradients, aurora-like colors",
  },
  "gradient-flow": {
    label: "Gradient Flow",
    hint: "Modern SaaS gradients, purple-blue flow",
  },
  "soft-clay": {
    label: "Soft Clay",
    hint: "Neumorphic clay, soft shadows, organic shapes",
  },
  "noir-pulse": {
    label: "Noir Pulse",
    hint: "Dark contrast, amber signal, sharp edges",
  },
  "dense-minimal": {
    label: "Dense Minimal",
    hint: "Compact, flat, minimal decoration",
  },
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
    const stored = parseThemeChoice(
      window.localStorage.getItem(THEME_STORAGE_KEY),
    );
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
