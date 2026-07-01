import { app, BrowserWindow, shell, Menu, ipcMain } from "electron";
import * as path from "path";
import { loadConfig } from "./config";

let mainWindow: BrowserWindow | null = null;

const APP_VERSION = app.getVersion();
const APP_NAME = app.getName();

// ---------------------------------------------------------------------------
// Health check
// ---------------------------------------------------------------------------

async function checkHealth(healthUrl: string, timeoutMs: number): Promise<boolean> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(healthUrl, { signal: controller.signal });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

async function waitForBackend(
  healthUrl: string,
  timeoutMs: number,
  intervalMs: number,
): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await checkHealth(healthUrl, 3000)) return true;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}

// ---------------------------------------------------------------------------
// Window creation
// ---------------------------------------------------------------------------

function createWindow(appUrl: string, healthUrl: string): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 600,
    title: "MailMind",
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
      sandbox: true,
    },
  });

  // External links → system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (
      url.startsWith("https:") ||
      url.startsWith("http:") ||
      url.startsWith("mailto:")
    ) {
      shell.openExternal(url);
    }
    return { action: "deny" };
  });

  // Block insecure navigation
  mainWindow.webContents.on("will-navigate", (event, url) => {
    const parsed = new URL(url);
    const allowed = new URL(appUrl);
    if (parsed.origin !== allowed.origin) {
      event.preventDefault();
    }
  });

  // Show when ready
  mainWindow.once("ready-to-show", () => {
    mainWindow?.show();
  });

  // Clean up on close
  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  // Load app or fallback
  loadApp(appUrl, healthUrl);
}

async function loadApp(appUrl: string, healthUrl: string): Promise<void> {
  if (!mainWindow) return;

  const healthy = await checkHealth(healthUrl, 5000);
  if (healthy) {
    mainWindow.loadURL(appUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, "fallback.html"));
  }
}

// ---------------------------------------------------------------------------
// IPC handlers
// ---------------------------------------------------------------------------

function registerIpcHandlers(appUrl: string, healthUrl: string): void {
  ipcMain.handle("get-app-info", () => ({
    name: APP_NAME,
    version: APP_VERSION,
    platform: process.platform,
  }));

  ipcMain.handle("get-config", () => ({
    appUrl,
    healthUrl,
  }));

  ipcMain.handle("retry-connection", async () => {
    if (!mainWindow) return false;
    const healthy = await checkHealth(healthUrl, 5000);
    if (healthy) {
      mainWindow.loadURL(appUrl);
      return true;
    }
    return false;
  });

  ipcMain.handle("open-external", (_event, url: string) => {
    if (
      url.startsWith("https:") ||
      url.startsWith("http:") ||
      url.startsWith("mailto:")
    ) {
      shell.openExternal(url);
    }
  });
}

// ---------------------------------------------------------------------------
// Application menu
// ---------------------------------------------------------------------------

function buildMenu(): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: "File",
      submenu: [{ role: "quit" }],
    },
    {
      label: "Edit",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" },
      ],
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    {
      label: "Window",
      submenu: [{ role: "minimize" }, { role: "close" }],
    },
    {
      label: "Help",
      submenu: [
        {
          label: "MailMind Documentation",
          click: () => shell.openExternal("https://github.com/Vibe-Coding-X/mailmind-ai-email-copilot"),
        },
        {
          label: "Report Issue",
          click: () =>
            shell.openExternal(
              "https://github.com/Vibe-Coding-X/mailmind-ai-email-copilot/issues",
            ),
        },
      ],
    },
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  const config = loadConfig();

  buildMenu();
  registerIpcHandlers(config.appUrl, config.healthUrl);
  createWindow(config.appUrl, config.healthUrl);

  // macOS: re-create window when dock icon clicked
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(config.appUrl, config.healthUrl);
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

// Security: prevent new WebContents creation
app.on("web-contents-created", (_event, contents) => {
  contents.on("will-attach-webview", (event) => {
    event.preventDefault();
  });
});
