import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";

/**
 * AppShell — product layout frame for MailMind (design preview).
 *
 * Structural/presentational only. It does not load user data, auth state, or
 * any Daily Digest content. Nav links point at documented routes; destination
 * pages are static design previews. A sidebar status block makes the
 * "not connected" state unmistakable.
 */

interface NavLink {
  href: string;
  label: string;
}

// Routes reflect docs/frontend/FRONTEND_DESIGN.md section 2 page structure.
// Product direction is dashboard-first, so Dashboard leads (not the inbox).
const PRIMARY_NAV: NavLink[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/emails", label: "Emails" },
  { href: "/emails/new", label: "New Emails" },
];

const SETTINGS_NAV: NavLink[] = [
  { href: "/settings/profile", label: "Profile" },
  { href: "/settings/mailboxes", label: "Mailboxes" },
  { href: "/settings/security", label: "Security" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="mm-shell">
      <aside className="mm-sidebar">
        <div>
          <div className="mm-brand-name">MailMind</div>
          <div className="mm-brand-sub">AI Email Copilot</div>
        </div>

        <NavSection title="Workspace" links={PRIMARY_NAV} />
        <NavSection title="Settings" links={SETTINGS_NAV} />

        <SidebarStatus />
      </aside>

      <main className="mm-main">{children}</main>
    </div>
  );
}

function NavSection({ title, links }: { title: string; links: NavLink[] }) {
  return (
    <nav>
      <div className="mm-nav-label">{title}</div>
      <ul className="mm-nav-list">
        {links.map((link) => (
          <li key={link.href}>
            <a className="mm-nav-link" href={link.href}>
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

function SidebarStatus() {
  return (
    <div style={{ marginTop: "auto" }}>
      <div className="mm-nav-label">Status</div>
      <div
        className="mm-stack"
        style={{ gap: 6, alignItems: "flex-start" }}
      >
        <Badge tone="warn" dot>
          Frontend scaffold
        </Badge>
        <Badge tone="neutral" dot>
          Backend not connected
        </Badge>
        <Badge tone="neutral" dot>
          Gmail not connected
        </Badge>
        <Badge tone="neutral" dot>
          AI not connected
        </Badge>
      </div>
    </div>
  );
}
