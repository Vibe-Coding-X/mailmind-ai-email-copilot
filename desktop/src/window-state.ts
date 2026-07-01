import * as fs from "fs";
import * as path from "path";

export interface WindowBounds {
  x?: number;
  y?: number;
  width: number;
  height: number;
  isMaximized: boolean;
}

const DEFAULT_WINDOW_STATE: WindowBounds = {
  width: 1280,
  height: 860,
  isMaximized: false,
};

const WINDOW_STATE_FILE = "window-state.json";

export function getDefaultWindowState(): WindowBounds {
  return { ...DEFAULT_WINDOW_STATE };
}

export function loadWindowState(userDataPath: string): WindowBounds {
  try {
    const filePath = path.join(userDataPath, WINDOW_STATE_FILE);
    if (!fs.existsSync(filePath)) {
      return getDefaultWindowState();
    }

    const raw = fs.readFileSync(filePath, "utf-8");
    const parsed = JSON.parse(raw) as Partial<WindowBounds>;

    return {
      x: typeof parsed.x === "number" ? parsed.x : undefined,
      y: typeof parsed.y === "number" ? parsed.y : undefined,
      width: typeof parsed.width === "number" ? parsed.width : DEFAULT_WINDOW_STATE.width,
      height: typeof parsed.height === "number" ? parsed.height : DEFAULT_WINDOW_STATE.height,
      isMaximized: parsed.isMaximized === true,
    };
  } catch {
    return getDefaultWindowState();
  }
}

export function saveWindowState(userDataPath: string, state: WindowBounds): void {
  try {
    fs.mkdirSync(userDataPath, { recursive: true });
    const filePath = path.join(userDataPath, WINDOW_STATE_FILE);
    fs.writeFileSync(filePath, JSON.stringify(state, null, 2), "utf-8");
  } catch {
    // Ignore persistence failures in desktop preview mode.
  }
}
