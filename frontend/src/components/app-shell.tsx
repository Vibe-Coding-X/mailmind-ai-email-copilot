import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { AuthStatus } from "@/components/auth-status";
import { ThemeSwitcher } from "@/components/theme-switcher";

/**
 * AppShell — product layout frame for MailMind (design preview).
 *
 * Product layout frame. Authentication status is live via GET /api/auth/me;
 * Gmail, Digest, and AI areas remain design previews until their own tasks.
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
    <div style={{ marginTop: "auto" }} className="mm-stack" >
      <div>
        <div className="mm-nav-label">Theme</div>
        <ThemeSwitcher />
      </div>
      <div>
        <div className="mm-nav-label">Status</div>
        <div
          className="mm-stack"
          style={{ gap: 6, alignItems: "flex-start" }}
        >
          <AuthStatus compact />
          <Badge tone="neutral" dot>
            Gmail not connected
          </Badge>
        </div>
      </div>
    </div>
  );
}
