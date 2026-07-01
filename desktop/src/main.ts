import { app, BrowserWindow, shell, Menu, ipcMain, Notification, Tray, nativeImage } from "electron";
import * as path from "path";
import { loadConfig } from "./config";
import { getConnectionTransition } from "./connection-state";
import { loadWindowState, saveWindowState, type WindowBounds } from "./window-state";

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let forceQuit = false;
let hasShownTrayHint = false;
let connectionHealthy: boolean | null = null;

const APP_VERSION = app.getVersion();
const APP_NAME = app.getName();
const TRAY_TOOLTIP = "MailMind";

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

// ---------------------------------------------------------------------------
// Window creation
// ---------------------------------------------------------------------------

function createWindow(appUrl: string, healthUrl: string): void {
  const userDataPath = app.getPath("userData");
  const persistedState = loadWindowState(userDataPath);

  mainWindow = new BrowserWindow({
    width: persistedState.width,
    height: persistedState.height,
    x: persistedState.x,
    y: persistedState.y,
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
    if (persistedState.isMaximized) {
      mainWindow?.maximize();
    }
    mainWindow?.show();
  });

  mainWindow.on("resize", () => {
    persistWindowState();
  });

  mainWindow.on("move", () => {
    persistWindowState();
  });

  mainWindow.on("maximize", () => {
    persistWindowState();
  });

  mainWindow.on("unmaximize", () => {
    persistWindowState();
  });

  mainWindow.on("close", (event) => {
    if (forceQuit || process.platform === "darwin") {
      return;
    }

    event.preventDefault();
    mainWindow?.hide();
    showTrayHint();
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
  notifyConnectionTransition(healthy);
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
      notifyConnectionTransition(true);
      mainWindow.loadURL(appUrl);
      return true;
    }
    notifyConnectionTransition(false);
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

function buildMenu(appUrl: string): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: "File",
      submenu: [
        {
          label: "Show MailMind",
          click: () => showMainWindow(),
        },
        {
          label: "Hide MailMind",
          click: () => mainWindow?.hide(),
        },
        { type: "separator" },
        {
          label: "Open Web App",
          click: () => shell.openExternal(appUrl),
        },
        { type: "separator" },
        { role: "quit" },
      ],
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
      submenu: [
        { role: "minimize" },
        {
          label: "Hide to Tray",
          click: () => mainWindow?.hide(),
        },
        { role: "close" },
      ],
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

function buildTray(appUrl: string): void {
  if (tray) {
    return;
  }

  const iconPath = path.join(__dirname, "..", "assets", "icon.png");
  const icon = nativeImage.createFromPath(iconPath);
  tray = new Tray(icon);
  tray.setToolTip(TRAY_TOOLTIP);
  tray.setContextMenu(
    Menu.buildFromTemplate([
      {
        label: "Show MailMind",
        click: () => showMainWindow(),
      },
      {
        label: "Open Web App",
        click: () => shell.openExternal(appUrl),
      },
      {
        label: "Quit",
        click: () => {
          forceQuit = true;
          app.quit();
        },
      },
    ]),
  );
  tray.on("click", () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide();
    } else {
      showMainWindow();
    }
  });
}

function showMainWindow(): void {
  if (!mainWindow) {
    return;
  }

  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }

  mainWindow.show();
  mainWindow.focus();
}

function persistWindowState(): void {
  if (!mainWindow) {
    return;
  }

  const bounds = mainWindow.getBounds();
  const state: WindowBounds = {
    x: bounds.x,
    y: bounds.y,
    width: bounds.width,
    height: bounds.height,
    isMaximized: mainWindow.isMaximized(),
  };

  saveWindowState(app.getPath("userData"), state);
}

function showNotification(title: string, body: string): void {
  if (!Notification.isSupported()) {
    return;
  }

  new Notification({ title, body }).show();
}

function showTrayHint(): void {
  if (hasShownTrayHint) {
    return;
  }

  hasShownTrayHint = true;
  showNotification("MailMind is still running", "The app was hidden to the system tray.");
}

function notifyConnectionTransition(healthy: boolean): void {
  const transition = getConnectionTransition(connectionHealthy, healthy);
  connectionHealthy = healthy;

  if (transition === "recovered") {
    showNotification("MailMind connected", "Local services are reachable again.");
  }

  if (transition === "lost") {
    showNotification("MailMind disconnected", "Local services are no longer reachable.");
  }
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  const config = loadConfig();

  buildMenu(config.appUrl);
  registerIpcHandlers(config.appUrl, config.healthUrl);
  buildTray(config.appUrl);
  createWindow(config.appUrl, config.healthUrl);

  // macOS: re-create window when dock icon clicked
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(config.appUrl, config.healthUrl);
    } else {
      showMainWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (forceQuit && process.platform !== "darwin") {
    app.quit();
  }
});

app.on("before-quit", () => {
  forceQuit = true;
});

// Security: prevent new WebContents creation
app.on("web-contents-created", (_event, contents) => {
  contents.on("will-attach-webview", (event) => {
    event.preventDefault();
  });
});
