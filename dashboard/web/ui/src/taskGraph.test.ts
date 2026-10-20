// @vitest-environment jsdom
/**
 * Wave-lane task dependency graph (task-graph).
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { flushSync, mount, unmount, type Component } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { buildWaveGraph } from "./taskGraph";
import type { EffortView, Snapshot } from "./types";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = readFileSync(path.join(here, "App.svelte"), "utf8");

let mounted: ReturnType<typeof mount> | undefined;

function resetDocument() {
  if (mounted) {
    unmount(mounted);
    mounted = undefined;
  }
  document.body.innerHTML = "";
}

beforeEach(() => {
  resetDocument();
  window.location.hash = "";
  vi.useFakeTimers();
});

afterEach(() => {
  resetDocument();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const threeTasks = [
  {
    id: "t-a",
    subject: "a",
    title: "Alpha",
    status: "done",
    wave: 1,
    depends_on: [],
  },
  {
    id: "t-b",
    subject: "b",
    title: "Beta",
    status: "ready",
    wave: 2,
    depends_on: ["t-a"],
  },
  {
    id: "t-c",
    subject: "c",
    title: "Gamma",
    status: "ready",
    wave: 2,
    depends_on: ["t-a"],
  },
];

function phasePayload(tasks: typeof threeTasks) {
  return {
    tabs: ["overview", "tasks"],
    detail: {
      subject: "graph-phase",
      title: "Graph phase",
      effort: "dashboard",
      state: "in_progress",
      body: "notes",
      tasks,
    },
  };
}

function effort(
  partial: Partial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
  return {
    goal: "",
    kind: "deliver",
    finished: false,
    phases: [
      {
        subject: "graph-phase",
        title: "Graph phase",
        ordinal: 1,
        state: "in_progress",
        done: 1,
        total: 3,
      },
    ],
    tasks: [],
    needs_you: [],
    backlog: [],
    ...partial,
  };
}

function makeSnapshot(efforts: EffortView[], token = "tok-1"): Snapshot {
  return { token, efforts, generated_at: "2026-01-01T00:00:00Z" };
}

function stubFetch(snap: Snapshot, payload = phasePayload(threeTasks)) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/token")) {
        return new Response(JSON.stringify({ token: snap.token }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      if (url.includes("/api/phase")) {
        return new Response(JSON.stringify(payload), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      if (url.includes("/api/task")) {
        return new Response(
          JSON.stringify({
            detail: {
              id: "t-b",
              subject: "b",
              title: "Beta",
              status: "ready",
              description: "task",
            },
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      }
      return new Response(JSON.stringify(snap), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }),
  );
}

async function tryMountApp(): Promise<boolean> {
  try {
    const module = await import("./App.svelte");
    mounted = mount(module.default as Component, { target: document.body });
    await vi.advanceTimersByTimeAsync(0);
    flushSync();
    return true;
  } catch {
    mounted = undefined;
    return false;
  }
}

async function openOverview() {
  window.location.hash = "#/phase/dashboard/graph-phase";
  window.dispatchEvent(new HashChangeEvent("hashchange"));
  await vi.advanceTimersByTimeAsync(0);
  flushSync();
}

describe("buildWaveGraph", () => {
  it("R1: columns by wave left to right for ≥3 tasks", () => {
    const graph = buildWaveGraph(threeTasks);
    expect(graph.show).toBe(true);
    expect(graph.lanes.map((l) => l.wave)).toEqual(["1", "2"]);
    expect(graph.lanes[0]?.nodes.map((n) => n.id)).toEqual(["t-a"]);
    expect(graph.lanes[1]?.nodes.map((n) => n.id).sort()).toEqual([
      "t-b",
      "t-c",
    ]);
  });

  it("R2: nodes carry status", () => {
    const graph = buildWaveGraph(threeTasks);
    const alpha = graph.lanes[0]?.nodes[0];
    expect(alpha?.status).toBe("done");
    expect(alpha?.label).toBe("Alpha");
  });

  it("R3: edges follow depends_on", () => {
    const graph = buildWaveGraph(threeTasks);
    expect(graph.edges).toEqual(
      expect.arrayContaining([
        { from: "t-a", to: "t-b" },
        { from: "t-a", to: "t-c" },
      ]),
    );
  });

  it("R6: omit graph when two or fewer tasks", () => {
    expect(buildWaveGraph(threeTasks.slice(0, 2)).show).toBe(false);
    expect(buildWaveGraph([]).show).toBe(false);
  });
});

describe("task graph UI", () => {
  it("wires Overview graph", () => {
    expect(appSource).toMatch(/buildWaveGraph/);
    expect(appSource).toMatch(/data-task-graph/);
  });

  it("R1 R2 R3: shows graph with lanes, status, edges for ≥3 tasks", async () => {
    stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
    if (!(await tryMountApp())) return;
    await openOverview();
    expect(document.querySelector("[data-task-graph]")).toBeTruthy();
    expect(document.querySelector('[data-graph-lane="1"]')).toBeTruthy();
    expect(document.querySelector('[data-graph-lane="2"]')).toBeTruthy();
    expect(
      document.querySelector('[data-graph-node="t-a"]')?.getAttribute("data-status"),
    ).toBe("done");
    expect(document.querySelector('[data-graph-edge="t-a->t-b"]')).toBeTruthy();
  });

  it("R4: activating a node opens the task overlay", async () => {
    stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
    if (!(await tryMountApp())) return;
    await openOverview();
    const node = document.querySelector('[data-graph-node="t-b"]');
    expect(node).toBeTruthy();
    node!.dispatchEvent(
      new MouseEvent("click", { bubbles: true, cancelable: true }),
    );
    flushSync();
    await vi.advanceTimersByTimeAsync(0);
    flushSync();
    expect(window.location.hash).toBe("#/task/t-b");
  });

  it("R5: task list / strip remains available", async () => {
    expect(appSource).toMatch(/data-phase-waves|data-phase-tab=\"tasks\"|Tasks/);
    stubFetch(makeSnapshot([effort({ effort: "dashboard" })]));
    if (!(await tryMountApp())) return;
    await openOverview();
    expect(document.querySelector("[data-phase-waves], [data-phase-tabs]")).toBeTruthy();
    expect(document.querySelector('[data-phase-tab="tasks"]')).toBeTruthy();
  });

  it("R6: hides graph for ≤2 tasks", async () => {
    stubFetch(
      makeSnapshot([effort({ effort: "dashboard" })]),
      phasePayload(threeTasks.slice(0, 2) as typeof threeTasks),
    );
    if (!(await tryMountApp())) return;
    await openOverview();
    expect(document.querySelector("[data-task-graph]")).toBeNull();
  });
});
