import type { ReactNode } from "react";
import { AccountMenu } from "@/components/account-menu";

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
  { href: "/actions", label: "Actions" },
];

const SETTINGS_NAV: NavLink[] = [
  { href: "/settings/mailboxes", label: "Mailboxes" },
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

        <div style={{ marginTop: "auto" }}>
          <AccountMenu />
        </div>
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
