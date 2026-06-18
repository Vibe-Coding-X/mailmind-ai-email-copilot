import { AppShell } from "@/components/app-shell";
import {
  PlaceholderPanel,
  RouteHeading,
  StatusPlaceholder,
} from "@/components/placeholders";

/**
 * /settings/profile (T005 scaffold). User profile/preferences placeholder.
 * Documented related routes: GET/PATCH /api/users/me (API_DESIGN.md section 8).
 * No profile data is loaded or saved here.
 */
export default function ProfileSettingsPage() {
  return (
    <AppShell>
      <RouteHeading
        title="Profile"
        description="User preferences such as timezone and display options."
      />
      <div style={{ marginBottom: 16 }}>
        <StatusPlaceholder feature="Profile settings" />
      </div>
      <PlaceholderPanel title="Preferences">
        Placeholder. No user data is loaded or persisted.
      </PlaceholderPanel>
    </AppShell>
  );
}
