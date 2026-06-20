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
  icon: "dashboard" | "emails" | "actions" | "mailboxes";
}

// Routes reflect docs/frontend/FRONTEND_DESIGN.md section 2 page structure.
// Product direction is dashboard-first, so Dashboard leads (not the inbox).
const PRIMARY_NAV: NavLink[] = [
  { href: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { href: "/emails", label: "Emails", icon: "emails" },
  { href: "/actions", label: "Actions", icon: "actions" },
];

const SETTINGS_NAV: NavLink[] = [
  { href: "/settings/mailboxes", label: "Mailboxes", icon: "mailboxes" },
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
              <NavIcon icon={link.icon} />
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}

function NavIcon({ icon }: { icon: NavLink["icon"] }) {
  const paths: Record<NavLink["icon"], ReactNode> = {
    dashboard: (
      <>
        <path d="M4 5h7v7H4z" />
        <path d="M13 5h7v4h-7z" />
        <path d="M13 11h7v8h-7z" />
        <path d="M4 14h7v5H4z" />
      </>
    ),
    emails: (
      <>
        <path d="M4 6h16v12H4z" />
        <path d="m4 7 8 6 8-6" />
      </>
    ),
    actions: (
      <>
        <path d="M5 7h14" />
        <path d="M5 12h10" />
        <path d="M5 17h7" />
        <path d="m16 15 2 2 4-5" />
      </>
    ),
    mailboxes: (
      <>
        <path d="M4 8h16v9H4z" />
        <path d="M8 8V6h8v2" />
        <path d="M4 12h16" />
      </>
    ),
  };

  return (
    <svg
      className="mm-nav-icon"
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[icon]}
    </svg>
  );
}
