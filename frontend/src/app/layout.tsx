import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/components/theme-provider";
import { MailMindI18nProvider } from "@/i18n/provider";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "MailMind · Email Workspace",
  description: "MailMind is a local email archive and daily digest workspace.",
};

/**
 * Applied before hydration so the first paint already matches the stored theme
 * (no flash, no hydration mismatch). Dense Minimal is now the default.
 */
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var d = document.documentElement;
    var defaultPreset = "dense-minimal";
    var defaultMode = "light";
    var versionKey = "mailmind-theme-version";
    var currentVersion = "2026-07-ui-polish";
    var preset = defaultPreset;
    var mode = defaultMode;
    var raw = null;
    var version = null;
    try { raw = localStorage.getItem("mailmind-theme"); } catch (e) {}
    try { version = localStorage.getItem(versionKey); } catch (e) {}
    if (version !== currentVersion && raw === "neon-cyber:dark") {
      raw = null;
      try {
        localStorage.setItem("mailmind-theme", defaultPreset + ":" + defaultMode);
        localStorage.setItem(versionKey, currentVersion);
      } catch (e) {}
    }
    if (raw) {
      var parts = raw.split(":");
      var presets = ["neon-cyber", "glass-aurora", "gradient-flow", "soft-clay", "noir-pulse", "dense-minimal"];
      var legacyMap = { "amber-focus": "neon-cyber", "paper-calm": "glass-aurora" };
      var modes = ["light", "dark"];
      var p = parts[0];
      if (legacyMap[p]) p = legacyMap[p];
      if (presets.indexOf(p) !== -1) preset = p;
      if (modes.indexOf(parts[1]) !== -1) mode = parts[1];
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      mode = "dark";
    }
    d.setAttribute("data-theme-preset", preset);
    d.setAttribute("data-theme-mode", mode);
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html
      lang="en"
      data-theme-preset="dense-minimal"
      data-theme-mode="light"
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <ThemeProvider>
          <MailMindI18nProvider>
            <AuthProvider>{children}</AuthProvider>
          </MailMindI18nProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
