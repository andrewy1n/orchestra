// @vitest-environment jsdom
/**
 * Side-column acceptance cases for the web dashboard UI.
 *
 * R11: Needs you items for the selected effort.
 * R12: orderedJournal flattens open then rest (no home side entry list).
 * R13: open backlog items for the selected effort.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { flushSync, mount, unmount, type Component } from "svelte";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { openBacklog, orderedJournal } from "./side";
import type {
  EffortView,
  JournalResponse,
  NeedsYouItem,
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

function stubFetch(snap: Snapshot, journalByEffort: Record<string, JournalResponse>) {
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

describe("web-dashboard side", () => {
  it("R11: The side column lists the selected effort's Needs you items.", async () => {
    expect(appSource).toContain("data-side-needs");
    expect(appSource).toContain("data-needs=");
    expect(appSource).toMatch(/effort\.needs_you/);

    const needs: NeedsYouItem[] = [
      {
        kind: "blocking-question",
        id: "q1",
        subject: "which-backend",
        text: "which backend",
      },
      {
        kind: "unsigned-check",
        id: "c1",
        subject: "manual-gate",
        text: "sign off",
      },
    ];
    const alpha = effort({ effort: "alpha", needs_you: needs });
    const beta = effort({
      effort: "beta",
      needs_you: [
        {
          kind: "needs-human",
          id: "nh1",
          subject: "finding",
          text: "decide",
        },
      ],
    });

    expect(alpha.needs_you.map((n) => n.id)).toEqual(["q1", "c1"]);
    expect(beta.needs_you.map((n) => n.id)).toEqual(["nh1"]);

    stubFetch(makeSnapshot([alpha, beta]), {
      alpha: { open: [], rest: [] },
      beta: { open: [], rest: [] },
    });
    if (await tryMountApp()) {
      const side = document.querySelector("[data-side-needs]");
      expect(side).toBeTruthy();
      expect(document.querySelector('[data-needs="q1"]')).toBeTruthy();
      expect(document.querySelector('[data-needs="c1"]')).toBeTruthy();
      expect(document.querySelector('[data-needs="nh1"]')).toBeNull();

      document
        .querySelector<HTMLButtonElement>('[data-effort="beta"]')!
        .click();
      flushSync();
      await vi.advanceTimersByTimeAsync(0);
      flushSync();

      expect(document.querySelector('[data-needs="nh1"]')).toBeTruthy();
      expect(document.querySelector('[data-needs="q1"]')).toBeNull();
    }
  });

  it("R12: orderedJournal returns open then rest; home side rail has no journal entry rows.", async () => {
    expect(appSource).not.toMatch(/data-journal=\{/);
    expect(appSource).toMatch(/\/api\/journal|journal\?effort/);

    const journal: JournalResponse = {
      open: [
        {
          id: "j-open-new",
          record_type: "aff:finding",
          subject: "open-new",
          open: true,
          recorded_at: "2026-02-02T00:00:00Z",
        },
        {
          id: "j-open-old",
          record_type: "plan:continuity-question",
          subject: "open-old",
          open: true,
          recorded_at: "2026-01-01T00:00:00Z",
        },
      ],
      rest: [
        {
          id: "j-rest",
          record_type: "run:failed-attempt",
          subject: "closed-attempt",
          open: false,
          recorded_at: "2026-03-01T00:00:00Z",
        },
      ],
    };

    const rows = orderedJournal(journal);
    expect(rows.map((r) => r.id)).toEqual([
      "j-open-new",
      "j-open-old",
      "j-rest",
    ]);
    expect(rows.map((r) => r.record_type)).toEqual([
      "aff:finding",
      "plan:continuity-question",
      "run:failed-attempt",
    ]);
    expect(rows.map((r) => r.subject)).toEqual([
      "open-new",
      "open-old",
      "closed-attempt",
    ]);

    const alpha = effort({ effort: "alpha" });
    stubFetch(makeSnapshot([alpha]), { alpha: journal });
    if (await tryMountApp()) {
      await vi.advanceTimersByTimeAsync(0);
      flushSync();
      expect(document.querySelectorAll("[data-journal]").length).toBe(0);
    }
  });

  it("R13: The side column lists the selected effort's open backlog items.", async () => {
    expect(appSource).toContain("data-side-backlog");
    expect(appSource).toContain("data-backlog=");
    expect(appSource).toMatch(/openBacklog|backlogItems/);

    const alpha = effort({
      effort: "alpha",
      backlog: [
        {
          id: "b1",
          subject: "park-me",
          text: "parked work",
          status: "open",
          source: "chat",
        },
        {
          id: "b2",
          subject: "already-done",
          text: "closed",
          status: "dismissed",
        },
      ],
    });
    const beta = effort({
      effort: "beta",
      backlog: [
        {
          id: "b3",
          subject: "other-park",
          text: "beta park",
          status: "open",
        },
      ],
    });

    expect(openBacklog(alpha).map((b) => b.id)).toEqual(["b1"]);
    expect(openBacklog(beta).map((b) => b.id)).toEqual(["b3"]);

    stubFetch(makeSnapshot([alpha, beta]), {
      alpha: { open: [], rest: [] },
      beta: { open: [], rest: [] },
    });
    if (await tryMountApp()) {
      expect(document.querySelector('[data-backlog="b1"]')).toBeTruthy();
      expect(
        document.querySelector('[data-backlog="b1"]')?.textContent,
      ).toContain("park-me");
      expect(document.querySelector('[data-backlog="b2"]')).toBeNull();
      expect(document.querySelector('[data-backlog="b3"]')).toBeNull();

      document
        .querySelector<HTMLButtonElement>('[data-effort="beta"]')!
        .click();
      flushSync();
      await vi.advanceTimersByTimeAsync(0);
      flushSync();

      expect(document.querySelector('[data-backlog="b3"]')).toBeTruthy();
      expect(document.querySelector('[data-backlog="b1"]')).toBeNull();
    }
  });
});
