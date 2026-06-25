import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/components/theme-provider";
import { MailMindI18nProvider } from "@/i18n/provider";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "MailMind · AI Email Copilot",
  description: "MailMind is a dashboard-first AI Email Copilot.",
};

/**
 * Applied before hydration so the first paint already matches the stored theme
 * (no flash, no hydration mismatch). Neon Cyber is now the default.
 */
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var d = document.documentElement;
    var preset = "neon-cyber";
    var mode = "dark";
    var raw = null;
    try { raw = localStorage.getItem("mailmind-theme"); } catch (e) {}
    if (raw) {
      var parts = raw.split(":");
      var presets = ["neon-cyber", "glass-aurora", "gradient-flow", "soft-clay", "noir-pulse", "dense-minimal"];
      var legacyMap = { "amber-focus": "neon-cyber", "paper-calm": "glass-aurora" };
      var modes = ["light", "dark"];
      var p = parts[0];
      if (legacyMap[p]) p = legacyMap[p];
      if (presets.indexOf(p) !== -1) preset = p;
      if (modes.indexOf(parts[1]) !== -1) mode = parts[1];
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
      mode = "light";
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
      data-theme-preset="neon-cyber"
      data-theme-mode="dark"
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
