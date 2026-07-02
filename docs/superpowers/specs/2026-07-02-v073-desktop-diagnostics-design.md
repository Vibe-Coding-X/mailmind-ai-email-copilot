# v0.7.3 Desktop Diagnostics Design

## Goal

Deliver a desktop-focused diagnostics and configuration layer for the Electron shell so users can understand why MailMind is unavailable, inspect the active desktop configuration, open log output, and change desktop connection settings without editing files manually.

## Scope

This version adds four user-visible capabilities:

1. A desktop settings and diagnostics window
2. An upgraded fallback page with diagnostics actions
3. Persistent desktop logs written by the Electron main process
4. Copyable diagnostics output and desktop config editing

This version does not add embedded backend/runtime management, API-level backend diagnostics, or a full log viewer.

## User Experience

### Entry Points

Users can open desktop settings and diagnostics from:

- The application menu
- The tray menu
- The fallback page
- The main web UI through a desktop-specific settings route

### Diagnostics Content

The initial diagnostics payload contains:

- App name and version
- Platform
- Current `appUrl`
- Current `healthUrl`
- Desktop behavior flags
- Latest desktop connection result
- Log directory path

### Configuration Surface

The editable desktop settings are:

- `appUrl`
- `healthUrl`
- `minimizeToTray`
- `showWindowOnStartup`
- `notificationsEnabled`

These settings remain desktop-only and do not modify backend or frontend application settings.

## Architecture

The implementation keeps the Electron main process as the source of truth for desktop runtime state and filesystem access.

### Main Process Responsibilities

The main process owns:

- Reading and writing desktop config
- Reading and writing desktop logs
- Tracking the latest connection status
- Producing the diagnostics snapshot
- Opening the settings/diagnostics window
- Serving IPC methods used by both the fallback page and the frontend settings page

### Frontend Responsibilities

The frontend gets a new route, `/settings/desktop`, rendered inside the existing app shell. It displays desktop-only settings and diagnostics data by calling Electron IPC exposed through `preload.ts`.

This page must degrade safely: when opened in a plain browser, it should show a clear "desktop-only" unavailable state instead of breaking.

### Fallback Responsibilities

`fallback.html` remains a local page loaded directly by Electron when the MailMind services are unavailable. It is upgraded to show:

- Current desktop endpoints
- Latest connection result
- Open desktop settings
- Open log directory
- Copy diagnostics

This page remains the guaranteed diagnostics entry point when the frontend is unreachable.

## File Structure

### Desktop Main Process

- `desktop/src/main.ts`
  Add settings-window creation, diagnostics IPC, log writing hooks, and fallback action integration.
- `desktop/src/config.ts`
  Expand desktop config shape, defaults, read/write helpers.
- `desktop/src/connection-state.ts`
  Keep connection transition logic and add latest-check status shaping for diagnostics output.
- `desktop/src/window-state.ts`
  Continue to own persisted window state.
- `desktop/src/tray-policy.ts`
  Continue to own close-to-tray behavior.
- `desktop/src/preload.ts`
  Expose settings/diagnostics IPC APIs to renderer pages.

### New Desktop Support Modules

- `desktop/src/logger.ts`
  Append structured log lines to `userData/logs/desktop.log` and expose log path helpers.
- `desktop/src/diagnostics.ts`
  Build the user-facing diagnostics snapshot and copy text.
- `desktop/src/settings-window.ts`
  Centralize creation/loading behavior for the diagnostics/settings window.

### Frontend

- `frontend/src/app/settings/desktop/page.tsx`
  Desktop settings and diagnostics UI.
- `frontend/src/i18n/locales/en.json`
- `frontend/src/i18n/locales/zh.json`
  Desktop settings labels, actions, and unavailable-state copy.
- `frontend/src/components/app-shell.tsx`
  Add desktop settings navigation entry.

### Local Fallback UI

- `desktop/src/fallback.html`
  Add diagnostics actions and desktop settings action.
- `desktop/src/fallback.css`
  Extend layout to support configuration and diagnostics controls.

### Tests

- `desktop/tests/config.test.ts`
  Desktop config read/write and defaults.
- `desktop/tests/diagnostics.test.ts`
  Diagnostics snapshot and copy formatting.
- Existing desktop tests remain and expand as needed.

### Documentation

- `docs/desktop/DESKTOP_SHELL.md`
  Document desktop settings/diagnostics flow.
- `docs/release-notes/v0.7.3-config-diagnostics.md`
  Release notes for this version.

## Data Flow

### Settings Window

1. User triggers "Desktop Settings" from menu, tray, fallback page, or frontend entry
2. Electron opens a dedicated settings window
3. Electron attempts to load frontend route `/settings/desktop`
4. If frontend is unavailable, Electron loads a local diagnostics fallback page for that window

### Diagnostics Query

1. Renderer calls `window.electronAPI.getDesktopDiagnostics()`
2. Main process combines config, current connection status, app metadata, and log path
3. Renderer renders the snapshot or allows copying it

### Config Save

1. Renderer submits edited desktop settings
2. Main process validates and persists `config.json`
3. Main process returns the canonical saved config
4. Renderer shows success feedback and explains whether reconnect or reload is needed

## Error Handling

- Invalid desktop config file: ignore bad file contents, use defaults, log the parsing failure
- Invalid save input: reject through IPC with a user-facing validation message
- Frontend unavailable for settings window: fall back to local diagnostics page
- Log write failure: do not crash the app; keep the app functional and skip file logging
- Clipboard or shell-open failure: return a renderer-visible error state

## Testing Strategy

### Automated

- Node tests for config defaults and persistence
- Node tests for diagnostics snapshot formatting
- Existing Node tests for window state, tray policy, and connection transitions continue to run
- Desktop TypeScript compile and build verification

### Manual

- Open fallback page with frontend/backend unavailable
- Open desktop settings from menu
- Open desktop settings from tray
- Open desktop settings from fallback page
- Open desktop settings from main UI nav
- Save config and relaunch
- Copy diagnostics and confirm output structure
- Open log directory after log file creation

## Rollout Notes

The design intentionally avoids building a large desktop-only subsystem. The settings page uses the existing frontend shell where possible, while fallback diagnostics stay local so there is always at least one working support surface when the web UI cannot load.
