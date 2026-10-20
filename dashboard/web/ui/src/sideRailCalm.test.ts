// @vitest-environment jsdom
/**
 * Calm home side rail (side-rail-home).
 *
 * R1: home side rail has no individual journal entry rows.
 * R2: Needs you and Backlog remain.
 * R3: repair/evaluate show one journal teaser with open count when known →
 *     navigates to journal screen.
 * R4: deliver/incidental show no teaser.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { flushSync, mount, unmount, type Component } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  EffortView,
  JournalResponse,
  Snapshot,
} from "./types";

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

function effort(
  partial: Partial<EffortView> & Pick<EffortView, "effort">,
): EffortView {
  return {
    goal: "",
    kind: "deliver",
    finished: false,
    phases: [],
    tasks: [],
    needs_you: [],
    backlog: [],
    ...partial,
  };
}

function makeSnapshot(efforts: EffortView[], token = "tok-1"): Snapshot {
  return { token, efforts, generated_at: "2026-01-01T00:00:00Z" };
}

function stubFetch(
  snap: Snapshot,
  journalByEffort: Record<string, JournalResponse> = {},
) {
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
      if (url.includes("/api/journal")) {
        const match = /[?&]effort=([^&]+)/.exec(url);
        const name = match ? decodeURIComponent(match[1]!) : "";
        const data = journalByEffort[name] ?? { open: [], rest: [] };
        return new Response(JSON.stringify(data), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
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

describe("side-rail-home calm rail", () => {
  it("R1: home side rail has no individual journal entry rows", async () => {
    expect(appSource).not.toMatch(/data-journal=\{/);
    expect(appSource).not.toContain("data-side-journal>");

    const journal: JournalResponse = {
      open: [
        {
          id: "j1",
          record_type: "project:finding",
          subject: "open-finding",
          open: true,
        },
      ],
      rest: [
        {
          id: "j2",
          record_type: "project:failed-attempt",
          subject: "closed",
          open: false,
        },
      ],
    };
    stubFetch(makeSnapshot([effort({ effort: "alpha", kind: "repair" })]), {
      alpha: journal,
    });
    if (!(await tryMountApp())) return;
    await vi.advanceTimersByTimeAsync(0);
    flushSync();

    expect(document.querySelectorAll("[data-journal]").length).toBe(0);
    expect(document.querySelector('[data-journal="j1"]')).toBeNull();
    expect(document.querySelector('[data-journal="j2"]')).toBeNull();
  });

  it("R2: Needs you and Backlog remain", async () => {
    expect(appSource).toContain("data-side-needs");
    expect(appSource).toContain("data-side-backlog");

    const alpha = effort({
      effort: "alpha",
      kind: "deliver",
      needs_you: [
        {
          kind: "blocking-question",
          id: "q1",
          subject: "decide",
          text: "which?",
        },
      ],
      backlog: [
        {
          id: "b1",
          subject: "park",
          text: "later",
          status: "open",
        },
      ],
    });
    stubFetch(makeSnapshot([alpha]));
    if (!(await tryMountApp())) return;

    expect(document.querySelector("[data-side-needs]")).toBeTruthy();
    expect(document.querySelector('[data-needs="q1"]')).toBeTruthy();
    expect(document.querySelector("[data-side-backlog]")).toBeTruthy();
    expect(document.querySelector('[data-backlog="b1"]')).toBeTruthy();
  });

  it("R3: repair/evaluate show one journal teaser with open count when known → navigates to journal screen", async () => {
    expect(appSource).toContain("data-journal-teaser");
    expect(appSource).toMatch(/#\/journal\//);

    const journal: JournalResponse = {
      open: [
        {
          id: "j-open",
          record_type: "project:finding",
          subject: "find-me",
          open: true,
        },
        {
          id: "j-open-2",
          record_type: "project:continuity-question",
          subject: "ask",
          open: true,
        },
      ],
      rest: [],
    };

    for (const kind of ["repair", "evaluate"] as const) {
      resetDocument();
      window.location.hash = "";
      const name = `eff-${kind}`;
      stubFetch(makeSnapshot([effort({ effort: name, kind })]), {
        [name]: journal,
      });
      if (!(await tryMountApp())) return;
      await vi.advanceTimersByTimeAsync(0);
      flushSync();

      const teasers = document.querySelectorAll("[data-journal-teaser]");
      expect(teasers.length).toBe(1);
      const teaser = teasers[0] as HTMLAnchorElement;
      expect(teaser.getAttribute("href")).toBe(`#/journal/${name}`);
      expect(teaser.textContent).toMatch(/2/);
      expect(teaser.textContent).toMatch(/open/i);

      teaser.click();
      flushSync();
      expect(window.location.hash).toBe(`#/journal/${name}`);
      // jsdom does not always emit hashchange when hash is assigned
      window.dispatchEvent(new HashChangeEvent("hashchange"));
      flushSync();
      expect(
        document.querySelector<HTMLElement>("main")?.dataset.route,
      ).toBe("journal");
    }
  });

  it("R4: deliver/incidental show no teaser", async () => {
    for (const kind of ["deliver", "incidental"] as const) {
      resetDocument();
      window.location.hash = "";
      stubFetch(
        makeSnapshot([effort({ effort: `eff-${kind}`, kind })]),
        {
          [`eff-${kind}`]: {
            open: [
              {
                id: "j1",
                record_type: "project:finding",
                subject: "x",
                open: true,
              },
            ],
            rest: [],
          },
        },
      );
      if (!(await tryMountApp())) return;
      await vi.advanceTimersByTimeAsync(0);
      flushSync();

      expect(document.querySelector("[data-journal-teaser]")).toBeNull();
      expect(document.querySelector("[data-side-journal-teaser]")).toBeNull();
    }
  });
});
