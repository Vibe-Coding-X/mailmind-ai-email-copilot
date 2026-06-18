import type { ReactNode } from "react";

/**
 * AppShell — generic layout frame for MailMind pages (T005 scaffold).
 *
 * This is a structural placeholder only. It does not load user data, auth
 * state, or any Daily Digest content. Navigation links point at documented
 * routes but the destination pages are non-functional scaffolds.
 */

interface NavLink {
  href: string;
  label: string;
}

// Routes reflect docs/frontend/FRONTEND_DESIGN.md section 2 page structure.
// Product direction is dashboard-first, so /dashboard leads.
const PRIMARY_NAV: NavLink[] = [
  { href: "/dashboard", label: "Daily Digest" },
  { href: "/emails", label: "Today's Emails" },
  { href: "/emails/new", label: "New Emails" },
];

const SETTINGS_NAV: NavLink[] = [
  { href: "/settings/profile", label: "Profile" },
  { href: "/settings/mailboxes", label: "Mailboxes" },
  { href: "/settings/security", label: "Security" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "240px 1fr",
        minHeight: "100vh",
      }}
    >
      <aside
        style={{
          borderRight: "1px solid var(--mm-border)",
          background: "var(--mm-surface)",
          padding: "20px 16px",
        }}
      >
        <div style={{ fontWeight: 600, fontSize: 18, marginBottom: 4 }}>
          MailMind
        </div>
        <div style={{ color: "var(--mm-muted)", fontSize: 12, marginBottom: 24 }}>
          AI Email Copilot
        </div>

        <NavSection title="Workspace" links={PRIMARY_NAV} />
        <NavSection title="Settings" links={SETTINGS_NAV} />
      </aside>

      <main style={{ padding: "32px 40px", maxWidth: 1100 }}>{children}</main>
    </div>
  );
}

function NavSection({ title, links }: { title: string; links: NavLink[] }) {
  return (
    <nav style={{ marginBottom: 24 }}>
      <div
        style={{
          textTransform: "uppercase",
          fontSize: 11,
          letterSpacing: "0.06em",
          color: "var(--mm-muted)",
          marginBottom: 8,
        }}
      >
        {title}
      </div>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {links.map((link) => (
          <li key={link.href} style={{ marginBottom: 6 }}>
            <a href={link.href}>{link.label}</a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
