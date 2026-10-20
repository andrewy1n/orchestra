import { describe, expect, it } from "vitest";

import { linkifyText, resolveRef, type RefContext } from "./links";
import type { EffortView, Snapshot } from "./types";

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
    milestones: [],
    ...partial,
  };
}

function snap(efforts: EffortView[]): Snapshot {
  return { token: "t1", efforts };
}

function ctx(
  snapshot: Snapshot,
  extra: Partial<RefContext> = {},
): RefContext {
  return { snapshot, effort: snapshot.efforts[0]?.effort ?? null, ...extra };
}

describe("resolveRef", () => {
  it("R4: record id resolves to the record overlay hash", () => {
    const id = "rec-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
    const resolved = resolveRef(id, ctx(snap([effort({ effort: "demo" })])));
    expect(resolved).not.toBeNull();
    expect(resolved!.kind).toBe("record");
    expect(resolved!.href).toBe(`#/record/${id}`);
  });

  it("R7: prefers title from snapshot or detail over the raw id", () => {
    const view = effort({
      effort: "demo",
      tasks: [
        {
          id: "t-cut",
          subject: "t-cut",
          title: "Cut task",
          phase: "p1",
          status: "ready",
        },
      ],
      phases: [
        {
          subject: "p1",
          title: "Phase One",
          ordinal: 1,
          state: "in_progress",
          done: 0,
          total: 1,
        },
      ],
      milestones: [
        {
          subject: "cutover",
          title: "Cutover",
          ordinal: 1,
          state: "planned",
          done: 0,
          total: 1,
        },
      ],
    });
    const c = ctx(snap([view]), { effort: "demo" });

    expect(resolveRef("t-cut", c)!.label).toBe("Cut task");
    expect(resolveRef("p1", c)!.label).toBe("Phase One");
    expect(resolveRef("cutover", c)!.label).toBe("Cutover");

    const rec = "rec-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
    const withDetail = resolveRef(
      rec,
      ctx(snap([view]), {
        effort: "demo",
        detail: { id: rec, title: "Signed decision", record_type: "decision" },
      }),
    );
    expect(withDetail!.label).toBe("Signed decision");
  });

  it("R8: unresolved tokens return null (stay plain)", () => {
    const c = ctx(snap([effort({ effort: "demo" })]), { effort: "demo" });
    expect(resolveRef("not-a-thing", c)).toBeNull();
    expect(resolveRef("R12", c)).toBeNull(); // requirement needs phase context
    expect(resolveRef("ordinary", c)).toBeNull();
  });

  it("builds task, phase, requirement, and milestone hrefs", () => {
    const view = effort({
      effort: "demo",
      tasks: [
        {
          id: "t1",
          subject: "t1",
          title: "T",
          phase: "p1",
          status: "ready",
        },
      ],
      phases: [
        {
          subject: "p1",
          title: "P",
          ordinal: 1,
          state: "planned",
          done: 0,
          total: 1,
        },
      ],
      milestones: [
        {
          subject: "m1",
          title: "M",
          ordinal: 1,
          state: "planned",
          done: 0,
          total: 1,
        },
      ],
    });
    const c = ctx(snap([view]), { effort: "demo", phase: "p1" });

    expect(resolveRef("t1", c)!.href).toBe("#/task/t1");
    expect(resolveRef("p1", c)!.href).toBe("#/phase/demo/p1");
    expect(resolveRef("R3", c)!.href).toBe("#/requirement/demo/p1/R3");
    expect(resolveRef("m1", c)!.kind).toBe("milestone");
    expect(resolveRef("m1", c)!.href).toContain("milestone");
  });
});

describe("linkifyText", () => {
  it("R8: leaves unresolved prose unchanged", () => {
    const c = ctx(snap([effort({ effort: "demo" })]), { effort: "demo" });
    expect(linkifyText("see ordinary words here", c)).toBe(
      "see ordinary words here",
    );
  });

  it("wraps a known record id in an anchor", () => {
    const id = "rec-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
    const c = ctx(snap([effort({ effort: "demo" })]));
    const html = linkifyText(`see ${id} please`, c, (s) => s);
    expect(html).toContain(`href="#/record/${id}"`);
    expect(html).toContain("data-ref=\"record\"");
  });
});
