import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * /settings/security (T005 scaffold). Security settings placeholder.
 * Documented related route: PATCH /api/users/me/password (API_DESIGN.md
 * section 8). No password change is implemented here.
 */
export default function SecuritySettingsPage() {
  return (
    <AppShell>
      <RouteHeading
        title="Security"
        description="System login security settings such as password change."
      />
      <div style={{ marginBottom: 16 }}>
        <StatusPlaceholder feature="Security settings" />
      </div>
      <PlaceholderPanel title="Password">
        Placeholder. Password change is not implemented in this scaffold.
      </PlaceholderPanel>
    </AppShell>
  );
}
