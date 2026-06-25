"use client";

import type { ReactNode } from "react";
import { AccountMenu } from "@/components/account-menu";
import { useI18n } from "@/i18n/provider";

/**
 * AppShell — product layout frame for MailMind.
 * Enhanced with dramatic visual effects per theme.
 */

interface NavLink {
  href: string;
  labelKey:
    | "nav.dashboard"
    | "nav.emails"
    | "nav.actions"
    | "nav.mailboxes";
  icon: "dashboard" | "emails" | "actions" | "mailboxes";
}

const PRIMARY_NAV: NavLink[] = [
  { href: "/dashboard", labelKey: "nav.dashboard", icon: "dashboard" },
  { href: "/emails", labelKey: "nav.emails", icon: "emails" },
  { href: "/actions", labelKey: "nav.actions", icon: "actions" },
];

const SETTINGS_NAV: NavLink[] = [
  { href: "/settings/mailboxes", labelKey: "nav.mailboxes", icon: "mailboxes" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { t } = useI18n();

  return (
    <div className="mm-shell">
      <aside className="mm-sidebar">
        {/* Brand */}
        <div>
          <div className="mm-brand-name">MailMind</div>
          <div className="mm-brand-sub">{t("app.subtitle")}</div>
        </div>

        {/* Navigation */}
        <NavSection title={t("nav.workspace")} links={PRIMARY_NAV} />
        <NavSection title={t("nav.settings")} links={SETTINGS_NAV} />

        {/* Account at bottom */}
        <div style={{ marginTop: "auto" }}>
          <AccountMenu />
        </div>
      </aside>

      {/* Main content with page-level animation */}
      <main className="mm-main">{children}</main>
    </div>
  );
}

function NavSection({ title, links }: { title: string; links: NavLink[] }) {
  const { t } = useI18n();

  return (
    <nav>
      <div className="mm-nav-label">{title}</div>
      <ul className="mm-nav-list">
        {links.map((link) => (
          <li key={link.href}>
            <a className="mm-nav-link" href={link.href}>
              <NavIcon icon={link.icon} />
              {t(link.labelKey)}
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
