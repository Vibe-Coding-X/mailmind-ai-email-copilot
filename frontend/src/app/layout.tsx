import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/components/theme-provider";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "MailMind · AI Email Copilot",
  description:
    "MailMind is a dashboard-first AI Email Copilot. This is an early scaffold.",
};

/**
 * Applied before hydration so the first paint already matches the stored theme
 * (no flash, no hydration mismatch). It only reads one localStorage key
 * (theme preference) and falls back to Amber Focus + prefers-color-scheme. No user,
 * session, or token data is read.
 */
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var d = document.documentElement;
    var preset = "amber-focus";
    var mode = "light";
    var raw = null;
    try { raw = localStorage.getItem("mailmind-theme"); } catch (e) {}
    if (raw) {
      var parts = raw.split(":");
      var presets = ["amber-focus", "noir-pulse", "paper-calm", "dense-minimal"];
      var modes = ["light", "dark"];
      if (presets.indexOf(parts[0]) !== -1) preset = parts[0];
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
      data-theme-preset="amber-focus"
      data-theme-mode="light"
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
