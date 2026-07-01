import test from "node:test";
import assert from "node:assert/strict";

import { type ConnectionTransition, getConnectionTransition } from "../src/connection-state";

test("getConnectionTransition returns recovered when backend becomes reachable", () => {
  const transition = getConnectionTransition(false, true);
  assert.equal(transition, "recovered");
});

test("getConnectionTransition does not notify on first failed startup check", () => {
  const transition = getConnectionTransition(null, false);
  assert.equal(transition, "none");
});

test("getConnectionTransition returns lost when backend becomes unreachable", () => {
  const transition: ConnectionTransition = getConnectionTransition(true, false);
  assert.equal(transition, "lost");
});
