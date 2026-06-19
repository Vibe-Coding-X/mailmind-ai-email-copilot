"use client";

/**
 * ThemeSwitcher — lets the user pick a preset and light/dark mode. Changes take
 * effect immediately (via ThemeProvider → <html> data attributes) and persist
 * to localStorage. It reads/writes ONLY the theme preference; it does not touch
 * auth, mailbox, or any backend state.
 *
 * `compact` renders just the mode toggle (for tight spots like auth cards);
 * the full control also exposes the preset choices.
 */

import { useTheme } from "@/components/theme-provider";
import {
  SegmentedControl,
  type SegmentedOption,
} from "@/components/ui/segmented-control";
import {
  MODE_META,
  PRESET_META,
  THEME_MODES,
  THEME_PRESETS,
  type ThemeMode,
  type ThemePreset,
} from "@/lib/theme";

const PRESET_OPTIONS: SegmentedOption<ThemePreset>[] = THEME_PRESETS.map(
  (preset) => ({
    value: preset,
    label: PRESET_META[preset].label,
    title: PRESET_META[preset].hint,
  }),
);

const MODE_OPTIONS: SegmentedOption<ThemeMode>[] = THEME_MODES.map((mode) => ({
  value: mode,
  label: MODE_META[mode].label,
}));

export function ThemeSwitcher({ compact = false }: { compact?: boolean }) {
  const { preset, mode, setPreset, setMode } = useTheme();

  if (compact) {
    return (
      <SegmentedControl
        label="Color mode"
        value={mode}
        options={MODE_OPTIONS}
        onChange={setMode}
      />
    );
  }

  return (
    <div className="mm-stack" style={{ gap: 10, alignItems: "flex-start" }}>
      <div className="mm-stack" style={{ gap: 6, alignItems: "flex-start" }}>
        <span className="mm-nav-label" style={{ marginBottom: 0 }}>
          Style
        </span>
        <SegmentedControl
          label="Theme style"
          value={preset}
          options={PRESET_OPTIONS}
          onChange={setPreset}
        />
      </div>
      <div className="mm-stack" style={{ gap: 6, alignItems: "flex-start" }}>
        <span className="mm-nav-label" style={{ marginBottom: 0 }}>
          Mode
        </span>
        <SegmentedControl
          label="Color mode"
          value={mode}
          options={MODE_OPTIONS}
          onChange={setMode}
        />
      </div>
    </div>
  );
}
