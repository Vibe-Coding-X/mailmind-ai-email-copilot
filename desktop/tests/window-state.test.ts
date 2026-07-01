import test from "node:test";
import assert from "node:assert/strict";
import * as os from "node:os";
import * as path from "node:path";
import * as fs from "node:fs";

import {
  type WindowBounds,
  loadWindowState,
  saveWindowState,
} from "../src/window-state";

function createTempDir(): string {
  return fs.mkdtempSync(path.join(os.tmpdir(), "mailmind-window-state-"));
}

function cleanupTempDir(dir: string): void {
  fs.rmSync(dir, { recursive: true, force: true });
}

test("loadWindowState returns defaults when file is missing", () => {
  const userDataPath = createTempDir();

  try {
    const state = loadWindowState(userDataPath);
    assert.equal(state.width, 1280);
    assert.equal(state.height, 860);
    assert.equal(state.isMaximized, false);
    assert.equal("x" in state, false);
    assert.equal("y" in state, false);
  } finally {
    cleanupTempDir(userDataPath);
  }
});

test("saveWindowState persists bounds and maximized state", () => {
  const userDataPath = createTempDir();
  const expected: WindowBounds = {
    x: 120,
    y: 80,
    width: 1440,
    height: 900,
    isMaximized: true,
  };

  try {
    saveWindowState(userDataPath, expected);
    const actual = loadWindowState(userDataPath);
    assert.deepEqual(actual, expected);
  } finally {
    cleanupTempDir(userDataPath);
  }
});
